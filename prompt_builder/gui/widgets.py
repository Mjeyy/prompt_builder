from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeVar

import customtkinter as ctk

from prompt_builder.gui.theme import ACCENT, MUTED, SURFACE, SURFACE_ALT, TEXT, ui_font

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
