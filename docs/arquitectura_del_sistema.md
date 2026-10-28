# Arquitectura del Sistema

El sistema utiliza una arquitectura de **capas puras**, separando completamente el motor lógico (Core) y la manipulación de datos de las interfaces de usuario (Desktop y Web).

## Diagrama de Componentes (PlantUML)

```plantuml
@startuml
skinparam backgroundColor #111318
skinparam fontColor #d8dee9
skinparam component {
    BackgroundColor #181b22
    BorderColor #38bdf8
    ArrowColor #6c7689
    FontColor #d8dee9
}

package "Presentación (Interfaces)" {
    [Desktop GUI\n(src/gui/app.py)] as GUI
    [Web Portal\n(src/web/app.py)] as WEB
}

package "Núcleo de Negocio (Core)" {
    [Motor Auditor\n(src/auditor.py)] as AUDITOR
    [Gestor de Inventario\n(src/inventory_manager.py)] as INV_MANAGER
}

database "Persistencia\n(data/)" as STORAGE
cloud "API OSV.dev" as OSV_API

GUI --> AUDITOR : Invoca escaneo
GUI --> INV_MANAGER : Operaciones CRUD
WEB --> AUDITOR : Invoca escaneo
WEB --> INV_MANAGER : Operaciones CRUD

AUDITOR <--> OSV_API : Consultas batch y concurrencia (HTTP)
INV_MANAGER <--> STORAGE : Escritura Atómica (.tmp -> .json)
@enduml
```
*(Nota: Este diagrama puede renderizarse con cualquier extensión de PlantUML de tu IDE o visores web).*

## Decisiones Críticas de Diseño

1. **Concurrencia de Red:** En lugar de escanear linealmente paquete por paquete, `auditor.py` realiza primero una consulta masiva (`querybatch`) a OSV.dev y luego hidrata los detalles complejos de las vulnerabilidades usando un `ThreadPoolExecutor` con 15 hilos en paralelo.
2. **Escritura Atómica de Archivos:** Para evitar corrupción del inventario base (`inventory.json`) durante apagones o fallas del servidor, la función `save_inventory_atomic` escribe la data nueva en un archivo temporal `.tmp`, fuerza la sincronización física del disco con `os.fsync()`, y finalmente realiza un reemplazo a nivel del sistema operativo.
3. **Determinismo e Inmutabilidad:** El estado de las dependencias se transfiere sistemáticamente mediante tuplas en lugar de listas para evitar efectos secundarios. Adicionalmente, las versiones con comodines o condiciones (`^`, `~`, `>`, `latest`) son estrictamente rechazadas mediante expresiones regulares para garantizar una validación exacta.