# Tasks: loader_node

Pasos discretos para implementación. Cada task cubre al menos un requirement (R<n>).

---

## Task 1: Crear clase `CodeSanitizer` en `infra/helpers/sanitizer.py`

- [ ] Crear archivo `src/infra/helpers/sanitizer.py`.
- [ ] Implementar método `remove_blank_lines(content: str) -> str` que elimina líneas que contengan solo espacios/tabulaciones.
- [ ] Implementar método `sanitize_files(files: List[FileContent]) -> List[FileContent]` que retorna solo archivos con contenido no vacío.
- [ ] Implementar método `count_lines(files: List[FileContent]) -> int` que suma líneas de todos los archivos.
- [ ] Verificar que `CodeSanitizer` es importable desde `src/infra/helpers/__init__.py`.

**Cubre:** R4, R5, R6

---

## Task 2: Crear clase `MetadataExtractor` en `infra/helpers/metadata_extractor.py`

- [ ] Crear archivo `src/infra/helpers/metadata_extractor.py`.
- [ ] Implementar método `extract_from_repository(repo_data: dict) -> RepositoryMetadata` que:
  - Extrae `owner` desde la URL del repositorio (segundo-a-último segmento de la ruta).
  - Extrae `repo_name` desde la URL (último segmento sin `.git`).
  - Mapea `target` a `branch` en el modelo.
  - Mapea `commit_sha` del diccionario al modelo.
  - Usa `author_name` y `author_email` del diccionario o valores por defecto.
  - Retorna instancia de `RepositoryMetadata`.
- [ ] Verificar que `MetadataExtractor` es importable desde `src/infra/helpers/__init__.py`.

**Cubre:** R7

---

## Task 3: Crear clase `JSONLValidator` en `infra/helpers/jsonl_validator.py`

- [ ] Crear archivo `src/infra/helpers/jsonl_validator.py`.
- [ ] Implementar método `is_valid_jsonl(content: str) -> bool` que:
  - Retorna `False` si el contenido está vacío.
  - Itera líneas, saltando líneas vacías.
  - Intenta parsear cada línea como JSON.
  - Retorna `True` solo si todas las líneas válidas son JSON válido.
- [ ] Implementar método `extract_attribution_file(files: List[FileContent]) -> tuple[List[FileContent], Optional[str]]` que:
  - Itera la lista de archivos.
  - Detecta archivo con nombre `.devcore-attribution.jsonl`.
  - Si lo encuentra, valida con `is_valid_jsonl()`.
  - Si es válido, extrae el contenido y lo guarda.
  - Si no es válido, registra WARNING (no lanza excepción).
  - Retorna tupla: (archivos sin attribution, contenido_attribution_o_None).
- [ ] Verificar que `JSONLValidator` es importable desde `src/infra/helpers/__init__.py`.

**Cubre:** R8, R9

---

## Task 4: Crear excepciones en `domain/models/errors/loader_errors.py`

- [ ] Crear archivo `src/domain/models/errors/loader_errors.py`.
- [ ] Definir `LoaderNodeError(AgenticError)` como excepción base.
- [ ] Definir `SanitizationError(LoaderNodeError)`.
- [ ] Definir `MetadataExtractionError(LoaderNodeError)`.
- [ ] Definir `InvalidJSONLError(LoaderNodeError)`.
- [ ] Verificar que todas son importables desde `src/domain/models/__init__.py`.

**Cubre:** R12

---

## Task 5: Crear función `node_loader_task()` en `infra/adapters/workflow/nodes/loader.py`

- [ ] Crear archivo `src/infra/adapters/workflow/nodes/loader.py`.
- [ ] Implementar función async `node_loader_task(state: AgentState) -> dict` que:
  - Lee `state.get("files_content")` y `state.get("repository")`.
  - Determina ruta: `"clone"` si repository existe, `"simple"` si files_content existe.
  - Si ninguno existe, lanza `LoaderNodeError`.
  - Si ambos existen, elige `"clone"` (R3).
  - Escribe `load_to` en resultado.
