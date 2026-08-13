from __future__ import annotations

import tkinter
from typing import Any

import customtkinter as ctk

_BUTTONS_PATCHED = False


def apply_click_patches() -> None:
    """CTkButton ignores a click unless <Enter> already set _mouse_inside.

    On macOS the window often never gets Enter until it is cycled, so the
    command never runs. Treat a release on the widget as a valid click.
    """
    global _BUTTONS_PATCHED
    if _BUTTONS_PATCHED:
        return
    _BUTTONS_PATCHED = True

    original_release = ctk.CTkButton._on_release

    def _on_release(self: ctk.CTkButton, event: tkinter.Event | None = None) -> Any:
        self._mouse_inside = True
        return original_release(self, event)

    ctk.CTkButton._on_release = _on_release  # type: ignore[method-assign]


def lower_frame_canvases(widget: tkinter.Misc) -> None:
    """Put CTkFrame background canvases behind children so they do not eat clicks."""
    try:
        children = list(widget.winfo_children())
    except tkinter.TclError:
        return

    for child in children:
        lower_frame_canvases(child)

    if widget.__class__ is not ctk.CTkFrame:
        return
    canvas = getattr(widget, "_canvas", None)
    if canvas is None:
        return
    try:
        canvas.lower()
    except tkinter.TclError:
        pass


def install_window_click_fixes(window: ctk.CTk) -> None:
    """Stop CTk from focusing canvases on click and from lift() on FocusIn."""

    def _safe_click_focus(event: tkinter.Event) -> None:
        widget = event.widget
        if isinstance(widget, str):
            return
        if isinstance(widget, tkinter.Canvas):
            return
        try:
            cls_name = widget.winfo_class()
        except tkinter.TclError:
            return
        if cls_name in {"Entry", "Text"}:
            widget.focus_set()

    try:
        window.unbind_all("<Button-1>")
    except tkinter.TclError:
        pass
    window.bind_all("<Button-1>", _safe_click_focus, add=True)

    def _focus_in_event(_event: tkinter.Event) -> None:
        return

    window._focus_in_event = _focus_in_event  # type: ignore[method-assign]
