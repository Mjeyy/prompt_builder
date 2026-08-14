from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from prompt_builder.gui.theme import (
    ACCENT,
    BORDER,
    MUTED,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    ui_font,
)
from prompt_builder.models import CARS_LIST_LABEL, Car
from prompt_builder.parsers.autos import save_hidden_cars


class CarsListScreen(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        cars: list[Car],
        hidden: set[Car],
        hidden_path: Path,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._cars = list(cars)
        self._hidden = set(hidden)
        self._hidden_path = hidden_path

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self,
            text=CARS_LIST_LABEL,
            font=ui_font(22, "bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=32, pady=(20, 4))

        ctk.CTkLabel(
            self,
            text="Скрытие действует только на сборку промпта (ремонт и тюнинг). "
            "Гороскоп, поиск ссылок и терминал показывают все авто.",
            font=ui_font(14),
            text_color=MUTED,
            anchor="w",
            justify="left",
            wraplength=900,
        ).grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 12))

        self._search = ctk.CTkEntry(
            self,
            placeholder_text="Поиск по марке, модели, мотору…",
            font=ui_font(13),
            height=36,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
        )
        self._search.grid(row=2, column=0, sticky="ew", padx=32, pady=(0, 8))
        self._search.bind("<KeyRelease>", lambda _event: self._rebuild())

        self._list = ctk.CTkScrollableFrame(self, fg_color=SURFACE, corner_radius=16)
        self._list.grid(row=3, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._list.grid_columnconfigure(0, weight=1)
        self._rebuild()

    def _filtered_cars(self) -> list[Car]:
        query = self._search.get().strip().lower()
        if not query:
            return list(self._cars)
        return [car for car in self._cars if query in car.display().lower()]

    def _rebuild(self) -> None:
        for child in self._list.winfo_children():
            child.destroy()

        cars = self._filtered_cars()
        if not cars:
            ctk.CTkLabel(
                self._list,
                text="Ничего не найдено",
                text_color=MUTED,
                font=ui_font(13),
                anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=16, pady=16)
            return

        for index, car in enumerate(cars):
            self._add_row(index, car)

    def _add_row(self, index: int, car: Car) -> None:
        hidden = car in self._hidden
        row = ctk.CTkFrame(self._list, fg_color="transparent")
        row.grid(row=index, column=0, sticky="ew", padx=8, pady=4)
        row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            row,
            text=car.display(),
            font=ui_font(13),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=(8, 12), pady=8)

        switch = ctk.CTkSwitch(
            row,
            text="Скрыто" if hidden else "Видно",
            font=ui_font(13),
            text_color=MUTED,
            progress_color=ACCENT,
        )
        switch.grid(row=0, column=1, sticky="e", padx=(0, 8), pady=8)
        if hidden:
            switch.select()
        else:
            switch.deselect()
        switch.configure(command=lambda current=car: self._toggle(current))

    def _toggle(self, car: Car) -> None:
        previous = set(self._hidden)
        if car in self._hidden:
            self._hidden.discard(car)
        else:
            self._hidden.add(car)
        try:
            save_hidden_cars(self._hidden_path, self._hidden, self._cars)
        except OSError as exc:
            self._hidden = previous
            messagebox.showerror("Не удалось сохранить список", str(exc), parent=self)
        self._rebuild()
