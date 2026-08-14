from __future__ import annotations

from datetime import date

import customtkinter as ctk

from prompt_builder.gui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BORDER,
    DANGER,
    SUCCESS,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    ui_font,
)
from prompt_builder.gui.widgets import CarPickerPane, MonthCalendar, PromptPreviewPanel, copy_prompt
from prompt_builder.models import WORK_MODE_LABELS, Car, HoroscopeMode, HoroscopeTemplates
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
        self._templates = templates
        self._mode = mode
        self._car: Car | None = None
        self._start_date = date.today()
        self._days = 7

        self.grid_columnconfigure(0, weight=0, minsize=340)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._car_picker = CarPickerPane(self, cars, on_select=self._on_car_selected)
        self._car_picker.grid(row=0, column=0, sticky="nsew", padx=(24, 12), pady=20)
        self._build_work_pane()
        self._refresh_preview()

    def _build_work_pane(self) -> None:
        pane = ctk.CTkFrame(self, fg_color="transparent")
        pane.grid(row=0, column=1, sticky="nsew", padx=(12, 24), pady=20)
        pane.grid_columnconfigure(0, weight=1)

        title = (
            WORK_MODE_LABELS["horoscope_auto"]
            if self._mode == "auto"
            else WORK_MODE_LABELS["horoscope_date"]
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
        self._preview = PromptPreviewPanel(pane, on_copy=self._copy)
        self._preview.grid(row=next_row, column=0, sticky="nsew", pady=(12, 0))
        self._preview.set_status("Выберите автомобиль")

    def _on_car_selected(self, car: Car | None) -> None:
        self._car = car
        if car is None:
            self._preview.set_status("Выберите автомобиль")
        else:
            self._preview.set_status(f"Авто: {car.display_short()}")
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
            self._custom_days.insert(0, str(self._days if self._days >= 1 else 7))
            self._on_custom_days()
            return
        self._custom_days.grid_forget()
        self._days = int(label)
        self._refresh_preview()

    def _on_custom_days(self) -> None:
        parsed = _parse_days(self._custom_days.get())
        self._days = 0 if parsed is None else parsed
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
        if prompt is None and self._mode == "date" and self._car is not None and self._days < 1:
            placeholder = "Укажите количество дней — целое число не меньше 1."
        else:
            placeholder = "Выберите автомобиль — здесь появится готовый промпт."
        self._preview.set_prompt(prompt, placeholder)

    def _copy(self) -> bool:
        prompt = self._current_prompt()
        if prompt is None or self._car is None:
            self._preview.set_status("Сначала выберите автомобиль", DANGER)
            return False
        error = copy_prompt(prompt)
        if error is not None:
            self._preview.set_status(f"Не удалось скопировать: {error}", DANGER)
            return False
        if self._mode == "auto":
            self._preview.set_status(
                f"Промпт скопирован · {self._car.display_short()} · описание",
                SUCCESS,
            )
        else:
            self._preview.set_status(
                f"Промпт скопирован · {self._car.display_short()} · "
                f"{self._start_date.isoformat()} · {self._days} дн.",
                SUCCESS,
            )
        return True


def _parse_days(raw: str) -> int | None:
    try:
        days = int(raw.strip())
    except ValueError:
        return None
    if days < 1:
        return None
    return days