- [ ] Si ruta es `"simple"`:
  - Extrae archivo `.devcore-attribution.jsonl` usando `JSONLValidator`.
  - Si válido, escribe `ai_attribution_jsonl` en resultado.
  - Sanitiza archivos usando `CodeSanitizer.sanitize_files()`.
  - Cuenta líneas usando `CodeSanitizer.count_lines()`.
  - Escribe `files_content` (sanitizado) y `total_lines` en resultado.
- [ ] Si ruta es `"clone"`:
  - Extrae metadatos usando `MetadataExtractor`.
  - Escribe `metadata` en resultado (como diccionario via `model_dump()`).
- [ ] Decorar con `@with_logging()` desde `src/infra/adapters/workflow/log.py`.
- [ ] Verificar que es importable desde `src/infra/adapters/workflow/nodes/__init__.py`.

**Cubre:** R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13

---

## Task 6: Modificar `WorkflowBuilder` en `infra/adapters/workflow/builder.py`

- [ ] Abrir archivo `src/infra/adapters/workflow/builder.py`.
- [ ] Importar `node_loader_task` desde `src/infra/adapters.workflow.nodes`.
- [ ] En método `build()`:
  - Añadir nodo `"loader"` con `graph.add_node("loader", node_loader_task)`.
  - Establecer `"loader"` como punto de entrada: `graph.set_entry_point("loader")`.
  - Añadir edge desde `"loader"` al siguiente nodo (p.ej. `"start"`).
  - Mantener edges existentes.
- [ ] Compilar grafo con `graph.compile()`.

**Cubre:** Integración del nodo en el workflow.

---

## Task 7: Actualizar exportaciones en `__init__.py`

- [ ] Actualizar `src/infra/helpers/__init__.py`:
  - Exportar `CodeSanitizer` desde `sanitizer`.
  - Exportar `MetadataExtractor` desde `metadata_extractor`.
  - Exportar `JSONLValidator` desde `jsonl_validator`.
- [ ] Actualizar `src/infra/adapters/workflow/nodes/__init__.py`:
  - Exportar `node_loader_task` desde `loader`.
- [ ] Actualizar `src/domain/models/__init__.py`:
  - Exportar `LoaderNodeError`, `SanitizationError`, `MetadataExtractionError`, `InvalidJSONLError`.

**Cubre:** Convención de exportaciones.

---

## Task 8: Crear tests en `tests/infra/helpers/test_sanitizer.py`

- [ ] Crear archivo `tests/infra/helpers/test_sanitizer.py`.
- [ ] Clase `TestCodeSanitizer(unittest.TestCase)`:
  - `test_remove_blank_lines_simple` — Verifica que líneas vacías se eliminan. **Cubre R4.**
  - `test_remove_blank_lines_preserves_code` — Verifica que líneas con código se preservan.
  - `test_sanitize_files_keeps_non_empty` — Verifica que archivos no vacíos se preservan. **Cubre R5.**
  - `test_sanitize_files_removes_empty` — Verifica que archivos vacíos se eliminan. **Cubre R5.**
  - `test_count_lines_single_file` — Verifica conteo en un archivo. **Cubre R6.**
  - `test_count_lines_multiple_files` — Verifica conteo en múltiples archivos. **Cubre R6.**
  - `test_count_lines_zero_empty_list` — Verifica conteo de lista vacía.

**Cubre:** R4, R5, R6

---

## Task 9: Crear tests en `tests/infra/helpers/test_metadata_extractor.py`

- [ ] Crear archivo `tests/infra/helpers/test_metadata_extractor.py`.
- [ ] Clase `TestMetadataExtractor(unittest.TestCase)`:
  - `test_extract_from_repository_parses_url` — Verifica extracción de owner y repo_name desde URL. **Cubre R7.**
  - `test_extract_from_repository_uses_defaults` — Verifica valores por defecto para author_name.
  - `test_extract_from_repository_maps_target_to_branch` — Verifica que `target` mapea a `branch`.
  - `test_extract_from_repository_sets_commit_sha` — Verifica que `commit_sha` se copia.

**Cubre:** R7

