from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from prompt_builder.gui.clickfix import lower_frame_canvases
from prompt_builder.gui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BORDER,
    MUTED,
    SURFACE,
    TEXT,
    ui_font,
)


class HomeScreen(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        on_builder: Callable[[], None],
        on_qa: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Что нужно сделать?",
            font=ui_font(28, "bold"),
            text_color=TEXT,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=32, pady=(28, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Выберите режим. Проверка таблиц доступна только в визуальной версии.",
            font=ui_font(14),
            text_color=MUTED,
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", padx=32, pady=(0, 8))

        builder_card = _ModeCard(
            self,
            title="Сборка промпта",
            description="Выберите авто, категорию и раздел.\nГотовый промпт копируется в буфер обмена.",
            action="Открыть сборку",
            on_click=on_builder,
        )
        builder_card.grid(row=2, column=0, sticky="nsew", padx=(32, 12), pady=(20, 32))

        qa_card = _ModeCard(
            self,
            title="Проверка таблиц",
            description="Откройте MD-таблицу и проверьте поле summary:\nровно 4 абзаца, разделённых <br><br>.",
            action="Открыть проверку",
            on_click=on_qa,
        )
        qa_card.grid(row=2, column=1, sticky="nsew", padx=(12, 32), pady=(20, 32))


class _ModeCard(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        title: str,
        description: str,
        action: str,
        on_click: Callable[[], None],
    ) -> None:
        super().__init__(
            master,
            fg_color=SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
        )
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=ui_font(22, "bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=28, pady=(28, 8))

        ctk.CTkLabel(
            self,
            text=description,
            font=ui_font(14),
            text_color=MUTED,
            justify="left",
            anchor="nw",
        ).grid(row=1, column=0, sticky="new", padx=28, pady=(0, 16))

        ctk.CTkButton(
            self,
            text=action,
            font=ui_font(14, "bold"),
            height=42,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=on_click,
        ).grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 28))
        lower_frame_canvases(self)
