# Design: prompt_builder

Servicio de construcción de prompts con saneamiento de entrada y
renderizado Jinja2, siguiendo la arquitectura hexagonal de
`docs/architecture.md`.

## Arquitectura General

```
Domain
  ├─ models/prompt_scope.py         (PromptScope: Enum)
  ├─ models/errors/prompt_errors.py (PromptBuilderError, ...)
  ├─ ports/input/prompt/prompt_builder.py   (PromptBuilder: puerto entrada)
  └─ ports/output/prompt/prompt_renderer.py (PromptRenderer: puerto salida)
        ↑ implements                              ↑ implements
Application                                   Infra
  application/prompt/                          infra/adapters/prompt/
    prompt_builder_service.py                    jinja_prompt_renderer.py
    (implementa PromptBuilder,                   (implementa PromptRenderer,
     sanea entrada, delega a                      usa Jinja2)
     PromptRenderer)
```

- **Domain**: enum de scopes, contratos (protocols) y excepciones. Sin
  dependencias de terceros salvo Pydantic (aquí ni siquiera se necesita).
- **Application**: `PromptBuilderService` implementa `PromptBuilder`,
  realiza el saneamiento y delega el renderizado al puerto de salida
  `PromptRenderer`. NO importa Jinja2 (R18).
- **Infra**: `JinjaPromptRenderer` implementa `PromptRenderer` usando
  Jinja2; contiene el mapa `PromptScope → template`.

Este reparto replica el patrón `ContextRetriever` (input) +
`ContextRetrievalService` (application) + adaptadores de salida ya
existentes.

## Archivos a crear

### Domain
1. `src/domain/models/prompt_scope.py` — `PromptScope(str, Enum)` con
   `CHECKLIST`, `ARCHITECTURE`, `BUSINESS_RULES`. Sigue el patrón de
   `TreeObjectType(str, Enum)` en `src/domain/models/repo/tree.py`.
2. `src/domain/models/errors/prompt_errors.py` — `PromptBuilderError`,
   `UnknownPromptScopeError`, `PromptRenderError`.
3. `src/domain/ports/input/prompt/__init__.py` — exporta `PromptBuilder`.
4. `src/domain/ports/input/prompt/prompt_builder.py` — protocolo
   `PromptBuilder` (ABC).
5. `src/domain/ports/output/prompt/__init__.py` — exporta `PromptRenderer`.
6. `src/domain/ports/output/prompt/prompt_renderer.py` — protocolo
   `PromptRenderer` (ABC).

### Application
7. `src/application/prompt/__init__.py` — exporta `PromptBuilderService`.
8. `src/application/prompt/prompt_builder_service.py` — implementación del
   servicio.

### Infra
9. `src/infra/adapters/prompt/__init__.py` — exporta `JinjaPromptRenderer`.
10. `src/infra/adapters/prompt/jinja_prompt_renderer.py` — adaptador Jinja2.
11. `src/infra/adapters/prompt/templates.py` — mapa
    `PromptScope → str` con las plantillas Jinja2 por scope.

## Archivos a modificar

1. `src/domain/models/__init__.py` — exportar `PromptScope`,
   `PromptBuilderError`, `UnknownPromptScopeError`, `PromptRenderError`.
2. `src/domain/models/errors/__init__.py` — exportar las 3 excepciones.
3. `src/domain/ports/input/__init__.py` — exportar `PromptBuilder`.
4. `src/domain/ports/output/__init__.py` — exportar `PromptRenderer`.
5. `src/infra/helper/adapter_injector.py` — registrar `PromptRenderer`
   (nuevo miembro en `OutPortType`, factory y binding).
6. `src/infra/helper/usecase_injector.py` — registrar `PromptBuilder`
   (nuevo miembro en `InPortType`, factory que inyecta `PromptRenderer`).
7. `src/infra/helper/inject.py` — añadir los `@overload` para los nuevos
   tipos, siguiendo el patrón existente.

## Decisiones de diseño

