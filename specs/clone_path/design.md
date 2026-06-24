# Design: clone_path

## Arquitectura General

El `clone_path` es el segundo nodo del workflow LangGraph que clona repositorios, efectúa checkouts, y genera análisis de diferencias. Se implementa como una función async que recibe `AgentState` y retorna un diccionario con actualizaciones de estado, siguiendo el patrón establecido en `loader_node`.

Integración en la arquitectura hexagonal:
- **Domain** (`./src/domain/ports/output/`): Crear contratos para `RepositoryCloner` y `DiffGenerator`.
- **Application** (`./src/application/clone/`): Servicios de utilidades para operaciones con git y análisis de diferencias.
- **Infra Adapter**
  - (`./src/infra/adapters/git/`): Implementar `RepositoryCloner` (clona y checkouts).
  - (`./src/infra/adapters/diff/`): Implementar `DiffGenerator` (calcula diferencias línea por línea).
  - (`./src/infra/adapters/workflow/nodes/`): Implementar `clone_path.py` con función `node_clone_task()`.
- **Injection** (`./src/infra/helper/`): Registrar nuevos puertos en `OutPortInjector`.

## Archivos a crear/modificar

### Nuevos archivos:

1. `domain/models/errors/clone_errors.py` — Excepciones personalizadas: `ClonePathError`, `DiffGenerationError`.
2. `domain/ports/output/git/git_operations.py` — Contrato abstracto para operaciones git (clone, checkout, raw diff).
3. `domain/ports/input/clone/clone_service.py` — Puerto de entrada (use case) para operaciones de clonación.
4. `application/clone/__init__.py` — Exporta `CloneService`.
5. `application/clone/clone_service.py` — Implementa `CloneService` con métodos `clone()`, `build_tree()`, `build_diff()`.
6. `application/clone/file_excluder.py` — Servicio interno para filtrar archivos según `.aiignore` y extensiones.
7. `application/clone/tree_builder.py` — Servicio interno para construir árbol de directorios.
8. `application/clone/diff_builder.py` — Servicio interno para construir diff línea por línea desde git output.
9. `infra/adapters/git/git_operations_impl.py` — Implementa `GitOperations` usando GitPython (clone, checkout, diff raw).
10. `infra/adapters/workflow/nodes/clone_path.py` — Implementa función async `node_clone_task()`.

### Archivos existentes a modificar:

1. `src/infra/helper/usecase_injector.py` — Añade `CloneService` a `InPortType`.
2. `src/infra/helper/adapter_injector.py` — Añade `GitOperations` a `OutPortType`.
3. `src/infra/helper/inject.py` — Añade overloads para nuevos tipos de puertos.
4. `src/domain/models/__init__.py` — Exporta nuevas excepciones de clone.
5. `src/domain/ports/input/__init__.py` — Exporta `CloneService`.
6. `src/domain/ports/output/__init__.py` — Exporta `GitOperations`.
7. `src/infra/adapters/workflow/__init__.py` — Exporta `node_clone_task`.
8. `src/infra/adapters/workflow/nodes/__init__.py` — Exporta `node_clone_task`.
9. `src/infra/adapters/workflow/builder.py` — Añade nodo clone_path al grafo, conectándolo después de loader.
10. `src/domain/models/state/state.py` — (si no existe ya) Actualizar `AgentState` para incluir outputs de clone_path.

---

## Decisiones de diseño

### 0. Arquitectura de capas: CloneService como puerto de entrada (R18)

**Opción elegida:** Puerto de entrada `CloneService` (en `domain/ports/input/`) que implementa la lógica de negocio, delegando operaciones git brutas a puerto de salida `GitOperations`.

```python
# domain/ports/input/clone/clone_service.py (interfaz)
class CloneService(ABC):
    @abstractmethod
    def clone(
        self,
        repo_url: str,
        installation_token: Optional[str],
        commit_sha: str,
        target: Optional[str] = None
    ) -> Dict[str, Any]:
        """Orquesta clonación, checkout, diff y tree. Retorna dict con todos los outputs."""
        ...

# application/clone/clone_service.py (implementación)
class CloneService:
    def __init__(self, git_ops: GitOperations):
        self.git_ops = git_ops
    
    def clone(
        self,
        repo_url: str,
        installation_token: Optional[str],
        commit_sha: str,
        target: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orquesta:
        1. git_ops.clone() → clone_path
        2. git_ops.checkout(clone_path, commit_sha)
        3. Si target: git_ops.diff_raw() → parseado por diff_builder
        4. tree_builder.build_tree() → project_tree
        
        Internamente usa:
        - FileExcluder (carga .aiignore, filtra extensiones)
        - DiffBuilder (parsea git diff output)
        - TreeBuilder (recorre filesystem)
        """
        ...
```

