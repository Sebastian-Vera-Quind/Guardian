# Design: load_rules

Integración de capa de persistencia PostgreSQL mediante arquitectura hexagonal
con validación de seguridad (defense-in-depth) y parseo de JSONB.

## Arquitectura General

Seguiremos la arquitectura hexagonal definida en `docs/architecture.md`:

- **Domain** (`./src/domain/`): Contratos (protocols) y modelos.
- **Infra** (`./src/infra/`): Adaptadores concretos a PostgreSQL/SQLAlchemy.
- **Application**: No afectada directamente (future services pueden inyectar
  `RulesRepository`).

```
Domain (Port: RulesRepository)
       ↑
       | implements
       |
Infra (Adapter: PostgresRulesRepositoryAdapter)
       → SQLAlchemy Core + guardian_db
```

## Archivos a crear/modificar

### Nuevos archivos:

1. `src/domain/ports/output/rules/__init__.py` — Paquete de puertos de salida
   para reglas.
2. `src/domain/ports/output/rules/rules_repository.py` — Contrato
   `RulesRepository` con método `get_project_context()`.
3. `src/domain/models/project_context.py` — Entidad `ProjectContext`
   (Pydantic o dataclass).
4. `src/domain/models/errors.py` (modificar) — Excepciones:
   `RulesRepositoryError`, `InvalidScopeError`, `MissingViewError`,
   `ProjectContextNotFoundError`.
5. `src/infra/db/__init__.py` — Paquete de configuración DB.
6. `src/infra/db/config.py` — Engine SQLAlchemy a partir de variable de
   entorno `TML_DATABASE_URL`.
7. `src/infra/adapters/db/__init__.py` — Paquete de adaptadores DB.
8. `src/infra/adapters/db/postgres_rules_repository.py` — Implementación
   `PostgresRulesRepositoryAdapter`.

### Archivos a modificar:

1. `src/domain/ports/output/__init__.py` — Exportar `RulesRepository`.
2. `src/domain/models/__init__.py` — Exportar `ProjectContext` y excepciones.
3. `src/infra/helper/adapter_injector.py` — Registrar inyección de
   `RulesRepository` → `PostgresRulesRepositoryAdapter`.

## Decisiones de diseño

### 1. SQLAlchemy Core vs ORM

**Opción elegida:** SQLAlchemy Core (`.text()`, `.select()`) sin mapeos ORM.

**Justificación:**
- Los requerimientos explícitamente piden NO crear entidades por tabla
  (R24).
- SQLAlchemy Core es más ligero y adecuado para queries directas a una
  vista.
- Evita overhead de ORM para una consulta simple.
- Facilita iteración si la vista `view_project_rules` cambia.

**Alternativa descartada:** Full ORM (SQLAlchemy declarative_base).
- Requeriría mapeos de `projects`, `use_cases`, `checklists` innecesarios.
- Aumenta complejidad sin beneficio tangible.

### 2. Validación SQL Injection

**Opción elegida:** Allow-list regex `^[a-z_,\s*]+$` + parametrización con
`:project_code`.

**Justificación:**
- Defense-in-depth: dos capas de protección.
- Regex restringe scope a lowercase + underscore + commas + asteriscos.
- Parámetros nombrados previenen inyección en `project_code`.
- Coincide con patrón del código de ejemplo en aceptación.

**Alternativa descartada:** Confiar solo en parámetros.
- Menos defensivo si scope se gestiona dinámicamente.
- El ejemplo de código usa regex explícitamente.

### 3. Parseo de JSONB

**Opción elegida:** Helper `_parse_json_field()` con try/except + default `[]`.

**Justificación:**
- Algunos campos pueden ser NULL o strings JSON inválidos.
- Función helper centraliza lógica reutilizable.
- Evita fallos abruptos; retorna default seguro.

**Alternativa descartada:** Validar en la vista SQL.
- Complica DDL de vista.
- Responsabilidad de la aplicación es manejar datos.

### 4. Estructura de entidades

**Opción elegida:** Pydantic `ProjectContext` con campos dinámicos (dict).

**Justificación:**
- Permite representar scopes variados sin N clases.
- Pydantic proporciona validación y serialización.
- Fácil de extender si scopes cambian.

**Alternativa descartada:** Dataclass estricta por scope.
- Requeriría `StructureContext`, `DomainContext`, etc.
- Menos flexible.

### 5. Ubicación de helpers

**Opción elegida:** Módulo `postgres_rules_repository.py` contiene
`_parse_json_field()`, `_JSONB_FIELDS`, `_SAFE_FIELDS_RE`.

**Justificación:**
- Encapsulación: helpers privados solo usados por adapter.
- Fácil testeo dentro del módulo.
- No contamina namespace global.

### 6. Inyección de dependencias

**Opción elegida:** Adaptador recibe solo contratos (protocols), no
dependencias concretas. El paquete `src/infra/db/` instancia el engine
Alembic.

**Justificación:**
- Conforme a `docs/architecture.md`: dependencias inyectadas, no
  instanciadas dentro de la clase.
