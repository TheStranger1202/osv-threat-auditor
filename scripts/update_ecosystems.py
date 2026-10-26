"""Script utilitario para sincronizar el catálogo oficial de ecosistemas de OSV.

Descarga la lista viva desde el bucket de Google y genera el archivo
data/osv_ecosystems.json enriquecido con alias comunes.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping
import requests

# Resuelve la raíz del proyecto y la inserta en sys.path para permitir
# imports de 'src' independientemente de la carpeta donde se ejecute el script.
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_DIR, REQUEST_TIMEOUT_SECONDS

OFFICIAL_ECOSYSTEMS_URL: str = (
    "https://storage.googleapis.com/osv-vulnerabilities/ecosystems.txt"
)
OUTPUT_FILE: Path = DATA_DIR / "osv_ecosystems.json"

# Diccionario de enriquecimiento con nombres amigables y alias de búsqueda
HUMAN_MAPPINGS: Mapping[str, dict[str, Any]] = {
    "PyPI": {
        "label": "Python (PyPI)",
        "aliases": ["python", "pip", "py", "django", "fastapi", "flask"],
    },
    "npm": {
        "label": "JavaScript / Node.js (npm)",
        "aliases": ["node", "nodejs", "js", "typescript", "ts", "react", "vue", "express"],
    },
    "Maven": {
        "label": "Java / Kotlin (Maven)",
        "aliases": ["java", "jvm", "kotlin", "scala", "spring", "spring-boot", "gradle"],
    },
    "Go": {
        "label": "Go (Golang)",
        "aliases": ["go", "golang", "gin", "fiber"],
    },
    "crates.io": {
        "label": "Rust (crates.io)",
        "aliases": ["rust", "cargo", "tokio", "serde"],
    },
    "NuGet": {
        "label": ".NET / C# (NuGet)",
        "aliases": ["dotnet", "c#", "csharp", "nuget", "aspnet"],
    },
    "Packagist": {
        "label": "PHP (Packagist)",
        "aliases": ["php", "composer", "laravel", "symfony"],
    },
    "RubyGems": {
        "label": "Ruby (RubyGems)",
        "aliases": ["ruby", "rails", "gem"],
    },
    "Pub": {
        "label": "Dart / Flutter (Pub)",
        "aliases": ["flutter", "dart", "pub"],
    },
    "Hex": {
        "label": "Elixir / Erlang (Hex)",
        "aliases": ["elixir", "erlang", "mix", "phoenix"],
    },
    "Conan": {
        "label": "C / C++ (Conan)",
        "aliases": ["c", "c++", "cpp", "conan"],
    },
    "SwiftURL": {
        "label": "Swift (Swift Package Manager)",
        "aliases": ["swift", "spm", "apple", "ios"],
    },
}


def fetch_raw_ecosystems() -> tuple[str, ...]:
    """Obtiene la lista plana de ecosistemas desde la fuente oficial de OSV."""
    response = requests.get(OFFICIAL_ECOSYSTEMS_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    lines = (line.strip() for line in response.text.splitlines())
    return tuple(line for line in lines if line)


def build_ecosystem_catalog(raw_ecosystems: tuple[str, ...]) -> list[dict[str, Any]]:
    """Transforma la lista plana en un catálogo estructurado para autocompletado."""
    catalog = []
    for eco in raw_ecosystems:
        meta = HUMAN_MAPPINGS.get(eco, {})
        label = meta.get("label", f"{eco} (Sistema / OS)")
        aliases = meta.get("aliases", [eco.lower()])

        catalog.append({
            "ecosystem": eco,
            "label": label,
            "aliases": aliases,
        })
    return catalog


def main() -> None:
    print("[*] Descargando catálogo oficial de ecosistemas desde OSV.dev...")
    raw = fetch_raw_ecosystems()
    catalog = build_ecosystem_catalog(raw)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"[+] Éxito: {len(catalog)} ecosistemas sincronizados en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
