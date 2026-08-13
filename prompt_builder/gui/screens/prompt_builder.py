from __future__ import annotations

import customtkinter as ctk

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
    ui_font,
)
from prompt_builder.gui.widgets import SelectableList
from prompt_builder.models import CATEGORY_LABELS, Car, Category, PromptSection, Selection
from prompt_builder.parsers.prompts import sections_for_category
from prompt_builder.services.clipboard import ClipboardError, copy_to_clipboard
from prompt_builder.services.prompt_builder import build_prompt


class PromptBuilderScreen(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        cars: list[Car],
        sections: list[PromptSection],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._cars = cars
        self._sections = sections
        self._category: Category = "repair"
        self._car: Car | None = None
        self._section: PromptSection | None = None

        self.grid_columnconfigure(0, weight=0, minsize=340)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_car_pane()
        self._build_work_pane()
        self._refresh_cars()
        self._refresh_sections()
        self._refresh_preview()

    def _build_car_pane(self) -> None:
        pane = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=16)
        pane.grid(row=0, column=0, sticky="nsew", padx=(24, 12), pady=20)
        pane.grid_rowconfigure(2, weight=1)
        pane.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            pane,
            text="Автомобиль",
            font=ui_font(16, "bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        self._search = ctk.CTkEntry(
            pane,
            placeholder_text="Поиск по марке, модели, мотору…",
            font=ui_font(13),
            height=36,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
        )
        self._search.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self._search.bind("<KeyRelease>", lambda _event: self._refresh_cars())

        self._car_list = SelectableList(pane, on_select=self._on_car_selected)
        self._car_list.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 16))

    def _build_work_pane(self) -> None:
        pane = ctk.CTkFrame(self, fg_color="transparent")
        pane.grid(row=0, column=1, sticky="nsew", padx=(12, 24), pady=20)
        pane.grid_columnconfigure(0, weight=1)
        pane.grid_rowconfigure(3, weight=1)

        top = ctk.CTkFrame(pane, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top,
            text="Категория",
            font=ui_font(16, "bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w")

        self._category_control = ctk.CTkSegmentedButton(
            top,
            values=[CATEGORY_LABELS["repair"], CATEGORY_LABELS["tuning"]],
            command=self._on_category_change,
            font=ui_font(13),
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=SURFACE,
            unselected_hover_color=SURFACE_ALT,
            height=36,
        )
        self._category_control.set(CATEGORY_LABELS[self._category])
        self._category_control.grid(row=0, column=1, sticky="e", padx=(12, 0))

        ctk.CTkLabel(
            pane,
            text="Раздел",
            font=ui_font(16, "bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(16, 8))

        self._section_list = SelectableList(pane, on_select=self._on_section_selected)
        self._section_list.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self._section_list.configure(height=180)

        preview_frame = ctk.CTkFrame(pane, fg_color=SURFACE, corner_radius=16)
        preview_frame.grid(row=3, column=0, sticky="nsew")
        preview_frame.grid_rowconfigure(1, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_frame,
            text="Превью промпта",
            font=ui_font(16, "bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        self._preview = ctk.CTkTextbox(
            preview_frame,
            font=ui_font(13),
            fg_color=SURFACE_ALT,
            text_color=TEXT,
            wrap="word",
            activate_scrollbars=True,
        )
        self._preview.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self._preview.configure(state="disabled")

        actions = ctk.CTkFrame(pane, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        actions.grid_columnconfigure(0, weight=1)

        self._status = ctk.CTkLabel(
            actions,
            text="Выберите авто и раздел",
            font=ui_font(13),
            text_color=MUTED,
            anchor="w",
        )
        self._status.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        buttons = ctk.CTkFrame(actions, fg_color="transparent")
        buttons.grid(row=1, column=0, sticky="ew")

        self._copy_button = ctk.CTkButton(
            buttons,
            text="Скопировать в буфер",
            font=ui_font(14, "bold"),
            height=40,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._copy,
        )
        self._copy_button.pack(side="left")

    def _refresh_cars(self) -> None:
        query = self._search.get().strip().lower()
        items: list[tuple[str, Car]] = []
        for car in self._cars:
            label = car.display()
            if query and query not in label.lower():
                continue
            items.append((label, car))
        selected = self._car if self._car in {item[1] for item in items} else None
        if selected is None:
            self._car = None
        self._car_list.set_items(items, selected=selected)
        self._refresh_preview()

    def _refresh_sections(self) -> None:
        category_sections = sections_for_category(self._sections, self._category)
        items = [(section.display(), section) for section in category_sections]
        selected = self._section if self._section in {item[1] for item in items} else None
        if selected is None:
            self._section = None
        self._section_list.set_items(items, selected=selected)

    def _on_car_selected(self, car: Car) -> None:
        self._car = car
        self._set_status(f"Авто: {car.display()}", MUTED)
        self._refresh_preview()

    def _on_section_selected(self, section: PromptSection) -> None:
        self._section = section
        self._refresh_preview()

    def _on_category_change(self, label: str) -> None:
        self._category = "repair" if label == CATEGORY_LABELS["repair"] else "tuning"
        self._section = None
        self._refresh_sections()
        self._refresh_preview()

    def _current_prompt(self) -> str | None:
        if self._car is None or self._section is None:
            return None
        return build_prompt(self._section.template, self._car)

    def _refresh_preview(self) -> None:
        prompt = self._current_prompt()
        self._preview.configure(state="normal")
        self._preview.delete("1.0", "end")
        if prompt is None:
            self._preview.insert("1.0", "Выберите автомобиль и раздел — здесь появится готовый промпт.")
            self._copy_button.configure(state="disabled")
        else:
            self._preview.insert("1.0", prompt)
            self._copy_button.configure(state="normal")
        self._preview.configure(state="disabled")

    def _copy(self) -> None:
        prompt = self._current_prompt()
        if prompt is None or self._car is None or self._section is None:
            self._set_status("Сначала выберите авто и раздел", DANGER)
            return
        try:
            copy_to_clipboard(prompt)
        except ClipboardError as exc:
            self._set_status(f"Не удалось скопировать: {exc}", DANGER)
            return

        selection = Selection(car=self._car, section=self._section)
        self._set_status(
            f"Промпт скопирован · {selection.car.display()} · {selection.category_label} · {selection.section.display()}",
            SUCCESS,
        )

    def _set_status(self, text: str, color: str) -> None:
        self._status.configure(text=text, text_color=color)