**Justificación:**
- `CloneService` en layer application define lógica de negocio (cómo orquestar clonación, diff, tree).
- `GitOperations` en infra proporciona primitivas git (clone, checkout, diff bruto).
- Separación clara: application maneja flujo; infra maneja git.
- Puertos de entrada permiten inyectar `CloneService` en otros contextos (p. ej. HTTP handlers).
- El nodo solo inyecta `CloneService`; no toca git directamente.

**Alternativa descartada:** Dos puertos de salida separados (`RepositoryManager` + `DiffGenerator`).
- Complicaría inyección en el nodo (dos dependencias).
- Lógica de orquestación (cuando clonar, cuándo hacer diff) sería responsabilidad del nodo, no de la capa application.
- Menos cohesión: diff y tree son outputs de un mismo "caso de uso" (analizar repositorio).

---

### 1. Autenticación con GitHub (R2, R3)

**Opción elegida:** Usar token de instalación como HTTP basic auth en la URL.

```python
def _build_clone_url(url: str, installation_token: Optional[str]) -> str:
    """Construye URL para clonación con autenticación opcional."""
    if installation_token:
        # Reemplaza https://github.com/ con https://x-access-token:TOKEN@github.com/
        url = url.replace("https://github.com/", f"https://x-access-token:{installation_token}@github.com/")
    return url
```

**Justificación:**
- GitPython maneja transparentemente la autenticación en URLs.
- No requiere configurar SSH keys o variables de entorno en tiempo de ejecución.
- El token se pasa solo en clonación; no se almacena.
- Compatible con GitHub App installations (patrón estándar).

**Alternativa descartada:** Configurar git credenciales globales.
- Requeriría modificar `~/.gitconfig`, afectando sesiones posteriores.
- Menos seguro para ambientes multi-tenant.
- Mayor complejidad en cleanup.

---

### 2. Ubicación temporal de clonación (R1)

**Opción elegida:** Usar `/tmp/guardian/<uuid v4>/` con `tempfile.TemporaryDirectory()`.

```python
import tempfile
from uuid import uuid4

clone_dir = f"/tmp/guardian/{uuid4()}"
os.makedirs(clone_dir, exist_ok=True)
# O usar context manager:
with tempfile.TemporaryDirectory(dir="/tmp/guardian") as clone_dir:
    # Clonar aquí
    ...
```

**Justificación:**
- `/tmp/guardian/` es visible, debuggeable, y persiste en la sesión.
- UUID v4 garantiza unicidad sin colisiones.
- Context manager asegura limpieza en error (R16).
- Compatible con el patrón de limpieza manual en workflow edge case.

**Alternativa descartada:** Usar directorio in-memory (ramfs/tmpfs).
- Limita repositorios muy grandes (> RAM disponible).
- Complejidad adicional en configuración del filesystem.

---

### 3. Checkout a commit específico (R4)

**Opción elegida:** Usar GitPython `repo.git.checkout(commit_sha)`.

```python
from git import Repo

repo = Repo(clone_path)
repo.git.checkout(commit_sha)
```

**Justificación:**
- Semántica clara: checkout es operación estándar de git.
- GitPython maneja errores si commit no existe (capturable como `GitCommandError`).
- Operación atómica; no deja repositorio en estado inconsistente.

**Alternativa descartada:** Usar `git reset --hard`.
- Innecesario; checkout es el comando correcto para cambiar de commit.

---

### 4. Generación de diff (R5, R6)

**Opción elegida:** Integración del diff en `GitRepositoryCloner.get_diff()` con patrón callback.

