"""Componentes visuales especializados para la GUI (Dark Tactical / Cyber-Goth).

Implementa entradas con placeholders, autocompletado en tiempo real,
smart-paste para dependencias y notificaciones en línea.
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


class PlaceholderEntry(tk.Entry):
    """Entry de Tkinter con soporte para texto de ayuda (placeholder) y Smart-Paste."""

    def __init__(
        self,
        master: tk.Widget,
        placeholder: str,
        on_smart_paste: Callable[[str, str, str | None], None] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            bg=COLOR_BG_INPUT,
            fg=COLOR_TEXT_MAIN,
            insertbackground=COLOR_TEXT_ACCENT,  # Color del cursor parpadeante
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_TEXT_ACCENT,
            font=FONT_BODY,
            *args,
            **kwargs,
        )
        self.placeholder: str = placeholder
        self.on_smart_paste: Callable[[str, str, str | None], None] | None = on_smart_paste
        self._is_showing_placeholder: bool = False

        self.bind("<FocusIn>", self._handle_focus_in)
        self.bind("<FocusOut>", self._handle_focus_out)
        self.bind("<<Paste>>", self._handle_paste)

        self.put_placeholder()

    def put_placeholder(self) -> None:
        """Restaura el placeholder visual si el campo está vacío."""
        if not self.get():
            self._is_showing_placeholder = True
            self.configure(fg=COLOR_TEXT_MUTED)
            self.delete(0, tk.END)
            self.insert(0, self.placeholder)

    def get_clean_value(self) -> str:
        """Retorna el contenido real ignorando el texto del placeholder."""
        if self._is_showing_placeholder:
            return ""
        return self.get().strip()

    def set_clean_value(self, value: str) -> None:
        """Establece un valor explícito eliminando el placeholder."""
        self._is_showing_placeholder = False
        self.configure(fg=COLOR_TEXT_MAIN)
        self.delete(0, tk.END)
        self.insert(0, value)

    def _handle_focus_in(self, _event: tk.Event[Any]) -> None:
        if self._is_showing_placeholder:
            self._is_showing_placeholder = False
            self.delete(0, tk.END)
            self.configure(fg=COLOR_TEXT_MAIN)

    def _handle_focus_out(self, _event: tk.Event[Any]) -> None:
        if not self.get().strip():
            self.put_placeholder()

    def _handle_paste(self, _event: tk.Event[Any]) -> str | None:
        """Detecta pegado con formato 'nombre==versión' o 'nombre@versión'."""
        if not self.on_smart_paste:
            return None

        try:
            clipboard_text = self.clipboard_get().strip()
        except tk.TclError:
            return None

        match = SMART_PASTE_REGEX.match(clipboard_text)
        if match:
            parsed = match.groupdict()
            self.on_smart_paste(
                parsed["name"],
                parsed["ver"],
                parsed.get("eco"),
            )
            return "break"  # Interrumpe el pegado estándar de Tkinter
        return None


class EcosystemCombobox(ttk.Combobox):
    """Combobox reactivo con autocompletado y búsqueda predictiva sobre el catálogo OSV."""

    def __init__(
        self,
        master: tk.Widget,
        catalog: Sequence[Mapping[str, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.catalog: Sequence[Mapping[str, Any]] = catalog
        self.all_labels: list[str] = [str(item.get("label", "")) for item in catalog]

        super().__init__(
            master,
            values=self.all_labels,
            font=FONT_BODY,
            *args,
            **kwargs,
        )
        self.bind("<KeyRelease>", self._on_key_release)

    def _on_key_release(self, event: tk.Event[Any]) -> None:
        """Filtra las opciones desplegables mientras el usuario escribe."""
        # Ignorar teclas de navegación
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return

        query = self.get().strip().lower()
        if not query:
            self["values"] = self.all_labels
            return

        filtered: list[str] = []
        for item in self.catalog:
            label = str(item.get("label", ""))
            eco = str(item.get("ecosystem", "")).lower()
            aliases = [str(a).lower() for a in item.get("aliases", [])]

            # Coincidencia por etiqueta visual, ecosistema o alias
            if query in label.lower() or query in eco or any(query in a for a in aliases):
                filtered.append(label)

        self["values"] = filtered if filtered else [f"[Sin coincidencia: '{query}']"]

    def get_selected_ecosystem(self) -> str:
        """Obtiene el nombre técnico de OSV correspondiente a la opción seleccionada."""
        current_text = self.get().strip()
        for item in self.catalog:
            if current_text == item.get("label"):
                return str(item.get("ecosystem", ""))
        # Si el usuario escribió un alias o el nombre directamente
        return current_text

    def set_ecosystem_by_name(self, ecosystem_name: str) -> None:
        """Selecciona el label correspondiente a partir de un nombre de ecosistema."""
        target = ecosystem_name.strip().lower()
        for item in self.catalog:
            if str(item.get("ecosystem", "")).lower() == target:
                self.set(str(item.get("label", "")))
                return
        self.set(ecosystem_name)


class FeedbackBanner(tk.Frame):
    """Banner de notificación en línea para feedback inmediato sin diálogos modales."""

    def __init__(self, master: tk.Widget, *args: Any, **kwargs: Any) -> None:
        super().__init__(master, bg=COLOR_BG_PANEL, relief="flat", *args, **kwargs)
        self.label: tk.Label = tk.Label(
            self,
            text="",
            bg=COLOR_BG_PANEL,
            fg=COLOR_TEXT_MAIN,
            font=FONT_MUTED,
            anchor="w",
            padx=10,
            pady=4,
        )
        self.label.pack(fill="x", expand=True)
        self._clear_timer_id: str | None = None

    def show_success(self, message: str, timeout_ms: int = 3500) -> None:
        """Muestra una confirmación en verde y programa su limpieza automática."""
        self._show_message(f"✓  {message}", COLOR_STATUS_CLEAN, timeout_ms)

    def show_error(self, message: str) -> None:
        """Muestra un error en carmesí orientado a la solución (permanece visible)."""
        self._show_message(f"⚠  {message}", COLOR_STATUS_ALERT, timeout_ms=None)

    def show_info(self, message: str, timeout_ms: int = 3500) -> None:
        """Muestra un aviso informativo en cyan."""
        self._show_message(f"ℹ  {message}", COLOR_TEXT_ACCENT, timeout_ms)

    def clear(self) -> None:
        """Limpia el mensaje visible inmediatamente."""
        if self._clear_timer_id:
            self.after_cancel(self._clear_timer_id)
            self._clear_timer_id = None
        self.label.configure(text="", fg=COLOR_TEXT_MAIN)

    def _show_message(self, text: str, color: str, timeout_ms: int | None) -> None:
        self.clear()
        self.label.configure(text=text, fg=color)
        if timeout_ms:
            self._clear_timer_id = self.after(timeout_ms, self.clear)
