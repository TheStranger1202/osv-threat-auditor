# OSV Threat Auditor

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![OSV.dev](https://img.shields.io/badge/Powered_by-OSV.dev-purple.svg)

Una herramienta de escritorio con interfaz gráfica (GUI) para auditar vulnerabilidades en dependencias de software, respaldada por la base de datos oficial de Google **OSV.dev**. 

Diseñada con una estética táctica (*cyber-goth*) y una arquitectura funcional, permite a los analistas de seguridad y desarrolladores escanear proyectos enteros sin necesidad de usar la terminal ni instalar complejas cadenas de dependencias.

## ✨ Características Principales

* **Auditoría Asíncrona:** Motor de red basado en `ThreadPoolExecutor` que realiza consultas por lotes (batch) e hidrata los datos en paralelo sin congelar la interfaz.
* **Extracción Profunda de Parches:** Algoritmo recursivo que inspecciona los manifiestos JSON de OSV para descubrir versiones de remediación (`fixed`), filtrando automáticamente hashes de Git (SHA-1) para mostrar únicamente versiones semánticas limpias.
* **Smart-Paste:** Pega dependencias directamente con el formato `paquete==version` (ej. `django==1.11.0`) y el sistema autocompletará los campos.
* **Catálogo Integrado:** Selector predictivo con más de 40 ecosistemas soportados (PyPI, npm, Maven, Go, Rust, AlmaLinux, etc.).
* **Arquitectura Inmutable:** Estado gestionado mediante clausuras y funciones puras, garantizando persistencia atómica en disco (`data/inventory.json`).

## 🚀 Instalación (Usuarios Finales)

No necesitas instalar Python. Descarga el ejecutable para tu sistema operativo y ábrelo directamente:

1. Ve a la pestaña **[Releases](../../releases)** del repositorio.
2. Descarga el binario correspondiente a tu sistema (Windows, Linux o macOS).
3. En Linux/macOS, recuerda otorgar permisos de ejecución (`chmod +x OSV_Threat_Auditor-Linux`) la primera vez.

## 🛠️ Desarrollo (Compilación Local)


Si deseas modificar el código o compilar el proyecto manualmente:

1. **Clona el repositorio:**
   ```bash
   git clone [https://github.com/TuUsuario/osv-threat-auditor.git](https://github.com/TuUsuario/osv-threat-auditor.git)
   cd osv-threat-auditor

3. **Instala las dependencias:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # En Windows: .venv\Scripts\activate
    pip install -r requirements.txt

3. **Ejecuta la interfaz en modo desarrollo:**
    ```bash
    python -m src.gui.app

4. **Genera el ejecutable con PyInstaller:**
    ```bash
    pyinstaller auditor.spec --clean