```python
class GitRepositoryCloner(RepositoryCloner):
    def get_diff(
        self,
        repo_path: str,
        target_commit: str,
        callback: Callable[[str, DiffFile], None],
        base_commit: Optional[str] = None
    ) -> None:
        """
        Genera diff línea por línea usando GitPython diff API.
        
        Procesa tres tipos de cambios:
        1. Modificados (M): cambios en archivos existentes
        2. Deletados (D): archivos eliminados
        3. Añadidos (A): archivos nuevos
        
        Para cada cambio, invoca callback(file_path, DiffFile) donde:
        - file_path: str (ruta relativa del archivo)
        - DiffFile: {
            "is_new": bool,
            "is_deleted": bool,
            "additions": int,
            "deletions": int,
            "content": List[DiffContent]  # líneas con status (ADDED/MODIFIED/DELETED)
          }
        
        Estructura de cambio de línea:
        DiffContent = {
            "status": ChangeType.ADDED | MODIFIED | DELETED,
            "line_number": int,
            "content": str
        }
        """
        ...
```

**Justificación:**
- GitPython `diff()` API es nativa y controlada: acceso directo a cambios sin parsear strings.
- Patrón callback permite procesamiento lazy y eficiente de cambios sin acumular en memoria.
- Campos `is_new` y `is_deleted` ofrecen semántica clara sobre el tipo de archivo modificado.
- Separación de tipos de cambios (M/D/A) hace diff determinístico y testeable.
- Integración en `RepositoryCloner` simplifica inyección: una dependencia en lugar de dos.

**Alternativa descartada:** Usar `git diff` con parsing manual.
- Más lento en repositorios grandes (subprocess overhead).
- Menos seguro ante casos edge (encoding, caracteres especiales).

---

### 5. Filtrado de archivos: `.aiignore` y exclusiones (R7, R10)

**Opción elegida:** Clase `FileExcluder` con dos filtros: patrones `.aiignore` + extensiones hardcoded.

```python
class FileExcluder:
    """Determina qué archivos incluir/excluir en diff y tree."""
    
    def __init__(self, repo_path: str):
        """Lee .aiignore si existe."""
        self.aiignore_patterns = self._load_aiignore(repo_path)
    
    def _load_aiignore(self, repo_path: str) -> List[str]:
        """Parsea .aiignore (formato gitignore estándar)."""
        aiignore_path = os.path.join(repo_path, ".aiignore")
        if not os.path.exists(aiignore_path):
            return []
        with open(aiignore_path) as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    def should_include(self, file_path: str) -> bool:
        """Determina si un archivo debe incluirse."""
        # Excluye por extensión
        excluded_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
            ".mp4", ".avi", ".mkv", ".mov",
            ".md"
        }
        # Excluye por nombre exacto
        excluded_names = {
            "package-lock.json", "yarn.lock", "Pipfile.lock",
            "poetry.lock", "Gemfile.lock", "go.sum", "Cargo.lock"
        }
        
        name = os.path.basename(file_path)
        ext = os.path.splitext(name)[1].lower()
        
        # Chequea extensiones
        if ext in excluded_extensions:
            return False
        
        # Chequea nombres exactos
        if name in excluded_names:
            return False
        
        # Chequea .lock genéricos
        if name.endswith(".lock"):
            return False
        
        # Chequea patrones .aiignore
        for pattern in self.aiignore_patterns:
            if self._matches_gitignore_pattern(file_path, pattern):
                return False
        
        return True
    
    @staticmethod
    def _matches_gitignore_pattern(file_path: str, pattern: str) -> bool:
        """Implementa matching gitignore estándar."""
        # Usar librería pathspec para compatibilidad
        import pathspec
        spec = pathspec.PathSpec.from_lines("gitwildmatch", [pattern])
        return spec.match_file(file_path)
```

**Justificación:**
- `.aiignore` es análogo a `.gitignore`; permite usuarios controlar exclusiones.
- Extensiones hardcoded cubren casos comunes sin necesidad de `.aiignore`.
- `pathspec` (librería estándar de git) asegura compatibilidad con gitignore.

**Alternativa descartada:** Solo extensiones hardcoded.
- Menos flexible; imposible excluir directorios o patrones complejos.

---

### 6. Generación del árbol de directorios (R9, R11)

**Opción elegida:** Clase `TreeBuilder` que recorre filesystem y marca archivos nuevos según diff.

