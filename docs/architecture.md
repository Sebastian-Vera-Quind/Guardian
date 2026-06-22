# Arquitectura

> Este documento define el estándar de calidad. Los agentes revisores evalúan código contra este archivo. Si no está aquí, no es un requisito.

## Principios
1. **Arquitectura hexagonal**: Las capas debe ser independientes, con dependencias unidireccionales hacia adentro. La lógica de negocio no debe depender de detalles de infraestructura.
   - `./src/domain/`: No debe depender de nada, solo contiene definiciones de contratos, solo se puede hacer uso de librerias estandar de python que no impliquen lógica de negocio de negocion (ej. collections, typing, datetime), y pydantic para validación de datos.
     - `./src/domain/models/`: Modelos de dominio, solo clases de datos (dataclasses o pydantic), sin lógica de negocio.
     - `./src/domain/ports/`: Interfaces (protocols) que definen contratos para la lógica de negocio, sin implementaciones concretas.
   - `./src/application/`: Contiene la lógica de negocio, implementa los contratos definidos en `./src/domain/ports/`, y no debe depender de detalles de infraestructura.
   - `./src/infra/`: Implementaciones concretas de los contratos definidos en `./src/domain/ports/`, como acceso a bases de datos, servicios externos, etc. Puede depender de librerías de terceros.
2. **Single Responsibility Principle**: Cada módulo, clase o función debe tener una única responsabilidad o razón para cambiar.
3. **Errores explícitos**: Las funciones que pueden fallar (id no existe, archivo corrupto) lanzan excepciones nombradas, no devuelven None.
4. **Dependencias**: Las dependencias deben ser injectadas y no instanciadas directamente dentro de la clase. Siempre que un modulo dependa de otro, ya sea de infra a infra o de application a infra, debe ser a través de interfaces (protocols) definidas en `./src/domain/ports/`. Esto permite cambiar la implementación concreta sin afectar la lógica de negocio.

## LangGraph

El modulo `./src/infra/adapters/workflow`, es principalmente el nucleo de la aplicacion, y contiene la implementación de un workflow engine que permite ejecutar nodos de procesamiento de manera secuencial para crear un reporte sobre el codigo fuente. Cada nodo responde a los siguientes principios:

- **Nodos independientes**: Cada nodo es independiente y encapsula una unidad de procesamiento. No debe depender de otros nodos ni de la infraestructura.
- **Entrada y salida estandarizada**: Cada nodo recibe una entrada estandarizada (por ejemplo, un diccionario o un objeto de datos) y produce una salida estandarizada. Esto permite encadenar nodos de manera flexible.
- **Unica Responsabilidad**: Los nodos orquetan tareas sin logica de negocio, y delegan la logica de negocio a los servicios de application. 
- **Trazabilidad**: Cada nodo debe estar decorado con la funcion `@with_logging()`, definida en `./src/infra/adapters/workflow/log.py`, para asegurar que cada paso del workflow sea trazable y auditable. Esto facilita la depuración y el monitoreo del flujo de ejecución.
