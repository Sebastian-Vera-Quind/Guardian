# Tasks: load_rules

## Implementation Checklist

- [ ] T1 — Crear estructura de paquetes `src/domain/ports/output/rules/`.
  Cubre: R1.

- [ ] T2 — Implementar `src/domain/ports/output/rules/rules_repository.py`
  con el protocolo `RulesRepository` que define el método abstracto
  `get_project_context()`. Cubre: R1.

- [ ] T3 — Crear `src/domain/models/project_context.py` con entidad
  Pydantic `ProjectContext` que represente la respuesta del contrato.
  Cubre: R2.

- [ ] T4 — Agregar excepciones a `src/domain/models/errors.py`:
  `RulesRepositoryError`, `InvalidScopeError`, `MissingViewError`,
  `ProjectContextNotFoundError`. Todas deben heredar de `AgenticError`.
  Cubre: R20.

- [ ] T5 — Crear estructura de paquetes `src/infra/db/`.
  Cubre: R17, R18.

- [ ] T6 — Implementar `src/infra/db/config.py` con función `get_engine()`
  que lea `TML_DATABASE_URL` y retorne un engine SQLAlchemy configurado.
  El engine debe ser compatible con Alembic.
  Cubre: R17, R18.

- [ ] T7 — Crear estructura de paquetes `src/infra/adapters/db/`.
  Cubre: R10.

- [ ] T8 — Implementar `src/infra/adapters/db/postgres_rules_repository.py`
  con clase `PostgresRulesRepositoryAdapter` que implemente `RulesRepository`.
  Cubre: R10, R15, R21, R22, R23.

- [ ] T9 — En `PostgresRulesRepositoryAdapter.__init__()`, implementar
  `_validate_view_exists()` que verifique la existencia de la vista
  `view_project_rules`. Si no existe, lanzar `MissingViewError`.
  Cubre: R11.

- [ ] T10 — En `PostgresRulesRepositoryAdapter`, implementar validación de
  scope: constante `_SAFE_FIELDS_RE` (regex `^[a-z_,\s*]+$`), diccionario
  `_fields_map` con mapeo scope → campos, y validar contra allow-list.
  Si scope inválido, lanzar `InvalidScopeError`.
  Cubre: R8, R9, R25.

- [ ] T11 — Implementar helper function `_parse_json_field(value)` en
  `postgres_rules_repository.py` que parsee strings JSON a objetos Python,
  retornando `[]` por defecto si falla o es None.
  Cubre: R12, R13, R14.

- [ ] T12 — Definir constante `_JSONB_FIELDS` en `postgres_rules_repository.py`
  con conjunto de nombres de campos JSONB a parsear.
  Cubre: R12, R25.

- [ ] T13 — Implementar método `get_project_context()` que:
  a) Valide scope contra allow-list (R8, R9).
  b) Construya query SQL dinamicamente usando `text()` de SQLAlchemy.
  c) Ejecute query con parámetro nombrado `:project_code` (R15).
  d) Parsee campos JSONB usando `_parse_json_field()` (R12, R13).
  e) Retorne dict con campos del scope (R3-R7).
  f) Si no hay resultados, lanzar `ProjectContextNotFoundError` (R19).
  Cubre: R3, R4, R5, R6, R7, R15, R19, R21, R22.

- [ ] T14 — Modificar `src/domain/ports/output/__init__.py` para exportar
  `RulesRepository`. Cubre: R1.

- [ ] T15 — Modificar `src/domain/models/__init__.py` para exportar
  `ProjectContext`, `RulesRepositoryError`, `InvalidScopeError`,
  `MissingViewError`, `ProjectContextNotFoundError`.
  Cubre: R1, R2, R20.

- [ ] T16 — Modificar `src/infra/helper/adapter_injector.py` para:
  a) Importar `get_engine()` desde `src/infra/db/config.py`.
  b) Importar `PostgresRulesRepositoryAdapter`.
  c) Instanciar engine, pasar a adaptador.
  d) Registrar binding `RulesRepository` → adaptador en contenedor.
  Cubre: R16, R21.

- [ ] T17 — Crear `tests/domain/ports/output/test_rules_repository.py` para
  validar que el protocolo `RulesRepository` está correctamente definido.
  Cubre: R1.

- [ ] T18 — Crear `tests/domain/models/test_project_context.py` para validar
  creación e inmutabilidad de `ProjectContext`.
  Cubre: R2.

- [ ] T19 — Crear `tests/infra/db/test_config.py` para validar que
  `get_engine()` retorna un engine válido y es compatible con la URL de
  conexión `TML_DATABASE_URL`.
  Cubre: R17, R18.

- [ ] T20 — Crear `tests/infra/adapters/db/test_postgres_rules_repository.py`
  para validar:
  a) `get_project_context()` con scope válido retorna dict con campos
     del scope (R3-R7).
  b) Scope inválido lanza `InvalidScopeError` (R8).
  c) Regex `_SAFE_FIELDS_RE` rechaza scopes con caracteres inválidos (R9).
  d) Campos JSONB válidos son parseados correctamente (R12).
  e) Campos JSONB NULL o inválidos retornan `[]` (R13).
  f) Si no hay filas, lanza `ProjectContextNotFoundError` (R19).
  Cubre: R3, R4, R5, R6, R7, R8, R9, R12, R13, R19.

- [ ] T21 — Crear `tests/infra/adapters/db/test_view_validation.py` para
  validar que `_validate_view_exists()` lanza `MissingViewError` si la
  vista `view_project_rules` no existe en la BD.
  Cubre: R11.

- [ ] T22 — Crear `tests/infra/adapters/db/test_jsonb_parsing.py` para
  validar exhaustivamente `_parse_json_field()` con diferentes tipos de
  entrada: string JSON válido, string inválido, dict, list, None.
  Cubre: R12, R13, R14.

- [ ] T23 — Crear test de integración que:
  a) Configura una BD de test con tabla `view_project_rules`.
  b) Inserta datos de prueba.
  c) Invoca `get_project_context()` con diferentes scopes.
  d) Verifica que los datos retornados son correctos.
  Cubre: R3, R4, R5, R6, R7, R10, R12.

## Orden de ejecución

La ejecución debe ser secuencial dentro de cada grupo:

1. **Dominio** (T1–T4): Crear puertos, entidades, excepciones.
2. **Base de datos** (T5–T6): Configurar engine SQLAlchemy.
3. **Adaptador** (T7–T13): Implementar repositorio concreto.
4. **Inyección de dependencias** (T14–T16): Registrar en contenedor.
5. **Tests** (T17–T23): Validar comportamiento con tests unitarios e
   integración.

## Trazabilidad

| Requirement | Tasks |
|-------------|-------|
| R1          | T2, T14, T17 |
| R2          | T3, T15, T18 |
| R3          | T13, T20, T23 |
| R4          | T13, T20, T23 |
| R5          | T13, T20, T23 |
| R6          | T13, T20, T23 |
| R7          | T13, T20, T23 |
| R8          | T10, T13, T20 |
| R9          | T10, T20 |
| R10         | T8, T23 |
| R11         | T9, T21 |
| R12         | T11, T12, T13, T20, T22, T23 |
| R13         | T11, T13, T20, T22 |
| R14         | T11, T22 |
| R15         | T8, T13 |
| R16         | T16 |
| R17         | T5, T6, T19 |
| R18         | T6, T19 |
| R19         | T13, T20 |
| R20         | T4, T15 |
| R21         | T8, T16 |
| R22         | T8 |
| R23         | T8 |
| R24         | (Design constraint, no test directo) |
| R25         | T12 |
