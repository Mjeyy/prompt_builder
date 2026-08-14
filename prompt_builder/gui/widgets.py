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
    CARD_HOVER,
    DANGER,
    MUTED,
    SUCCESS,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    ui_font,
)
from prompt_builder.models import Car
from prompt_builder.services.cars import sorted_cars
from prompt_builder.services.clipboard import ClipboardError, copy_to_clipboard

T = TypeVar("T")

_COPY_LABEL = "Скопировать в буфер"
_COPIED_LABEL = "Скопировано"
_COPY_FLASH_MS = 1500


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

    def set_items(
        self,
        items: Sequence[tuple[str, T]],
        selected: T | None = None,
        empty_text: str | None = None,
    ) -> None:
        self._items = list(items)
        self._selected = selected
        if empty_text is not None:
            self._empty_text = empty_text
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


_SORT_FILE = "Как в файле"
_SORT_ALPHA = "По алфавиту"
_EMPTY_HIDDEN = "Все автомобили скрыты"
_EMPTY_SEARCH = "Ничего не найдено"


class CarPickerPane(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        cars: Sequence[Car],
        on_select: Callable[[Car | None], None],
        *,
        short_labels: bool = False,
        **kwargs: object,
    ) -> None:
        super().__init__(master, fg_color=SURFACE, corner_radius=16, **kwargs)
        self._cars = list(cars)
        self._on_select = on_select
        self._short_labels = short_labels
        self._alphabetical = False
        self._car: Car | None = None

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Автомобиль",
            font=ui_font(16, "bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        search_placeholder = (
            "Поиск по марке и модели…"
            if short_labels
            else "Поиск по марке, модели, мотору…"
        )
        self._search = ctk.CTkEntry(
            self,
            placeholder_text=search_placeholder,
            font=ui_font(13),
            height=36,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
        )
        self._search.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self._search.bind("<KeyRelease>", lambda _event: self._refresh_cars())

        self._sort = ctk.CTkSegmentedButton(
            self,
            values=[_SORT_FILE, _SORT_ALPHA],
            font=ui_font(13),
            height=32,
        )
        self._sort.set(_SORT_FILE)
        self._sort.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))

        self._car_list = SelectableList(self, on_select=self._on_car_selected)
        self._car_list.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 16))
        self._sort.configure(command=self._on_sort_changed)
        self._refresh_cars()

    @property
    def selected(self) -> Car | None:
        return self._car

    def _on_sort_changed(self, value: str) -> None:
        self._alphabetical = value == _SORT_ALPHA
        self._refresh_cars()

    def _on_car_selected(self, car: Car) -> None:
        self._car = car
        self._on_select(car)

    def _car_label(self, car: Car) -> str:
        return car.display_short() if self._short_labels else car.display()

    def _refresh_cars(self) -> None:
        query = self._search.get().strip().lower()
        items: list[tuple[str, Car]] = []
        for car in sorted_cars(self._cars, alphabetical=self._alphabetical):
            label = self._car_label(car)
            if query and query not in label.lower():
                continue
            items.append((label, car))
        selected = self._car if self._car in {item[1] for item in items} else None
        if selected is None and self._car is not None:
            self._car = None
            self._on_select(None)
        empty_text = _EMPTY_HIDDEN if not self._cars else _EMPTY_SEARCH
        self._car_list.set_items(items, selected=selected, empty_text=empty_text)


