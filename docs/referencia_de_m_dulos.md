# Referencia de Módulos de Código

La estructura funcional previene las dependencias circulares y aísla las responsabilidades en áreas de dominio muy específicas.

## 1. Núcleo (Core) y Persistencia
*   **`src/config.py`:** Punto centralizado para resolución absoluta de rutas (Data/Cache). Contiene funciones de validación funcionales puras para la carga del catálogo y configura los *timeouts*.
*   **`src/inventory_manager.py`:** Provee operaciones CRUD (Create, Read, Update, Delete) 100% puras (sin efectos secundarios en memoria) para mutar el inventario de dependencias. Contiene la lógica defensiva y la persistencia atómica.
*   **`src/auditor.py`:** Motor de red de alto rendimiento. Se comunica con la API de OSV, filtra versiones mitigadas usando `SHA1_REGEX` (descartando así hashes de commits de Git inyectados erróneamente por algunos mantenedores), e hidrata los manifiestos mediante hilos.
*   **`src/reporter.py`:** Módulo de presentación de datos para consola. Incluye funciones de mitigación activa, destacando la inyección de *prompts* estructurados en casos de vulnerabilidades Zero-Day para asistir con Inteligencia Artificial.
*   **`src/scanner.py`:** *(Legacy)* Implementación lineal con algoritmo de *backoff* exponencial para consultas en redes altamente inestables.

## 2. Presentación: Módulo Web (`src/web/`)
*   **`app.py`:** Servidor Flask minimalista. Envuelve el motor existente sin alterar las estructuras de datos. Gestiona el enrutamiento HTTP y transfiere la manipulación (Update/Edit) utilizando parámetros GET (`?edit=`) replicando el comportamiento de la interfaz local.
*   **`templates/index.html`:** Interfaz web táctica (*Dark Tactical*) construida 100% en HTML5 y CSS3. No posee dependencias de JavaScript ni de terceros, manteniendo la superficie de ataque al mínimo posible.

## 3. Presentación: Módulo Desktop (`src/gui/`)
*   **`app.py`:** Orquestador interactivo en Tkinter. Utiliza una cola segura de subprocesos (`queue.Queue`) para delegar el escaneo intensivo a un *Worker Thread*, evitando así que la interfaz gráfica congele el sistema operativo de la estación.
*   **`components.py`:** Fábricas funcionales (*closures*) de elementos visuales tácticos. Desecha la herencia profunda típica de OOP en favor de funciones puras. Implementa un sistema avanzado de pegado inteligente mediante captura de portapapeles (`SMART_PASTE_REGEX`).
*   **`theme.py`:** Centraliza las variables cromáticas (Estilo *Cyber-Goth*) limitando la fatiga visual de los operadores en sesiones prolongadas.

## 4. Pruebas e Infraestructura
*   **`pytest.ini` & `tests/`:** Define el entorno de validación automática. Asegura que el intérprete reconozca el directorio raíz como base (`pythonpath = .`), permitiendo ejecutar las aserciones sobre `auditor` e `inventory_manager` en ambientes de integración continua (CI) de forma aislada.
*   **`scripts/update_ecosystems.py`:** Utilidad independiente diseñada para sincronizar dinámicamente el diccionario de ecosistemas válidos desde los buckets de Google Cloud de OSV.