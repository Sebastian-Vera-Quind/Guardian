# Review: 9 — prompt_builder

## Veredicto: APROBADO

Fecha: 2026-07-01. Reviewer.

La implementación cubre íntegramente R1–R18, respeta la arquitectura
hexagonal y las convenciones del repo. Todos los tests pasan.

## Resultado de pytest

`python -m pytest -q` → **255 passed, 1 warning in ~11s**.

- Coincide con lo reportado por el implementer (255, baseline 244, +11 nuevos).
- El único warning es pre-existente (StarletteDeprecationWarning de FastAPI
  TestClient), ajeno a esta feature.
- Nuevos tests confirmados: `tests/application/prompt` (6),
  `tests/infra/adapters/prompt` (3), `tests/infra/helper` (2) = 11.

## Tabla de cobertura R1–R18

| Req | Estado    | Evidencia |
|-----|-----------|-----------|
| R1  | cubierto  | `prompt_scope.py`: `PromptScope(str, Enum)` con CHECKLIST/ARCHITECTURE/BUSINESS_RULES y valores correctos |
| R2  | cubierto  | `ports/input/prompt/prompt_builder.py` (ABC); exportado en `ports/input/__init__.py` |
| R3  | cubierto  | `ports/output/prompt/prompt_renderer.py` (ABC); exportado en `ports/output/__init__.py` |
| R4  | cubierto  | `errors/prompt_errors.py`: `PromptBuilderError(AgenticError)` |
| R5  | cubierto  | `prompt_builder_service.py:42-44` valida `isinstance` y lanza `UnknownPromptScopeError` |
| R6  | cubierto  | `build_for_scope` delega en `render_scope`; test `test_build_for_scope_returns_rendered_prompt` |
| R7  | cubierto  | `sanitize` reutiliza `sanitize_file_content` (control chars) |
| R8  | cubierto  | `sanitize` reutiliza `CodeSanitizer.remove_blank_lines` (líneas en blanco / solo-espacios) |
| R9  | cubierto  | Método público `sanitize(content)` independiente en el servicio |
| R10 | cubierto  | `build_from_template(template, attributes)` delega en `render_template` |
| R11 | cubierto  | `_sanitize_attributes` sanea solo valores `str`; test `test_sanitize_attributes_sanitizes_only_strings` |
| R12 | cubierto  | `jinja_prompt_renderer.py` usa `jinja2.Environment.from_string(...).render(...)` |
| R13 | cubierto  | `render_scope` resuelve `SCOPE_TEMPLATES[scope]` y delega |
| R14 | cubierto  | Captura `jinja2.TemplateError` y relanza `PromptRenderError` con `from error`; test `test_invalid_template_raises_prompt_render_error` |
| R15 | cubierto  | Registrado en `adapter_injector.py`, `usecase_injector.py`, `inject.py`; tests de inyección OK |
| R16 | cubierto  | Grep de `Any` en archivos nuevos = 0; se usa `Dict[str, JsonValue]` |
| R17 | cubierto  | `logging.getLogger(__name__)`; DEBUG en construcción, WARNING en scope desconocido, ERROR en fallo de render; sin `print()` |
| R18 | cubierto  | `application` no importa jinja2; delega vía `PromptRenderer`; jinja2 solo en `infra` |

## Convenciones duras

- CERO `Any`: verificado por grep en todos los archivos nuevos (0 coincidencias).
- Orientación de puertos: correcta. Servicio (`application`) implementa el
  input port `PromptBuilder`; adaptador (`infra`) implementa el output port
  `PromptRenderer`. `application/prompt/*` NO importa jinja2 (solo `infra`).
- Excepciones: heredan de `AgenticError` / `PromptBuilderError`, patrón idéntico
  a `rules_errors.py` (docstring + `pass`). Errores de jinja2 envueltos, no
  propagados.
- Enum de scopes en dominio (`domain/models/prompt_scope.py`), sigue el patrón
  de `TreeObjectType(str, Enum)`.
- Saneamiento reutiliza utilidades existentes (`sanitize_file_content`,
  `CodeSanitizer.remove_blank_lines`); no reimplementa.
- Inyección coherente con el patrón existente (`OutPortType`/`InPortType`,
  factories, `@overload`, uniones de retorno). Import lazy dentro de factories
  como el resto.
- Longitud de línea ≤ 79 y 2 espacios de indentación: verificado, sin
  violaciones en archivos nuevos.

## Calidad de tests

- Scopes: `test_render_scope_resolves_scope_template` cubre CHECKLIST. El
  método `render_scope` es genérico (`SCOPE_TEMPLATES[scope]`), pero solo se
  ejercita explícitamente el scope CHECKLIST en tests. ARCHITECTURE y
  BUSINESS_RULES no tienen test de render dedicado (menor).
- Método genérico string+dict: `test_build_from_template_delegates_with_sanitized_attrs`
  y `test_render_template_renders_attributes` cubren R10/R12.
- Saneamiento: control chars (R7), líneas en blanco (R8) y no-string intacto
  (R11) cubiertos.
- Casos borde: scope inválido (`UnknownPromptScopeError`) y template inválido
  (`PromptRenderError`) cubiertos.

## Hallazgos

### Menores

1. **[menor] Cobertura de tests parcial sobre los tres scopes** —
   `tests/infra/adapters/prompt/test_jinja_prompt_renderer.py:18`. Solo se
   testea `PromptScope.CHECKLIST` en `render_scope`. ARCHITECTURE y
   BUSINESS_RULES quedan sin test de render explícito (aunque el mapa
   `SCOPE_TEMPLATES` los define y la ruta de código es idéntica). Sugerencia:
   parametrizar sobre los tres scopes. No bloqueante.

2. **[menor] `render_scope` sin manejo explícito de `KeyError`** —
   `src/infra/adapters/prompt/jinja_prompt_renderer.py:39`. `SCOPE_TEMPLATES[scope]`
   lanzaría `KeyError` (excepción genérica) si en el futuro se añade un miembro
   a `PromptScope` sin plantilla asociada. Hoy es imposible alcanzarlo porque el
   servicio valida `isinstance(scope, PromptScope)` antes y el mapa cubre los 3
   miembros actuales, por eso es menor y no bloqueante. Convención de "errores
   explícitos" sugeriría envolverlo en `UnknownPromptScopeError`.

3. **[menor] `PromptAttributes` duplicado en dos módulos** — el alias
   `PromptAttributes = Dict[str, JsonValue]` se define idéntico en
   `ports/input/prompt/prompt_builder.py:6` y
   `ports/output/prompt/prompt_renderer.py:6`. El design lo describe así (cada
   puerto lo declara), y ambos se re-exportan; es aceptable, pero es una leve
   duplicación de la fuente de verdad del tipo. No bloqueante.

## Notas

- Docstrings en dominio están mayormente en inglés (bien); las excepciones
  conservan docstrings en español coincidiendo con el patrón vecino
  (`rules_errors.py`), lo cual es consistente con el repo.
- `Environment(autoescape=False)` es intencional (prompts en texto plano,
  no HTML) y coherente con el design §4/§6.

## Resumen

- Bloqueantes: 0
- Mayores: 0
- Menores: 3
