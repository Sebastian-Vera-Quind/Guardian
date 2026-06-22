# Design: loader_node

## Arquitectura General

El `loader_node` es el primer nodo del workflow LangGraph que orquesta la carga y sanitización de datos. Se implementa como una función async que recibe `AgentState` y retorna un diccionario con actualizaciones de estado, siguiendo el patrón establecido en la feature `workflow_start`.

Integración en la arquitectura hexagonal:
- **Domain** (`./domain/models/state/`): Usa modelos existentes `FileContent`, `RepositoryMetadata`, `AgentState`.
- **Infra Adapter** (`./infra/adapters/workflow/nodes/`): Implementa `loader.py` con función `node_loader_task()`.
- **Utility** (`./infra/helpers/sanitizer.py`): Servicio reutilizable de sanitización de código.

## Archivos a crear/modificar

### Nuevos archivos:

1. `infra/adapters/workflow/nodes/loader.py` — Implementa función async `node_loader_task()` que orquesta la carga.
2. `infra/helpers/sanitizer.py` — Clase `CodeSanitizer` con métodos para sanitizar líneas, contar código, validar JSONL.
3. `infra/helpers/metadata_extractor.py` — Clase `MetadataExtractor` para extraer `owner`, `author_name`, `commit_message`, `repo_name` desde repositorio.
4. `domain/models/errors/loader_errors.py` — Excepciones personalizadas: `LoaderNodeError`, `SanitizationError`, `MetadataExtractionError`, `InvalidJSONLError`.

### Archivos existentes a modificar:

1. `src/infra/adapters/workflow/__init__.py` — Exporta `node_loader_task`.
2. `src/infra/adapters/workflow/nodes/__init__.py` — Exporta `node_loader_task`.
3. `src/domain/models/__init__.py` — Exporta nuevas excepciones de loader.
4. `src/infra/helpers/__init__.py` — Exporta `CodeSanitizer`, `MetadataExtractor`.
5. `src/infra/adapters/workflow/builder.py` (existente de feature 2) — Añade nodo loader al grafo.

## Decisiones de diseño

### 1. Ruta de carga: Decisión basada en prioridad (R1, R2, R3)

**Opción elegida:** Evaluación secuencial con prioridad explícita.

```python
def determine_load_route(state: AgentState) -> str:
    """Determina ruta: 'clone' si repository, 'simple' si files_content, Error si ninguno."""
    has_files = state.get("files_content") and len(state["files_content"]) > 0
    has_repo = state.get("repository") is not None
    
    if has_repo:
        return "clone"  # Prioridad: repositorio
    elif has_files:
        return "simple"
    else:
        raise LoaderNodeError("No files_content or repository provided")
```

**Justificación:**
- Explícita y verificable por tests.
- Prioridad clara: repositorio > archivos.
- Fácil de extender en futuro si hay más rutas.

**Alternativa descartada:** Flag de preferencia en estado.
- Añade complejidad sin beneficio.
- La prioridad debe ser inmutable en la definición del protocolo.

---

### 2. Sanitización de código (R4, R5, R6)

**Opción elegida:** Clase `CodeSanitizer` con responsabilidad única.

```python
class CodeSanitizer:
    """Sanitiza contenido de archivos de código."""
    
    @staticmethod
    def remove_blank_lines(content: str) -> str:
        """Elimina líneas en blanco (solo espacios/tabs)."""
        lines = content.split('\n')
        cleaned = [line for line in lines if line.strip()]
        return '\n'.join(cleaned)
    
    @staticmethod
    def sanitize_files(files: List[FileContent]) -> List[FileContent]:
        """Sanitiza lista de archivos. Retorna solo archivos no vacíos."""
        result = []
        for file in files:
            sanitized_content = CodeSanitizer.remove_blank_lines(file.content)
            if sanitized_content.strip():  # Solo si hay contenido real
                result.append(FileContent(
                    path=file.path,
                    content=sanitized_content,
                    extension=file.extension
                ))
        return result
    
    @staticmethod
    def count_lines(files: List[FileContent]) -> int:
        """Cuenta total de líneas en todos los archivos."""
        return sum(len(f.content.split('\n')) for f in files)
```

**Justificación:**
- Separación de responsabilidades: la lógica de sanitización está encapsulada.
- Reutilizable en otros nodos que pudieran necesitar sanitización.
- Fácil de testear en aislamiento.
- Sigue el principio SRP y la arquitectura hexagonal.

**Alternativa descartada:** Lógica inline en el nodo.
- Haría el nodo más difícil de leer y testear.
- Duplicaría código si otro nodo necesita sanitización.

---

### 3. Extracción de metadatos (R7)

**Opción elegida:** Clase `MetadataExtractor` que mapea datos del repositorio a `RepositoryMetadata`.

