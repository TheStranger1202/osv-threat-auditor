# OSV Threat Auditor [v1.1.0]

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![OSV.dev](https://img.shields.io/badge/Powered_by-OSV.dev-purple.svg)

Una herramienta de auditoría de seguridad y gestión de dependencias respaldada por la base de datos oficial de Google **OSV.dev**. 

Diseñada con una estética táctica (*cyber-goth*) y una arquitectura funcional desacoplada, permite a los analistas de seguridad y desarrolladores escanear proyectos enteros, descubrir remediaciones deterministas y gestionar inventarios sin cadenas de dependencias complejas. Ofrece dos modalidades de operación: cliente de escritorio nativo (Desktop GUI) y portal web para intranet (Flask).

## ✨ Características Principales

- **Auditoría Asíncrona y Concurrente:** Motor de red basado en `ThreadPoolExecutor` que realiza consultas masivas por lotes (`querybatch`) e hidrata los datos en paralelo sin congelar la interfaz de usuario.
- **Extracción Profunda de Parches:** Algoritmo recursivo que inspecciona los manifiestos JSON de OSV para descubrir versiones de remediación (`fixed`), filtrando automáticamente hashes de Git (SHA-1 de 40 caracteres) para conservar únicamente versiones semánticas limpias.
- **Smart-Paste:** Pega dependencias directamente con el formato `paquete==version` o `ecosistema:paquete@version` (ej. `django==1.11.0`) y el sistema autocompletará los campos del formulario.
- **Catálogo Integrado y Normalizado:** Selector predictivo con más de 40 ecosistemas sincronizados (PyPI, npm, Maven, Go, Rust, AlmaLinux, NuGet, Packagist, etc.).
- **Arquitectura Inmutable y Persistencia Atómica:** Estado gestionado mediante funciones puras y tuplas inmutables, asegurando persistencia en disco (`data/inventory.json`) mediante reemplazo atómico a nivel de sistema operativo para prevenir corrupción de datos.
- **Doble Interfaz Compartida:** Soporte nativo de escritorio (Tkinter) y portal web táctil ligero (Flask con HTML5/CSS3 puro sin dependencias de JavaScript).

---

## 🚀 Instalación (Usuarios Finales)

No necesitas instalar Python ni configurar entornos si usas las versiones portables:

1. Ve a la pestaña **[Releases](../../releases)** del repositorio.
2. Descarga el binario correspondiente a tu sistema (Windows, Linux o macOS).
3. En Linux/macOS, otorga permisos de ejecución la primera vez:
   ```bash
   chmod +x OSV_Threat_Auditor-Linux
   ./OSV_Threat_Auditor-Linux
   ```

---

## 🛠️ Desarrollo y Compilación Local

Si deseas auditar el código, agregar funcionalidades o compilar el proyecto manualmente:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/TuUsuario/osv-threat-auditor.git
   cd osv-threat-auditor
   ```

2. **Configurar el entorno virtual aislado:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Ejecutar en modo Desarrollo:**
   * **Interfaz de Escritorio (Desktop):**
     ```bash
     python -m src.gui.app
     ```
   * **Portal Web (Intranet / Localhost):**
     ```bash
     python -m src.web.app
     ```
     *Acceso local:* `http://localhost:5000`

4. **Ejecutar Suite de Pruebas Unitarias:**
   ```bash
   pytest
   ```

5. **Generar el ejecutable standalone con PyInstaller:**
   ```bash
   pyinstaller auditor.spec --clean
   ```

---

## 📚 Documentación Técnica Detallada

Para consultar las especificaciones internas de ingeniería, patrones de diseño y diagramas de componentes:

* [**Arquitectura del Sistema y Diagramas**](docs/arquitectura_del_sistema.md): Flujo de datos, concurrencia de red y garantías de persistencia.
* [**Referencia de Módulos de Código**](docs/referencia_de_modulos.md): Desglose técnico archivo por archivo y catálogo de funciones.