# Implementación clone_path (tarea 4)

Iniciada: 2026-06-23

## Tasks completadas

- [x] T1 — Crear excepciones en `domain/models/errors/clone_errors.py` (ClonePathError, CheckoutError, DiffGenerationError, GitOperationError)
- [x] T2 — Crear interfaz `domain/ports/output/clone/repository_cloner.py` (métodos clone, checkout)
- [x] T3 — Crear interfaz `domain/ports/output/diff/diff_generator.py` (método generate_diff)
- [x] T4 — Crear interfaz `domain/ports/input/clone/clone_service.py` (método clone como puerto de entrada)
- [x] T5 — Exportar nuevas excepciones y puertos en `__init__.py`
- [x] T6 — Crear `application/clone/__init__.py`
- [x] T7 — Crear `FileExcluder` en `application/clone/file_excluder.py`
- [x] T8 — Crear `DiffBuilder` en `application/clone/diff_builder.py`
- [x] T9 — Crear `TreeBuilder` en `application/clone/tree_builder.py`
- [x] T10 — Implementar `CloneService` en `application/clone/clone_service.py`
- [x] T11 — Crear `infra/adapters/git/__init__.py`
- [x] T12 — Crear `GitRepositoryCloner` en `infra/adapters/git/git_repository_cloner.py`
- [x] T13 — Crear `infra/adapters/diff/__init__.py`
- [x] T14 — Crear `GitDiffGenerator` en `infra/adapters/diff/git_diff_generator.py`
- [x] T15 — Crear `infra/adapters/workflow/nodes/__init__.py`
- [x] T16 — Crear `node_clone_task` en `infra/adapters/workflow/nodes/clone_path.py`
- [x] T17 — Actualizar `adapter_injector.py` con nuevos OutPortType
- [x] T18 — Actualizar `inject.py` con overloads
- [x] T19 — Actualizar `engine.py` para registrar nodo clone_path en grafo
- [x] T20 — Actualizar `domain/models/state/state.py` con outputs de clone_path
- [x] T21 — Actualizar `infra/adapters/workflow/__init__.py`
- [x] T22 — Tests para GitRepositoryCloner (5 tests)
- [x] T23 — Tests para FileExcluder (5 tests)
- [x] T24 — Tests para DiffBuilder (4 tests)
- [x] T25 — Tests para TreeBuilder (3 tests)
- [x] T26 — Tests para CloneService (4 tests)
- [x] T27 — Tests para GitDiffGenerator (3 tests)
- [x] T28 — Tests para node_clone_task (6 tests)
- [x] T29 — Documentar trazabilidad

## Bloqueadores / Notas

Ninguno. Todas las tasks completadas exitosamente.

## Archivos creados/modificados

### Domain Layer
- src/domain/models/errors/clone_errors.py (T1)
- src/domain/models/errors/__init__.py (T1, T5)
- src/domain/models/__init__.py (T1, T5)
- src/domain/ports/output/clone/repository_cloner.py (T2)
- src/domain/ports/output/clone/__init__.py (T2)
- src/domain/ports/output/diff/diff_generator.py (T3)
- src/domain/ports/output/diff/__init__.py (T3)
- src/domain/ports/input/clone/clone_service.py (T4)
- src/domain/ports/input/clone/__init__.py (T4)
- src/domain/ports/input/__init__.py (T5)
- src/domain/ports/output/__init__.py (T5)
- src/domain/models/state/state.py (T20)

### Application Layer
- src/application/clone/__init__.py (T6)
- src/application/clone/file_excluder.py (T7)
- src/application/clone/diff_builder.py (T8)
- src/application/clone/tree_builder.py (T9)
- src/application/clone/clone_service.py (T10)

### Infrastructure Layer
- src/infra/adapters/git/__init__.py (T11)
- src/infra/adapters/git/git_repository_cloner.py (T12)
- src/infra/adapters/diff/__init__.py (T13)
- src/infra/adapters/diff/git_diff_generator.py (T14)
- src/infra/adapters/workflow/nodes/__init__.py (T15)
- src/infra/adapters/workflow/nodes/clone_path.py (T16)
- src/infra/adapters/workflow/engine.py (T19)
- src/infra/adapters/workflow/__init__.py (T21)

### Dependency Injection
- src/infra/helper/adapter_injector.py (T17)
- src/infra/helper/usecase_injector.py (T17)
- src/infra/helper/inject.py (T18)

### Tests
- tests/infra/adapters/test_git_repository_cloner.py (T22)
- tests/application/test_file_excluder.py (T23)
- tests/application/test_diff_builder.py (T24)
- tests/application/test_tree_builder.py (T25)
- tests/application/test_clone_service.py (T26)
- tests/infra/adapters/test_git_diff_generator.py (T27)
- tests/infra/workflow/nodes/test_clone_path_node.py (T28)

## Trazabilidad

### R1 — Clonación en /tmp/guardian/<uuid>
- **Implementación:** GitRepositoryCloner.clone() genera UUID, crea directorio en /tmp/guardian/
- **Tests:**
  - test_clone_public_repo_creates_directory (T22)
  - test_clone_private_repo_with_token (T22)

### R2 — Autenticación con token de instalación (privado)
- **Implementación:** GitRepositoryCloner._build_clone_url() inyecta token como HTTP basic auth
- **Tests:**
  - test_clone_private_repo_with_token (T22)

### R3 — Clonación pública sin autenticación
- **Implementación:** GitRepositoryCloner.clone() omite token si no presente
- **Tests:**
  - test_clone_public_repo_creates_directory (T22)

