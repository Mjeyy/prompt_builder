from __future__ import annotations

from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from prompt_builder.gui.clickfix import install_window_click_fixes, lower_frame_canvases
from prompt_builder.gui.screens.home import HomeScreen
from prompt_builder.gui.screens.horoscope import HoroscopeScreen
from prompt_builder.gui.screens.links import LinksScreen
from prompt_builder.gui.screens.prompt_builder import PromptBuilderScreen
from prompt_builder.gui.screens.table_qa import TableQaScreen
from prompt_builder.gui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG,
    MUTED,
    SURFACE,
    TEXT,
    apply_theme,
    ui_font,
)
from prompt_builder.models import BUILDER_LABEL, HOME_LABEL, TABLE_QA_LABEL, WORK_MODE_LABELS, HoroscopeMode
from prompt_builder.parsers.autos import load_cars
from prompt_builder.parsers.horoscope import load_horoscope_templates
from prompt_builder.parsers.links import load_links_template
from prompt_builder.parsers.prompts import load_prompt_sections
from prompt_builder.paths import (
    AUTOS_PATH,
    HOROSCOPE_AUTO_PATH,
    HOROSCOPE_DATE_PATH,
    LINKS_PATH,
    REPAIR_PROMPTS_PATH,
    TUNING_PROMPTS_PATH,
)


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
        self._header.set_mode(HOME_LABEL, show_home=False)
        self._set_body(
            HomeScreen(
                self._body,
                on_builder=self.show_builder,
                on_qa=self.show_table_qa,
                on_horoscope_auto=lambda: self.show_horoscope("auto"),
                on_horoscope_date=lambda: self.show_horoscope("date"),
                on_links=self.show_links,
            )
        )

    def show_builder(self) -> None:
        try:
            cars = load_cars(AUTOS_PATH)
            sections = load_prompt_sections(REPAIR_PROMPTS_PATH, TUNING_PROMPTS_PATH)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Ошибка загрузки данных", str(exc), parent=self)
            return
        self._header.set_mode(BUILDER_LABEL)
        self._set_body(PromptBuilderScreen(self._body, cars, sections))

    def show_horoscope(self, mode: HoroscopeMode) -> None:
        try:
            cars = load_cars(AUTOS_PATH)
            templates = load_horoscope_templates(HOROSCOPE_AUTO_PATH, HOROSCOPE_DATE_PATH)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Ошибка загрузки данных", str(exc), parent=self)
            return
        title = (
            WORK_MODE_LABELS["horoscope_auto"]
            if mode == "auto"
            else WORK_MODE_LABELS["horoscope_date"]
        )
        self._header.set_mode(title)
        self._set_body(HoroscopeScreen(self._body, cars, templates, mode))

    def show_links(self) -> None:
        try:
            cars = load_cars(AUTOS_PATH)
            template = load_links_template(LINKS_PATH)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Ошибка загрузки данных", str(exc), parent=self)
            return
        self._header.set_mode(WORK_MODE_LABELS["links"])
        self._set_body(LinksScreen(self._body, cars, template))

    def show_table_qa(self) -> None:
        self._header.set_mode(TABLE_QA_LABEL)
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
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._go_home,
        )
        self._home_button.grid(row=0, column=2, sticky="e", padx=(12, 24))

    def _go_home(self) -> None:
        self._on_home()

    def set_mode(self, title: str, show_home: bool = True) -> None:
        self._mode.configure(text=title)
        if show_home:
            self._home_button.grid()
        else:
            self._home_button.grid_remove()


def main() -> None:
    apply_theme()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
