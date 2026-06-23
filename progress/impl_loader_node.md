# Impl: loader_node

## Archivos creados en esta sesión

- `src/infra/adapters/workflow/nodes/base.py` — migración de node_start, node_process, node_end desde nodes.py (resuelve conflicto estructural)
- `src/infra/adapters/workflow/nodes/loader.py` — node_loader_task y determine_load_route
- `src/infra/adapters/workflow/nodes/__init__.py` — exporta base + loader, mantiene compatibilidad con engine.py
- `src/infra/adapters/workflow/builder.py` — WorkflowBuilder con loader como entry point
- `tests/infra/__init__.py`
- `tests/infra/adapters/__init__.py`
- `tests/infra/adapters/github/__init__.py`
- `tests/infra/adapters/workflow/__init__.py`
- `tests/infra/adapters/github/test_metadata_reader.py` — T10
- `tests/infra/adapters/workflow/test_loader_node.py` — T11
- `tests/infra/adapters/workflow/test_builder_with_loader.py` — T12

## Archivos modificados

- `src/infra/adapters/workflow/__init__.py` — uncomment WorkflowBuilder, export node_loader_task
- `specs/loader_node/tasks.md` — marcados T5, T6, T7, T10, T11, T12 como completos
- `progress/current.md` — actualizado estado

## Conflicto estructural resuelto

`nodes.py` (módulo plano) coexistía con `nodes/` (directorio sin `__init__.py`).
Solución: las funciones de `nodes.py` se copiaron a `nodes/base.py`. Se creó
`nodes/__init__.py` que re-exporta todo, de modo que `engine.py` sigue importando
`from src.infra.adapters.workflow.nodes import node_end, node_process, node_start`
sin ningún cambio. El archivo `nodes.py` queda en su lugar (shadowed por el paquete,
sin causar error).

## Trazabilidad R -> Test

| Requirement | Test |
|---|---|
| R1 (simple route when files_content) | `test_loader_node.py::TestDetermineLoadRoute::test_simple_route_when_only_files_content` |
| R2 (clone route when repository) | `test_loader_node.py::TestDetermineLoadRoute::test_clone_route_when_only_repository` |
| R3 (clone takes priority) | `test_loader_node.py::TestDetermineLoadRoute::test_clone_route_takes_priority_when_both_present` |
| R4 (blank line removal) | `test_sanitizer.py::TestCodeSanitizerRemoveBlankLines::test_remove_blank_lines_eliminates_whitespace_only_lines` + `test_loader_node.py::TestNodeLoaderTaskSimpleRoute::test_simple_route_sanitizes_files_content` |
| R5 (remove empty files) | `test_sanitizer.py::TestCodeSanitizerSanitizeFiles::test_sanitize_files_removes_empty_files` |
| R6 (count lines) | `test_sanitizer.py::TestCodeSanitizerCountLines` + `test_loader_node.py::test_simple_route_writes_total_lines` |
| R7 (metadata extraction) | `test_metadata_reader.py` (all tests) + `test_loader_node.py::TestNodeLoaderTaskCloneRoute::test_clone_route_writes_metadata` |
| R8 (attribution JSONL valid) | `test_jsonl_validator.py::test_extract_attribution_found_and_valid_extracts_content` + `test_loader_node.py::test_simple_route_extracts_valid_attribution` |
| R9 (attribution JSONL invalid warning) | `test_jsonl_validator.py::test_extract_attribution_found_invalid_logs_warning_returns_none` |
| R10 (files_content not modified on clone) | `test_loader_node.py::TestNodeLoaderTaskCloneRoute::test_clone_route_passes_files_content_unchanged` |
| R11 (repository not modified on simple) | `test_loader_node.py::TestNodeLoaderTaskSimpleRoute::test_simple_route_passes_repository_unchanged` |
| R12 (LoaderNodeError when no inputs) | `test_loader_node.py::TestDetermineLoadRoute::test_raises_loader_node_error_when_no_inputs` |
| R13 (@with_logging decorator) | `test_loader_node.py::TestNodeLoaderTaskDecorator::test_node_is_decorated_with_logging` |
