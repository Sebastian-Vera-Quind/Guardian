# Implementación: 9 — prompt_builder

## Estado: Implementado, pendiente de review (2026-07-01)

Ejecutadas las tasks T1–T25 de `specs/prompt_builder/tasks.md` en orden,
todas marcadas `[x]`.

## Resultado de pytest

- Baseline previo: **244 passed** (confirmado antes de empezar).
- Tras la feature: **255 passed, 1 warning** (`python -m pytest -q`).
- Nuevos tests: **11** (`tests/application/prompt` = 6,
  `tests/infra/adapters/prompt` = 3, `tests/infra/helper` = 2).
- El único warning es pre-existente (StarletteDeprecationWarning de
  FastAPI TestClient), ajeno a esta feature.

## Archivos creados

Dominio:
- `src/domain/models/prompt_scope.py` — `PromptScope(str, Enum)`
  (CHECKLIST, ARCHITECTURE, BUSINESS_RULES).
- `src/domain/models/errors/prompt_errors.py` — `PromptBuilderError`,
  `UnknownPromptScopeError`, `PromptRenderError` (heredan de
  `AgenticError` / `PromptBuilderError`).
- `src/domain/ports/input/prompt/prompt_builder.py` — puerto entrada
  `PromptBuilder` (ABC) + alias `PromptAttributes = Dict[str, JsonValue]`.
- `src/domain/ports/input/prompt/__init__.py`.
- `src/domain/ports/output/prompt/prompt_renderer.py` — puerto salida
  `PromptRenderer` (ABC).
- `src/domain/ports/output/prompt/__init__.py`.

Application:
- `src/application/prompt/prompt_builder_service.py` —
  `PromptBuilderService(PromptBuilder)`; sanea y delega en el renderer.
- `src/application/prompt/__init__.py`.

Infra:
- `src/infra/adapters/prompt/templates.py` —
  `SCOPE_TEMPLATES: Dict[PromptScope, str]`.
- `src/infra/adapters/prompt/jinja_prompt_renderer.py` —
  `JinjaPromptRenderer(PromptRenderer)` con Jinja2, envuelve
  `jinja2.TemplateError` en `PromptRenderError`.
- `src/infra/adapters/prompt/__init__.py`.

Tests:
- `tests/application/prompt/test_prompt_builder_service.py` (+ `__init__.py`)
- `tests/infra/adapters/prompt/test_jinja_prompt_renderer.py` (+ `__init__.py`)
- `tests/infra/helper/test_prompt_injection.py` (+ `__init__.py`)

## Archivos modificados

- `src/domain/models/errors/__init__.py` — exporta las 3 excepciones.
- `src/domain/models/__init__.py` — exporta `PromptScope` y las 3
  excepciones.
- `src/domain/ports/input/__init__.py` — exporta `PromptBuilder`.
- `src/domain/ports/output/__init__.py` — exporta `PromptRenderer`.
- `src/infra/helper/adapter_injector.py` — `OutPortType.PromptRenderer`,
  factory `_create_prompt_renderer`, entradas en `_OutPort` y
  `_out_port_factories`.
- `src/infra/helper/usecase_injector.py` —
  `InPortType.PromptBuilderService`, factory
  `_create_prompt_builder_service` (inyecta `OutPortType.PromptRenderer`),
  entradas en `_InPort` y `_in_port_factories`.
- `src/infra/helper/inject.py` — `@overload` para
  `InPortType.PromptBuilderService` y `OutPortType.PromptRenderer`;
  uniones de import y de retorno extendidas.

## Trazabilidad Requisito → test

- **R1** (`PromptScope` con miembros/valores) →
  `test_render_scope_resolves_scope_template`,
  `test_inject_prompt_renderer_returns_output_port` (uso del enum);
  verificado indirectamente vía todos los tests que usan
  `PromptScope.CHECKLIST`.
- **R2** (puerto entrada `PromptBuilder`) →
  `test_inject_prompt_builder_returns_input_port` (isinstance
  `PromptBuilder`).
- **R3** (puerto salida `PromptRenderer`) →
  `test_inject_prompt_renderer_returns_output_port` (isinstance
  `PromptRenderer`).
- **R4** (`PromptBuilderError` base) → cubierto por R5/R14 (subclases
  heredan y se capturan como tal).
- **R5** (scope inválido → `UnknownPromptScopeError`) →
  `test_build_for_scope_invalid_scope_raises`.
- **R6** (build por scope válido retorna prompt) →
  `test_build_for_scope_returns_rendered_prompt`.
