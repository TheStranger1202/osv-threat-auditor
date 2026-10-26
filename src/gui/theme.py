"""Módulo de tema visual ergonómico (Dark Tactical / Cyber-Goth).

Centraliza la paleta de colores, fuentes y configuración de ttk.Style
para prevenir fatiga visual mediante funciones puras y constantes inmutables.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Final

# --- Paleta Ergonómica (Baja Saturación / Alto Confort Visual) ---
COLOR_BG_DARK: Final[str] = "#111318"       # Fondo base ventana (Grafito frío)
COLOR_BG_PANEL: Final[str] = "#181b22"      # Superficie de contenedores/tarjetas
COLOR_BG_INPUT: Final[str] = "#1f232c"      # Entradas de texto y selects
COLOR_BORDER: Final[str] = "#2d3340"        # Bordes sutiles

COLOR_TEXT_MAIN: Final[str] = "#d8dee9"     # Texto principal (Gris gélido legible)
COLOR_TEXT_MUTED: Final[str] = "#6c7689"    # Placeholders y ayudas (Atenuado)
COLOR_TEXT_ACCENT: Final[str] = "#38bdf8"   # Cyan suave (Acentos y foco)

# Semáforo de estados (Tonos pastel / desaturados para prevenir fatiga visual)
COLOR_STATUS_CLEAN: Final[str] = "#34d399"    # Verde esmeralda (Seguro)
COLOR_STATUS_PATCH: Final[str] = "#fbbf24"    # Ámbar cálido (Parche disponible)
COLOR_STATUS_ALERT: Final[str] = "#f87171"    # Carmesí suave (Zero-Day / Error)
COLOR_BTN_PRIMARY: Final[str] = "#7c3aed"     # Púrpura táctico (Acción principal)
COLOR_BTN_HOVER: Final[str] = "#6d28d9"       # Púrpura resaltado

# Tipografías monoespaciadas tácticas
FONT_FAMILY: Final[str] = "Consolas" if tk.TkVersion >= 8.6 else "Courier"
FONT_TITLE: Final[tuple[str, int, str]] = (FONT_FAMILY, 13, "bold")
FONT_BODY: Final[tuple[str, int, str]] = (FONT_FAMILY, 10, "normal")
FONT_MUTED: Final[tuple[str, int, str]] = (FONT_FAMILY, 9, "italic")
FONT_BUTTON: Final[tuple[str, int, str]] = (FONT_FAMILY, 10, "bold")


def configure_app_theme(root: tk.Tk) -> ttk.Style:
    """Configura los estilos globales de ttk aplicando la paleta táctica."""
    root.configure(bg=COLOR_BG_DARK)

    style = ttk.Style(root)
    style.theme_use("clam")

    # Contenedores y Etiquetas
    style.configure("TFrame", background=COLOR_BG_DARK)
    style.configure(
        "Panel.TFrame",
        background=COLOR_BG_PANEL,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "TLabel",
        background=COLOR_BG_DARK,
        foreground=COLOR_TEXT_MAIN,
        font=FONT_BODY,
    )
    style.configure(
        "Muted.TLabel",
        background=COLOR_BG_DARK,
        foreground=COLOR_TEXT_MUTED,
        font=FONT_MUTED,
    )
    style.configure(
        "Header.TLabel",
        background=COLOR_BG_DARK,
        foreground=COLOR_TEXT_ACCENT,
        font=FONT_TITLE,
    )

    # Selector Desplegable (Combobox)
    style.configure(
        "TCombobox",
        fieldbackground=COLOR_BG_INPUT,
        background=COLOR_BG_PANEL,
        foreground=COLOR_TEXT_MAIN,
        arrowcolor=COLOR_TEXT_ACCENT,
        bordercolor=COLOR_BORDER,
        lightcolor=COLOR_BORDER,
        darkcolor=COLOR_BORDER,
        font=FONT_BODY,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLOR_BG_INPUT), ("focus", COLOR_BG_INPUT)],
        foreground=[("readonly", COLOR_TEXT_MAIN), ("focus", COLOR_TEXT_MAIN)],
    )

    # Botones
    style.configure(
        "Primary.TButton",
        background=COLOR_BTN_PRIMARY,
        foreground="#ffffff",
        bordercolor=COLOR_BTN_PRIMARY,
        font=FONT_BUTTON,
        padding=(10, 6),
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLOR_BTN_HOVER), ("disabled", COLOR_BORDER)],
        foreground=[("disabled", COLOR_TEXT_MUTED)],
    )

    # Tabla de Inventario (Treeview)
    style.configure(
        "Treeview",
        background=COLOR_BG_PANEL,
        foreground=COLOR_TEXT_MAIN,
        fieldbackground=COLOR_BG_PANEL,
        bordercolor=COLOR_BORDER,
        rowheight=26,
        font=FONT_BODY,
    )
    style.configure(
        "Treeview.Heading",
        background=COLOR_BG_INPUT,
        foreground=COLOR_TEXT_ACCENT,
        bordercolor=COLOR_BORDER,
        font=FONT_BUTTON,
        padding=(6, 4),
    )
    style.map(
        "Treeview",
        background=[("selected", "#2e3440")],
        foreground=[("selected", "#ffffff")],
    )

    return style
