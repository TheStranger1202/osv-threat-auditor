"""Servidor web y API REST mínima para OSV Threat Auditor.

Reutiliza de forma determinista el motor de auditoría concurrente y
las operaciones CRUD puras del inventario de software.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from flask import Flask, flash, redirect, render_template, request, url_for

from src.auditor import audit_dependencies
from src.config import DATA_DIR
from src.inventory_manager import (
    add_dependency,
    delete_dependency,
    load_ecosystem_catalog,
    save_inventory_atomic,
)

CATALOG_PATH: Path = DATA_DIR / "osv_ecosystems.json"
INVENTORY_PATH: Path = DATA_DIR / "inventory.json"

app = Flask(__name__, template_folder="templates")
app.secret_key = "osv-threat-auditor-internal-key"

# Estado en memoria para resultados de auditoría en la sesión del portal
STATE: dict[str, Any] = {
    "last_audit_results": (),
}


def get_current_inventory() -> tuple[str, tuple[dict[str, str], ...]]:
    """Carga el inventario actual desde disco de forma defensiva."""
    project_name = "Enterprise-Core"
    dependencies: tuple[dict[str, str], ...] = ()
    if INVENTORY_PATH.exists():
        try:
            with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            project_name = data.get("project_name", "Enterprise-Core")
            dependencies = tuple(dict(d) for d in data.get("dependencies", []))
        except Exception as e:
            flash(f"Error al leer el archivo de inventario: {e}", "error")
    return project_name, dependencies


@app.route("/", methods=["GET"])
def index() -> str:
    catalog = load_ecosystem_catalog(CATALOG_PATH)
    project_name, dependencies = get_current_inventory()

    # Si hay una auditoría activa, mostramos los hallazgos con mitigación;
    # si no, mostramos el inventario en crudo como 'unscanned'.
    if STATE["last_audit_results"]:
        items_to_render = STATE["last_audit_results"]
    else:
        items_to_render = [
            {
                **dep,
                "audit_status": "unscanned",
                "mitigation": "[PENDING AUDIT]",
            }
            for dep in dependencies
        ]

    return render_template(
        "index.html",
        project_name=project_name,
        catalog=catalog,
        items=items_to_render,
        total_targets=len(items_to_render),
    )


@app.route("/inject", methods=["POST"])
def inject_target() -> Any:
    catalog = load_ecosystem_catalog(CATALOG_PATH)
    project_name, current_deps = get_current_inventory()

    payload = {
        "ecosystem": request.form.get("ecosystem", "").strip(),
        "name": request.form.get("name", "").strip(),
        "version": request.form.get("version", "").strip(),
    }

    try:
        updated_deps = add_dependency(current_deps, payload, catalog)
        save_inventory_atomic(INVENTORY_PATH, project_name, updated_deps)
        STATE["last_audit_results"] = ()  # Invalida caché visual al mutar datos
        flash(f"Objetivo '{payload['name']}' inyectado exitosamente.", "success")
    except ValueError as err:
        flash(str(err), "error")

    return redirect(url_for("index"))


@app.route("/delete/<int:index>", methods=["POST"])
def remove_target(index: int) -> Any:
    project_name, current_deps = get_current_inventory()
    try:
        updated_deps = delete_dependency(current_deps, index)
        save_inventory_atomic(INVENTORY_PATH, project_name, updated_deps)
        STATE["last_audit_results"] = ()
        flash("Objetivo purgado del inventario.", "success")
    except (IndexError, ValueError) as err:
        flash(str(err), "error")

    return redirect(url_for("index"))


@app.route("/audit", methods=["POST"])
def run_audit() -> Any:
    _, dependencies = get_current_inventory()
    if not dependencies:
        flash("El inventario está vacío. Inyecta objetivos antes de auditar.", "error")
        return redirect(url_for("index"))

    try:
        results = audit_dependencies(dependencies)
        STATE["last_audit_results"] = results
        flash(f"Auditoría finalizada. {len(results)} dependencias evaluadas contra OSV.dev.", "success")
    except Exception as err:
        flash(f"Fallo en la comunicación con OSV.dev: {err}", "error")

    return redirect(url_for("index"))


if __name__ == "__main__":
    # Escucha en todas las interfaces de red locales para acceso en la intranet
    app.run(host="0.0.0.0", port=5000, debug=False)
