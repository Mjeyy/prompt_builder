from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from prompt_builder.gui.theme import MUTED, TEXT, ui_font
from prompt_builder.gui.widgets import ModeCard
from prompt_builder.models import BUILDER_LABEL, TABLE_QA_LABEL, WORK_MODE_LABELS


class HomeScreen(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        on_builder: Callable[[], None],
        on_qa: Callable[[], None],
        on_horoscope_auto: Callable[[], None],
        on_horoscope_date: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Что нужно сделать?",
            font=ui_font(28, "bold"),
            text_color=TEXT,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=32, pady=(20, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Выберите режим. Проверка таблиц доступна только в визуальной версии.",
            font=ui_font(14),
            text_color=MUTED,
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", padx=32, pady=(0, 8))

        builder_card = ModeCard(
            self,
            title=BUILDER_LABEL,
            description="Авто, категория и раздел.\nВ буфер — только кнопка «Скопировать в буфер».",
            action="Открыть сборку",
            on_click=on_builder,
        )
        builder_card.grid(row=2, column=0, sticky="nsew", padx=(32, 12), pady=(12, 8))

        qa_card = ModeCard(
            self,
            title=TABLE_QA_LABEL,
            description="Откройте MD-таблицу и проверьте поле summary:\nровно 4 абзаца, разделённых <br><br>.",
            action="Открыть проверку",
            on_click=on_qa,
        )
        qa_card.grid(row=2, column=1, sticky="nsew", padx=(12, 32), pady=(12, 8))

        horoscope_auto_card = ModeCard(
            self,
            title=WORK_MODE_LABELS["horoscope_auto"],
            description="Марка и модель из списка авто.\nВ буфер — только кнопка «Скопировать в буфер».",
            action="Открыть описание",
            on_click=on_horoscope_auto,
        )
        horoscope_auto_card.grid(row=3, column=0, sticky="nsew", padx=(32, 12), pady=(8, 24))

        horoscope_date_card = ModeCard(
            self,
            title=WORK_MODE_LABELS["horoscope_date"],
            description="Авто, дата старта по календарю и число дней.\nВ буфер — только кнопка «Скопировать в буфер».",
            action="Открыть прогноз",
            on_click=on_horoscope_date,
        )
        horoscope_date_card.grid(row=3, column=1, sticky="nsew", padx=(12, 32), pady=(8, 24))
