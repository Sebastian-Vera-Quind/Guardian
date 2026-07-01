# Tasks: prompt_builder

## Implementation Checklist

### Dominio

- [x] T1 — Crear `src/domain/models/prompt_scope.py` con
  `PromptScope(str, Enum)` y miembros `CHECKLIST`, `ARCHITECTURE`,
  `BUSINESS_RULES` (valores `checklist`, `architecture`, `business_rules`).
  Cubre: R1.

- [x] T2 — Crear `src/domain/models/errors/prompt_errors.py` con
  `PromptBuilderError` (hereda de `AgenticError`),
  `UnknownPromptScopeError` y `PromptRenderError` (heredan de
  `PromptBuilderError`). Cubre: R4, R5, R14.

- [x] T3 — Modificar `src/domain/models/errors/__init__.py` para exportar
  `PromptBuilderError`, `UnknownPromptScopeError`, `PromptRenderError`.
  Cubre: R4, R5, R14.

- [x] T4 — Modificar `src/domain/models/__init__.py` para exportar
  `PromptScope`, `PromptBuilderError`, `UnknownPromptScopeError`,
  `PromptRenderError`. Cubre: R1, R4.

- [x] T5 — Crear `src/domain/ports/input/prompt/prompt_builder.py` con el
  protocolo `PromptBuilder` (ABC) y el alias
  `PromptAttributes = Dict[str, JsonValue]`, declarando `build_for_scope`,
  `build_from_template` y `sanitize`. Crear
  `src/domain/ports/input/prompt/__init__.py` que exporte `PromptBuilder`.
  Cubre: R2, R6, R9, R10, R16.

- [x] T6 — Crear `src/domain/ports/output/prompt/prompt_renderer.py` con el
  protocolo `PromptRenderer` (ABC) declarando `render_scope` y
  `render_template`. Crear `src/domain/ports/output/prompt/__init__.py`
  que exporte `PromptRenderer`. Cubre: R3, R13, R16.

- [x] T7 — Modificar `src/domain/ports/input/__init__.py` para exportar
  `PromptBuilder`. Cubre: R2.

- [x] T8 — Modificar `src/domain/ports/output/__init__.py` para exportar
  `PromptRenderer`. Cubre: R3.

### Application (servicio)

- [x] T9 — Crear `src/application/prompt/prompt_builder_service.py` con
  `PromptBuilderService(PromptBuilder)`, que recibe un `PromptRenderer`
  por inyección en `__init__`. Cubre: R2, R18.

- [x] T10 — Implementar `PromptBuilderService.sanitize(content)` que
  elimine caracteres de control (reutiliza `sanitize_file_content` de
  `src/application/security/prompt_guard.py`) y elimine líneas en blanco
  (reutiliza el criterio de `CodeSanitizer.remove_blank_lines`).
  Cubre: R7, R8, R9.

- [x] T11 — Implementar `_sanitize_attributes(attributes)` que aplique
  `sanitize` a todos los valores de tipo `str` del diccionario, dejando
  intactos los valores no-string. Cubre: R7, R8, R11.

- [x] T12 — Implementar `build_for_scope(scope, attributes)`: validar que
  `scope` es un `PromptScope` (si no, lanzar `UnknownPromptScopeError`),
  sanear atributos con `_sanitize_attributes`, y delegar en
  `renderer.render_scope`. Cubre: R5, R6, R7, R8, R18.

- [x] T13 — Implementar `build_from_template(template, attributes)`:
  sanear atributos con `_sanitize_attributes` y delegar en
  `renderer.render_template`. Cubre: R10, R11, R18.

- [x] T14 — Añadir `logging` (DEBUG en construcción; WARNING/ERROR en
  fallos propagados) en `PromptBuilderService`, sin `print()`.
  Crear `src/application/prompt/__init__.py` exportando
  `PromptBuilderService`. Cubre: R17.

### Infra (adaptador Jinja2)

- [x] T15 — Verificar que `jinja2` está disponible como dependencia (ya
  declarado `jinja2 (>=3.1.6,<4.0.0)` en `pyproject.toml` e instalado).
  No requiere cambios en `pyproject.toml`. Cubre: R12.

- [x] T16 — Crear `src/infra/adapters/prompt/templates.py` con
  `SCOPE_TEMPLATES: Dict[PromptScope, str]` que asocie cada scope
  (`CHECKLIST`, `ARCHITECTURE`, `BUSINESS_RULES`) a su plantilla Jinja2.
  Cubre: R13.

