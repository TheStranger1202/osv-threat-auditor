"""Módulo de gestión funcional del inventario de dependencias.

Provee operaciones CRUD puras, validación contra el catálogo de OSV
y persistencia atómica en disco sin mutación de estado.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

FORBIDDEN_VERSION_CHARS_REGEX: re.Pattern[str] = re.compile(r"[\^~><=*]")


def load_ecosystem_catalog(catalog_path: Path) -> tuple[dict[str, Any], ...]:
    """Carga de forma inmutable el catálogo local de ecosistemas sincronizados."""
    if not catalog_path.exists():
        raise FileNotFoundError(
            f"El catálogo {catalog_path} no existe. Ejecuta scripts/update_ecosystems.py primero."
        )
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("El catálogo de ecosistemas debe ser un arreglo JSON.")
    return tuple(data)


def resolve_ecosystem(user_input: str, catalog: Sequence[Mapping[str, Any]]) -> str:
    """Resuelve y normaliza el ecosistema ingresado por el usuario usando coincidencia directa o alias.

    Args:
        user_input: Cadena ingresada por el usuario (ej: 'python', 'PyPI', 'node').
        catalog: Catálogo inmutable de ecosistemas de OSV.

    Returns:
        str: El nombre oficial del ecosistema reconocido por OSV (ej: 'PyPI').

    Raises:
        ValueError: Si el ecosistema o alias no está soportado.
    """
    cleaned = user_input.strip()
    if not cleaned:
        raise ValueError("El ecosistema no puede estar vacío.")

    cleaned_lower = cleaned.lower()

    # 1. Búsqueda exacta case-insensitive sobre el nombre oficial
    for item in catalog:
        official_name = str(item.get("ecosystem", ""))
        if official_name.lower() == cleaned_lower:
            return official_name

    # 2. Búsqueda sobre la lista de alias
    for item in catalog:
        aliases = [str(a).lower() for a in item.get("aliases", [])]
        if cleaned_lower in aliases:
            return str(item.get("ecosystem", ""))

    raise ValueError(
        f"El ecosistema o lenguaje '{cleaned}' no está soportado por OSV.dev."
    )


def validate_dependency(
    dep: Mapping[str, str], catalog: Sequence[Mapping[str, Any]]
) -> dict[str, str]:
    """Valida que una dependencia cumpla con las reglas estrictas de integridad.

    Returns:
        dict[str, str]: Registro limpio y estandarizado.

    Raises:
        ValueError: Si faltan campos o contienen operadores de rango abiertos.
    """
    raw_eco = dep.get("ecosystem", "")
    raw_name = dep.get("name", "")
    raw_ver = dep.get("version", "")

    if not raw_name or not raw_name.strip():
        raise ValueError("El nombre del paquete/librería es obligatorio.")
    if not raw_ver or not raw_ver.strip():
        raise ValueError("La versión del paquete/librería es obligatoria.")

    name = raw_name.strip()
    version = raw_ver.strip()

    if FORBIDDEN_VERSION_CHARS_REGEX.search(version) or version.lower() == "latest":
        raise ValueError(
            f"Versión inválida '{version}'. Solo se admiten versiones fijas exactas (sin '^', '~', '>=', '*')."
        )

    official_ecosystem = resolve_ecosystem(raw_eco, catalog)

    return {
        "ecosystem": official_ecosystem,
        "name": name,
        "version": version,
    }


def add_dependency(
    current_deps: Sequence[Mapping[str, str]],
    new_dep: Mapping[str, str],
    catalog: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, str], ...]:
    """Operación pura: Agrega una nueva dependencia retornando una nueva tupla.

    Raises:
        ValueError: Si la dependencia ya existe en el inventario bajo el mismo ecosistema.
    """
    validated = validate_dependency(new_dep, catalog)

    target_key = (validated["ecosystem"].lower(), validated["name"].lower())
    for dep in current_deps:
        existing_key = (dep.get("ecosystem", "").lower(), dep.get("name", "").lower())
        if existing_key == target_key:
            raise ValueError(
                f"El paquete '{validated['name']}' ya está registrado en {validated['ecosystem']}."
            )

    return tuple(dict(d) for d in current_deps) + (validated,)


def update_dependency(
    current_deps: Sequence[Mapping[str, str]],
    index: int,
    updated_dep: Mapping[str, str],
    catalog: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, str], ...]:
    """Operación pura: Reemplaza una dependencia en la posición indicada."""
    if not 0 <= index < len(current_deps):
        raise IndexError(f"Índice de inventario fuera de rango: {index}")

    validated = validate_dependency(updated_dep, catalog)
    target_key = (validated["ecosystem"].lower(), validated["name"].lower())

    # Comprobar que no colisione con otro registro existente en una posición distinta
    for i, dep in enumerate(current_deps):
        if i != index:
            existing_key = (dep.get("ecosystem", "").lower(), dep.get("name", "").lower())
            if existing_key == target_key:
                raise ValueError(
                    f"No se puede actualizar: '{validated['name']}' ya existe en la posición {i}."
                )

    new_list = [dict(d) for d in current_deps]
    new_list[index] = validated
    return tuple(new_list)


def delete_dependency(
    current_deps: Sequence[Mapping[str, str]], index: int
) -> tuple[dict[str, str], ...]:
    """Operación pura: Elimina una dependencia por índice retornando una nueva tupla."""
    if not 0 <= index < len(current_deps):
        raise IndexError(f"Índice de inventario fuera de rango: {index}")

    return tuple(dict(d) for i, d in enumerate(current_deps) if i != index)


def save_inventory_atomic(
    inventory_path: Path,
    project_name: str,
    dependencies: Sequence[Mapping[str, str]],
) -> None:
    """Escribe el inventario de forma atómica en disco usando un archivo temporal."""
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = inventory_path.with_suffix(".tmp")

    payload = {
        "project_name": project_name,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "dependencies": [dict(d) for d in dependencies],
    }

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())

    os.replace(temp_path, inventory_path)
