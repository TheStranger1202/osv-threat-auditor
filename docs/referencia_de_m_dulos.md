# Referencia de Módulos // OSV Threat Auditor

Catálogo técnico de los archivos que conforman el proyecto y su rol dentro de la arquitectura.

---

## 1. Raíz del Repositorio

* **`auditor.spec`:** Especificación de empaquetado para PyInstaller. Configura los recursos embebidos (catálogo de ecosistemas, plantillas, íconos) y compila la aplicación en un binario ejecutable único para distribución en Releases.
* **`pytest.ini`:** Archivo de configuración para testing automatizado. Fija `pythonpath = .` y localiza la suite de pruebas en el directorio `tests/` para evitar errores de resolución de paquetes.
* **`requirements.txt`:** Especificación de dependencias fijadas (Flask, requests, packaging, pyinstaller, pytest, etc.).

---

## 2. Directorio `data/` (Persistencia)

* **`inventory.json`:** Almacén de datos persistente. Contiene el nombre del proyecto bajo análisis, fecha de última modificación y la lista de dependencias auditadas.
* **`osv_ecosystems.json`:** Catálogo de ecosistemas soportados, mapeando nombres canónicos de OSV con nombres legibles y alias comunes para autocompletado predictivo.
* **`cache.json`:** Almacenamiento local temporal para optimizar consultas de red y evitar llamadas repetitivas.

---

## 3. Directorio `scripts/` (Utilitarios)

* **`update_ecosystems.py`:** Herramienta administrativa para sincronizar el catálogo de tecnologías. Descarga la lista viva desde el bucket oficial de Google OSV (`ecosystems.txt`), aplica el mapeo de alias y sobreescribe `data/osv_ecosystems.json`.

---

## 4. Directorio `src/` (Núcleo Funcional / Core)

* **`config.py`:** Centraliza constantes de infraestructura (timeouts de red, reintentos, URLs oficiales de OSV.dev) y funciones de validación funcional inmutable (`validate_dependency`, `parse_inventory_content`).
* **`inventory_manager.py`:** Implementa las operaciones CRUD puras del inventario (`add_dependency`, `update_dependency`, `delete_dependency`). Contiene la lógica de validación de sintaxis contra operadores de rango abierto (`^`, `~`, `*`) y la rutina de persistencia atómica `save_inventory_atomic`.
* **`auditor.py`:** Motor principal de auditoría. Ejecuta consultas HTTP por lote hacia OSV.dev, administra el `ThreadPoolExecutor` para hidratación paralela de manifiestos, filtra hashes SHA-1 y determina si el hallazgo tiene parche disponible o califica como Zero-Day.
* **`scanner.py`:** Módulo de consulta individual con retroceso exponencial (*exponential backoff*), mantenido como alternativa de contingencia para conexiones con alta latencia o pérdida de paquetes.
* **`reporter.py`:** Módulo de salida y generación de reportes estructurados en Markdown. Incluye la plantilla de asistencia para Zero-Days con prompts listos para interactuar con modelos de lenguaje DevSecOps.

---

## 5. Directorio `src/gui/` (Interfaz de Escritorio)

* **`app.py`:** Ensamblador de la ventana principal de Tkinter. Orquesta el ciclo de eventos sin clases mediante clausuras funcionales y administra la comunicación asíncrona mediante colas de mensajes (`queue.Queue`).
* **`components.py`:** Fábricas de widgets desacopladas. Incluye:
  * Entradas de texto con soporte para `Smart-Paste` por expresión regular.
  * Selector desplegable (`ttk.Combobox`) con filtrado predictivo y autocompletado mediante la tecla `[Tab]`.
  * Banner de retroalimentación de estado transitorio (sin diálogos modales intrusivos).
* **`theme.py`:** Definición centralizada del tema *Dark Tactical / Cyber-Goth* (paleta grafito frío `#111318`, acentos cyan `#38bdf8`, semáforos de vulnerabilidad esmeralda/ámbar/carmesí) y estilización para `ttk.Style`.

---

## 6. Directorio `src/web/` (Portal Web Intranet)

* **`app.py`:** Controlador web basado en Flask. Expone rutas REST y gestión CRUD sobre el inventario local mediante peticiones HTTP estándar. Implementa el ciclo de edición en línea sin dependencias pesadas de sesión.
* **`templates/index.html`:** Plantilla de interfaz web construida en HTML5 y CSS3 nativo. Reproduce fielmente la paleta ergonómica del cliente de escritorio, integrando soporte para acciones de edición rápida, eliminación de registros y visualización de mitigaciones mediante insignias tácticas.