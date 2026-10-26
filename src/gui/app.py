"""Ventana principal y orquestador de interfaz gráfica (Tkinter).

Ensambla la vista Dark Tactical / Cyber-Goth, gestiona la máquina de estados
del inventario y conecta eventos con el motor funcional.
"""

from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Any, Mapping

from src.config import DATA_DIR
from src.gui.components import (
    EcosystemCombobox,
    FeedbackBanner,
    PlaceholderEntry,
)
from src.gui.theme import (
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_BORDER,
    COLOR_BTN_PRIMARY,
    COLOR_STATUS_ALERT,
    COLOR_STATUS_CLEAN,
    COLOR_STATUS_PATCH,
    COLOR_TEXT_ACCENT,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
    FONT_BODY,
    FONT_BUTTON,
    FONT_MUTED,
    FONT_TITLE,
    configure_app_theme,
)
from src.inventory_manager import (
    add_dependency,
    delete_dependency,
    load_ecosystem_catalog,
    save_inventory_atomic,
    update_dependency,
)

CATALOG_PATH: Path = DATA_DIR / "osv_ecosystems.json"
INVENTORY_PATH: Path = DATA_DIR / "inventory.json"


class AuditorApp(tk.Tk):
    """Aplicación principal de auditoría con interfaz desacoplada."""

    def __init__(self) -> None:
        super().__init__()
        self.title("OSV // THREAT_AUDITOR [v1.0.0]")
        self.geometry("980x720")
        self.minsize(850, 600)

        # Cargar catálogo de ecosistemas
        self.catalog = load_ecosystem_catalog(CATALOG_PATH)

        # Estado local de la aplicación
        self.project_name: str = "Enterprise-Core"
        self.dependencies: tuple[dict[str, str], ...] = ()
        self.selected_index: int | None = None

        # Configuración del tema visual
        self.style = configure_app_theme(self)

        # Construcción visual
        self._build_layout()
        self._load_initial_inventory()

    def _build_layout(self) -> None:
        """Construye las 6 zonas de la interfaz táctica."""
        # Contenedor raíz con padding
        self.main_container = tk.Frame(self, bg=COLOR_BG_DARK, padx=16, pady=14)
        self.main_container.pack(fill="both", expand=True)

        self._build_header_zone()
        self._build_form_zone()
        self._build_feedback_zone()
        self._build_table_zone()
        self._build_action_zone()

    def _build_header_zone(self) -> None:
        """Zona 1: Header de telemetría y metadatos de proyecto."""
        header_frame = tk.Frame(self.main_container, bg=COLOR_BG_DARK)
        header_frame.pack(fill="x", pady=(0, 10))

        title_label = tk.Label(
            header_frame,
            text="OSV // THREAT_AUDITOR",
            font=FONT_TITLE,
            fg=COLOR_TEXT_ACCENT,
            bg=COLOR_BG_DARK,
        )
        title_label.pack(side="left")

        self.lbl_telemetry = tk.Label(
            header_frame,
            text="[SYNC: READY | TARGETS: 00]",
            font=FONT_MUTED,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_DARK,
        )
        self.lbl_telemetry.pack(side="right")

    def _build_form_zone(self) -> None:
        """Zona 2: Formulario reactivo para operaciones CRUD."""
        form_panel = tk.Frame(
            self.main_container,
            bg=COLOR_BG_PANEL,
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=10,
        )
        form_panel.pack(fill="x", pady=(0, 6))

        # Rejilla de 3 campos: Ecosistema, Nombre, Versión
        form_panel.columnconfigure(0, weight=2)
        form_panel.columnconfigure(1, weight=2)
        form_panel.columnconfigure(2, weight=1)

        # Campo 1: Ecosistema / Lenguaje
        tk.Label(
            form_panel,
            text="> ECOSYSTEM / RUNTIME",
            font=FONT_MUTED,
            fg=COLOR_TEXT_ACCENT,
            bg=COLOR_BG_PANEL,
        ).grid(row=0, column=0, sticky="w", padx=4, pady=(0, 2))

        self.combo_eco = EcosystemCombobox(form_panel, catalog=self.catalog)
        self.combo_eco.grid(row=1, column=0, sticky="ew", padx=4)
        if self.catalog:
            self.combo_eco.set(str(self.catalog[0].get("label", "")))

        # Campo 2: Nombre de la Librería con Smart-Paste
        tk.Label(
            form_panel,
            text="> TARGET ARTIFACT",
            font=FONT_MUTED,
            fg=COLOR_TEXT_ACCENT,
            bg=COLOR_BG_PANEL,
        ).grid(row=0, column=1, sticky="w", padx=4, pady=(0, 2))

        self.entry_name = PlaceholderEntry(
            form_panel,
            placeholder="Ej: requests, express, log4j-core",
            on_smart_paste=self._handle_smart_paste,
        )
        self.entry_name.grid(row=1, column=1, sticky="ew", padx=4)

        # Campo 3: Versión Fija
        tk.Label(
            form_panel,
            text="> LOCKED VERSION",
            font=FONT_MUTED,
            fg=COLOR_TEXT_ACCENT,
            bg=COLOR_BG_PANEL,
        ).grid(row=0, column=2, sticky="w", padx=4, pady=(0, 2))

        self.entry_ver = PlaceholderEntry(
            form_panel,
            placeholder="Ej: 2.25.0, 4.17.1",
        )
        self.entry_ver.grid(row=1, column=2, sticky="ew", padx=4)

        # Atajo: presionar Enter en versión guarda directamente
        self.entry_ver.bind("<Return>", lambda _e: self._handle_submit())

        # Botonera de acciones CRUD
        btn_bar = tk.Frame(form_panel, bg=COLOR_BG_PANEL)
        btn_bar.grid(row=2, column=0, columnspan=3, sticky="e", pady=(10, 0), padx=4)

        self.btn_submit = tk.Button(
            btn_bar,
            text="[ + INJECT TARGET ]",
            font=FONT_BUTTON,
            bg=COLOR_BTN_PRIMARY,
            fg="#ffffff",
            activebackground=COLOR_TEXT_ACCENT,
            relief="flat",
            padx=10,
            pady=4,
            command=self._handle_submit,
        )
        self.btn_submit.pack(side="left", padx=4)

        self.btn_cancel = tk.Button(
            btn_bar,
            text="[ ✕ CANCEL ]",
            font=FONT_BUTTON,
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_MUTED,
            relief="flat",
            padx=8,
            pady=4,
            command=self._reset_form,
        )
        self.btn_cancel.pack(side="left", padx=4)
        self.btn_cancel.pack_forget()  # Oculto en modo creación

        self.btn_delete = tk.Button(
            btn_bar,
            text="[ 🗑 REMOVE ]",
            font=FONT_BUTTON,
            bg=COLOR_BG_DARK,
            fg=COLOR_STATUS_ALERT,
            relief="flat",
            padx=8,
            pady=4,
            command=self._handle_delete,
        )
        self.btn_delete.pack(side="left", padx=4)
        self.btn_delete.pack_forget()  # Oculto en modo creación

    def _build_feedback_zone(self) -> None:
        """Zona 3: Banner de notificaciones en línea."""
        self.feedback = FeedbackBanner(self.main_container)
        self.feedback.pack(fill="x", pady=(0, 6))

    def _build_table_zone(self) -> None:
        """Zona 4: Matriz de inventario y estado."""
        table_frame = tk.Frame(self.main_container, bg=COLOR_BG_PANEL, relief="solid", borderwidth=1)
        table_frame.pack(fill="both", expand=True, pady=(0, 8))

        columns = ("id", "ecosystem", "name", "version", "status")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("id", text="#", anchor="center")
        self.tree.heading("ecosystem", text="ECOSYSTEM", anchor="w")
        self.tree.heading("name", text="ARTIFACT / PKG", anchor="w")
        self.tree.heading("version", text="VERSION", anchor="center")
        self.tree.heading("status", text="AUDIT STATUS", anchor="w")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("ecosystem", width=140, anchor="w")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("version", width=110, anchor="center")
        self.tree.column("status", width=280, anchor="w")

        # Scrollbar vertical ergonómico
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Configuración de tags de color para las filas
        self.tree.tag_configure("clean", foreground=COLOR_STATUS_CLEAN)
        self.tree.tag_configure("patch", foreground=COLOR_STATUS_PATCH)
        self.tree.tag_configure("alert", foreground=COLOR_STATUS_ALERT)
        self.tree.tag_configure("unscanned", foreground=COLOR_TEXT_MAIN)

        # Evento de selección de fila
        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

    def _build_action_zone(self) -> None:
        """Zona 5: Barra de control para disparar auditorías."""
        action_bar = tk.Frame(self.main_container, bg=COLOR_BG_DARK)
        action_bar.pack(fill="x")

        self.btn_audit = tk.Button(
            action_bar,
            text="[ 🚀 RUN THREAT AUDIT ]",
            font=FONT_BUTTON,
            bg=COLOR_BTN_PRIMARY,
            fg="#ffffff",
            activebackground=COLOR_TEXT_ACCENT,
            relief="flat",
            padx=14,
            pady=8,
            command=self._trigger_audit,
        )
        self.btn_audit.pack(side="right")

    # --- Lógica de Manejo de Estado e Inventario ---

    def _load_initial_inventory(self) -> None:
        """Lee el inventario de data/inventory.json y refresca la tabla."""
        if INVENTORY_PATH.exists():
            try:
                with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.project_name = data.get("project_name", "Enterprise-Core")
                raw_deps = data.get("dependencies", [])
                self.dependencies = tuple(dict(d) for d in raw_deps)
            except Exception as e:
                self.feedback.show_error(f"Fallo al leer inventario: {e}")
                self.dependencies = ()
        else:
            self.dependencies = ()

        self._refresh_table()

    def _refresh_table(self) -> None:
        """Limpia y repuebla el Treeview a partir de la tupla inmutable de dependencias."""
        self.tree.delete(*self.tree.get_children())
        for idx, dep in enumerate(self.dependencies):
            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    idx + 1,
                    dep.get("ecosystem", ""),
                    dep.get("name", ""),
                    dep.get("version", ""),
                    "[PENDING AUDIT]",
                ),
                tags=("unscanned",),
            )
        self.lbl_telemetry.configure(
            text=f"[PROJECT: {self.project_name} | TARGETS: {len(self.dependencies):02d}]"
        )

    def _on_row_selected(self, _event: tk.Event[Any]) -> None:
        """Carga los datos de la fila seleccionada en el formulario en modo edición."""
        selected = self.tree.selection()
        if not selected:
            return

        index = int(selected[0])
        self.selected_index = index
        dep = self.dependencies[index]

        self.combo_eco.set_ecosystem_by_name(dep.get("ecosystem", ""))
        self.entry_name.set_clean_value(dep.get("name", ""))
        self.entry_ver.set_clean_value(dep.get("version", ""))

        # Transición a Modo Edición
        self.btn_submit.configure(text="[ ⚡ OVERWRITE ]")
        self.btn_cancel.pack(side="left", padx=4)
        self.btn_delete.pack(side="left", padx=4)

    def _reset_form(self) -> None:
        """Restaura el formulario al estado de inserción limpia."""
        self.selected_index = None
        self.entry_name.delete(0, tk.END)
        self.entry_name.put_placeholder()
        self.entry_ver.delete(0, tk.END)
        self.entry_ver.put_placeholder()

        self.btn_submit.configure(text="[ + INJECT TARGET ]")
        self.btn_cancel.pack_forget()
        self.btn_delete.pack_forget()

        # Deseleccionar fila en el Treeview
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def _handle_smart_paste(self, name: str, version: str, eco: str | None) -> None:
        """Callback invocado por PlaceholderEntry cuando detecta texto 'pkg==ver'."""
        self.entry_name.set_clean_value(name)
        self.entry_ver.set_clean_value(version)
        if eco:
            self.combo_eco.set_ecosystem_by_name(eco)
        self.feedback.show_info(f"Smart-Paste detectado: {name} v{version}")

    def _handle_submit(self) -> None:
        """Procesa la inserción o actualización funcional del inventario."""
        raw_eco = self.combo_eco.get_selected_ecosystem()
        name = self.entry_name.get_clean_value()
        version = self.entry_ver.get_clean_value()

        payload = {"ecosystem": raw_eco, "name": name, "version": version}

        try:
            if self.selected_index is None:
                # Inserción pura
                new_deps = add_dependency(self.dependencies, payload, self.catalog)
                action_text = f"Objetivo '{name} {version}' inyectado exitosamente."
            else:
                # Modificación pura
                new_deps = update_dependency(
                    self.dependencies, self.selected_index, payload, self.catalog
                )
                action_text = f"Registro #{self.selected_index + 1} actualizado a '{name} {version}'."

            # Persistencia atómica
            save_inventory_atomic(INVENTORY_PATH, self.project_name, new_deps)
            self.dependencies = new_deps
            self._refresh_table()
            self._reset_form()
            self.feedback.show_success(action_text)

        except (ValueError, IndexError) as err:
            self.feedback.show_error(str(err))

    def _handle_delete(self) -> None:
        """Elimina el registro actualmente seleccionado."""
        if self.selected_index is None:
            return

        try:
            target_dep = self.dependencies[self.selected_index]
            new_deps = delete_dependency(self.dependencies, self.selected_index)
            save_inventory_atomic(INVENTORY_PATH, self.project_name, new_deps)

            self.dependencies = new_deps
            self._refresh_table()
            self._reset_form()
            self.feedback.show_success(
                f"Objetivo '{target_dep.get('name')}' purgado del inventario."
            )
        except (ValueError, IndexError) as err:
            self.feedback.show_error(str(err))

    def _trigger_audit(self) -> None:
        """Punto de enganche para la auditoría asíncrona (Hito 2)."""
        self.feedback.show_info("Iniciando conexión con OSV.dev...")


def launch_gui() -> None:
    """Función de entrada para arrancar la aplicación de escritorio."""
    app = AuditorApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
