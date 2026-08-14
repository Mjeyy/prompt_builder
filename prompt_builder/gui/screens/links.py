from __future__ import annotations

import customtkinter as ctk

from prompt_builder.gui.theme import DANGER, SUCCESS, TEXT, ui_font
from prompt_builder.gui.widgets import CarPickerPane, PromptPreviewPanel, copy_prompt
from prompt_builder.models import WORK_MODE_LABELS, Car
from prompt_builder.services.prompt_builder import build_links_prompt


class LinksScreen(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        cars: list[Car],
        template: str,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._template = template
        self._car: Car | None = None

        self.grid_columnconfigure(0, weight=0, minsize=340)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._car_picker = CarPickerPane(
            self, cars, on_select=self._on_car_selected, short_labels=True
        )
        self._car_picker.grid(row=0, column=0, sticky="nsew", padx=(24, 12), pady=20)
        self._build_work_pane()
        self._refresh_preview()

    def _build_work_pane(self) -> None:
        pane = ctk.CTkFrame(self, fg_color="transparent")
        pane.grid(row=0, column=1, sticky="nsew", padx=(12, 24), pady=20)
        pane.grid_columnconfigure(0, weight=1)
        pane.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            pane,
            text=WORK_MODE_LABELS["links"],
            font=ui_font(16, "bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        self._preview = PromptPreviewPanel(pane, on_copy=self._copy)
        self._preview.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self._preview.set_status("Выберите автомобиль")

    def _on_car_selected(self, car: Car | None) -> None:
        self._car = car
        if car is None:
            self._preview.set_status("Выберите автомобиль")
        else:
            self._preview.set_status(f"Авто: {car.display_short()}")
        self._refresh_preview()

    def _current_prompt(self) -> str | None:
        if self._car is None:
            return None
        return build_links_prompt(self._template, self._car)

    def _refresh_preview(self) -> None:
        prompt = self._current_prompt()
        self._preview.set_prompt(
            prompt,
            "Выберите автомобиль — здесь появится готовый промпт.",
        )

    def _copy(self) -> bool:
        prompt = self._current_prompt()
        if prompt is None or self._car is None:
            self._preview.set_status("Сначала выберите автомобиль", DANGER)
            return False
        error = copy_prompt(prompt)
        if error is not None:
            self._preview.set_status(f"Не удалось скопировать: {error}", DANGER)
            return False
        self._preview.set_status(
            f"Промпт скопирован · {self._car.display_short()} · {WORK_MODE_LABELS['links']}",
            SUCCESS,
        )
        return True
