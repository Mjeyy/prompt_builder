from __future__ import annotations

from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from prompt_builder.gui.clickfix import install_window_click_fixes, lower_frame_canvases
from prompt_builder.gui import PROJECT_ROOT
from prompt_builder.gui.screens.home import HomeScreen
from prompt_builder.gui.screens.horoscope import HoroscopeScreen
from prompt_builder.gui.screens.prompt_builder import PromptBuilderScreen
from prompt_builder.gui.screens.table_qa import TableQaScreen
from prompt_builder.gui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG,
    MUTED,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    apply_theme,
    ui_font,
)
from prompt_builder.models import HoroscopeMode
from prompt_builder.parsers.autos import load_cars
from prompt_builder.parsers.horoscope import load_horoscope_templates
from prompt_builder.parsers.prompts import load_prompt_sections


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        install_window_click_fixes(self)
        self.title("Prompt Builder")
        self.geometry("1180x780")
        self.minsize(980, 640)
        self.configure(fg_color=BG)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._header = _Header(self, on_home=self.show_home)
        self._header.grid(row=0, column=0, sticky="ew")

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.grid(row=1, column=0, sticky="nsew")
        self._body.grid_rowconfigure(0, weight=1)
        self._body.grid_columnconfigure(0, weight=1)
        self._current: ctk.CTkFrame | None = None

        self.show_home()

    def _set_body(self, widget: ctk.CTkFrame) -> None:
        if self._current is not None:
            self._current.destroy()
        self._current = widget
        widget.grid(row=0, column=0, sticky="nsew")
        self.after_idle(lambda: lower_frame_canvases(self))

    def show_home(self) -> None:
        self._header.set_mode("Главная", show_home=False)
        self._set_body(
            HomeScreen(
                self._body,
                on_builder=self.show_builder,
                on_qa=self.show_table_qa,
                on_horoscope_auto=lambda: self.show_horoscope("auto"),
                on_horoscope_date=lambda: self.show_horoscope("date"),
            )
        )

    def show_builder(self) -> None:
        try:
            cars = load_cars(PROJECT_ROOT / "autos.md")
            sections = load_prompt_sections(
                PROJECT_ROOT / "repair_prompts.md",
                PROJECT_ROOT / "tuning_prompts.md",
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror("Ошибка загрузки данных", str(exc), parent=self)
            return
        self._header.set_mode("Сборка промпта")
        self._set_body(PromptBuilderScreen(self._body, cars, sections))

    def show_horoscope(self, mode: HoroscopeMode) -> None:
        try:
            cars = load_cars(PROJECT_ROOT / "autos.md")
            templates = load_horoscope_templates(
                PROJECT_ROOT / "horoscop_auto.md",
                PROJECT_ROOT / "horoscop_date.md",
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror("Ошибка загрузки данных", str(exc), parent=self)
            return
        title = "Гороскоп: описание" if mode == "auto" else "Гороскоп: прогноз"
        self._header.set_mode(title)
        self._set_body(HoroscopeScreen(self._body, cars, templates, mode))

    def show_table_qa(self) -> None:
        self._header.set_mode("Проверка таблиц")
        self._set_body(TableQaScreen(self._body))


class _Header(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, on_home: Callable[[], None]) -> None:
        super().__init__(master, fg_color=SURFACE, height=64, corner_radius=0)
        self._on_home = on_home
        self.grid_columnconfigure(1, weight=1)
        self.grid_propagate(False)

        ctk.CTkLabel(
            self,
            text="Prompt Builder",
            font=ui_font(18, "bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w", padx=(24, 12), pady=16)

        self._mode = ctk.CTkLabel(
            self,
            text="",
            font=ui_font(14),
            text_color=MUTED,
            anchor="w",
        )
        self._mode.grid(row=0, column=1, sticky="ew")

        self._home_button = ctk.CTkButton(
            self,
            text="На главную",
            font=ui_font(13),
            width=120,
            height=32,
            fg_color=SURFACE_ALT,
            hover_color=ACCENT_HOVER,
            command=self._go_home,
        )
        self._home_button.grid(row=0, column=2, sticky="e", padx=(12, 24))

    def _go_home(self) -> None:
        self._on_home()

    def set_mode(self, title: str, show_home: bool = True) -> None:
        self._mode.configure(text=title)
        self._home_button.configure(state="normal" if show_home else "disabled")
        if show_home:
            self._home_button.configure(fg_color=ACCENT)
        else:
            self._home_button.configure(fg_color=SURFACE_ALT)


def main() -> None:
    apply_theme()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