class PromptPreviewPanel(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        on_copy: Callable[[], bool],
        title: str = "Превью промпта",
        **kwargs: object,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_copy = on_copy
        self._flash_job: str | None = None
        self._has_prompt = False

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        preview_frame = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=16)
        preview_frame.grid(row=0, column=0, sticky="nsew")
        preview_frame.grid_rowconfigure(1, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_frame,
            text=title,
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
        self._preview.bind("<Key>", self._block_edit)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        actions.grid_columnconfigure(0, weight=1)

        self._status = ctk.CTkLabel(
            actions,
            text="",
            font=ui_font(13),
            text_color=MUTED,
            anchor="w",
        )
        self._status.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self._copy_button = ctk.CTkButton(
            actions,
            text=_COPY_LABEL,
            font=ui_font(14, "bold"),
            height=40,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._copy,
        )
        self._copy_button.grid(row=1, column=0, sticky="w")
        self._copy_button.configure(state="disabled")

    def set_prompt(self, prompt: str | None, placeholder: str) -> None:
        self._has_prompt = prompt is not None
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", prompt if prompt is not None else placeholder)
        self._copy_button.configure(state="normal" if prompt is not None else "disabled")

    def set_status(self, text: str, color: str = MUTED) -> None:
        self._status.configure(text=text, text_color=color)

    def _copy(self) -> None:
        if not self._has_prompt:
            self.set_status("Сначала соберите промпт", DANGER)
            return
        if not self._on_copy():
            return
        self._flash_copied()

    def _flash_copied(self) -> None:
        if self._flash_job is not None:
            self.after_cancel(self._flash_job)
        self._copy_button.configure(text=_COPIED_LABEL)
        self._flash_job = self.after(_COPY_FLASH_MS, self._restore_copy_label)

    def _restore_copy_label(self) -> None:
        self._flash_job = None
        self._copy_button.configure(text=_COPY_LABEL)

    @staticmethod
    def _block_edit(event: Any) -> str | None:
        if event.keysym in {
            "Left",
            "Right",
            "Up",
            "Down",
            "Home",
            "End",
            "Prior",
            "Next",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
            "Meta_L",
            "Meta_R",
            "Command",
        }:
            return None
        modifiers = int(getattr(event, "state", 0))
        if modifiers & 0xC and event.keysym.lower() in {"c", "a"}:
            return None
        return "break"


def copy_prompt(prompt: str) -> str | None:
    """Copy text to the clipboard. Returns an error message, or None on success."""
    try:
        copy_to_clipboard(prompt)
    except ClipboardError as exc:
        return str(exc)
    return None


class ModeCard(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        title: str,
        description: str,
        action: str,
        on_click: Callable[[], None],
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
        self._on_click = on_click
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ui_font(20, "bold"),
            text_color=TEXT,
            anchor="w",
        )
        title_label.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 6))

        description_label = ctk.CTkLabel(
            self,
            text=description,
            font=ui_font(14),
            text_color=MUTED,
            justify="left",
            anchor="nw",
        )
        description_label.grid(row=1, column=0, sticky="new", padx=24, pady=(0, 12))

        ctk.CTkButton(
            self,
            text=action,
            font=ui_font(14, "bold"),
            height=42,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=on_click,
        ).grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 20))

        for widget in (self, title_label, description_label):
            widget.bind("<Button-1>", self._handle_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
        lower_frame_canvases(self)

    def _handle_click(self, _event: Any) -> None:
        self._on_click()

    def _on_enter(self, _event: Any) -> None:
        self.configure(fg_color=CARD_HOVER)

    def _on_leave(self, event: Any) -> None:
        x, y = event.x_root, event.y_root
        left = self.winfo_rootx()
        top = self.winfo_rooty()
        if left <= x < left + self.winfo_width() and top <= y < top + self.winfo_height():
            return
        self.configure(fg_color=SURFACE)


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
        ).grid(row=0, column=2, sticky="e", padx=(0, 8))

        ctk.CTkButton(
            header,
            text="Сегодня",
            width=88,
            height=32,
            font=ui_font(13),
            fg_color=SURFACE_ALT,
            hover_color=ACCENT_HOVER,
            command=self.go_today,
        ).grid(row=0, column=3, sticky="e")

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

    def go_today(self) -> None:
        today = date.today()
        self._selected = today
        self._year = today.year
        self._month = today.month
        self._rebuild_days()
        self._on_change(today)

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
