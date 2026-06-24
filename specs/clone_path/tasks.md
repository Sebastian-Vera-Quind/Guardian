# Tasks: clone_path

## Overview

Implementación del nodo `clone_path` en el workflow LangGraph. Los tasks se ejecutan en orden de dependencias de arquitectura (domain → application → infra → integration).

## Task List

### Domain Layer

- [ ] **T1** — Crear `domain/models/errors/clone_errors.py` con excepciones `ClonePathError`, `CheckoutError`, `DiffGenerationError`, `GitOperationError` (heredando de `AgenticError`). Cubre: R12, R13, R14.

- [ ] **T2** — Crear interfaz `domain/ports/output/clone/repository_cloner.py` con métodos `clone(repo_url, installation_token=None) -> str` y `checkout(repo_path, commit_sha) -> None`. Cubre: R1, R2, R3, R4.

- [ ] **T3** — Crear interfaz `domain/ports/output/diff/diff_generator.py` con método `generate_diff(repo_path, base_commit, target_commit) -> Dict[str, Any]`. Cubre: R5, R6, R7.

- [ ] **T4** — Crear interfaz `domain/ports/input/clone/clone_service.py` con método `clone(repo_url, installation_token=None, commit_sha, target=None) -> Dict[str, Any]`. Cubre: R1–R11, R18.

- [ ] **T5** — Exportar nuevas excepciones y puertos en `domain/models/__init__.py`, `domain/ports/input/__init__.py`, `domain/ports/output/__init__.py`. Cubre: R18.

### Application Layer

- [ ] **T6** — Crear `application/clone/__init__.py` que exporte `CloneService`. Cubre: R18.

- [ ] **T7** — Crear `application/clone/file_excluder.py` con clase `FileExcluder` (métodos `__init__(repo_path)`, `_load_aiignore(repo_path)`, `should_include(file_path)`, `_matches_gitignore_pattern(file_path, pattern)`). Cubre: R7, R10.

- [ ] **T8** — Crear `application/clone/diff_builder.py` con clase `DiffBuilder` (método `parse_git_diff(git_output, file_excluder) -> Tuple[List[Dict], Set[str], int]`). Cubre: R5, R6, R7, R10.

- [ ] **T9** — Crear `application/clone/tree_builder.py` con clase `TreeBuilder` (método `build_tree(repo_path, file_excluder, added_files_set=None) -> Dict[str, Any]`). Cubre: R9, R10, R11.

- [ ] **T10** — Implementar `application/clone/clone_service.py` con clase `CloneService` (método `clone(repo_url, installation_token=None, commit_sha, target=None) -> Dict[str, Any]` que orquesta clonación, checkout, diff y tree). Usa inyección de `GitOperations`. Cubre: R1–R11, R16, R18.

### Infrastructure Layer

- [ ] **T11** — Crear `infra/adapters/git/__init__.py` (si no existe) que exporte `GitRepositoryCloner`. Cubre: R18.

- [ ] **T12** — Crear `infra/adapters/git/git_repository_cloner.py` implementando `RepositoryCloner` (método `clone()` con URL autenticada opcional, `checkout()` usando GitPython). Cubre: R1, R2, R3, R4, R12, R13.

- [ ] **T13** — Crear `infra/adapters/diff/__init__.py` (si no existe) que exporte `GitDiffGenerator`. Cubre: R18.

- [ ] **T14** — Crear `infra/adapters/diff/git_diff_generator.py` implementando `DiffGenerator` (método `generate_diff()` usando `git diff`, inyectando `FileExcluder` y `DiffBuilder`). Cubre: R5, R6, R7, R10, R14.

- [ ] **T15** — Crear `infra/adapters/workflow/nodes/__init__.py` (si no existe) que exporte `node_clone_task`. Cubre: R18.

- [ ] **T16** — Crear `infra/adapters/workflow/nodes/clone_path.py` con función async `node_clone_task(state: AgentState) -> dict` decorada con `@with_logging()`. Valida `load_to == "clone"`, inyecta `CloneService`, orquesta clonación/checkout/diff/tree, captura excepciones, escribe `clone_path`, `diff`, `modified_lines`, `project_tree` en estado. Cubre: R1–R17.

### Dependency Injection

- [ ] **T17** — Crear/actualizar `infra/helper/adapter_injector.py`: añadir valores a enum `OutPortType` (`RepositoryCloner`, `DiffGenerator`, `FileExcluder`, `TreeBuilder`), implementar factories `_create_repository_cloner()`, `_create_diff_generator()`, `_create_file_excluder()`, `_create_tree_builder()`, registrar en `_out_port_factories`. Cubre: R18.

