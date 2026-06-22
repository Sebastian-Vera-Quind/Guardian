# Arquitectura

> Este documento define el estándar de calidad. Los agentes revisores evalúan código contra este archivo. Si no está aquí, no es un requisito.

## Principios
1. **Arquitectura hexagonal**: Las capas debe ser independientes, con dependencias unidireccionales hacia adentro. La lógica de negocio no debe depender de detalles de infraestructura.
   - `./src/domain/`: No debe depender de nada, solo contiene definiciones de contratos, solo se puede hacer uso de librerias estandar de python que no impliquen lógica de negocio de negocion (ej. collections, typing, datetime), y pydantic para validación de datos.
     - `./src/domain/models/`: Modelos de dominio, solo clases de datos (dataclasses o pydantic), sin lógica de negocio.
     - `./src/domain/ports/`: Interfaces (protocols) que definen contratos para la lógica de negocio, sin implementaciones concretas.
   - `./src/application/`: Contiene la lógica de negocio, implementa los contratos definidos en `./src/domain/ports/`, y no debe depender de detalles de infraestructura.
   - `./src/infra/`: Implementaciones concretas de los contratos definidos en `./src/domain/ports/`, como acceso a bases de datos, servicios externos, etc. Puede depender de librerías de terceros.
  
> **NOTA:** En el paquete `./src/infra/helper/` se configura la injeccion de dependencia, creando instancias concretas de los contratos definidos en `./src/domain/ports/` y la instanciación de los casos de uso de `./src/application/`.

2. **Single Responsibility Principle**: Cada módulo, clase o función debe tener una única responsabilidad o razón para cambiar.
3. **Errores explícitos**: Las funciones que pueden fallar (id no existe, archivo corrupto) lanzan excepciones nombradas, no devuelven None.
