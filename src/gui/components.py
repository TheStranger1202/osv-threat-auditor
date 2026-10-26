"""Factorías funcionales de componentes visuales (Dark Tactical).

Construye componentes GUI mediante clausuras y funciones puras, eliminando
la herencia de clases y el acoplamiento a objetos mutables.
"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Mapping, Sequence

from src.gui.theme import (
    COLOR_BG_INPUT,
    COLOR_BG_PANEL,
    COLOR_BORDER,
    COLOR_STATUS_ALERT,
    COLOR_STATUS_CLEAN,
    COLOR_TEXT_ACCENT,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
    FONT_BODY,
    FONT_MUTED,
)

SMART_PASTE_REGEX: re.Pattern[str] = re.compile(
    r"^(?:(?P<eco>[a-zA-Z0-9\.\-]+):)?(?P<name>[a-zA-Z0-9_\-\./]+)(?:==|@)(?P<ver>[a-zA-Z0-9_\-\.]+)$"
)


def create_placeholder_entry(
    parent: tk.Widget,
    placeholder: str,
    on_smart_paste: Callable[[str, str, str | None], None] | None = None,
) -> dict[str, Any]:
    """Factoría funcional para entradas de texto con placeholder y Smart-Paste.

    Returns:
        dict: Contenedor con el widget y sus funciones puras de acceso.
    """
    entry = tk.Entry(
        parent,
        bg=COLOR_BG_INPUT,
        fg=COLOR_TEXT_MAIN,
        insertbackground=COLOR_TEXT_ACCENT,
        relief="solid",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground=COLOR_BORDER,
        highlightcolor=COLOR_TEXT_ACCENT,
        font=FONT_BODY,
    )

    showing_placeholder = [False]

    def put_placeholder() -> None:
        if not entry.get():
            showing_placeholder[0] = True
            entry.configure(fg=COLOR_TEXT_MUTED)
            entry.delete(0, tk.END)
            entry.insert(0, placeholder)

    def get_clean_value() -> str:
        if showing_placeholder[0]:
            return ""
        return entry.get().strip()

    def set_clean_value(value: str) -> None:
        showing_placeholder[0] = False
        entry.configure(fg=COLOR_TEXT_MAIN)
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def on_focus_in(_event: tk.Event[Any]) -> None:
        if showing_placeholder[0]:
            showing_placeholder[0] = False
            entry.delete(0, tk.END)
            entry.configure(fg=COLOR_TEXT_MAIN)

    def on_focus_out(_event: tk.Event[Any]) -> None:
        if not entry.get().strip():
            put_placeholder()

    def on_paste(_event: tk.Event[Any]) -> str | None:
        if not on_smart_paste:
            return None
        try:
            clipboard_text = entry.clipboard_get().strip()
        except tk.TclError:
            return None

        match = SMART_PASTE_REGEX.match(clipboard_text)
        if match:
            parsed = match.groupdict()
            on_smart_paste(parsed["name"], parsed["ver"], parsed.get("eco"))
            return "break"
        return None

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    entry.bind("<<Paste>>", on_paste)

    put_placeholder()

    return {
        "widget": entry,
        "get_value": get_clean_value,
        "set_value": set_clean_value,
        "reset": put_placeholder,
    }


def create_ecosystem_combobox(
    parent: tk.Widget,
    catalog: Sequence[Mapping[str, Any]],
    on_match_callback: Callable[[str | None, str | None], None] | None = None,
) -> dict[str, Any]:
    """Factoría funcional para selector predictivo de ecosistemas con autocompletado."""
    all_labels = [str(item.get("label", "")) for item in catalog]
    matched_label: list[str | None] = [None]

    combo = ttk.Combobox(
        parent,
        values=all_labels,
        font=FONT_BODY,
        height=16,
    )

    def on_key_release(event: tk.Event[Any]) -> None:
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return

        query = combo.get().strip().lower()
        if not query:
            combo["values"] = all_labels
            matched_label[0] = None
            if on_match_callback:
                on_match_callback(None, None)
            return

        filtered: list[str] = []
        best_match_eco: str | None = None
        best_match_label: str | None = None

        for item in catalog:
            label = str(item.get("label", ""))
            eco = str(item.get("ecosystem", ""))
            aliases = [str(a).lower() for a in item.get("aliases", [])]

            if query == eco.lower() or query in aliases or query in label.lower():
                filtered.append(label)
                if not best_match_eco:
                    best_match_eco = eco
                    best_match_label = label

        combo["values"] = filtered if filtered else [f"[Sin coincidencia: '{query}']"]
        matched_label[0] = best_match_label

        if on_match_callback:
            on_match_callback(best_match_label, best_match_eco)

    def on_tab_complete(_event: tk.Event[Any]) -> str | None:
        if matched_label[0]:
            combo.set(matched_label[0])
            for item in catalog:
                if item.get("label") == matched_label[0]:
                    if on_match_callback:
                        on_match_callback(matched_label[0], str(item.get("ecosystem", "")))
                    break
        return None

    def on_selected(_event: tk.Event[Any]) -> None:
        current_text = combo.get().strip()
        for item in catalog:
            if current_text == item.get("label"):
                if on_match_callback:
                    on_match_callback(current_text, str(item.get("ecosystem", "")))
                return

    def get_selected_ecosystem() -> str:
        current_text = combo.get().strip()
        for item in catalog:
            if current_text == item.get("label"):
                return str(item.get("ecosystem", ""))
        return current_text

    def set_ecosystem_by_name(ecosystem_name: str) -> None:
        target = ecosystem_name.strip().lower()
        for item in catalog:
            if str(item.get("ecosystem", "")).lower() == target:
                label = str(item.get("label", ""))
                combo.set(label)
                if on_match_callback:
                    on_match_callback(label, str(item.get("ecosystem", "")))
                return
        combo.set(ecosystem_name)

    combo.bind("<KeyRelease>", on_key_release)
    combo.bind("<Tab>", on_tab_complete)
    combo.bind("<<ComboboxSelected>>", on_selected)

    return {
        "widget": combo,
        "get_selected": get_selected_ecosystem,
        "set_by_name": set_ecosystem_by_name,
        "set_text": combo.set,
    }


def create_feedback_banner(parent: tk.Widget) -> dict[str, Any]:
    """Factoría funcional para el banner de estado en línea sin diálogos modales."""
    banner_frame = tk.Frame(parent, bg=COLOR_BG_PANEL, relief="flat")
    label = tk.Label(
        banner_frame,
        text="",
        bg=COLOR_BG_PANEL,
        fg=COLOR_TEXT_MAIN,
        font=FONT_MUTED,
        anchor="w",
        padx=10,
        pady=4,
    )
    label.pack(fill="x", expand=True)

    timer_id: list[str | None] = [None]

    def clear() -> None:
        if timer_id[0]:
            banner_frame.after_cancel(timer_id[0])
            timer_id[0] = None
        label.configure(text="", fg=COLOR_TEXT_MAIN)

    def show_message(text: str, color: str, timeout_ms: int | None) -> None:
        clear()
        label.configure(text=text, fg=color)
        if timeout_ms:
            timer_id[0] = banner_frame.after(timeout_ms, clear)

    return {
        "widget": banner_frame,
        "show_success": lambda msg, t=3500: show_message(f"✓  {msg}", COLOR_STATUS_CLEAN, t),
        "show_error": lambda msg: show_message(f"⚠  {msg}", COLOR_STATUS_ALERT, None),
        "show_info": lambda msg, t=3500: show_message(f"ℹ  {msg}", COLOR_TEXT_ACCENT, t),
        "clear": clear,
    }
