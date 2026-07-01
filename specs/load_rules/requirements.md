# Requirements: load_rules

Integración de persistencia con base de datos PostgreSQL `guardian_db` para
recuperar contexto de reglas de proyectos según scopes incrementales.

## Overview

El sistema Guardian necesita una capa de persistencia que permita:

- Recuperar reglas de un proyecto desde la base de datos `guardian_db`.
- Consultar contexto incremental por scopes: `structure`, `domain`,
  `infrastructure`, `review`, `master`.
- Utilizar SQLAlchemy como ORM para abstracción de datos.
- Crear un repositorio que implemente el contrato para lectura de reglas.
- Validar scopes contra una allow-list antes de ejecutar queries.
- Parsear campos JSONB de la vista `view_project_rules`.

## R1

El sistema DEBE crear un contrato (protocol) en
`src/domain/ports/output/rules/` denominado `RulesRepository` que defina
un método `get_project_context(project_code: str, scope: str) -> dict`
para recuperar el contexto del proyecto desde la base de datos.

## R2

El sistema DEBE crear una entidad de dominio (dataclass o Pydantic) en
`src/domain/models/` denominada `ProjectContext` que represente la
respuesta del repositorio, sin mapear entidades por tabla, solo la
respuesta del contrato.

## R3

CUANDO se invoca `get_project_context` CON `project_code` válido y
`scope = "structure"`, el sistema DEBE retornar un diccionario con los
campos: `stack_tecnologico`, `estructura_directorios`, `project_name`.

## R4

CUANDO se invoca `get_project_context` CON `project_code` válido y
`scope = "domain"`, el sistema DEBE retornar un diccionario con los
campos: `reglas_dominio`, `lista_casos_uso`.

## R5

CUANDO se invoca `get_project_context` CON `project_code` válido y
`scope = "infrastructure"`, el sistema DEBE retornar un diccionario con
los campos: `specs_infraestructura`, `db_engines`, `api_types`,
`messaging`, `patrones_diseno`.

## R6

CUANDO se invoca `get_project_context` CON `project_code` válido y
`scope = "review"`, el sistema DEBE retornar un diccionario con los
campos: `checklist`, `coding_standards`.

## R7

CUANDO se invoca `get_project_context` CON `project_code` válido y
`scope = "master"`, el sistema DEBE retornar un diccionario con todos
los campos disponibles de todos los scopes anteriores.

## R8

SI se invoca `get_project_context` CON un `scope` que NO esté en la
allow-list (`structure`, `domain`, `infrastructure`, `review`, `master`),
el sistema DEBE lanzar una excepción denominada `InvalidScopeError`
indicando que el scope no es válido.

## R9

El sistema DEBE implementar validación de SQL injection a través de una
allow-list regex `^[a-z_,\s*]+$` que valide el scope antes de
interpolar campos en la query SQL, según el patrón defense-in-depth
especificado.

## R10

El sistema DEBE crear una implementación de `RulesRepository` en
`src/infra/adapters/db/` denominada `PostgresRulesRepositoryAdapter`
que utilice SQLAlchemy Core y se conecte a la base de datos
`guardian_db`.

## R11

La implementación DEBE consultar una vista denominada `view_project_rules`
que el desarrollador proporcionará. SI esta vista no es proporcionada,
el sistema DEBE lanzar una excepción `MissingViewError` indicando que
`view_project_rules` no existe en la base de datos.

## R12

El sistema DEBE parsear campos JSONB de la vista en la respuesta
(campos: `coding_standards`, `checklist`, `patrones_diseno`,
`reglas_dominio`, `lista_casos_uso`, `specs_infraestructura`,
`db_engines`, `api_types`, `messaging`). SI un campo JSONB contiene una
string JSON válida, DEBE parsearse a objeto Python (dict o list).

## R13

El sistema DEBE manejar campos JSONB que sean `NULL` o strings inválidos
retornando una lista vacía `[]` como valor por defecto, sin fallar.

## R14

El sistema DEBE crear una función helper `_parse_json_field(value)` que
acepte string, dict, list o None, intente parsear strings como JSON, y
retorne el valor parseado o una lista vacía por defecto.

## R15

El sistema DEBE utilizar `text()` de SQLAlchemy Core para construir
queries SQL dinámicas con parámetros nombrados (e.g.,
`:project_code`), NO string interpolation.

## R16

El sistema DEBE usar inyección de dependencias para instanciar
`PostgresRulesRepositoryAdapter` en el contenedor de dependencias
`src/infra/helper/adapter_injector.py`, exponiendo `RulesRepository`
como tipo inyectable.

## R17

La conexión a la base de datos DEBE ser configurable mediante variables
de entorno: `GUARDIAN_DB_HOST`, `GUARDIAN_DB_PORT`, `GUARDIAN_DB_NAME`,
`GUARDIAN_DB_USER`, `GUARDIAN_DB_PASSWORD`.

## R18

El sistema DEBE crear un modelo de configuración SQLAlchemy (SQLAlchemy
Engine) en `src/infra/db/` que inicialice la conexión a `guardian_db`
utilizando la URL construida a partir de variables de entorno.

## R19

SI la query a la base de datos retorna cero filas para un
`project_code` válido, el sistema DEBE lanzar una excepción
`ProjectContextNotFoundError` indicando que no hay contexto para el
proyecto especificado.

## R20

El sistema DEBE definir una excepción personalizada `RulesRepositoryError`
como clase base en `src/domain/models/errors.py`, de la cual hereden
`InvalidScopeError`, `MissingViewError`, `ProjectContextNotFoundError`,
todas conforme a `docs/conventions.md` (heredan de `AgenticError`).

## R21

El sistema DEBE estar completamente tipado con type hints
(`typing.Optional`, `typing.Dict`, etc.), siguiendo las convenciones en
`docs/conventions.md`, evitando `Any` al máximo.

## R22

El sistema DEBE utilizar logging (`logging.Logger`) para registrar
operaciones de consulta (nivel DEBUG), errores (nivel ERROR), y
consultas inválidas (nivel WARNING), sin uso de `print()`.

## R23

Todos los imports DEBE seguir el orden: stdlib, third-party, local,
según `docs/conventions.md`, con máximo 79 caracteres de ancho de línea
y 2 espacios de indentación.

## R24

El sistema NO DEBE crear entidades SQLAlchemy (ORM models) para
`projects`, `use_cases`, `checklists`. Solo utilizar SQLAlchemy Core
(`text()`, `select()`, `Result`) para queries directas.

## R25

El sistema DEBE mantener una definición centralizada de campos JSONB en
una constante `_JSONB_FIELDS` para facilitar mantenimiento y
extensibilidad futura.
