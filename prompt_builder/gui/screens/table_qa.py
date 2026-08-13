from __future__ import annotations

import shutil
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from prompt_builder.gui import PROJECT_ROOT
from prompt_builder.gui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BORDER,
    DANGER,
    MUTED,
    SUCCESS,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    WARNING,
    ui_font,
)
from prompt_builder.services.table_file import (
    EXPECTED_PARAGRAPHS,
    MarkdownTable,
    SummaryError,
    editor_to_summary,
    find_summary_errors,
    fixed_copy_path,
    load_table,
    paragraph_count,
    row_summary,
    save_table,
    set_row_summary,
    summary_to_editor,
)

DOCS_DIR = PROJECT_ROOT / "docs"


class TableQaScreen(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame) -> None:
        super().__init__(master, fg_color="transparent")
        self._table: MarkdownTable | None = None
        self._source_path: Path | None = None
        self._working_path: Path | None = None
        self._errors: list[SummaryError] = []
        self._error_index = 0
        self._mode = "idle"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_toolbar()
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self._body.grid_columnconfigure(0, weight=1)
        self._body.grid_rowconfigure(0, weight=1)
        self._show_idle()

    def _build_toolbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            bar,
            text="Открыть файл",
            font=ui_font(13, "bold"),
            height=36,
            width=140,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._open_file,
        ).grid(row=0, column=0, sticky="w")

        self._file_label = ctk.CTkLabel(
            bar,
            text="Файл не выбран",
            font=ui_font(13),
            text_color=MUTED,
            anchor="e",
        )
        self._file_label.grid(row=0, column=1, sticky="e", padx=(16, 0))

    def _clear_body(self) -> None:
        for child in self._body.winfo_children():
            child.destroy()

    def _show_idle(self) -> None:
        self._mode = "idle"
        self._clear_body()
        card = ctk.CTkFrame(self._body, fg_color=SURFACE, corner_radius=16)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, pady=80)

        ctk.CTkLabel(
            inner,
            text="Проверка поля Summary",
            font=ui_font(24, "bold"),
            text_color=TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text=(
                "Откройте локальный MD-файл с таблицей статей.\n"
                "Ошибка — если в summary меньше или больше 4 абзацев,\n"
                "разделённых тегом <br><br>."
            ),
            font=ui_font(14),
            text_color=MUTED,
            justify="left",
        ).pack(anchor="w", pady=(12, 20))
        ctk.CTkButton(
            inner,
            text="Выбрать MD-файл",
            font=ui_font(14, "bold"),
            height=42,
            width=200,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._open_file,
        ).pack(anchor="w")

    def _open_file(self) -> None:
        initial = str(DOCS_DIR if DOCS_DIR.is_dir() else PROJECT_ROOT)
        chosen = filedialog.askopenfilename(
            title="Открыть таблицу",
            initialdir=initial,
            filetypes=[("Markdown", "*.md"), ("Все файлы", "*.*")],
        )
        if not chosen:
            return
        self._load_path(Path(chosen), as_new_open=True)

    def _update_file_label(self) -> None:
        if self._source_path is None:
            self._file_label.configure(text="Файл не выбран", text_color=MUTED)
            return
        if self._working_path is not None and self._working_path != self._source_path:
            text = f"Исходный: {self._source_path.name}  ·  правки: {self._working_path.name}"
        else:
            text = f"Исходный: {self._source_path.name}"
        self._file_label.configure(text=text, text_color=TEXT)

    def _load_path(self, path: Path, *, as_new_open: bool) -> None:
        try:
            table = load_table(path)
            errors = find_summary_errors(table)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Не удалось открыть файл", str(exc), parent=self.winfo_toplevel())
            return
        self._table = table
        self._errors = errors
        self._error_index = 0
        if as_new_open:
            self._source_path = path
            self._working_path = path if path == fixed_copy_path(path) else None
        self._update_file_label()
        self._show_results()

    def _rescan(self) -> None:
        path = self._working_path or self._source_path
        if path is None:
            return
        self._load_path(path, as_new_open=False)

    def _prepare_working_copy(self) -> bool:
        if self._source_path is None:
            return False
        if self._working_path is not None:
            return True
        dest = fixed_copy_path(self._source_path)
        try:
            if dest.resolve() != self._source_path.resolve():
                shutil.copy2(self._source_path, dest)
            table = load_table(dest)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Не удалось создать копию", str(exc), parent=self.winfo_toplevel())
            return False
        self._working_path = dest
        self._table = table
        self._errors = find_summary_errors(table)
        self._update_file_label()
        return True

    def _show_results(self) -> None:
        if self._table is None:
            return
        self._mode = "results"
        self._clear_body()
        error_count = len(self._errors)
        is_ok = error_count == 0

        card = ctk.CTkFrame(self._body, fg_color=SURFACE, corner_radius=16)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="n", pady=64)

        ctk.CTkLabel(
            inner,
            text="Результат сканирования",
            font=ui_font(14),
            text_color=MUTED,
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text=str(error_count),
            font=ui_font(64, "bold"),
            text_color=SUCCESS if is_ok else DANGER,
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            inner,
            text="ошибок в поле summary" if error_count != 1 else "ошибка в поле summary",
            font=ui_font(18, "bold"),
            text_color=TEXT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text=(
                f"{len(self._table.rows)} статей · нужно ровно {EXPECTED_PARAGRAPHS} абзаца, "
                "разделённых <br><br>"
            ),
            font=ui_font(14),
            text_color=MUTED,
        ).pack(anchor="w", pady=(8, 24))

        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(anchor="w")

        edit_button = ctk.CTkButton(
            actions,
            text="Режим редактирования",
            font=ui_font(14, "bold"),
            height=42,
            width=220,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._start_editing,
            state="normal" if error_count else "disabled",
        )
        edit_button.pack(side="left")

        ctk.CTkButton(
            actions,
            text="Повторить сканирование",
            font=ui_font(13),
            height=42,
            width=200,
            fg_color=SURFACE_ALT,
            hover_color=BORDER,
            command=self._rescan,
        ).pack(side="left", padx=(8, 0))

        if is_ok:
            ctk.CTkLabel(
                inner,
                text="Проверка пройдена: во всех статьях ровно 4 абзаца.",
                font=ui_font(14),
                text_color=SUCCESS,
            ).pack(anchor="w", pady=(20, 0))

    def _start_editing(self) -> None:
        if not self._errors:
            return
        if not self._prepare_working_copy():
            return
        self._error_index = 0
        self._show_editor()

    def _show_editor(self) -> None:
        if self._table is None or not self._errors:
            self._show_results()
            return
        if self._error_index >= len(self._errors):
            self._on_queue_done()
            return

        self._mode = "edit"
        self._clear_body()
        error = self._errors[self._error_index]
        summary = row_summary(self._table, error.row_index)
        count = paragraph_count(summary)

        layout = ctk.CTkFrame(self._body, fg_color="transparent")
        layout.grid(row=0, column=0, sticky="nsew")
        layout.grid_columnconfigure(0, weight=1)
        layout.grid_rowconfigure(2, weight=1)

        meta = ctk.CTkFrame(layout, fg_color=SURFACE, corner_radius=16)
        meta.grid(row=0, column=0, sticky="ew")
        meta.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            meta,
            text=f"Ошибка {self._error_index + 1} из {len(self._errors)}",
            font=ui_font(14, "bold"),
            text_color=ACCENT,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 0))

        self._count_badge = ctk.CTkLabel(
            meta,
            text=self._count_label(count),
            font=ui_font(13, "bold"),
            text_color=SUCCESS if count == EXPECTED_PARAGRAPHS else DANGER,
        )
        self._count_badge.grid(row=0, column=1, sticky="e", padx=20, pady=(16, 0))

        ctk.CTkLabel(
            meta,
            text=f"Строка {error.line_no}  ·  Статья: {error.topic_title}",
            font=ui_font(16, "bold"),
            text_color=TEXT,
            wraplength=860,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(8, 0))

        ctk.CTkLabel(
            meta,
            text=f"Авто: {error.car_label}",
            font=ui_font(13),
            text_color=MUTED,
            anchor="w",
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(4, 16))

        hint = ctk.CTkLabel(
            layout,
            text="Абзацы разделяйте пустой строкой. Это соответствует тегу <br><br> в файле.",
            font=ui_font(13),
            text_color=MUTED,
            anchor="w",
        )
        hint.grid(row=1, column=0, sticky="ew", pady=(12, 8))

        self._editor = ctk.CTkTextbox(
            layout,
            font=ui_font(14),
            fg_color=SURFACE,
            text_color=TEXT,
            wrap="word",
            border_width=1,
            border_color=BORDER,
        )
        self._editor.grid(row=2, column=0, sticky="nsew")
        self._editor.insert("1.0", summary_to_editor(summary))
        self._editor.bind("<KeyRelease>", lambda _event: self._update_count_badge())

        actions = ctk.CTkFrame(layout, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 0))

        ctk.CTkButton(
            actions,
            text="Сохранить и далее",
            font=ui_font(14, "bold"),
            height=42,
            width=200,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._save_and_next,
        ).pack(side="left")

        ctk.CTkLabel(
            actions,
            text="Сохраняется копия *_fix.md. Исходный файл не меняется.",
            font=ui_font(12),
            text_color=MUTED,
        ).pack(side="left", padx=(16, 0))

    def _count_label(self, count: int) -> str:
        if count == EXPECTED_PARAGRAPHS:
            return f"Абзацев: {count} · норма"
        return f"Абзацев: {count} · нужно {EXPECTED_PARAGRAPHS}"

    def _update_count_badge(self) -> None:
        summary = editor_to_summary(self._editor.get("1.0", "end-1c"))
        count = paragraph_count(summary)
        color = SUCCESS if count == EXPECTED_PARAGRAPHS else (WARNING if count > 0 else DANGER)
        self._count_badge.configure(text=self._count_label(count), text_color=color)

    def _save_and_next(self) -> None:
        if self._table is None or self._error_index >= len(self._errors):
            return
        summary = editor_to_summary(self._editor.get("1.0", "end-1c"))
        count = paragraph_count(summary)
        if count != EXPECTED_PARAGRAPHS:
            messagebox.showwarning(
                "Пока нельзя сохранить",
                f"Сейчас абзацев: {count}. Нужно ровно {EXPECTED_PARAGRAPHS}, "
                "разделённых пустой строкой.",
                parent=self.winfo_toplevel(),
            )
            return

        error = self._errors[self._error_index]
        set_row_summary(self._table, error.row_index, summary)
        if self._working_path is None:
            return
        try:
            save_table(self._table, self._working_path)
        except OSError as exc:
            messagebox.showerror("Не удалось сохранить", str(exc), parent=self.winfo_toplevel())
            return

        self._error_index += 1
        if self._error_index >= len(self._errors):
            self._on_queue_done()
            return
        self._show_editor()

    def _on_queue_done(self) -> None:
        self._mode = "done"
        messagebox.showinfo(
            "Ошибок в очереди больше нет",
            "Все найденные ошибки просмотрены.\n"
            "Повторите сканирование копии, чтобы убедиться, что ошибок 0.",
            parent=self.winfo_toplevel(),
        )
        self._show_done()

    def _show_done(self) -> None:
        self._clear_body()
        card = ctk.CTkFrame(self._body, fg_color=SURFACE, corner_radius=16)
        card.grid(row=0, column=0, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, pady=80)

        ctk.CTkLabel(
            inner,
            text="Очередь ошибок пройдена",
            font=ui_font(24, "bold"),
            text_color=TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text="Правки записаны в копию *_fix.md. Повторите сканирование — ожидаемый результат: 0 ошибок.",
            font=ui_font(14),
            text_color=MUTED,
        ).pack(anchor="w", pady=(12, 24))
        ctk.CTkButton(
            inner,
            text="Повторить сканирование",
            font=ui_font(14, "bold"),
            height=42,
            width=240,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._rescan,
        ).pack(anchor="w")
