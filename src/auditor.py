"""Motor de auditoría y clasificación contra OSV.dev.

Implementa consultas en bloque, hidratación concurrente de vulnerabilidades
mediante ThreadPoolExecutor, y saneamiento de versiones para descartar hashes.
"""

from __future__ import annotations

import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Mapping, Sequence

OSV_QUERYBATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_VULN_URL = "https://api.osv.dev/v1/vulns/"

# Expresión regular para detectar hashes SHA-1 de Git (40 caracteres hexadecimales)
SHA1_REGEX = re.compile(r"^[0-9a-f]{40}$")


def extract_best_patch(vuln_data: Mapping[str, Any]) -> str | None:
    """Busca versiones 'fixed', filtrando hashes de Git para conservar versiones semánticas."""
    fixes: set[str] = set()
    
    def find_fixed_recursive(obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "fixed" and isinstance(v, str):
                    # Solo agregamos el parche si NO es un hash de commit
                    if not SHA1_REGEX.match(v):
                        fixes.add(v.strip())
                else:
                    find_fixed_recursive(v)
        elif isinstance(obj, list):
            for item in obj:
                find_fixed_recursive(item)
                
    find_fixed_recursive(vuln_data)
    
    if not fixes:
        return None
        
    try:
        from packaging.version import parse as parse_version
        return str(max(fixes, key=parse_version))
    except Exception:
        return sorted(list(fixes))[-1]


def get_full_vuln_details(vuln_id: str) -> tuple[str, dict[str, Any]]:
    """Descarga el manifiesto de una vulnerabilidad. Retorna tupla (id, datos) para el caché."""
    try:
        res = requests.get(f"{OSV_VULN_URL}{vuln_id}", timeout=10)
        res.raise_for_status()
        return vuln_id, res.json()
    except requests.RequestException:
        return vuln_id, {}


def audit_dependencies(
    dependencies: Sequence[Mapping[str, str]]
) -> tuple[dict[str, Any], ...]:
    """Evalúa dependencias con hidratación concurrente de metadatos."""
    if not dependencies:
        return ()

    queries = [
        {
            "package": {"ecosystem": dep.get("ecosystem", ""), "name": dep.get("name", "")},
            "version": dep.get("version", "")
        }
        for dep in dependencies
    ]

    # 1. Consulta inicial en bloque
    response = requests.post(OSV_QUERYBATCH_URL, json={"queries": queries}, timeout=20)
    response.raise_for_status()
    results = response.json().get("results", [])
    
    # 2. Recolectar todos los IDs únicos de vulnerabilidades para paralelizar su descarga
    unique_vuln_ids = set()
    for result in results:
        for vuln in result.get("vulns", []):
            if "id" in vuln:
                unique_vuln_ids.add(vuln["id"])

    # 3. Hidratación concurrente (Descarga masiva en paralelo)
    vuln_cache: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(get_full_vuln_details, vid) for vid in unique_vuln_ids}
        for future in as_completed(futures):
            vid, data = future.result()
            vuln_cache[vid] = data

    # 4. Consolidación de resultados usando los datos cacheados
    audit_report = []
    for dep, result in zip(dependencies, results):
        batch_vulns = result.get("vulns", [])
        enriched = dict(dep)
        enriched["vulns"] = batch_vulns
        
        if not batch_vulns:
            enriched["audit_status"] = "clean"
            enriched["mitigation"] = "[CLEAN] Sin riesgos conocidos"
        else:
            all_fixes = set()
            
            for batch_vuln in batch_vulns:
                vuln_id = batch_vuln.get("id")
                if vuln_id and vuln_id in vuln_cache:
                    full_vuln = vuln_cache[vuln_id]
                    patch = extract_best_patch(full_vuln)
                    if patch:
                        all_fixes.add(patch)

            if all_fixes:
                try:
                    from packaging.version import parse as parse_version
                    best_patch = str(max(list(all_fixes), key=parse_version))
                except Exception:
                    best_patch = sorted(list(all_fixes))[-1]
                    
                enriched["audit_status"] = "patch"
                enriched["mitigation"] = f"[UPGRADE -> {best_patch}] Parche disponible"
            else:
                enriched["audit_status"] = "alert"
                enriched["mitigation"] = f"[CRITICAL] {len(batch_vulns)} alerta(s) (Zero-Day/Sin parche)"
            
        audit_report.append(enriched)

    return tuple(audit_report)
