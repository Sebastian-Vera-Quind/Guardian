# Design: refactor_clonepath

Desacoplamiento del nodo monolítico `clone_path` en cuatro nodos
independientes, refactorización de puertos y servicios, e introducción
de conditional edges en el workflow.

## Archivos a crear

1. `src/infra/adapters/workflow/nodes/clone_repository.py`
   - Nodo independiente para clonación del repositorio.
   - Firma: `async def node_clone_repository(state: AgentState) -> AgentState`
   - Responsabilidad única: clonar en `/tmp/guardian/<uuid>/` respetando
     tokens de autenticación.

2. `src/infra/adapters/workflow/nodes/checkout_commit.py`
   - Nodo independiente para checkout a commit específico.
   - Firma: `async def node_checkout_commit(state: AgentState) -> AgentState`
   - Responsabilidad única: hacer checkout a `repository.commit_sha`.

3. `src/infra/adapters/workflow/nodes/replace_files_content.py`
   - Nodo independiente para reemplazo de contenido de archivos.
   - Firma: `async def node_replace_files_content(state: AgentState) -> AgentState`
   - Responsabilidad única: reemplazar archivos en el repo clonado según
     `files_content`.

4. `src/infra/adapters/workflow/nodes/generate_diff.py`
   - Nodo independiente para generación de diff y project_tree.
   - Firma: `async def node_generate_diff(state: AgentState) -> AgentState`
   - Responsabilidad única: generar diff, project_tree y calcular métricas.

## Archivos a modificar

1. `src/infra/adapters/workflow/nodes/__init__.py`
   - Importar y exportar los cuatro nodos nuevos.
   - Mantener la exportación de `node_loader_task` (que se refactorizará).

2. `src/infra/adapters/workflow/engine.py`
   - Reemplazar el flujo lineal `loader → clone_path → END`
   - Nuevo flujo:
     ```
     loader →[conditional]→ clone_repository → [conditional]→ 
     checkout_commit / replace_files_content / both →
     [conditional]→ generate_diff → END
     ```
   - Condicionales basadas en presencia de `files_content`, `commit_sha`, `target`.

3. `src/infra/adapters/workflow/nodes/loader.py`
   - Refactorizar para que establezca flags en el estado:
     * `has_files_content: bool`
     * `has_commit_sha: bool`
     * `has_target: bool`
   - Estos flags permiten al engine decidir el enrutamiento.

4. `src/domain/ports/input/clone/clone_service.py`
   - Refactorizar el contrato monolítico `CloneService` en métodos
     especializados (sin eliminar `clone()` si se mantiene para compatibilidad):
     * `clone_repository(repo_url, installation_token) -> str`
     * `checkout_commit(repo_path, commit_sha) -> None`
     * `replace_files_content(repo_path, files_content) -> None`
     * `generate_diff_and_tree(repo_path, base_commit, target_commit, files_modified) -> Dict`

5. `src/application/clone/clone_service.py`
   - Implementar los métodos especializados en `CloneService`.
   - Eliminar el método `clone()` delegando a los métodos especializados.

6. `src/infra/adapters/workflow/nodes/clone_path.py`
   - Marcar como deprecated (si se mantiene) o eliminar si se está seguro
     de que el nuevo flujo cubre todos los casos de uso.

## Nuevas firmas en puertos y servicios

### `CloneService` (input port)

```python
@abstractmethod
def clone_repository(
  self,
  repo_url: str,
  installation_token: Optional[str] = None
) -> str:
  """
  Clona repositorio en /tmp/guardian/<uuid>, retorna ruta absoluta.
  """
  ...

@abstractmethod
def checkout_commit(
  self,
  repo_path: str,
  commit_sha: str
) -> None:
  """
  Hace checkout a commit específico.
  """
  ...

@abstractmethod
def replace_files_content(
  self,
  repo_path: str,
  files_content: List[Dict[str, str]]
) -> None:
  """
  Reemplaza contenido de archivos, creando si no existen.
  """
  ...

@abstractmethod
def generate_diff_and_tree(
  self,
  repo_path: str,
  base_commit: Optional[str],
  target_commit: Optional[str],
  files_modified_by_replacement: Optional[Set[str]] = None
) -> Dict[str, Any]:
  """
  Genera diff, project_tree, y métricas de cambios.
  """
  ...
```

## Excepciones existentes reutilizadas

- `ClonePathError` (base para errores de clonación)
- `CheckoutError` (erro durante checkout)
- `DiffGenerationError` (error durante diff)
- `GitOperationError` (error en git)

No se añaden nuevas excepciones; se reutilizan las existentes.

## Alternativas descartadas

### Alternativa 1: Mantener un único nodo con parámetros configurables
**Descartada** porque:
- Violaría el Single Responsibility Principle (SRP).
- Dificultaría testing y debugging de responsabilidades individuales.
- No permitiría reutilizar operaciones (ej. clonar sin generar diff).

### Alternativa 2: Crear un servicio `DiffGenerator` separado en puertos
**Descartada** porque:
- La generación de diff ya está parcialmente en `RepositoryCloner.get_diff()`.
- Crear un nuevo puerto incrementaría la complejidad de inyección.
- Es mejor refactorizar el contrato existente `CloneService` para ser
  más granular, manteniendo un puerto principal.

### Alternativa 3: Manejar condicionales en el loader con estados secundarios
**Descartada** porque:
- Complicaría la lógica del loader.
- Es más claro que el engine (WorkflowEngine) maneje las condicionales
  usando `conditional_edges` de LangGraph.

## Invariantes a mantener

1. Hexagonal architecture: Los nodos orquestan, no implementan lógica de
   negocio. Ésta sigue en `CloneService` y `RepositoryCloner`.

2. Inyección de dependencias: Todos los nodos obtienen servicios via
   `inject()` desde el contenedor, no instancian directamente.

3. Trazabilidad: Cada nodo mantiene la decoración `@with_logging()`.

4. Estructura de `AgentState`: Se preserva la interfaz de entrada/salida.
   Nuevos campos (flags condicionales) se agregan pero son internos del
   workflow.

5. /tmp/guardian base path: Se mantiene la convención de clonar en
   `/tmp/guardian/<uuid>/`.
