from __future__ import annotations

import calendar
from collections.abc import Callable, Sequence
from datetime import date
from typing import Any, TypeVar

import customtkinter as ctk

from prompt_builder.gui.clickfix import lower_frame_canvases
from prompt_builder.gui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BORDER,
    MUTED,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    ui_font,
)

T = TypeVar("T")


class SelectableList(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master: Any,
        on_select: Callable[[T], None],
        empty_text: str = "Ничего не найдено",
        **kwargs: object,
    ) -> None:
        super().__init__(master, fg_color=SURFACE, corner_radius=12, **kwargs)
        self._on_select = on_select
        self._empty_text = empty_text
        self._items: list[tuple[str, T]] = []
        self._selected: T | None = None
        self._buttons: list[ctk.CTkButton] = []

    @property
    def selected(self) -> T | None:
        return self._selected

    def set_items(self, items: Sequence[tuple[str, T]], selected: T | None = None) -> None:
        self._items = list(items)
        self._selected = selected
        self._rebuild()

    def select(self, value: T | None) -> None:
        self._selected = value
        self._refresh_styles()

    def clear_selection(self) -> None:
        self._selected = None
        self._refresh_styles()

    def _rebuild(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._buttons = []

        if not self._items:
            ctk.CTkLabel(
                self,
                text=self._empty_text,
                text_color=MUTED,
                font=ui_font(13),
                anchor="w",
            ).pack(fill="x", padx=12, pady=16)
            return

        for label, value in self._items:
            button = ctk.CTkButton(
                self,
                text=label,
                anchor="w",
                height=36,
                corner_radius=8,
                font=ui_font(13),
                fg_color="transparent",
                hover_color=SURFACE_ALT,
                text_color=TEXT,
                command=lambda current=value: self._handle_click(current),
            )
            button.pack(fill="x", padx=6, pady=2)
            self._buttons.append(button)
        self._refresh_styles()

    def _handle_click(self, value: T) -> None:
        self._selected = value
        self._refresh_styles()
        self._on_select(value)

    def _refresh_styles(self) -> None:
        for button, (_label, value) in zip(self._buttons, self._items, strict=True):
            if value == self._selected:
                button.configure(fg_color=ACCENT, hover_color=ACCENT, text_color="#ffffff")
            else:
                button.configure(fg_color="transparent", hover_color=SURFACE_ALT, text_color=TEXT)


_MONTHS_RU = (
    "",
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)
_WEEKDAYS_RU = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


class MonthCalendar(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        on_change: Callable[[date], None],
        selected: date | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(
            master,
            fg_color=SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        self._on_change = on_change
        self._selected = selected or date.today()
        self._year = self._selected.year
        self._month = self._selected.month
        self._day_buttons: list[ctk.CTkButton] = []

        for col in range(7):
            self.grid_columnconfigure(col, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=7, sticky="ew", padx=10, pady=(10, 6))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            header,
            text="‹",
            width=36,
            height=32,
            font=ui_font(16, "bold"),
            fg_color=SURFACE_ALT,
            hover_color=ACCENT_HOVER,
            command=self._prev_month,
        ).grid(row=0, column=0, sticky="w")

        self._month_label = ctk.CTkLabel(
            header,
            text="",
            font=ui_font(14, "bold"),
            text_color=TEXT,
        )
        self._month_label.grid(row=0, column=1, sticky="ew", padx=8)

        ctk.CTkButton(
            header,
            text="›",
            width=36,
            height=32,
            font=ui_font(16, "bold"),
            fg_color=SURFACE_ALT,
            hover_color=ACCENT_HOVER,
            command=self._next_month,
        ).grid(row=0, column=2, sticky="e")

        for col, name in enumerate(_WEEKDAYS_RU):
            ctk.CTkLabel(
                self,
                text=name,
                font=ui_font(11),
                text_color=MUTED,
            ).grid(row=1, column=col, pady=(0, 4))

        self._days_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._days_frame.grid(row=2, column=0, columnspan=7, sticky="ew", padx=8, pady=(0, 10))
        for col in range(7):
            self._days_frame.grid_columnconfigure(col, weight=1)

        self._rebuild_days()

    @property
    def selected(self) -> date:
        return self._selected

    def _shift_month(self, delta: int) -> None:
        month = self._month + delta
        year = self._year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        self._month = month
        self._year = year
        self._rebuild_days()

    def _prev_month(self) -> None:
        self._shift_month(-1)

    def _next_month(self) -> None:
        self._shift_month(1)

    def _rebuild_days(self) -> None:
        for child in self._days_frame.winfo_children():
            child.destroy()
        self._day_buttons = []
        self._month_label.configure(text=f"{_MONTHS_RU[self._month]} {self._year}")

        weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(self._year, self._month)
        today = date.today()
        for row, week in enumerate(weeks):
            for col, day_num in enumerate(week):
                if day_num == 0:
                    ctk.CTkLabel(self._days_frame, text="", width=36, height=28).grid(
                        row=row, column=col, padx=2, pady=2
                    )
                    continue
                current = date(self._year, self._month, day_num)
                is_selected = current == self._selected
                is_today = current == today and not is_selected
                button = ctk.CTkButton(
                    self._days_frame,
                    text=str(day_num),
                    width=36,
                    height=28,
                    corner_radius=6,
                    font=ui_font(12, "bold" if is_selected or is_today else "normal"),
                    fg_color=ACCENT if is_selected else SURFACE_ALT,
                    hover_color=ACCENT_HOVER,
                    text_color="#ffffff" if is_selected else TEXT,
                    border_width=1 if is_today else 0,
                    border_color=ACCENT if is_today else BORDER,
                    command=lambda value=current: self._pick(value),
                )
                button.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
                self._day_buttons.append(button)
        lower_frame_canvases(self)

    def _pick(self, value: date) -> None:
        self._selected = value
        self._rebuild_days()
        self._on_change(value)