- [x] T17 — Crear `src/infra/adapters/prompt/jinja_prompt_renderer.py` con
  `JinjaPromptRenderer(PromptRenderer)` que inicialice un
  `jinja2.Environment`. Crear `src/infra/adapters/prompt/__init__.py`
  exportando `JinjaPromptRenderer`. Cubre: R3, R12.

- [x] T18 — Implementar `render_template(template, attributes)` usando
  `Environment.from_string(template).render(**attributes)`, capturando
  `jinja2.TemplateError` y relanzando `PromptRenderError`.
  Cubre: R12, R14, R17.

- [x] T19 — Implementar `render_scope(scope, attributes)` que resuelva la
  plantilla desde `SCOPE_TEMPLATES[scope]` y delegue en
  `render_template`. Cubre: R12, R13.

### Inyección de dependencias

- [x] T20 — Modificar `src/infra/helper/adapter_injector.py`: añadir
  `OutPortType.PromptRenderer`, factory `_create_prompt_renderer()` que
  retorne `JinjaPromptRenderer()`, y registrarla en
  `_out_port_factories` y en la unión `_OutPort`. Cubre: R15.

- [x] T21 — Modificar `src/infra/helper/usecase_injector.py`: añadir
  `InPortType.PromptBuilderService`, factory
  `_create_prompt_builder_service()` que inyecte
  `OutPortType.PromptRenderer` y construya `PromptBuilderService`, y
  registrarla en `_in_port_factories` y en la unión `_InPort`.
  Cubre: R15.

- [x] T22 — Modificar `src/infra/helper/inject.py`: añadir los `@overload`
  para `InPortType.PromptBuilderService` y `OutPortType.PromptRenderer`, y
  extender las uniones de retorno. Cubre: R15.

### Tests

- [x] T23 — Crear `tests/application/prompt/test_prompt_builder_service.py`
  para validar:
  a) `build_for_scope` con scope válido retorna el prompt renderizado
     (usa un `PromptRenderer` mock). Cubre: R6.
  b) `build_for_scope` con scope inválido lanza
     `UnknownPromptScopeError`. Cubre: R5.
  c) `sanitize` elimina caracteres de control. Cubre: R7.
  d) `sanitize` elimina líneas en blanco. Cubre: R8, R9.
  e) `_sanitize_attributes` sanea solo valores string y deja intactos los
     no-string; `build_for_scope`/`build_from_template` pasan atributos
     saneados al renderer. Cubre: R11.
  f) `build_from_template` delega en `renderer.render_template` con
     atributos saneados. Cubre: R10, R11.
  Cubre: R5, R6, R7, R8, R9, R10, R11, R18.

- [x] T24 — Crear
  `tests/infra/adapters/prompt/test_jinja_prompt_renderer.py` para validar:
  a) `render_template` renderiza una plantilla Jinja2 con atributos.
     Cubre: R12.
  b) `render_scope` resuelve la plantilla por `PromptScope` y renderiza.
     Cubre: R13.
  c) Plantilla Jinja2 inválida lanza `PromptRenderError` (no
     `TemplateError`). Cubre: R14.
  Cubre: R12, R13, R14.

- [x] T25 — Crear `tests/infra/helper/test_prompt_injection.py` (o extender
  el test de inyección existente) para validar que
  `inject(InPortType.PromptBuilderService)` retorna un `PromptBuilder` y
  `inject(OutPortType.PromptRenderer)` retorna un `PromptRenderer`.
  Cubre: R15.

## Orden de ejecución

1. **Dominio** (T1–T8): enum, excepciones, puertos, exports.
2. **Application** (T9–T14): servicio + saneamiento.
3. **Infra** (T15–T19): dependencia Jinja2, plantillas y adaptador.
4. **Inyección** (T20–T22): registrar puertos.
5. **Tests** (T23–T25): unitarios e inyección.

## Trazabilidad

| Requirement | Tasks |
|-------------|-------|
| R1  | T1, T4 |
| R2  | T5, T7, T9 |
| R3  | T6, T8, T17 |
| R4  | T2, T3, T4 |
| R5  | T2, T3, T12, T23 |
| R6  | T5, T12, T23 |
| R7  | T10, T11, T12, T23 |
| R8  | T10, T11, T12, T23 |
| R9  | T5, T10, T23 |
| R10 | T5, T13, T23 |
| R11 | T11, T13, T23 |
| R12 | T15, T16*, T17, T18, T19, T24 |
| R13 | T6, T16, T19, T24 |
| R14 | T2, T3, T18, T24 |
| R15 | T20, T21, T22, T25 |
| R16 | T5, T6 |
| R17 | T14, T18 |
| R18 | T9, T12, T13, T23 |

(*) T16 crea las plantillas Jinja2 que R12 exige renderizar.