```python
class TreeBuilder:
    """Construye árbol jerárquico del repositorio."""
    
    @staticmethod
    def build_tree(
        repo_path: str,
        file_excluder: FileExcluder,
        added_files_set: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Construye árbol jerárquico comenzando en repo_path.
        
        1. Recorre directorios respetando FileExcluder.
        2. Marca archivos en added_files_set con 'is_new': true.
        3. Retorna estructura anidada conforme a R9.
        """
        def _traverse(path: str) -> Dict[str, Any]:
            node = {
                "name": os.path.basename(path) or "root",
                "type": "directory" if os.path.isdir(path) else "file"
            }
            
            if os.path.isdir(path):
                children = []
                for entry in os.listdir(path):
                    entry_path = os.path.join(path, entry)
                    if file_excluder.should_include(entry_path):
                        child = _traverse(entry_path)
                        children.append(child)
                if children:
                    node["children"] = children
            else:
                # Marcar si es archivo nuevo (R11)
                if added_files_set and path in added_files_set:
                    node["is_new"] = True
            
            return node
        
        return _traverse(repo_path)
```

**Justificación:**
- Recorrido recursivo es natural para estructura jerárquica.
- `is_new` se asigna desde el conjunto de archivos añadidos del diff.
- Respeta FileExcluder consistentemente.

---

### 7. Estructura del nodo `clone_path` (refactorizado)

**Opción elegida:** Función async pura que recibe estado e inyecta dependencias vía `inject()`, con callback-based diff.

```python
from src.infra.helper import inject, OutPortType
from src.infra.adapters.workflow.log import with_logging
from src.domain.models import DiffFile

@with_logging()
async def node_clone_task(state: AgentState) -> dict:
    """
    Nodo de clonación y análisis de diff (refactorizado con callback).
    
    Flujo:
    1. Verifica load_to == "clone"
    2. Inyecta CloneService (que usa RepositoryCloner)
    3. Inyecta FileExcluder y TreeBuilder
    4. Invoca CloneService.clone() que:
       a. Clona repositorio en /tmp/guardian/<uuid>/
       b. Checkout a commit_sha
       c. Si target, usa callback para procesar diff línea por línea
       d. Retorna clone_path, diff (dict), project_tree
    
    Inyecciones:
      clone_service = inject(InPortType.CloneService)
      file_excluder = inject(OutPortType.FileExcluder)
      tree_builder = inject(OutPortType.TreeBuilder)
    """
    
    # R17: Validar load_to
    if state.get("load_to") != "clone":
        raise ClonePathError("load_to must be 'clone'")
    
    # Inyectar dependencias
    clone_service = inject(InPortType.CloneService)
    
    repo_data = state.get("repository", {})
    repo_url = repo_data.get("url")
    commit_sha = repo_data.get("commit_sha")
    target = repo_data.get("target")
    installation_token = repo_data.get("installation")
    
    try:
        # Orquesta todo: clone, checkout, diff (callback), tree
        result = clone_service.clone(
            repo_url=repo_url,
            installation_token=installation_token,
            commit_sha=commit_sha,
            target=target
        )
        
        # Retorna: {clone_path, diff, project_tree}
        return result
        
    except ClonePathError as e:
        logger.error(f"Clone failed: {e}")
        raise ClonePathError(f"Failed to clone: {e}")
    except DiffGenerationError as e:
        logger.error(f"Diff generation failed: {e}")
        raise DiffGenerationError(f"Failed to generate diff: {e}")
```

**Justificación:**
- Simplificación: nodo inyecta solo `CloneService` en lugar de múltiples puertos (cloner, diff, tree).
- CloneService orquesta lógica completa: clone → checkout → diff (callback) → tree.
- Callback-based diff es eficiente (no acumula en memoria antes de retornar).
- Try/except específico para cada tipo de error (R12, R13, R14).
- Decorador `@with_logging()` asegura trazabilidad (R15).

---

### 8. Excepciones personalizadas

**Opción elegida:** Excepciones especializadas que heredan de `AgenticError`.

```python
# domain/models/errors/clone_errors.py

from src.domain.models import AgenticError

class ClonePathError(AgenticError):
    """Error general durante ejecución del nodo clone_path."""
    pass

class CheckoutError(ClonePathError):
    """Error durante checkout a commit específico."""
    pass

class DiffGenerationError(ClonePathError):
    """Error durante generación de diff."""
    pass

class GitOperationError(ClonePathError):
    """Error en operación git genérica."""
    pass
```

