from __future__ import annotations

import customtkinter as ctk

from prompt_builder.gui.theme import (
    ACCENT,
    ACCENT_HOVER,
    DANGER,
    SUCCESS,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    ui_font,
)
from prompt_builder.gui.widgets import CarPickerPane, PromptPreviewPanel, SelectableList, copy_prompt
from prompt_builder.models import CATEGORY_LABELS, Car, Category, PromptSection, Selection
from prompt_builder.parsers.prompts import sections_for_category
from prompt_builder.services.prompt_builder import build_prompt


class PromptBuilderScreen(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        cars: list[Car],
        sections: list[PromptSection],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._sections = sections
        self._category: Category = "repair"
        self._car: Car | None = None
        self._section: PromptSection | None = None

        self.grid_columnconfigure(0, weight=0, minsize=340)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._car_picker = CarPickerPane(self, cars, on_select=self._on_car_selected)
        self._car_picker.grid(row=0, column=0, sticky="nsew", padx=(24, 12), pady=20)
        self._build_work_pane()
        self._refresh_sections()
        self._refresh_preview()

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

        self._preview = PromptPreviewPanel(pane, on_copy=self._copy)
        self._preview.grid(row=3, column=0, sticky="nsew")
        self._preview.set_status("Выберите авто и раздел")

    def _refresh_sections(self) -> None:
        category_sections = sections_for_category(self._sections, self._category)
        items = [(section.display(), section) for section in category_sections]
        selected = self._section if self._section in {item[1] for item in items} else None
        if selected is None:
            self._section = None
        self._section_list.set_items(items, selected=selected)

    def _on_car_selected(self, car: Car | None) -> None:
        self._car = car
        if car is None:
            self._preview.set_status("Выберите авто и раздел")
        else:
            self._preview.set_status(f"Авто: {car.display()}")
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
        self._preview.set_prompt(
            prompt,
            "Выберите автомобиль и раздел — здесь появится готовый промпт.",
        )

    def _copy(self) -> bool:
        prompt = self._current_prompt()
        if prompt is None or self._car is None or self._section is None:
            self._preview.set_status("Сначала выберите авто и раздел", DANGER)
            return False
        error = copy_prompt(prompt)
        if error is not None:
            self._preview.set_status(f"Не удалось скопировать: {error}", DANGER)
            return False
        selection = Selection(car=self._car, section=self._section)
        self._preview.set_status(
            f"Промпт скопирован · {selection.car.display()} · "
            f"{selection.category_label} · {selection.section.display()}",
            SUCCESS,
        )
        return True
