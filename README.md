# OSV // THREAT_AUDITOR [v1.0.0]

Herramienta interna de auditoría de seguridad (DevSecOps) orientada a la detección de vulnerabilidades conocidas (CVEs) y Zero-Days. Utiliza la base de datos oficial de vulnerabilidades de código abierto (**OSV.dev**) de Google.

Este proyecto opera bajo principios de inmutabilidad, persistencia atómica y concurrencia. Soporta dos interfaces compartiendo el mismo núcleo lógico:
1. **Desktop Client:** Interfaz Tkinter nativa para estaciones de trabajo.
2. **Web Portal:** Aplicación Flask ligera para acceso en red local o corporativa.

## 🚀 Inicio Rápido e Instalación

Debido a las normativas de PEP 668 en distribuciones modernas (Linux/Debian/Ubuntu), se requiere un entorno virtual administrado:

```bash
# 1. Instalar dependencias del sistema operativo (si es necesario)
sudo apt update && sudo apt install -y python3-venv python3-full

# 2. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias del proyecto
pip install -r requirements.txt
```

## 🖥️ Modos de Ejecución

Ambas interfaces leen y escriben sobre el mismo inventario persistente (`data/inventory.json`).

*   **Modo Escritorio (Desktop):** Ideal para analistas locales.
    ```bash
    python -m src.gui.app
    ```
*   **Modo Web (Portal):** Levanta un servidor Flask accesible desde cualquier navegador.
    ```bash
    python -m src.web.app
    ```
    *Acceso local:* `http://localhost:5000`

## 🧪 Pruebas Unitarias

El proyecto cuenta con un entorno de pruebas configurado vía `pytest`. Para ejecutar la suite completa de tests:

```bash
pytest
```

---
*Para detalles técnicos profundos, revisa el directorio `/docs`:*
* [Arquitectura y Diseño](docs/ARCHITECTURE.md)
* [Referencia de Módulos](docs/MODULES.md)