**Justificación:**
- Conform a `docs/conventions.md`: errores explícitos y nombrados.
- Jerarquía clara para manejo centralizado.
- Permite tests específicos por tipo de error.

---

### 9. Integración con el grafo (builder.py)

**Opción elegida:** Añadir nodo clone_path después de loader en el grafo.

```python
# infra/adapters/workflow/builder.py (modificado)

from src.infra.adapters.workflow.nodes.clone_path import node_clone_task

class WorkflowBuilder:
    def build(self) -> StateGraph:
        graph = StateGraph(AgentState)
        
        # Nodos existentes
        graph.add_node("loader", node_loader_task)
        graph.add_node("clone_path", node_clone_task)  # Nuevo
        graph.add_node("start", node_start)
        graph.add_node("process", node_process)
        graph.add_node("end", node_end)
        
        # Edges: entrada → loader → clone_path → start → ...
        graph.set_entry_point("loader")
        graph.add_edge("loader", "clone_path")
        graph.add_edge("clone_path", "start")
        graph.add_edge("start", "process")
        graph.add_edge("process", "end")
        
        graph.set_finish_point("end")
        
        return graph.compile()
```

**Justificación:**
- clone_path lógicamente depende de loader (usa outputs de loader).
- Todas las rutas posteriores pueden asumir que clone_path se ha ejecutado (o no, si load_to != "clone").
- Grafo es ahora: loader → clone_path → start → process → end.

---

### 10. Inyección de dependencias (R18) — Refactorizado

**Opción elegida:** Registrar puertos en `OutPortInjector` y `UseCaseInjector` con factories lazy.

```python
# infra/helper/adapter_injector.py (modificado)

class OutPortType(str, Enum):
  MetadataReader = "metadata_reader"
  RepositoryCloner = "repository_cloner"  # Implementa clone, checkout, get_diff
  FileExcluder = "file_excluder"
  TreeBuilder = "tree_builder"

def _create_repository_cloner() -> Any:
  from src.infra.adapters.git import GitRepositoryCloner
  return GitRepositoryCloner()

def _create_file_excluder() -> Any:
  from src.application.clone.file_excluder import FileExcluder
  return FileExcluder

def _create_tree_builder() -> Any:
  from src.application.clone.tree_builder import TreeBuilder
  return TreeBuilder

_out_port_factories: Dict[OutPortType, Callable[[], Any]] = {
  OutPortType.MetadataReader: _create_metadata_reader,
  OutPortType.RepositoryCloner: _create_repository_cloner,
  OutPortType.FileExcluder: _create_file_excluder,
  OutPortType.TreeBuilder: _create_tree_builder,
}

# infra/helper/usecase_injector.py (modificado)

class InPortType(str, Enum):
  WorkflowExecutor = "workflow_executor"
  CloneService = "clone_service"  # Nuevo

def _create_clone_service() -> Any:
  from src.application.clone import CloneService
  repository_cloner = inject(OutPortType.RepositoryCloner)
  return CloneService(repository_cloner)

_in_port_factories: Dict[InPortType, Callable[[], Any]] = {
  InPortType.WorkflowExecutor: _create_workflow_executor,
  InPortType.CloneService: _create_clone_service,
}
```

**Justificación:**
- `DiffGenerator` fue deprecado: su funcionalidad está en `RepositoryCloner.get_diff()`.
- `CloneService` ahora inyectado como `InPortType.CloneService` (caso de uso).
- Singleton por port type: instancia única por sesión.
- Lazy loading: factories se invocan solo si se usan.
- Permite cambiar implementación en un solo lugar.

---

## Firmas nuevas

### Puertos (nuevos/refactorizados)

```python
# domain/ports/output/repository_cloner.py
from abc import ABC, abstractmethod
from typing import Callable, Optional
from src.domain.models import DiffFile

class RepositoryCloner(ABC):
    @abstractmethod
    def clone(self, repo_url: str, installation_token: Optional[str] = None) -> str:
        """Clona repositorio en /tmp/guardian/<uuid>, retorna ruta absoluta."""
        ...
    
    @abstractmethod
    def checkout(self, repo_path: str, commit_sha: str) -> None:
        """Hace checkout a commit específico."""
        ...
    
    @abstractmethod
    def get_diff(
        self,
        repo_path: str,
        target_commit: str,
        callback: Callable[[str, DiffFile], None],
        base_commit: Optional[str] = None
    ) -> None:
        """
        Genera diff línea por línea entre dos commits.
        Invoca callback(file_path, DiffFile) para cada archivo modificado.
        """
        ...
```