- El adaptador depende de `RulesRepository` (contrato), no de Engine
  directo.
- El paquete `db/` es responsable de crear y gestionar el engine.
- Mejor testabilidad: mockear el contrato es más limpio.

**Alternativa descartada:** Adaptador recibe Engine directamente.
- Acopla el adaptador a detalles de infraestructura.
- Dificulta testing con mocks.

## Firmas nuevas

### Puerto (Domain)
```python
# src/domain/ports/output/rules/rules_repository.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class RulesRepository(ABC):
    @abstractmethod
    def get_project_context(
        self, project_code: str, scope: str
    ) -> Dict[str, Any]:
        """
        Recuperar contexto del proyecto por scope.
        
        Args:
            project_code: Código único del proyecto.
            scope: Uno de: structure, domain, infrastructure, review, master.
        
        Returns:
            Dict con campos del scope solicitado.
        
        Raises:
            InvalidScopeError: Si scope no es válido.
            ProjectContextNotFoundError: Si no hay contexto para el proyecto.
            MissingViewError: Si view_project_rules no existe.
        """
        ...
```

### Entidad (Domain)
```python
# src/domain/models/project_context.py
from pydantic import BaseModel
from typing import Any, Dict

class ProjectContext(BaseModel):
    project_code: str
    scope: str
    data: Dict[str, Any]  # Campos del scope
    
    class Config:
        frozen = True  # Inmutable
```

### Adapter (Infra)
```python
# src/infra/adapters/db/postgres_rules_repository.py
from src.domain.ports.output.rules import RulesRepository
from typing import Dict, Any

class PostgresRulesRepositoryAdapter(RulesRepository):
    def __init__(self, engine: Engine):
        """
        Inicializar adaptador.
        
        NOTA: El parámetro engine es una dependencia concreta, pero viene
        inyectada desde src/infra/db/config.py (que maneja Alembic).
        El adaptador depende del contrato RulesRepository, no de Engine.
        """
        self._engine = engine
        self._validate_view_exists()
    
    def get_project_context(
        self, project_code: str, scope: str
    ) -> Dict[str, Any]:
        """Implementación concreta."""
        ...
    
    def _validate_view_exists(self) -> None:
        """Verificar que view_project_rules existe."""
        ...
```

### Helper functions
```python
_JSONB_FIELDS = {
    'coding_standards', 'checklist', 'patrones_diseno',
    'reglas_dominio', 'lista_casos_uso', 'specs_infraestructura',
    'db_engines', 'api_types', 'messaging',
}

_SAFE_FIELDS_RE = re.compile(r"^[a-z_,\s*]+$")

def _parse_json_field(value: Any) -> Any:
    """Parsear campo JSONB, retornar [] por defecto."""
    ...
```

## Excepciones

Nuevas excepciones en `src/domain/models/errors.py`:

```python
class RulesRepositoryError(AgenticError):
    """Base para errores de repositorio de reglas."""
    pass

class InvalidScopeError(RulesRepositoryError):
    """Scope inválido."""
    pass

class MissingViewError(RulesRepositoryError):
    """Vista view_project_rules no existe."""
    pass

class ProjectContextNotFoundError(RulesRepositoryError):
    """No hay contexto para el proyecto."""
    pass
```

Todas heredan de `AgenticError` (conforme a `docs/conventions.md`).

## Variable de entorno

Se utiliza una única variable de entorno:

```
TML_DATABASE_URL=postgresql://user:password@localhost:5432/guardian_db
```

Esta variable será leída por `src/infra/db/config.py`, que instancia el engine
SQLAlchemy que será utilizado por Alembic y los adaptadores.

## Responsabilidad del desarrollador

El desarrollador DEBE proporcionar:

1. Vista `view_project_rules` en la base de datos `guardian_db`.
2. Variable de entorno `TML_DATABASE_URL` configurada correctamente.

El sistema verificará la existencia de la vista en `PostgresRulesRepositoryAdapter.__init__()`;
si no existe, lanzará `MissingViewError`.

## Inyección de dependencias

En `src/infra/helper/adapter_injector.py`:

```python
def inject_repositories() -> None:
    from src.infra.adapters.db.postgres_rules_repository import (
        PostgresRulesRepositoryAdapter,
    )
    from src.domain.ports.output.rules import RulesRepository
    
    adapter = PostgresRulesRepositoryAdapter()
    # Registrar binding RulesRepository → adapter
    container.register(RulesRepository, instance=adapter)
```

El paquete `src/infra/db/` es responsable de:
- Leer `TML_DATABASE_URL`.
- Crear el engine SQLAlchemy.
- Gestionar migraciones Alembic.
- Proporcionar `get_engine()` para otros módulos.

## Restricciones y limitaciones

1. La vista `view_project_rules` DEBE ser proporcionada por el desarrollador.
2. No se crean mapeos ORM; solo queries directas.
3. Campos JSONB nulos o inválidos retornan `[]`.
4. Scope DEBE estar en allow-list (`structure`, `domain`, `infrastructure`,
   `review`, `master`).