- [ ] **T18** — Actualizar `infra/helper/inject.py`: añadir overloads para nuevos tipos de puertos. Cubre: R18.

### Integration & Workflow

- [ ] **T19** — Actualizar `infra/adapters/workflow/builder.py`: importar `node_clone_task`, registrar nodo `"clone_path"` en grafo después de `"loader"` (añadir edge `loader → clone_path`), conectar `clone_path → start`. Cubre: R1.

- [ ] **T20** — Actualizar `domain/models/state/state.py` (o crear si no existe): extender `AgentState` para incluir outputs opcionales (`clone_path`, `diff`, `modified_lines`, `project_tree`). Cubre: R1–R11.

- [ ] **T21** — Actualizar `infra/adapters/workflow/__init__.py`: exportar `node_clone_task`. Cubre: R18.

### Testing

- [ ] **T22** — Crear `tests/infra/adapters/test_git_repository_cloner.py` con tests: `test_clone_public_repo_creates_directory`, `test_clone_private_repo_with_token`, `test_clone_invalid_url_raises_error`, `test_checkout_valid_commit`, `test_checkout_invalid_commit_raises_error`. Cubre: R1, R2, R3, R4, R12, R13.

- [ ] **T23** — Crear `tests/application/test_file_excluder.py` con tests: `test_should_include_returns_true_for_code_files`, `test_should_include_returns_false_for_excluded_extensions`, `test_should_include_respects_aiignore_patterns`, `test_load_aiignore_parses_valid_file`, `test_load_aiignore_returns_empty_if_missing`. Cubre: R7, R10.

- [ ] **T24** — Crear `tests/application/test_diff_builder.py` con tests: `test_parse_git_diff_returns_correct_structure`, `test_parse_git_diff_respects_file_excluder`, `test_parse_git_diff_counts_additions_deletions`, `test_parse_git_diff_identifies_added_files`. Cubre: R5, R6, R7, R10.

- [ ] **T25** — Crear `tests/application/test_tree_builder.py` con tests: `test_build_tree_creates_valid_structure`, `test_build_tree_excludes_filtered_files`, `test_build_tree_marks_new_files_correctly`. Cubre: R9, R10, R11.

- [ ] **T26** — Crear `tests/application/test_clone_service.py` con tests: `test_clone_orchestrates_all_steps`, `test_clone_without_target_omits_diff`, `test_clone_cleans_up_on_error`, `test_clone_respects_installation_token`. Cubre: R1–R11, R16.

- [ ] **T27** — Crear `tests/infra/adapters/test_git_diff_generator.py` con tests: `test_generate_diff_returns_correct_format`, `test_generate_diff_respects_aiignore`, `test_generate_diff_handles_missing_target_raises_error`. Cubre: R5, R6, R7, R14.

- [ ] **T28** — Crear `tests/infra/workflow/nodes/test_clone_path_node.py` con tests: `test_node_clone_task_requires_load_to_clone`, `test_node_clone_task_calls_clone_service`, `test_node_clone_task_returns_expected_state`, `test_node_clone_task_logs_operations`, `test_node_clone_task_raises_clone_path_error_on_failure`, `test_node_clone_task_raises_diff_error_on_diff_failure`. Cubre: R1–R18.

### Documentation

- [ ] **T29** — Documentar trazabilidad en `progress/impl_clone_path.md`:
  - R1 → T1, T12, T16, T19, T22, T28
  - R2 → T2, T12, T22, T28
  - R3 → T2, T12, T22, T28
  - R4 → T2, T12, T22, T28
  - R5 → T3, T8, T14, T24, T27, T28
  - R6 → T3, T8, T14, T24, T27, T28
  - R7 → T7, T8, T14, T23, T24, T27, T28
  - R8 → T8, T14, T24, T27, T28
  - R9 → T9, T25, T28
  - R10 → T7, T8, T9, T14, T23, T24, T25, T27, T28
  - R11 → T9, T25, T28
  - R12 → T1, T12, T22, T28
  - R13 → T1, T12, T22, T28
  - R14 → T1, T14, T27, T28
  - R15 → T16, T28
  - R16 → T10, T26, T28
  - R17 → T16, T28
  - R18 → T2, T3, T4, T5, T11, T13, T15, T17, T18, T21, T26