- **R7** (sanea caracteres de control) →
  `test_sanitize_removes_control_characters`.
- **R8** (sanea líneas en blanco) →
  `test_sanitize_removes_blank_lines`.
- **R9** (método público `sanitize` independiente) →
  `test_sanitize_removes_control_characters`,
  `test_sanitize_removes_blank_lines`.
- **R10** (método genérico `build_from_template`) →
  `test_build_from_template_delegates_with_sanitized_attrs`.
- **R11** (sanea valores string del dict, deja no-string intactos) →
  `test_sanitize_attributes_sanitizes_only_strings`,
  `test_build_from_template_delegates_with_sanitized_attrs`.
- **R12** (adaptador usa Jinja2) →
  `test_render_template_renders_attributes`.
- **R13** (adaptador resuelve plantilla por scope) →
  `test_render_scope_resolves_scope_template`.
- **R14** (Jinja2 inválido → `PromptRenderError`, no `TemplateError`) →
  `test_invalid_template_raises_prompt_render_error`.
- **R15** (inyección registrada) →
  `test_inject_prompt_builder_returns_input_port`,
  `test_inject_prompt_renderer_returns_output_port`.
- **R16** (tipado sin `Any`) → verificado por inspección; se usa
  `Dict[str, JsonValue]` (alias `PromptAttributes`). Sin `Any` en el
  código de la feature.
- **R17** (logging, sin `print`) → verificado por inspección
  (`logging.getLogger(__name__)`, DEBUG en construcción, WARNING en
  scope desconocido, ERROR en fallo de render).
- **R18** (application no usa Jinja2, delega en puerto salida) →
  `test_build_for_scope_returns_rendered_prompt`,
  `test_build_from_template_delegates_with_sanitized_attrs` (el servicio
  delega en el renderer mockeado); verificado también por inspección
  (`prompt_builder_service.py` no importa jinja2).

## Segunda pasada (post-review, 2026-07-01)

El reviewer aprobó (255 passed, 0 bloqueantes/mayores). El humano pidió
pulir 2 menores dentro del alcance de la feature 9:

1. **Tests de render para ARCHITECTURE y BUSINESS_RULES** añadidos en
   `tests/infra/adapters/prompt/test_jinja_prompt_renderer.py`:
   `test_render_scope_architecture`, `test_render_scope_business_rules`
   (verifican que cada plantilla renderiza sus atributos de ejemplo).
2. **KeyError genérico envuelto en excepción nombrada**: en
   `render_scope` se cambió `SCOPE_TEMPLATES[scope]` por `.get(scope)`
   con guard que lanza `UnknownPromptScopeError` (excepción ya existente
   en `prompt_errors.py`, hereda de `PromptBuilderError` → `AgenticError`)
   cuando un scope no tiene plantilla. Se reutilizó en lugar de crear
   `MissingTemplateError`: encaja semánticamente (scope no resoluble a
   plantilla), respeta el set de errores del design aprobado y evita
   añadir un tipo nuevo fuera del alcance. Test:
   `test_scope_without_template_raises_named_error` (fuerza
   `SCOPE_TEMPLATES = {}` con `patch`).
3. Menor 3 (alias `PromptAttributes` duplicado) NO tocado — lo exige el
   design.

Resultado tras la segunda pasada: **258 passed, 1 warning**
(255 previos + 3 nuevos). Total de tests nuevos de la feature: **14**.

Trazabilidad adicional:
- R13 → también `test_render_scope_architecture`,
  `test_render_scope_business_rules`.
- R14 / convención errores explícitos →
  `test_scope_without_template_raises_named_error`.

## Decisiones / notas

- Saneamiento reutiliza `sanitize_file_content`
  (`security/prompt_guard.py`, R7) y
  `CodeSanitizer.remove_blank_lines` (`loader/sanitizer.py`, R8), sin
  reimplementar, conforme al design §5.
- Tipo de atributos: `Dict[str, JsonValue]` (alias `PromptAttributes`),
  sin `Any`, conforme al design §1 y R16.
- `JinjaPromptRenderer` usa `Environment(autoescape=False)` (design) y
  captura `jinja2.TemplateError` (clase base de errores de plantilla,
  cubre sintaxis inválida y undefined-en-strict) relanzando
  `PromptRenderError` sin propagar el tipo interno (R14).
- Sin desviaciones respecto al spec. No se detectaron conflictos entre
  spec y convenciones.
- `tasks.md`: T1–T25 marcadas `[x]`.
