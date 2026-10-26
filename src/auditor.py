"""Módulo de lógica y clasificación de mitigaciones contra OSV.dev.

Evalúa el esquema OSV para determinar la disponibilidad de versiones 
parcheadas (fixed) o la ausencia de parches oficiales (Zero-Day).
Incluye el motor de consultas por lotes (batch).
"""

from __future__ import annotations

import requests
from typing import Any, Mapping, Sequence
from packaging.version import InvalidVersion, parse as parse_version

OSV_QUERYBATCH_URL = "https://api.osv.dev/v1/querybatch"


def parse_safe_version(version_str: str) -> Any:
    """Intenta parsear la versión de forma semántica; si falla, devuelve la cadena plana."""
    try:
        return parse_version(version_str)
    except InvalidVersion:
        return version_str


def select_best_fixed_version(
    candidates: Sequence[str], current_version: str
) -> str | None:
    """Función pura que selecciona la versión de parche más adecuada."""
    if not candidates:
        return None

    parsed_current = parse_safe_version(current_version)
    strictly_higher: list[str] = []
    
    for cand in candidates:
        parsed_cand = parse_safe_version(cand)
        try:
            if parsed_cand > parsed_current:
                strictly_higher.append(cand)
        except TypeError:
            if str(parsed_cand) > str(parsed_current):
                strictly_higher.append(cand)

    if strictly_higher:
        try:
            return min(strictly_higher, key=parse_safe_version)
        except TypeError:
            return min(strictly_higher)

    return candidates[-1]


def extract_fixed_version(
    vuln_data: Mapping[str, Any], package_name: str, current_version: str
) -> str | None:
    """Inspecciona los eventos de rangos afectados en búsqueda de un parche ('fixed')."""
    affected_blocks = vuln_data.get("affected", [])
    collected_fixes: list[str] = []

    for block in affected_blocks:
        pkg_info = block.get("package", {})
        if pkg_info and pkg_info.get("name") != package_name:
            continue

        ranges = block.get("ranges", [])
        for rng in ranges:
            events = rng.get("events", [])
            for event in events:
                if "fixed" in event:
                    collected_fixes.append(str(event["fixed"]))

    return select_best_fixed_version(tuple(collected_fixes), current_version)


def audit_dependencies(
    dependencies: Sequence[Mapping[str, str]]
) -> tuple[dict[str, Any], ...]:
    """Evalúa un lote de dependencias contra OSV.dev y aplica la lógica de parcheo.
    
    Returns:
        Una nueva tupla de diccionarios enriquecida con 'audit_status' y 'mitigation'.
    """
    if not dependencies:
        return ()

    queries = []
    for dep in dependencies:
        queries.append({
            "package": {"ecosystem": dep.get("ecosystem", ""), "name": dep.get("name", "")},
            "version": dep.get("version", "")
        })

    # Petición a la API oficial
    response = requests.post(OSV_QUERYBATCH_URL, json={"queries": queries}, timeout=20)
    response.raise_for_status()
    
    results = response.json().get("results", [])
    audit_report = []

    for dep, result in zip(dependencies, results):
        vulns = result.get("vulns", [])
        enriched_dep = dict(dep)
        enriched_dep["vulns"] = vulns
        
        if not vulns:
            enriched_dep["audit_status"] = "clean"
            enriched_dep["mitigation"] = "[CLEAN] Sin riesgos conocidos"
        else:
            # Usar tu lógica experta para buscar el mejor parche entre todas las vulnerabilidades
            best_patch = None
            for vuln in vulns:
                patch = extract_fixed_version(vuln, dep.get("name", ""), dep.get("version", ""))
                if patch:
                    best_patch = patch
                    break # Con un parche disponible basta para cambiar el semáforo

            if best_patch:
                enriched_dep["audit_status"] = "patch"
                enriched_dep["mitigation"] = f"[UPGRADE -> {best_patch}] Parche disponible"
            else:
                enriched_dep["audit_status"] = "alert"
                enriched_dep["mitigation"] = f"[CRITICAL] {len(vulns)} alerta(s) (Zero-Day/Sin parche)"
            
        audit_report.append(enriched_dep)

    return tuple(audit_report)