### 1. Tipo de los "atributos de entrada" (evitar `Any`)

**Opción elegida:** reutilizar el alias `JsonValue` ya definido en
`src/domain/models/project_context.py` y tipar los atributos como
`Dict[str, JsonValue]` (alias `PromptAttributes = Dict[str, JsonValue]`).

**Justificación:**
- `JsonValue` es un tipo recursivo concreto (str/int/float/bool/None/list/
  dict) que ya se usa en el dominio; evita `Any` cumpliendo R16.
- Los atributos de un prompt son datos serializables sencillos, no objetos
  arbitrarios; `JsonValue` los cubre.
- Homogeneidad: el mismo alias ya cruza la frontera dominio→infra.

**Alternativa descartada:** `TypedDict` por scope
(`ChecklistAttributes`, etc.).
- Requeriría una clase por scope y acoplaría los contratos a la forma
  concreta de cada plantilla, dificultando añadir campos.
- El acceptance pide un método "genérico"; un dict tipado genérico encaja
  mejor que N TypedDict.

**Alternativa descartada:** `TypeVar` genérico ligado a un `BaseModel`.
- Añade complejidad de genéricos sin beneficio real: las plantillas Jinja2
  consumen un mapping, no un modelo tipado. El saneamiento (R7/R8) recorre
  valores string del mapping de forma uniforme.

### 2. Separación puerto entrada / puerto salida

**Opción elegida:** `PromptBuilder` (input, en `ports/input/prompt/`) lo
implementa el servicio de `application`; `PromptRenderer` (output, en
`ports/output/prompt/`) lo implementa el adaptador Jinja2 de `infra`.

**Justificación:**
- Es exactamente el patrón vigente (`ContextRetriever` input +
  adaptadores output). El servicio orquesta y sanea; el adaptador conoce
  Jinja2.
- Mantiene `application` libre de Jinja2 (R18).

**Alternativa descartada:** que el servicio use Jinja2 directamente.
- Violaría `docs/architecture.md` (application no depende de infra) y R18.

### 3. Ubicación de las plantillas por scope

**Opción elegida:** un módulo `templates.py` en `infra/adapters/prompt/`
con un `Dict[PromptScope, str]` de plantillas Jinja2 inline.

**Justificación:**
- Las plantillas son un detalle de infraestructura (dependen de Jinja2);
  no pertenecen al dominio.
- Mantenerlas como constantes en un módulo dedicado facilita edición y
  testeo del mapa scope→template.

**Alternativa descartada:** ficheros `.j2` cargados por `FileSystemLoader`.
- Añade I/O y gestión de rutas/empaquetado sin beneficio para plantillas
  cortas. Se puede migrar más adelante sin cambiar los contratos.

### 4. Dependencia Jinja2

`jinja2 (>=3.1.6,<4.0.0)` ya está declarado en `pyproject.toml` e instalado
(3.1.6). El adaptador lo usa directamente (R12); no se requiere ninguna
modificación fuera de `src/`.

### 5. Saneamiento reutilizando el saneador existente

**Opción elegida:** el saneamiento del servicio reutiliza
`sanitize_file_content` de `src/application/security/prompt_guard.py`
(elimina caracteres de control, R7) y la lógica de
`CodeSanitizer.remove_blank_lines` de `src/application/loader/sanitizer.py`
(elimina líneas en blanco, R8). El método público de saneamiento del
servicio compone ambas.

**Justificación:**
- Homogeneidad: ya existen ambas utilidades; no se reimplementa.
- El acceptance de la feature 3 (`loader_node`) definió el mismo criterio
  de "eliminar líneas en blanco"; reutilizar mantiene consistencia.

**Alternativa descartada:** reimplementar el saneamiento en el servicio.
- Duplicaría lógica y arriesgaría divergencia de comportamiento.

### 6. Manejo de errores de Jinja2

**Opción elegida:** el adaptador captura excepciones de Jinja2
(`TemplateError` y subclases) y relanza `PromptRenderError` (R14), sin
propagar el tipo interno de Jinja2 hacia application/dominio.