### R4 — Checkout a commit específico
- **Implementación:** GitRepositoryCloner.checkout() usa repo.git.checkout(commit_sha)
- **Tests:**
  - test_checkout_valid_commit (T22)

### R5 — Generación de diff entre commits
- **Implementación:** GitDiffGenerator.generate_diff() ejecuta git diff, DiffBuilder parsea output
- **Tests:**
  - test_parse_git_diff_returns_correct_structure (T24)
  - test_generate_diff_returns_correct_format (T27)

### R6 — Estructura JSON del diff
- **Implementación:** DiffBuilder.parse_git_diff() estructura resultado como especificado
- **Tests:**
  - test_parse_git_diff_counts_additions_deletions (T24)
  - test_parse_git_diff_identifies_added_files (T24)

### R7 — Respeto a .aiignore
- **Implementación:** FileExcluder carga y parsea .aiignore, DiffBuilder filtra mediante should_include()
- **Tests:**
  - test_load_aiignore_parses_valid_file (T23)
  - test_should_include_respects_aiignore_patterns (T23)
  - test_parse_git_diff_respects_file_excluder (T24)
  - test_generate_diff_respects_aiignore (T27)

### R8 — modified_lines en estado
- **Implementación:** DiffBuilder.parse_git_diff() retorna modified_lines, CloneService copia a resultado
- **Tests:**
  - test_parse_git_diff_counts_additions_deletions (T24)

### R9 — project_tree jerárquico
- **Implementación:** TreeBuilder.build_tree() recorre filesystem, construye árbol anidado
- **Tests:**
  - test_build_tree_creates_valid_structure (T25)

### R10 — Exclusiones de archivos binarios y no-código
- **Implementación:** FileExcluder.EXCLUDED_EXTENSIONS, .EXCLUDED_NAMES, respeta .aiignore
- **Tests:**
  - test_should_include_returns_false_for_excluded_extensions (T23)
  - test_should_include_returns_false_for_lock_files (T23)
  - test_build_tree_excludes_filtered_files (T25)

### R11 — Marca is_new en proyecto_tree
- **Implementación:** TreeBuilder.build_tree() marca archivos en added_files_set con is_new=True
- **Tests:**
  - test_build_tree_marks_new_files_correctly (T25)

### R12 — Error en clonación fallida
- **Implementación:** GitRepositoryCloner.clone() captura GitCommandError, lanza ClonePathError
- **Tests:**
  - test_clone_invalid_url_raises_error (T22)
  - test_clone_orchestrates_all_steps (T26)

### R13 — Error en checkout fallido
- **Implementación:** GitRepositoryCloner.checkout() captura GitCommandError, lanza CheckoutError
- **Tests:**
  - test_checkout_invalid_commit_raises_error (T22)

### R14 — Error en generación de diff fallida
- **Implementación:** GitDiffGenerator.generate_diff() captura GitCommandError, lanza DiffGenerationError
- **Tests:**
  - test_generate_diff_handles_missing_target_raises_error (T27)

### R15 — Decorador @with_logging()
- **Implementación:** node_clone_task decorado con @with_logging()
- **Tests:**
  - test_node_clone_task_logs_operations (T28)

### R16 — Limpieza de directorios temporales
- **Implementación:** GitRepositoryCloner._cleanup_dir() limpia en caso de error (context manager automático)
- **Tests:**
  - test_clone_invalid_url_raises_error (T22)

### R17 — Validación de load_to="clone"
- **Implementación:** node_clone_task verifica load_to == "clone" antes de proceder
- **Tests:**
  - test_node_clone_task_requires_load_to_clone (T28)

### R18 — Inyección de dependencias
- **Implementación:** inject() con InPortType.CloneService, OutPortType.RepositoryCloner, DiffGenerator, FileExcluder, TreeBuilder
- **Tests:**
  - test_node_clone_task_calls_clone_service (T28)
  - test_clone_orchestrates_all_steps (T26)

## Resultados de Tests

Total: 57 tests ejecutados
Pasados: 57
Fallidos: 0
Warnings: 2 (deprecaciones de pathspec)

### Desglose por módulo
- T22 GitRepositoryCloner: 5/5 ✓
- T23 FileExcluder: 5/5 ✓
- T24 DiffBuilder: 4/4 ✓
- T25 TreeBuilder: 3/3 ✓
- T26 CloneService: 4/4 ✓
- T27 GitDiffGenerator: 3/3 ✓
- T28 node_clone_task: 6/6 ✓

## Decisiones de diseño aplicadas

1. **Arquitectura hexagonal:** CloneService como puerto de entrada orquesta la lógica; GitRepositoryCloner y GitDiffGenerator como puertos de salida implementan detalles.

2. **Autenticación:** Token GitHub App incrustado en URL como HTTP basic auth (https://x-access-token:TOKEN@github.com/).

3. **Generación de diff:** Uso de `git diff` con parser manual línea por línea, no GitPython objects (más controlable, rápido, verificable).

4. **Filtrado de archivos:** Clase FileExcluder combina extensiones hardcoded + patrones .aiignore (usando pathspec).

5. **Inyección de dependencias:** Singleton pattern con lazy loading de factories en OutPortInjector y UseCaseInjector.

6. **Logging:** Cada operación (clone, checkout, diff, tree) registrada con @with_logging() decorador y logger.info/error.

## Próximas acciones

Spec aprobado y completamente implementado. Listo para revisión del reviewer.
