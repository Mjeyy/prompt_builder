from __future__ import annotations

from datetime import date

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
from prompt_builder.gui.widgets import MonthCalendar, SelectableList
from prompt_builder.models import Car, HoroscopeMode, HoroscopeTemplates
from prompt_builder.services.clipboard import ClipboardError, copy_to_clipboard
from prompt_builder.services.prompt_builder import (
    build_horoscope_auto_prompt,
    build_horoscope_date_prompt,
)

_DAYS_PRESETS = ("7", "10", "30")
_DAYS_MANUAL = "Вручную"


class HoroscopeScreen(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        cars: list[Car],
        templates: HoroscopeTemplates,
        mode: HoroscopeMode,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._cars = cars
        self._templates = templates
        self._mode = mode
        self._car: Car | None = None
        self._start_date = date.today()
        self._days = 7

        self.grid_columnconfigure(0, weight=0, minsize=340)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_car_pane()
        self._build_work_pane()
        self._refresh_cars()
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

        title = (
            "Гороскоп: описание авто"
            if self._mode == "auto"
            else "Гороскоп: прогноз"
        )
        ctk.CTkLabel(
            pane,
            text=title,
            font=ui_font(16, "bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        next_row = 1
        if self._mode == "date":
            self._calendar = MonthCalendar(pane, on_change=self._on_date_change, selected=self._start_date)
            self._calendar.grid(row=next_row, column=0, sticky="ew", pady=(12, 0))
            next_row += 1

            days_row = ctk.CTkFrame(pane, fg_color="transparent")
            days_row.grid(row=next_row, column=0, sticky="ew", pady=(12, 0))
            days_row.grid_columnconfigure(1, weight=1)
            next_row += 1

            ctk.CTkLabel(
                days_row,
                text="Дней прогноза",
                font=ui_font(14, "bold"),
                text_color=TEXT,
            ).grid(row=0, column=0, sticky="w", padx=(0, 12))

            self._days_control = ctk.CTkSegmentedButton(
                days_row,
                values=[*_DAYS_PRESETS, _DAYS_MANUAL],
                command=self._on_days_preset,
                font=ui_font(13),
                selected_color=ACCENT,
                selected_hover_color=ACCENT_HOVER,
                unselected_color=SURFACE,
                unselected_hover_color=SURFACE_ALT,
                height=36,
            )
            self._days_control.grid(row=0, column=1, sticky="e")

            self._custom_days_row = next_row
            self._custom_days = ctk.CTkEntry(
                pane,
                placeholder_text="Количество дней, целое число ≥ 1",
                font=ui_font(13),
                height=36,
                fg_color=SURFACE_ALT,
                border_color=BORDER,
            )
            self._custom_days.bind("<KeyRelease>", lambda _event: self._on_custom_days())
            self._days_control.set("7")
            next_row += 1

        pane.grid_rowconfigure(next_row, weight=1)
        preview_frame = ctk.CTkFrame(pane, fg_color=SURFACE, corner_radius=16)
        preview_frame.grid(row=next_row, column=0, sticky="nsew", pady=(12, 0))
        preview_frame.grid_rowconfigure(1, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        next_row += 1

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
        actions.grid(row=next_row, column=0, sticky="ew", pady=(12, 0))
        actions.grid_columnconfigure(0, weight=1)

        self._status = ctk.CTkLabel(
            actions,
            text="Выберите автомобиль",
            font=ui_font(13),
            text_color=MUTED,
            anchor="w",
        )
        self._status.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self._copy_button = ctk.CTkButton(
            actions,
            text="Скопировать в буфер",
            font=ui_font(14, "bold"),
            height=40,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._copy,
        )
        self._copy_button.grid(row=1, column=0, sticky="w")

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

    def _on_car_selected(self, car: Car) -> None:
        self._car = car
        self._set_status(f"Авто: {car.display_short()}", MUTED)
        self._refresh_preview()

    def _on_date_change(self, value: date) -> None:
        self._start_date = value
        self._refresh_preview()

    def _on_days_preset(self, label: str) -> None:
        if label == _DAYS_MANUAL:
            self._custom_days.grid(
                row=self._custom_days_row,
                column=0,
                sticky="ew",
                pady=(8, 0),
            )
            self._custom_days.delete(0, "end")
            self._custom_days.insert(0, str(self._days))
            self._on_custom_days()
            return
        self._custom_days.grid_forget()
        self._days = int(label)
        self._refresh_preview()

    def _on_custom_days(self) -> None:
        parsed = _parse_days(self._custom_days.get())
        if parsed is None:
            self._days = 0
        else:
            self._days = parsed
        self._refresh_preview()

    def _current_prompt(self) -> str | None:
        if self._car is None:
            return None
        if self._mode == "auto":
            return build_horoscope_auto_prompt(self._templates.auto, self._car)
        if self._days < 1:
            return None
        return build_horoscope_date_prompt(
            self._templates.date,
            self._car,
            self._start_date,
            self._days,
        )

    def _refresh_preview(self) -> None:
        prompt = self._current_prompt()
        self._preview.configure(state="normal")
        self._preview.delete("1.0", "end")
        if prompt is None:
            if self._mode == "date" and self._car is not None and self._days < 1:
                placeholder = "Укажите количество дней — целое число не меньше 1."
            else:
                placeholder = "Выберите автомобиль — здесь появится готовый промпт."
            self._preview.insert("1.0", placeholder)
            self._copy_button.configure(state="disabled")
        else:
            self._preview.insert("1.0", prompt)
            self._copy_button.configure(state="normal")
        self._preview.configure(state="disabled")

    def _copy(self) -> None:
        prompt = self._current_prompt()
        if prompt is None or self._car is None:
            self._set_status("Сначала выберите автомобиль", DANGER)
            return
        try:
            copy_to_clipboard(prompt)
        except ClipboardError as exc:
            self._set_status(f"Не удалось скопировать: {exc}", DANGER)
            return

        if self._mode == "auto":
            self._set_status(
                f"Промпт скопирован · {self._car.display_short()} · описание",
                SUCCESS,
            )
        else:
            self._set_status(
                f"Промпт скопирован · {self._car.display_short()} · "
                f"{self._start_date.isoformat()} · {self._days} дн.",
                SUCCESS,
            )

    def _set_status(self, text: str, color: str) -> None:
        self._status.configure(text=text, text_color=color)


def _parse_days(raw: str) -> int | None:
    try:
        days = int(raw.strip())
    except ValueError:
        return None
    if days < 1:
        return None
    return days