```python
class MetadataExtractor:
    """Extrae metadatos de repositorio para escribir en estado."""
    
    @staticmethod
    def extract_from_repository(repo_data: dict) -> RepositoryMetadata:
        """
        Extrae metadatos desde diccionario repository.
        
        repository shape:
        {
            "url": "https://github.com/user/repo.git",
            "installation": "github-installation-code",
            "commit_sha": "abc123...",
            "target": "main"
        }
        """
        url = repo_data.get("url", "")
        
        # Extrae owner y repo_name desde URL
        # https://github.com/user/repo.git -> (user, repo)
        parts = url.rstrip('/').replace('.git', '').split('/')
        owner = parts[-2] if len(parts) >= 2 else "Unknown"
        repo_name = parts[-1] if len(parts) >= 1 else "Unknown"
        
        return RepositoryMetadata(
            owner=owner,
            repo_name=repo_name,
            branch=repo_data.get("target", "main"),
            commit_sha=repo_data.get("commit_sha"),
            author_name=repo_data.get("author_name", "Unknown Author"),
            author_email=repo_data.get("author_email"),
            # commit_message se obtiene en futuro desde GitHub API
            timestamp=datetime.now(timezone.utc)
        )
```

**Justificación:**
- Los metadatos ya están parcialmente en el estado (`author_name`, `commit_sha`, `github_token`).
- `RepositoryMetadata` es el contrato estándar (ya definido en feature 2).
- La extracción es determinística y no requiere llamadas HTTP en esta fase.

**Nota:** El campo `commit_message` requeriría una llamada a GitHub API. En esta versión inicial se puede dejar como `None` o con un placeholder, y ampliarse en feature futura.

---

### 4. Validación y extracción de `.devcore-attribution.jsonl` (R8, R9)

**Opción elegida:** Método `JSONLValidator` y lógica condicional en el nodo.

```python
class JSONLValidator:
    """Valida y extrae JSONL."""
    
    @staticmethod
    def is_valid_jsonl(content: str) -> bool:
        """Verifica que cada línea sea un JSON válido."""
        if not content.strip():
            return False
        lines = content.strip().split('\n')
        for line in lines:
            if line.strip():  # Salta líneas vacías
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    return False
        return True
    
    @staticmethod
    def extract_attribution_file(files: List[FileContent]) -> tuple[List[FileContent], Optional[str]]:
        """
        Extrae .devcore-attribution.jsonl si existe y es válido.
        Retorna (archivos_sin_attribution, contenido_jsonl_o_None).
        """
        remaining_files = []
        attribution_content = None
        
        for file in files:
            if file.path.endswith('.devcore-attribution.jsonl'):
                if JSONLValidator.is_valid_jsonl(file.content):
                    attribution_content = file.content
                else:
                    # Log warning: JSONL inválido
                    logger.warning(f"Invalid JSONL in {file.path}, skipping")
            else:
                remaining_files.append(file)
        
        return remaining_files, attribution_content
```

**Justificación:**
- JSONL es formato estándar en LLM observability.
- Validación explícita previene corrupción de datos.
- Logging de fallos para debugging.

**Alternativa descartada:** Intentar reparar JSONL inválido.
- Complica la lógica sin garantía de corrección.
- Mejor fallar explícitamente y dejar que el usuario corrija.

---

### 5. Estructura del nodo `loader_node`

**Opción elegida:** Función async pura que recibe estado y retorna actualizaciones.

```python
from src.infra.adapters.workflow.log import with_logging

@with_logging()
async def node_loader_task(state: AgentState) -> dict:
    """
    Nodo inicial del workflow.
    
    - Determina ruta (simple vs clone)
    - Sanitiza archivos (si ruta simple)
    - Cuenta líneas (si ruta simple)
    - Extrae metadatos (si ruta clone)
    - Extrae y valida .devcore-attribution.jsonl
    
    Escribe en estado:
      load_to: "simple" | "clone"
      files_content: List[FileContent] (sanitizado)
      total_lines: int (si simple)
      metadata: RepositoryMetadata (si clone)
      ai_attribution_jsonl: str (si presente y válido)
    """
    
    # 1. Determinar ruta
    load_route = determine_load_route(state)
    result = {"load_to": load_route}
    
    # 2. Procesar según ruta
    if load_route == "simple":
        files = state.get("files_content", [])
        
        # Extraer .devcore-attribution.jsonl
        files, attribution = JSONLValidator.extract_attribution_file(files)
        if attribution:
            result["ai_attribution_jsonl"] = attribution
        
        # Sanitizar
        sanitized = CodeSanitizer.sanitize_files(files)
        result["files_content"] = sanitized
        
        # Contar líneas
        result["total_lines"] = CodeSanitizer.count_lines(sanitized)
    
    elif load_route == "clone":
        repo_data = state.get("repository", {})
        
        # Extraer metadatos
        try:
            metadata = MetadataExtractor.extract_from_repository(repo_data)
            result["metadata"] = metadata.model_dump()  # Convierte a dict
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            raise MetadataExtractionError(str(e))
    
    return result
```

**Justificación:**
- Retorna dict que LangGraph usa automáticamente para actualizar estado.
- Decorado con `@with_logging()` para trazabilidad.
- Flujo claro y secuencial.
- Manejo de excepciones explícito.

---

### 6. Excepciones personalizadas

**Opción elegida:** Excepciones especializadas que heredan de `AgenticError`.

```python
# domain/models/errors/loader_errors.py

from src.domain.models import AgenticError

class LoaderNodeError(AgenticError):
    """Error general durante ejecución del nodo loader."""
    pass

class SanitizationError(LoaderNodeError):
    """Error durante sanitización de código."""
    pass

class MetadataExtractionError(LoaderNodeError):
    """Error durante extracción de metadatos."""
    pass

class InvalidJSONLError(LoaderNodeError):
    """JSONL inválido detectado."""
    pass
```

**Justificación:**
- Conform a `docs/conventions.md`: errores explícitos y nombrados.
- Jerarquía clara para manejo centralizado.
- Permite tests específicos por tipo de error.

---

### 7. Integración con el grafo (builder.py)

**Opción elegida:** Añadir nodo loader como entrada al grafo en `WorkflowBuilder`.

```python
# infra/adapters/workflow/builder.py (modificado)

from src.infra.adapters.workflow.nodes.loader import node_loader_task

class WorkflowBuilder:
    def build(self) -> StateGraph:
        graph = StateGraph(AgentState)
        
        # Añadir nodo loader al inicio
        graph.add_node("loader", node_loader_task)
        graph.add_node("start", node_start)  # Nodo de feature 2
        graph.add_node("process", node_process)
        graph.add_node("end", node_end)
        
        # Edges: loader es el punto de entrada
        graph.set_entry_point("loader")
        graph.add_edge("loader", "start")
        graph.add_edge("start", "process")
        graph.add_edge("process", "end")
        
        graph.set_finish_point("end")
        
        return graph.compile()
```

**Justificación:**
- El loader es conceptualmente el primer nodo (entrada).
- Todas las rutas posteriores dependen de sus salidas.
- El grafo es ahora: loader → start → process → end.

---

## Firmas nuevas

### Utilidades (nuevas)

```python
# infra/helpers/sanitizer.py
from typing import List
from src.domain.models.state.file import FileContent

class CodeSanitizer:
    @staticmethod
    def remove_blank_lines(content: str) -> str:
        """Elimina líneas que solo contengan espacios/tabs."""
        ...
    
    @staticmethod
    def sanitize_files(files: List[FileContent]) -> List[FileContent]:
        """Retorna archivos con contenido sanitizado, sin vacíos."""
        ...
    
    @staticmethod
    def count_lines(files: List[FileContent]) -> int:
        """Cuenta líneas totales de código."""
        ...

# infra/helpers/metadata_extractor.py
from src.domain.models.state.repository import RepositoryMetadata

class MetadataExtractor:
    @staticmethod
    def extract_from_repository(repo_data: dict) -> RepositoryMetadata:
        """Extrae owner, repo_name, branch desde diccionario repository."""
        ...

# infra/helpers/jsonl_validator.py
import json

class JSONLValidator:
    @staticmethod
    def is_valid_jsonl(content: str) -> bool:
        """Verifica que cada línea sea JSON válido."""
        ...
    
    @staticmethod
    def extract_attribution_file(
        files: List[FileContent]
    ) -> tuple[List[FileContent], Optional[str]]:
        """Extrae .devcore-attribution.jsonl si es válido."""
        ...
```

### Nodo (nueva función)

```python
# infra/adapters/workflow/nodes/loader.py
from src.domain.models.state.state import AgentState
from src.infra.adapters.workflow.log import with_logging

@with_logging()
async def node_loader_task(state: AgentState) -> dict:
    """Nodo inicial: carga y prepara datos."""
    ...
```

### Excepciones (nuevas)

```python
# domain/models/errors/loader_errors.py
from src.domain.models import AgenticError

class LoaderNodeError(AgenticError): ...
class SanitizationError(LoaderNodeError): ...
class MetadataExtractionError(LoaderNodeError): ...
class InvalidJSONLError(LoaderNodeError): ...
```

---

## Alternativa descartada: Múltiples nodos especializados

Se consideró dividir `loader_node` en tres nodos separados:
- `loader_files` — sanitiza y cuenta líneas
- `loader_repo` — extrae metadatos
- `loader_attribution` — extrae JSONL

**Motivo del descarte:**
- Añade complejidad al grafo sin beneficio tangible.
- La lógica de `loader_node` es secuencial y determinística.
- Una decisión de ruta (`load_to`) da forma a todo el procesamiento.
- Nodos separados requieren coordinación explícita en el grafo, duplicando lógica de routing.
- El patrón Kiro-style favorece nodos cohesivos sobre nodos micro.

**Por qué este diseño es mejor:**
- Un único nodo responsable de la transición "entrada bruta → estado preparado".
- Fácil de testear como unidad.
- Cambios en sanitización no requieren modificar el grafo.