**Justificación:**
- Errores explícitos y nombrados (`docs/architecture.md` §3,
  `docs/conventions.md` §Errores).
- Aísla al dominio de detalles de la librería de terceros.

## Firmas nuevas

### Domain — enum
```python
# src/domain/models/prompt_scope.py
from enum import Enum

class PromptScope(str, Enum):
  CHECKLIST = "checklist"
  ARCHITECTURE = "architecture"
  BUSINESS_RULES = "business_rules"
```

### Domain — puerto de entrada
```python
# src/domain/ports/input/prompt/prompt_builder.py
from abc import ABC, abstractmethod
from typing import Dict

from src.domain.models import PromptScope, JsonValue

PromptAttributes = Dict[str, JsonValue]

class PromptBuilder(ABC):
  @abstractmethod
  def build_for_scope(
    self, scope: PromptScope, attributes: PromptAttributes
  ) -> str: ...

  @abstractmethod
  def build_from_template(
    self, template: str, attributes: PromptAttributes
  ) -> str: ...

  @abstractmethod
  def sanitize(self, content: str) -> str: ...
```

### Domain — puerto de salida
```python
# src/domain/ports/output/prompt/prompt_renderer.py
from abc import ABC, abstractmethod
from typing import Dict

from src.domain.models import PromptScope, JsonValue

PromptAttributes = Dict[str, JsonValue]

class PromptRenderer(ABC):
  @abstractmethod
  def render_scope(
    self, scope: PromptScope, attributes: PromptAttributes
  ) -> str: ...

  @abstractmethod
  def render_template(
    self, template: str, attributes: PromptAttributes
  ) -> str: ...
```

### Application — servicio
```python
# src/application/prompt/prompt_builder_service.py
class PromptBuilderService(PromptBuilder):
  def __init__(self, renderer: PromptRenderer) -> None:
    self._renderer = renderer

  def build_for_scope(self, scope, attributes) -> str: ...
  def build_from_template(self, template, attributes) -> str: ...
  def sanitize(self, content: str) -> str: ...
  def _sanitize_attributes(
    self, attributes: PromptAttributes
  ) -> PromptAttributes: ...
```

### Infra — adaptador
```python
# src/infra/adapters/prompt/jinja_prompt_renderer.py
class JinjaPromptRenderer(PromptRenderer):
  def __init__(self) -> None:
    self._env = jinja2.Environment(autoescape=False)

  def render_scope(self, scope, attributes) -> str: ...
  def render_template(self, template, attributes) -> str: ...
```

## Excepciones

Nuevas en `src/domain/models/errors/prompt_errors.py`:

```python
from src.domain.models import AgenticError

class PromptBuilderError(AgenticError):
  """Error base de construcción de prompts."""

class UnknownPromptScopeError(PromptBuilderError):
  """Scope no reconocido por PromptScope."""

class PromptRenderError(PromptBuilderError):
  """Fallo al renderizar la plantilla Jinja2."""
```

Todas heredan de `AgenticError` conforme a `docs/conventions.md`.

## Inyección de dependencias

- `adapter_injector.py`: añadir `OutPortType.PromptRenderer` y factory
  `_create_prompt_renderer()` que retorne `JinjaPromptRenderer()`.
- `usecase_injector.py`: añadir `InPortType.PromptBuilderService` y factory
  `_create_prompt_builder_service()` que inyecte el `PromptRenderer` vía
  `inject(OutPortType.PromptRenderer)` y construya `PromptBuilderService`.
- `inject.py`: añadir los `@overload` correspondientes y las entradas en
  las uniones de retorno.

## Restricciones y limitaciones

1. `jinja2` ya está disponible como dependencia (decisión 4); no requiere
   cambios en `pyproject.toml`.
2. Los atributos de entrada se tipan como `Dict[str, JsonValue]`; valores
   no serializables no están soportados.
3. `application` NO importa Jinja2; todo renderizado pasa por el adaptador.
