"""Ventana principal y controlador de la interfaz gráfica (Dark Tactical HUD).

Orquesta el estado unidireccional de la UI, enlaza las operaciones CRUD
funcionales con persistencia atómica y ejecuta escaneos asíncronos en segundo plano.
"""

from __future__ import annotations

import json
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk
from typing import Any, Mapping

# Asegurar importación de src independientemente de la ruta de invocación
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.config import DATA_DIR
except ImportError:
    DATA_DIR = PROJECT_ROOT / "data"

from src.gui.components import (
    EcosystemCombobox,
    FeedbackBanner,
    PlaceholderEntry,
)
from src.gui.theme import (
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_BORDER,
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

INVENTORY_PATH: Path = DATA_DIR / "inventory.json"
CATALOG_PATH: Path = DATA_DIR / "osv_ecosystems.json"


class ThreatAuditorApp:
    """Controlador y contenedor visual de la aplicación."""

    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        self.root.title("OSV // THREAT_AUDITOR — [CYBER_DEFENSE]")
        self.root.geometry("1020x720")
        self.root.minsize(920, 640)

        configure_app_theme(self.root)

        # Estado en memoria
        self.catalog: tuple[dict[str, Any], ...] = self._safe_load_catalog()
        self.project_name: str = "Enterprise-Core"
        self.dependencies: tuple[dict[str, str], ...] = ()
        self.selected_index: int | None = None
        self.audit_results: dict[tuple[str, str], dict[str, Any]] = {}

        # Cola de comunicación entre hilos
        self.audit_queue: queue.Queue[Any] = queue.Queue()

        # Construcción visual
        self._build_header()
        self._build_form_deck()
        self._build_banner()
        self._build_matrix_treeview()
        self._build_action_bar()
        self._build_mitigation_panel()

        # Cargar datos iniciales
        self._load_initial_inventory()
        self._check_audit_queue()

    # --- Carga y Persistencia Segura ---

    def _safe_load_catalog(self) -> tuple[dict[str, Any], ...]:
        try:
            return load_ecosystem_catalog(CATALOG_PATH)
        except Exception:
            # Fallback seguro con ecosistemas primarios si el JSON no existe aún
            return (
                {"ecosystem": "PyPI", "label": "Python (PyPI)", "aliases": ["python", "pip"]},
                {"ecosystem": "npm", "label": "JavaScript (npm)", "aliases": ["node", "js"]},
                {"ecosystem": "Maven", "label": "Java (Maven)", "aliases": ["java", "jvm"]},
                {"ecosystem": "crates.io", "label": "Rust (crates.io)", "aliases": ["rust", "cargo"]},
                {"ecosystem": "Go", "label": "Go (Golang)", "aliases": ["go"]},
            )

    def _load_initial_inventory(self) -> None:
        if not INVENTORY_PATH.exists():
            self.dependencies = ()
            self._render_treeview()
            return

        try:
            with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.project_name = data.get("project_name", "Enterprise-Core")
                self.dependencies = tuple(data.get("dependencies", []))
        except Exception as e:
            self.banner.show_error(f"Error al leer {INVENTORY_PATH.name}: {e}")
            self.dependencies = ()

        self.lbl_telemetry.configure(
            text=f"TARGETS: {len(self.dependencies):02d} | ECOSYSTEMS: {len(self.catalog):02d}"
        )
        self._render_treeview()

    # --- Ensamblado del Layout ---

    def _build_header(self) -> None:
        header_frame = tk.Frame(self.root, bg=COLOR_BG_DARK, pady=10, padx=15)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="OSV // THREAT_AUDITOR",
            font=FONT_TITLE,
            fg=COLOR_TEXT_ACCENT,
            bg=COLOR_BG_DARK,
        )
        title_lbl.pack(side="left")

        self.lbl_telemetry = tk.Label(
            header_frame,
            text="TARGETS: 00 | ECOSYSTEMS: 00",
            font=FONT_MUTED,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_DARK,
        )
        self.lbl_telemetry.pack(side="right")

    def _build_form_deck(self) -> None:
        form_frame = tk.LabelFrame(
            self.root,
            text=" [ DEPENDENCY_INJECTION_DECK ] ",
            bg=COLOR_BG_PANEL,
            fg=COLOR_TEXT_ACCENT,
            font=FONT_BUTTON,
            relief="solid",
            bd=1,
            padx=12,
            pady=10,
        )
        form_frame.pack(fill="x", padx=15, pady=(0, 6))

        # Grid de campos
        form_frame.columnconfigure(0, weight=2)
        form_frame.columnconfigure(1, weight=2)
        form_frame.columnconfigure(2, weight=1)

        # Fila 1: Labels
        tk.Label(form_frame, text="> ECOSYSTEM:", bg=COLOR_BG_PANEL, fg=COLOR_TEXT_MAIN, font=FONT_BODY).grid(
            row=0, column=0, sticky="w", padx=4, pady=(0, 2)
        )
        tk.Label(form_frame, text="> TARGET_PKG:", bg=COLOR_BG_PANEL, fg=COLOR_TEXT_MAIN, font=FONT_BODY).grid(
            row=0, column=1, sticky="w", padx=4, pady=(0, 2)
        )
        tk.Label(form_frame, text="> LOCKED_VER:", bg=COLOR_BG_PANEL, fg=COLOR_TEXT_MAIN, font=FONT_BODY).grid(
            row=0, column=2, sticky="w", padx=4, pady=(0, 2)
        )

        # Fila 2: Inputs
        self.cmb_eco = EcosystemCombobox(form_frame, catalog=self.catalog)
        self.cmb_eco.grid(row=1, column=0, sticky="ew", padx=4, pady=2)
        if self.catalog:
            self.cmb_eco.set(str(self.catalog[0].get("label", "")))

        self.ent_name = PlaceholderEntry(
            form_frame,
            placeholder="Ej: requests, lodash, log4j-core",
            on_smart_paste=self._handle_smart_paste,
        )
        self.ent_name.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        self.ent_ver = PlaceholderEntry(
            form_frame,
            placeholder="Ej: 2.25.0",
        )
        self.ent_ver.grid(row=1, column=2, sticky="ew", padx=4, pady=2)
        self.ent_ver.bind("<Return>", lambda _e: self._on_save_clicked())

        # Fila 3: Botonera de acciones
        btn_frame = tk.Frame(form_frame, bg=COLOR_BG_PANEL)
        btn_frame.grid(row=2, column=0, columnspan=3, sticky="e", pady=(10, 0), padx=4)

        self.btn_save = ttk.Button(
            btn_frame,
            text="+ INJECT_DEPENDENCY",
            style="Primary.TButton",
            command=self._on_save_clicked,
        )
        self.btn_save.pack(side="left", padx=4)

        self.btn_cancel = ttk.Button(
            btn_frame,
            text="✕ CANCEL",
            style="Secondary.TButton",
            command=self._reset_form,
        )

        self.btn_delete = ttk.Button(
            btn_frame,
            text="🗑 DELETE",
            style="Secondary.TButton",
            command=self._on_delete_clicked,
        )

    def _build_banner(self) -> None:
        self.banner = FeedbackBanner(self.root)
        self.banner.pack(fill="x", padx=15, pady=(0, 4))

    def _build_matrix_treeview(self) -> None:
        tree_frame = tk.Frame(self.root, bg=COLOR_BG_DARK)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=4)

        columns = ("idx", "eco", "name", "ver", "verdict")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("idx", text="#")
        self.tree.heading("eco", text="ECOSYSTEM")
        self.tree.heading("name", text="PACKAGE_NAME")
        self.tree.heading("ver", text="LOCKED_VERSION")
        self.tree.heading("verdict", text="TACTICAL_STATUS")

        self.tree.column("idx", width=45, anchor="center")
        self.tree.column("eco", width=140, anchor="w")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("ver", width=120, anchor="w")
        self.tree.column("verdict", width=340, anchor="w")

        # Scrollbar vertical ergonómica
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Tags de color para el semáforo
        self.tree.tag_configure("clean", foreground=COLOR_STATUS_CLEAN)
        self.tree.tag_configure("patch", foreground=COLOR_STATUS_PATCH)
        self.tree.tag_configure("alert", foreground=COLOR_STATUS_ALERT)
        self.tree.tag_configure("pending", foreground=COLOR_TEXT_MUTED)

        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)
        self.tree.bind("<Delete>", lambda _e: self._on_delete_clicked())

    def _build_action_bar(self) -> None:
        bar_frame = tk.Frame(self.root, bg=COLOR_BG_DARK, pady=6, padx=15)
        bar_frame.pack(fill="x")

        self.btn_audit = ttk.Button(
            bar_frame,
            text="⚡ EXECUTE_THREAT_AUDIT (OSV.dev)",
            style="Primary.TButton",
            command=self._on_audit_clicked,
        )
        self.btn_audit.pack(side="left")

        self.progress = ttk.Progressbar(bar_frame, mode="indeterminate", length=220)

    def _build_mitigation_panel(self) -> None:
        self.pnl_mitigation = tk.LabelFrame(
            self.root,
            text=" [ MITIGATION_CONSOLE ] ",
            bg=COLOR_BG_PANEL,
            fg=COLOR_TEXT_ACCENT,
            font=FONT_BUTTON,
            relief="solid",
            bd=1,
            padx=10,
            pady=6,
        )
        self.pnl_mitigation.pack(fill="x", padx=15, pady=(0, 10))

        self.lbl_mitigation = tk.Label(
            self.pnl_mitigation,
            text="Selecciona una dependencia o ejecuta una auditoría para desplegar tácticas de mitigación.",
            bg=COLOR_BG_PANEL,
            fg=COLOR_TEXT_MUTED,
            font=FONT_MUTED,
            anchor="w",
            justify="left",
        )
        self.lbl_mitigation.pack(side="left", fill="x", expand=True)

        self.btn_copy_prompt = ttk.Button(
            self.pnl_mitigation,
            text="📋 COPY_AI_PROMPT",
            style="Secondary.TButton",
            command=self._on_copy_prompt_clicked,
        )

    # --- Renderizado de Datos ---

    def _render_treeview(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for idx, dep in enumerate(self.dependencies, start=1):
            key = (dep.get("ecosystem", "").lower(), dep.get("name", "").lower())
            audit = self.audit_results.get(key)

            if audit is None:
                tag = "pending"
                verdict = "[PENDING_AUDIT]"
            elif audit.get("vuln_count", 0) == 0:
                tag = "clean"
                verdict = "✓ CLEAN (No OSV CVEs)"
            elif audit.get("patch_version"):
                tag = "patch"
                verdict = f"⚠ UPGRADE -> >= {audit['patch_version']}"
            else:
                tag = "alert"
                verdict = f"🚨 ZERO-DAY / NO PATCH ({audit.get('vuln_count')} CVEs)"

            self.tree.insert(
                "",
                "end",
                iid=str(idx - 1),
                values=(
                    f"{idx:02d}",
                    dep.get("ecosystem", ""),
                    dep.get("name", ""),
                    dep.get("version", ""),
                    verdict,
                ),
                tags=(tag,),
            )

        self.lbl_telemetry.configure(
            text=f"TARGETS: {len(self.dependencies):02d} | ECOSYSTEMS: {len(self.catalog):02d}"
        )

    # --- Controladores de Eventos CRUD ---

    def _handle_smart_paste(self, name: str, ver: str, eco: str | None) -> None:
        """Pega inteligentemente valores estructurados tipo requests==2.25.0."""
        self.ent_name.set_clean_value(name)
        self.ent_ver.set_clean_value(ver)
        if eco:
            self.cmb_eco.set_ecosystem_by_name(eco)
        self.banner.show_info(f"Smart-Paste detectado: '{name} v{ver}'", timeout_ms=2500)

    def _on_row_selected(self, _event: tk.Event[Any]) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        idx = int(selected[0])
        self.selected_index = idx
        dep = self.dependencies[idx]

        # Cargar datos en el formulario
        self.cmb_eco.set_ecosystem_by_name(dep.get("ecosystem", ""))
        self.ent_name.set_clean_value(dep.get("name", ""))
        self.ent_ver.set_clean_value(dep.get("version", ""))

        # Activar modo edición
        self.btn_save.configure(text="⚡ OVERWRITE_RECORD")
        self.btn_cancel.pack(side="left", padx=4)
        self.btn_delete.pack(side="left", padx=4)

        # Actualizar panel de mitigación
        key = (dep.get("ecosystem", "").lower(), dep.get("name", "").lower())
        audit = self.audit_results.get(key)
        if audit and audit.get("vuln_count", 0) > 0:
            msg = f"Alerta en {dep['name']}: {audit.get('summary', 'Vulnerabilidades detectadas.')}"
            self.lbl_mitigation.configure(text=msg, fg=COLOR_STATUS_ALERT)
            self.btn_copy_prompt.pack(side="right", padx=6)
        else:
            self.lbl_mitigation.configure(
                text=f"Objetivo: {dep['name']} ({dep['version']}) en {dep['ecosystem']}. Sin mitigaciones requeridas.",
                fg=COLOR_TEXT_MAIN,
            )
            self.btn_copy_prompt.pack_forget()

    def _reset_form(self) -> None:
        self.selected_index = None
        self.ent_name.set_clean_value("")
        self.ent_name.put_placeholder()
        self.ent_ver.set_clean_value("")
        self.ent_ver.put_placeholder()

        self.btn_save.configure(text="+ INJECT_DEPENDENCY")
        self.btn_cancel.pack_forget()
        self.btn_delete.pack_forget()
        self.btn_copy_prompt.pack_forget()
        self.tree.selection_remove(self.tree.selection())
        self.lbl_mitigation.configure(
            text="Selecciona una dependencia o ejecuta una auditoría para desplegar tácticas de mitigación.",
            fg=COLOR_TEXT_MUTED,
        )

    def _on_save_clicked(self) -> None:
        eco_raw = self.cmb_eco.get_selected_ecosystem()
        name_raw = self.ent_name.get_clean_value()
        ver_raw = self.ent_ver.get_clean_value()

        candidate = {"ecosystem": eco_raw, "name": name_raw, "version": ver_raw}

        try:
            if self.selected_index is None:
                # CREATE
                new_deps = add_dependency(self.dependencies, candidate, self.catalog)
                self.dependencies = new_deps
                save_inventory_atomic(INVENTORY_PATH, self.project_name, self.dependencies)
                self.banner.show_success(f"Inyectado con éxito: '{name_raw} {ver_raw}'")
            else:
                # UPDATE
                new_deps = update_dependency(
                    self.dependencies, self.selected_index, candidate, self.catalog
                )
                self.dependencies = new_deps
                save_inventory_atomic(INVENTORY_PATH, self.project_name, self.dependencies)
                self.banner.show_success(f"Actualizado con éxito: '{name_raw} {ver_raw}'")

            self._reset_form()
            self._render_treeview()

        except (ValueError, IndexError) as err:
            self.banner.show_error(str(err))

    def _on_delete_clicked(self) -> None:
        if self.selected_index is None:
            return

        target_name = self.dependencies[self.selected_index].get("name", "dependencia")
        try:
            self.dependencies = delete_dependency(self.dependencies, self.selected_index)
            save_inventory_atomic(INVENTORY_PATH, self.project_name, self.dependencies)
            self.banner.show_success(f"Objetivo '{target_name}' eliminado del inventario.")
            self._reset_form()
            self._render_treeview()
        except IndexError as err:
