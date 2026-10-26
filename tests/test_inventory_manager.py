"""Pruebas unitarias para el gestor de inventario (src/inventory_manager.py)."""

import json
from pathlib import Path
import pytest

from src.inventory_manager import (
    add_dependency,
    delete_dependency,
    resolve_ecosystem,
    save_inventory_atomic,
    update_dependency,
    validate_dependency,
)

MOCK_CATALOG = (
    {"ecosystem": "PyPI", "label": "Python (PyPI)", "aliases": ["python", "pip"]},
    {"ecosystem": "npm", "label": "JavaScript (npm)", "aliases": ["node", "js"]},
    {"ecosystem": "Maven", "label": "Java (Maven)", "aliases": ["java", "spring"]},
)


def test_resolve_ecosystem_direct_and_alias():
    """Valida la resolución por nombre oficial y por alias de lenguaje."""
    assert resolve_ecosystem("pypi", MOCK_CATALOG) == "PyPI"
    assert resolve_ecosystem("python", MOCK_CATALOG) == "PyPI"
    assert resolve_ecosystem("node", MOCK_CATALOG) == "npm"


def test_resolve_ecosystem_invalid():
    """Valida que rechace ecosistemas inexistentes en el catálogo."""
    with pytest.raises(ValueError, match="no está soportado"):
        resolve_ecosystem("cobol", MOCK_CATALOG)


def test_validate_dependency_rejects_open_ranges():
    """Verifica que rechace operadores de rango abiertos."""
    bad_dep = {"ecosystem": "PyPI", "name": "requests", "version": "^2.25.0"}
    with pytest.raises(ValueError, match="Versión inválida"):
        validate_dependency(bad_dep, MOCK_CATALOG)


def test_add_dependency_success():
    """Verifica la agregación pura de una nueva dependencia."""
    initial = ({"ecosystem": "PyPI", "name": "requests", "version": "2.25.0"},)
    new_dep = {"ecosystem": "node", "name": "express", "version": "4.17.1"}

    result = add_dependency(initial, new_dep, MOCK_CATALOG)

    assert len(result) == 2
    assert result[1] == {"ecosystem": "npm", "name": "express", "version": "4.17.1"}
    # Verifica inmutabilidad de la tupla inicial
    assert len(initial) == 1


def test_add_dependency_duplicate_prevention():
    """Verifica que impida registrar duplicados en el mismo ecosistema."""
    initial = ({"ecosystem": "PyPI", "name": "requests", "version": "2.25.0"},)
    duplicate = {"ecosystem": "PyPI", "name": "requests", "version": "2.31.0"}

    with pytest.raises(ValueError, match="ya está registrado"):
        add_dependency(initial, duplicate, MOCK_CATALOG)


def test_update_dependency_success():
    """Verifica la sustitución inmutable de una versión."""
    initial = (
        {"ecosystem": "PyPI", "name": "requests", "version": "2.25.0"},
        {"ecosystem": "npm", "name": "express", "version": "4.17.1"},
    )
    updated = {"ecosystem": "PyPI", "name": "requests", "version": "2.31.0"}

    result = update_dependency(initial, 0, updated, MOCK_CATALOG)

    assert result[0]["version"] == "2.31.0"
    assert result[1]["name"] == "express"


def test_delete_dependency_success():
    """Verifica la eliminación por índice."""
    initial = (
        {"ecosystem": "PyPI", "name": "requests", "version": "2.25.0"},
        {"ecosystem": "npm", "name": "express", "version": "4.17.1"},
    )

    result = delete_dependency(initial, 0)

    assert len(result) == 1
    assert result[0]["name"] == "express"


def test_save_inventory_atomic(tmp_path: Path):
    """Verifica la persistencia atómica en disco."""
    test_file = tmp_path / "inventory.json"
    deps = ({"ecosystem": "PyPI", "name": "fastapi", "version": "0.95.0"},)

    save_inventory_atomic(test_file, "TestProject", deps)

    assert test_file.exists()
    with open(test_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["project_name"] == "TestProject"
    assert len(data["dependencies"]) == 1
    assert data["dependencies"][0]["name"] == "fastapi"