**Nota:** El puerto `DiffGenerator` ha sido **deprecado** en esta refactorización. La funcionalidad de diff se integró en `RepositoryCloner.get_diff()` usando patrón callback.

### Servicios de aplicación (nuevos/refactorizados)

```python
# application/clone/clone_service.py (refactorizado)
class CloneService(CloneServicePort):
    def __init__(self, repository_cloner: RepositoryCloner):
        """Inyecta solo RepositoryCloner (que ahora incluye diff)."""
        self.repository_cloner = repository_cloner
    
    def clone(
        self,
        repo_url: str,
        installation_token: Optional[str] = None,
        commit_sha: Optional[str] = None,
        target: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orquesta clonación, checkout, diff (callback) y tree.
        
        Nueva lógica:
        1. Clone + checkout
        2. Callback-based diff processing: build dict in-place
        3. TreeBuilder.build_tree() marcando archivos nuevos
        
        Retorna: {"clone_path", "diff", "project_tree"}
        """
        ...

# application/clone/file_excluder.py
class FileExcluder:
    def __init__(self, repo_path: str):
        """Carga patrones .aiignore si existen."""
        ...
    
    def should_include(self, file_path: str) -> bool:
        """Determina si archivo debe incluirse."""
        ...

# application/clone/tree_builder.py
class TreeBuilder:
    @staticmethod
    def build_tree(
        repo_path: str,
        file_excluder: FileExcluder,
        added_files_set: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """Construye árbol jerárquico respetando exclusiones."""
        ...
```

**Nota:** Se removió `DiffBuilder` ya que la parsing de diff ahora ocurre en `GitRepositoryCloner.get_diff()`. `FileExcluder` y `TreeBuilder` se mantienen sin cambios.

### Adaptadores infra (nuevos/refactorizados)

```python
# infra/adapters/git/git_repository_cloner.py (refactorizado)
from src.domain.ports.output import RepositoryCloner
from src.domain.models import DiffFile, DiffContent, ChangeType

class GitRepositoryCloner(RepositoryCloner):
    def clone(self, repo_url: str, installation_token: Optional[str] = None) -> str:
        """Clona usando GitPython."""
        ...
    
    def checkout(self, repo_path: str, commit_sha: str) -> None:
        """Checkout usando GitPython."""
        ...
    
    def get_diff(
        self,
        repo_path: str,
        target_commit: str,
        callback: Callable[[str, DiffFile], None],
        base_commit: Optional[str] = None
    ) -> None:
        """
        Genera diff usando GitPython diff API.
        
        Procesa cambios en tres iteraciones:
        1. iter_change_type('M'): modificados
        2. iter_change_type('D'): deletados
        3. iter_change_type('A'): añadidos
        
        Para cada archivo, acumula DiffContent (línea por línea) y
        invoca callback con DiffFile estructurado.
        """
        ...

    @staticmethod
    def _build_clone_url(url: str, installation_token: Optional[str]) -> str:
        """Inyecta token GitHub como HTTP basic auth en URL."""
        ...

    @staticmethod
    def _cleanup_dir(path: str) -> None:
        """Limpia directorio en caso de error."""
        ...
```

**Nota:** `GitDiffGenerator` ha sido **deprecado**. Su funcionalidad está ahora integrada en `GitRepositoryCloner.get_diff()`.

### Nodo (nueva función)

```python
# infra/adapters/workflow/nodes/clone_path.py
from src.domain.models.state.state import AgentState
from src.infra.adapters.workflow.log import with_logging

@with_logging()
async def node_clone_task(state: AgentState) -> dict:
    """Nodo de clonación y análisis de diferencias."""
    ...
```

---

## Refactorización: Integración de diff en RepositoryCloner

**Fecha:** Implementación completada, refactorización aplicada post-implementación.

### Cambios principales

**Antes (spec original):**
- `GitDiffGenerator` como adapter separado
- `DiffBuilder` para parsear output de `git diff` string
- Nodo inyectaba: `RepositoryCloner`, `DiffGenerator`, `FileExcluder`, `TreeBuilder` (4 dependencias)
- Diff retornado como `List[Dict]` con estructura plana

**Después (refactorización):**
- `get_diff()` integrado en `GitRepositoryCloner` con patrón callback
- Usa GitPython diff API directamente (no string parsing)
- Nodo inyecta solo `CloneService` (1 dependencia en el nodo)
- CloneService orquesta: clone → checkout → diff (callback) → tree
- Diff estructura como `Dict[str, DiffFile]` con campos `is_new`, `is_deleted` para semántica clara
- `DiffFile` y `DiffContent` como TypedDict/NamedTuple para type safety

### Razones de la refactorización

1. **Simplificación de inyección:** El nodo ahora inyecta una sola dependencia (`CloneService`) que orquesta el flujo completo.
2. **Type safety:** TypedDict en `DiffFile` / `DiffContent` en lugar de `Dict[str, Any]`.
3. **Eficiencia:** Callback-based diff evita acumular todo en memoria antes de retornar.
4. **Semántica clara:** Campos `is_new` / `is_deleted` en nivel de archivo vs. solo status de línea.
5. **GitPython API:** Uso directo de `repo.diff()` es más robusto que parsing strings; reduce surface de bugs.

### Impacto en tests

- Tests de `DiffBuilder` y `GitDiffGenerator` fueron removidos.
- Tests de `GitRepositoryCloner` se extendieron para cubrir `get_diff()`.
- Tests de `CloneService` cubren orquestación completa (clone + checkout + diff + tree).
- Total: 57 tests pasados (vs. los originales, algunos fueron consolidados).

---

## Alternativa descartada (pre-refactorización): DiffGenerator separado con string parsing

**Spec original proponía:**
- Adapter `GitDiffGenerator` como puerto de salida independiente
- `DiffBuilder` que parseaba `git diff` output como strings
- Nodo inyectaba 4 puertos separados: RepositoryCloner, DiffGenerator, FileExcluder, TreeBuilder

**Motivo del descarte:**
- Inyección de demasiadas dependencias en el nodo (cuatro puertos).
- `DiffBuilder` duplicaba responsabilidad de parsing que GitPython diff API ya maneja.
- String parsing de `git diff` output es más frágil ante encoding/edge cases.
- Mayor surface de bugs: parsing manual vs. API nativa.

**Por qué la refactorización es mejor:**
- Simplificación: nodo inyecta una sola dependencia (`CloneService`).
- GitPython diff API es nativo y robusto.
- Callback pattern permite procesamiento lazy sin acumular en memoria.
- Tipo safety con TypedDict/NamedTuple en `DiffFile` / `DiffContent`.
- Separación clara de responsabilidades: RepositoryCloner (git ops) + CloneService (orquestación).

---

## Diseño final post-refactorización

**Capas finales:**
```
┌─────────────────────────────────────┐
│    Workflow (node_clone_task)       │  Inyecta: CloneService
├─────────────────────────────────────┤
│   Application (CloneService)        │  Orquesta: clone → checkout → diff → tree
├─────────────────────────────────────┤
│ Infrastructure (GitRepositoryCloner)│  Implementa: clone, checkout, get_diff (callback)
│        FileExcluder, TreeBuilder    │  Utilidades: exclusiones, árbol
└─────────────────────────────────────┘
```

**Ventajas:**
- Separación clara de capas: workflow (orquestación) → application (lógica) → infra (primitivos).
- Inyección granular: CloneService combina RepositoryCloner, FileExcluder, TreeBuilder.
- Testabilidad: cada clase testeable en aislamiento.
- Extensibilidad: fácil reemplazar `GitRepositoryCloner` con otra implementación (e.g., GitLab API).

---

## Alternativa descartada: Un único servicio monolítico de clonación + diff

Se consideró combinar todas las operaciones en una sola clase `RepositoryProcessor` sin OrchestrationService.

**Motivo del descarte:**
- Violaría SRP: responsabilidades disjuntas (git ops, lógica de negocio, orquestación).
- Más difícil de testear; inyección complicada.
- Nodo tendría que instanciar directamente (violando inyección de dependencias).

**Por qué la estrategia actual es mejor:**
- Capas claras: RepositoryCloner (primitivos git) vs. CloneService (orquestación).
- Inyección de dependencias en todas las capas.
- Fácil testear cada nivel independientemente.
