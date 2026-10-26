"""Orquestador funcional de la interfaz gráfica (Tkinter).

Monta y renderiza la GUI sin clases ni herencia, conectando eventos
con el núcleo funcional inmutable y la persistencia atómica.
Incluye concurrencia asíncrona para auditorías en red.
"""

from __future__ import annotations

import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Any

from src.config import DATA_DIR
from src.gui.components import (
    create_ecosystem_combobox,
    create_feedback_banner,
    create_placeholder_entry,
)
from src.gui.theme import (
    COLOR_BG_DARK,
    COLOR_BG_PANEL,
    COLOR_BTN_PRIMARY,
    COLOR_STATUS_ALERT,
    COLOR_STATUS_CLEAN,
    COLOR_STATUS_PATCH,
    COLOR_TEXT_ACCENT,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
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
from src.auditor import audit_dependencies

CATALOG_PATH: Path = DATA_DIR / "osv_ecosystems.json"
INVENTORY_PATH: Path = DATA_DIR / "inventory.json"


def mount_app() -> tk.Tk:
    """Función constructora pura que ensambla la ventana y orquesta el flujo de eventos."""
    root = tk.Tk()
    root.title("OSV // THREAT_AUDITOR [v1.0.0]")
    root.geometry("980x720")
    root.minsize(850, 600)

    catalog = load_ecosystem_catalog(CATALOG_PATH)

    state: dict[str, Any] = {
        "project_name": "Enterprise-Core",
        "dependencies": (),
        "selected_index": None,
        "last_audit_results": (),
    }

    # Cola segura para comunicar el hilo de fondo con Tkinter
    audit_queue: queue.Queue[Any] = queue.Queue()

    configure_app_theme(root)

    main_container = tk.Frame(root, bg=COLOR_BG_DARK, padx=16, pady=14)
    main_container.pack(fill="both", expand=True)

    # --- ZONA 1: Telemetría ---
    header_frame = tk.Frame(main_container, bg=COLOR_BG_DARK)
    header_frame.pack(fill="x", pady=(0, 10))

    tk.Label(
        header_frame,
        text="OSV // THREAT_AUDITOR",
        font=FONT_TITLE,
        fg=COLOR_TEXT_ACCENT,
        bg=COLOR_BG_DARK,
    ).pack(side="left")

    lbl_telemetry = tk.Label(
        header_frame,
        text="[SYNC: READY | TARGETS: 00]",
        font=FONT_MUTED,
        fg=COLOR_TEXT_MUTED,
        bg=COLOR_BG_DARK,
    )
    lbl_telemetry.pack(side="right")

    # --- ZONA 2: Formulario ---
    form_panel = tk.Frame(main_container, bg=COLOR_BG_PANEL, relief="solid", borderwidth=1, padx=12, pady=10)
    form_panel.pack(fill="x", pady=(0, 6))

    form_panel.columnconfigure(0, weight=2)
    form_panel.columnconfigure(1, weight=2)
    form_panel.columnconfigure(2, weight=1)

    tk.Label(form_panel, text=f"> ECOSYSTEM / RUNTIME [{len(catalog)} SYNCED]", font=FONT_MUTED, fg=COLOR_TEXT_ACCENT, bg=COLOR_BG_PANEL).grid(row=0, column=0, sticky="w", padx=4, pady=(0, 2))
    lbl_eco_match = tk.Label(form_panel, text="↳ Presiona [Tab] para autocompletar sugerencias", font=FONT_MUTED, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_PANEL, anchor="w")

    def on_ecosystem_match(label: str | None, eco: str | None) -> None:
        if not label:
            query = combo_eco["get_selected"]()
            lbl_eco_match.configure(text=f"↳ ⚠ '{query}' no reconocido" if query else "↳ Presiona [Tab] para autocompletar", fg=COLOR_STATUS_ALERT if query else COLOR_TEXT_MUTED)
            return
        lbl_eco_match.configure(text=f"↳ ✓ Mapeado: {label} [Tab]", fg=COLOR_STATUS_CLEAN)

    combo_eco = create_ecosystem_combobox(form_panel, catalog=catalog, on_match_callback=on_ecosystem_match)
    combo_eco["widget"].grid(row=1, column=0, sticky="ew", padx=4)
    lbl_eco_match.grid(row=2, column=0, sticky="w", padx=4, pady=(2, 0))

    if catalog:
        combo_eco["set_text"](str(catalog[0].get("label", "")))

    def handle_smart_paste(name: str, version: str, eco: str | None) -> None:
        entry_name["set_value"](name)
        entry_ver["set_value"](version)
        if eco: combo_eco["set_by_name"](eco)
        feedback["show_info"](f"Smart-Paste: {name} v{version}")

    tk.Label(form_panel, text="> TARGET ARTIFACT", font=FONT_MUTED, fg=COLOR_TEXT_ACCENT, bg=COLOR_BG_PANEL).grid(row=0, column=1, sticky="w", padx=4, pady=(0, 2))
    entry_name = create_placeholder_entry(form_panel, placeholder="Ej: requests", on_smart_paste=handle_smart_paste)
    entry_name["widget"].grid(row=1, column=1, sticky="ew", padx=4)

    tk.Label(form_panel, text="> LOCKED VERSION", font=FONT_MUTED, fg=COLOR_TEXT_ACCENT, bg=COLOR_BG_PANEL).grid(row=0, column=2, sticky="w", padx=4, pady=(0, 2))
    entry_ver = create_placeholder_entry(form_panel, placeholder="Ej: 2.25.0")
    entry_ver["widget"].grid(row=1, column=2, sticky="ew", padx=4)

    # --- ZONA 3: Banner ---
    feedback = create_feedback_banner(main_container)
    feedback["widget"].pack(fill="x", pady=(0, 6))

    # --- ZONA 4: Tabla ---
    table_frame = tk.Frame(main_container, bg=COLOR_BG_PANEL, relief="solid", borderwidth=1)
    table_frame.pack(fill="both", expand=True, pady=(0, 8))

    columns = ("id", "ecosystem", "name", "version", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

    tree.heading("id", text="#"); tree.column("id", width=40, anchor="center")
    tree.heading("ecosystem", text="ECOSYSTEM"); tree.column("ecosystem", width=140, anchor="w")
    tree.heading("name", text="ARTIFACT / PKG"); tree.column("name", width=260, anchor="w")
    tree.heading("version", text="VERSION"); tree.column("version", width=110, anchor="center")
    tree.heading("status", text="AUDIT STATUS"); tree.column("status", width=280, anchor="w")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tree.tag_configure("clean", foreground=COLOR_STATUS_CLEAN)
    tree.tag_configure("patch", foreground=COLOR_STATUS_PATCH)
    tree.tag_configure("alert", foreground=COLOR_STATUS_ALERT)
    tree.tag_configure("unscanned", foreground=COLOR_TEXT_MAIN)

    def refresh_table() -> None:
        tree.delete(*tree.get_children())
        
        # Si tenemos resultados de auditoría recientes, los mostramos. Si no, datos en crudo.
        data_to_render = state["last_audit_results"] if state["last_audit_results"] else state["dependencies"]
        
        for idx, dep in enumerate(data_to_render):
            status_tag = dep.get("audit_status", "unscanned")
            mitigation = dep.get("mitigation", "[PENDING AUDIT]")
            
            tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    idx + 1,
                    dep.get("ecosystem", ""),
                    dep.get("name", ""),
                    dep.get("version", ""),
                    mitigation,
                ),
                tags=(status_tag,),
            )
        lbl_telemetry.configure(text=f"[PROJECT: {state['project_name']} | TARGETS: {len(data_to_render):02d}]")

    def reset_form() -> None:
        state["selected_index"] = None
        entry_name["reset"]()
        entry_ver["reset"]()
        btn_submit.configure(text="[ + INJECT TARGET ]")
        btn_cancel.pack_forget()
        btn_delete.pack_forget()
        for item in tree.selection():
            tree.selection_remove(item)

    def on_row_selected(_event: tk.Event[Any]) -> None:
        selected = tree.selection()
        if not selected: return
        index = int(selected[0])
        state["selected_index"] = index
        dep = state["dependencies"][index]
        combo_eco["set_by_name"](dep.get("ecosystem", ""))
        entry_name["set_value"](dep.get("name", ""))
        entry_ver["set_value"](dep.get("version", ""))
        btn_submit.configure(text="[ ⚡ OVERWRITE ]")
        btn_cancel.pack(side="left", padx=4)
        btn_delete.pack(side="left", padx=4)

    tree.bind("<<TreeviewSelect>>", on_row_selected)

    def handle_submit() -> None:
        payload = {"ecosystem": combo_eco["get_selected"](), "name": entry_name["get_value"](), "version": entry_ver["get_value"]()}
        try:
            if state["selected_index"] is None:
                state["dependencies"] = add_dependency(state["dependencies"], payload, catalog)
                msg = "Objetivo inyectado exitosamente."
            else:
                state["dependencies"] = update_dependency(state["dependencies"], state["selected_index"], payload, catalog)
                msg = "Registro actualizado."
            
            save_inventory_atomic(INVENTORY_PATH, state["project_name"], state["dependencies"])
            state["last_audit_results"] = () # Invalidar caché visual al mutar datos
            refresh_table()
            reset_form()
            feedback["show_success"](msg)
        except (ValueError, IndexError) as err:
            feedback["show_error"](str(err))

    def handle_delete() -> None:
        if state["selected_index"] is None: return
        try:
            state["dependencies"] = delete_dependency(state["dependencies"], state["selected_index"])
            save_inventory_atomic(INVENTORY_PATH, state["project_name"], state["dependencies"])
            state["last_audit_results"] = ()
            refresh_table()
            reset_form()
            feedback["show_success"]("Objetivo purgado.")
        except (ValueError, IndexError) as err:
            feedback["show_error"](str(err))

    btn_bar = tk.Frame(form_panel, bg=COLOR_BG_PANEL)
    btn_bar.grid(row=3, column=0, columnspan=3, sticky="e", pady=(10, 0), padx=4)
    btn_submit = tk.Button(btn_bar, text="[ + INJECT TARGET ]", font=FONT_BUTTON, bg=COLOR_BTN_PRIMARY, fg="#ffffff", activebackground=COLOR_TEXT_ACCENT, relief="flat", padx=10, pady=4, command=handle_submit)
    btn_submit.pack(side="left", padx=4)
    btn_cancel = tk.Button(btn_bar, text="[ ✕ CANCEL ]", font=FONT_BUTTON, bg=COLOR_BG_DARK, fg=COLOR_TEXT_MUTED, relief="flat", padx=8, pady=4, command=reset_form)
    btn_delete = tk.Button(btn_bar, text="[ 🗑 REMOVE ]", font=FONT_BUTTON, bg=COLOR_BG_DARK, fg=COLOR_STATUS_ALERT, relief="flat", padx=8, pady=4, command=handle_delete)
    entry_ver["widget"].bind("<Return>", lambda _e: handle_submit())

    # --- ZONA 5: Botonera y Hilos ---
    action_bar = tk.Frame(main_container, bg=COLOR_BG_DARK)
    action_bar.pack(fill="x")

    def check_audit_queue() -> None:
        try:
            result = audit_queue.get_nowait()
            if isinstance(result, Exception):
                feedback["show_error"](f"Error en red: {str(result)}")
            else:
                state["last_audit_results"] = result
                refresh_table()
                feedback["show_success"]("Escaneo de vulnerabilidades finalizado.")
            
            btn_audit.configure(text="[ 🚀 RUN THREAT AUDIT ]", state="normal")
            root.config(cursor="")
        except queue.Empty:
            root.after(150, check_audit_queue)

    def worker_scan(deps: tuple[dict[str, str], ...]) -> None:
        try:
            results = audit_dependencies(deps)
            audit_queue.put(results)
        except Exception as e:
            audit_queue.put(e)

    def trigger_audit() -> None:
        if not state["dependencies"]:
            feedback["show_error"]("El inventario está vacío. Añade objetivos primero.")
            return

        feedback["show_info"]("Escaneando objetivos contra OSV.dev (No cierres la ventana)...")
        btn_audit.configure(text="[ ⏳ SCANNING... ]", state="disabled")
        root.config(cursor="watch")

        # Inicia el hilo en segundo plano (daemon) para no bloquear la interfaz
        threading.Thread(target=worker_scan, args=(state["dependencies"],), daemon=True).start()
        root.after(150, check_audit_queue)

    btn_audit = tk.Button(action_bar, text="[ 🚀 RUN THREAT AUDIT ]", font=FONT_BUTTON, bg=COLOR_BTN_PRIMARY, fg="#ffffff", activebackground=COLOR_TEXT_ACCENT, relief="flat", padx=14, pady=8, command=trigger_audit)
    btn_audit.pack(side="right")

    if INVENTORY_PATH.exists():
        try:
            with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            state["project_name"] = data.get("project_name", "Enterprise-Core")
            state["dependencies"] = tuple(dict(d) for d in data.get("dependencies", []))
        except Exception as e:
            feedback["show_error"](f"Fallo al leer inventario: {e}")

    refresh_table()
    return root

def launch_gui() -> None:
    app = mount_app()
    app.mainloop()

if __name__ == "__main__":
    launch_gui()
