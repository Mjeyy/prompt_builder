from __future__ import annotations

import customtkinter as ctk

from prompt_builder.gui.clickfix import apply_click_patches

BG = "#0e1116"
SURFACE = "#161b22"
SURFACE_ALT = "#1c2333"
BORDER = "#30363d"
ACCENT = "#3d8bfd"
ACCENT_HOVER = "#5a9dff"
SUCCESS = "#3fb950"
DANGER = "#f85149"
WARNING = "#d29922"
TEXT = "#e6edf3"
MUTED = "#8b949e"
CARD_HOVER = "#21283a"


def apply_theme() -> None:
    apply_click_patches()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def ui_font(size: int, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(size=size, weight=weight)