---

## Task 10: Crear tests en `tests/infra/helpers/test_jsonl_validator.py`

- [ ] Crear archivo `tests/infra/helpers/test_jsonl_validator.py`.
- [ ] Clase `TestJSONLValidator(unittest.TestCase)`:
  - `test_is_valid_jsonl_empty_returns_false` — Verifica rechazo de contenido vacío.
  - `test_is_valid_jsonl_valid_returns_true` — Verifica aceptación de JSONL válido. **Cubre R8.**
  - `test_is_valid_jsonl_invalid_returns_false` — Verifica rechazo de JSON inválido. **Cubre R8.**
  - `test_extract_attribution_file_found_and_valid` — Verifica extracción cuando existe y es válido. **Cubre R8.**
  - `test_extract_attribution_file_found_invalid_logs_warning` — Verifica WARNING cuando es inválido. **Cubre R9.**
  - `test_extract_attribution_file_not_found` — Verifica que retorna None cuando no existe.

**Cubre:** R8, R9

---

## Task 11: Crear tests en `tests/infra/adapters/workflow/test_loader_node.py`

- [ ] Crear archivo `tests/infra/adapters/workflow/test_loader_node.py`.
- [ ] Clase `TestLoaderNode(unittest.TestCase)`:
  - `test_node_loader_task_simple_route` — Verifica que `load_to="simple"` cuando solo `files_content`. **Cubre R1.**
  - `test_node_loader_task_clone_route` — Verifica que `load_to="clone"` cuando solo `repository`. **Cubre R2.**
  - `test_node_loader_task_both_inputs_chooses_clone` — Verifica que `load_to="clone"` cuando ambos. **Cubre R3.**
  - `test_node_loader_task_no_inputs_raises_error` — Verifica que lanza `LoaderNodeError` cuando ninguno. **Cubre R12.**
  - `test_node_loader_task_simple_sanitizes_files` — Verifica que `files_content` se sanitiza. **Cubre R4, R5.**
  - `test_node_loader_task_simple_counts_lines` — Verifica que `total_lines` se escribe. **Cubre R6.**
  - `test_node_loader_task_simple_extracts_attribution` — Verifica extracción de `.devcore-attribution.jsonl`. **Cubre R8.**
  - `test_node_loader_task_clone_extracts_metadata` — Verifica que `metadata` se escribe. **Cubre R7.**
  - `test_node_loader_task_simple_passes_files_downstream` — Verifica que `files_content` se pasa sin cambios adicionales. **Cubre R10.**
  - `test_node_loader_task_clone_passes_repository_downstream` — Verifica que `repository` se pasa sin cambios. **Cubre R11.**
  - `test_node_loader_task_is_decorated_with_logging` — Verifica que función tiene decorador `@with_logging()`. **Cubre R13.**

**Cubre:** R1, R2, R3, R4, R5, R6, R7, R8, R10, R11, R12, R13

---

## Task 12: Integración en workflow — tests de grafo

- [ ] Crear archivo `tests/infra/adapters/workflow/test_builder_with_loader.py` (o ampliar test del builder existente).
- [ ] Clase `TestWorkflowBuilderWithLoader(unittest.TestCase)`:
  - `test_builder_includes_loader_node` — Verifica que nodo `"loader"` existe en grafo.
  - `test_loader_is_entry_point` — Verifica que `"loader"` es punto de entrada.
  - `test_loader_connects_to_next_node` — Verifica edge de `"loader"` al siguiente nodo.

**Cubre:** Integración en workflow.

---

## Notas de implementación

- **Estado seguro:** `state.get()` con default para evitar KeyError.
- **Logging:** Usar `logger` de stdlib, niveles INFO (decisiones) y ERROR (fallos).
- **Trazabilidad:** Decorador `@with_logging()` en `node_loader_task`.
- **Tests:** Usar `tempfile.TemporaryDirectory()` para tests con archivos.
- **Excepciones:** Lanzar explícitamente, no retornar None.
- **Pydantic:** Usar `.model_dump()` para convertir RepositoryMetadata a dict.
