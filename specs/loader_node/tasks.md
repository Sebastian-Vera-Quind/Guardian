# Tasks: loader_node

Pasos discretos para implementación. Cada task cubre al menos un requirement (R<n>).
El orden respeta dependencias entre capas: Domain → Application → Infra → Integración → Tests.

---

## Task 1: Crear excepciones en `domain/models/errors/loader_errors.py`

- [ ] Crear archivo `src/domain/models/errors/loader_errors.py`.
- [ ] Definir `LoaderNodeError(AgenticError)` como excepción base del nodo.
- [ ] Definir `SanitizationError(LoaderNodeError)`.
- [ ] Definir `MetadataExtractionError(LoaderNodeError)`.
- [ ] Definir `InvalidJSONLError(LoaderNodeError)`.
- [ ] Exportar las cuatro excepciones desde `src/domain/models/__init__.py`.

**Cubre:** R12

---

## Task 2: Crear contrato `MetadataReader` en `domain/ports/output/metadata/`

- [ ] Crear directorio `src/domain/ports/output/metadata/` con `__init__.py`.
- [ ] Crear `src/domain/ports/output/metadata/metadata_reader.py`.
- [ ] Definir clase abstracta (ABC) `MetadataReader` con método:
  - `extract_from_repository(repo_data: dict) -> RepositoryMetadata`
- [ ] Exportar `MetadataReader` desde `src/domain/ports/output/metadata/__init__.py`.

**Cubre:** R7 (contrato)

---

## Task 3: Crear `CodeSanitizer` en `application/loader/sanitizer.py`

- [x] Crear directorio `src/application/loader/` con `__init__.py`.
- [x] Crear archivo `src/application/loader/sanitizer.py`.
- [x] Implementar clase `CodeSanitizer` con métodos estáticos:
  - `remove_blank_lines(content: str) -> str` — elimina líneas que contengan solo espacios/tabulaciones.
  - `sanitize_files(files: List[FileContent]) -> List[FileContent]` — retorna solo archivos con contenido no vacío tras sanitización.
  - `count_lines(files: List[FileContent]) -> int` — suma total de líneas de todos los archivos.
- [x] Exportar `CodeSanitizer` desde `src/application/loader/__init__.py`.

**Cubre:** R4, R5, R6

---

## Task 4: Crear `JSONLValidator` en `application/loader/jsonl_validator.py`

- [x] Crear archivo `src/application/loader/jsonl_validator.py`.
- [x] Implementar clase `JSONLValidator` con métodos estáticos:
  - `is_valid_jsonl(content: str) -> bool`:
    - Retorna `False` si el contenido está vacío.
    - Itera líneas no vacías e intenta parsear cada una con `json.loads()`.
    - Retorna `True` solo si todas las líneas no vacías son JSON válido.
  - `extract_attribution_file(files: List[FileContent]) -> tuple[List[FileContent], Optional[str]]`:
    - Detecta archivo con nombre exacto `.devcore-attribution.jsonl`.
    - Si lo encuentra y es válido, extrae el contenido como `str`.
    - Si no es válido, registra `logger.warning()` y no extrae nada.
    - Retorna `(archivos_sin_attribution, contenido_o_None)`.
- [x] Exportar `JSONLValidator` desde `src/application/loader/__init__.py`.

**Cubre:** R8, R9

---

## Task 5: Crear `MetadataReader` adapter en `infra/adapters/github/metadata_reader.py`

- [x] Crear directorio `src/infra/adapters/github/` con `__init__.py`.
- [x] Crear archivo `src/infra/adapters/github/metadata_reader.py`.
- [x] Implementar clase `GithubMetadataReader` que implementa el contrato `MetadataReader`:
  - `extract_from_repository(repo_data: dict) -> RepositoryMetadata`:
    - Extrae `owner` desde la URL (penúltimo segmento tras strip de `.git`).
    - Extrae `repo_name` desde la URL (último segmento sin `.git`).
    - Mapea `target` → `branch`, `commit_sha`, `author_name`, `author_email` del diccionario.
    - Genera `timestamp=datetime.now(timezone.utc)`.
    - Retorna instancia de `RepositoryMetadata`.
- [x] Exportar `GithubMetadataReader` desde `src/infra/adapters/github/__init__.py`.

**Cubre:** R7

---

## Task 6: Crear función `node_loader_task()` en `infra/adapters/workflow/nodes/loader.py`

- [x] Crear archivo `src/infra/adapters/workflow/nodes/loader.py`.
- [x] Implementar función `determine_load_route(state: AgentState) -> str`:
  - Retorna `"clone"` si `state.get("repository")` no es `None`.
  - Retorna `"simple"` si `state.get("files_content")` no está vacío.
  - Lanza `LoaderNodeError` si ninguno está presente (R12).
- [x] Implementar función async `node_loader_task(state: AgentState) -> dict` decorada con `@with_logging()`:
  - Llama a `determine_load_route()` y escribe `load_to` en resultado.
  - **Ruta `"simple"`:**
    - Extrae `.devcore-attribution.jsonl` con `JSONLValidator.extract_attribution_file()`. Si válido, escribe `ai_attribution_jsonl`.
    - Sanitiza con `CodeSanitizer.sanitize_files()`, escribe `files_content`.
    - Cuenta líneas con `CodeSanitizer.count_lines()`, escribe `total_lines`.
  - **Ruta `"clone"`:**
    - Extrae metadatos con `GithubMetadataReader().extract_from_repository()`.
    - Escribe `metadata` como dict vía `.model_dump()`.
    - Si falla, lanza `MetadataExtractionError`.
- [x] Exportar `node_loader_task` desde `src/infra/adapters/workflow/nodes/__init__.py`.

**Cubre:** R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13

---

## Task 7: Integrar loader en `infra/adapters/workflow/builder.py`

- [x] Abrir `src/infra/adapters/workflow/builder.py`.
- [x] Importar `node_loader_task` desde `src.infra.adapters.workflow.nodes`.
- [x] En `build()`:
  - Añadir nodo `"loader"` con `graph.add_node("loader", node_loader_task)`.
  - Establecer `"loader"` como punto de entrada: `graph.set_entry_point("loader")`.
  - Añadir edge `"loader"` → siguiente nodo (p. ej. `"start"`).
  - Mantener edges y nodos existentes sin modificación.
- [x] Exportar `node_loader_task` desde `src/infra/adapters/workflow/__init__.py`.

**Cubre:** Integración del nodo en el grafo.

---

## Task 8: Tests de `CodeSanitizer` — `tests/application/loader/test_sanitizer.py`

- [x] Crear archivo `tests/application/loader/test_sanitizer.py`.
- [x] `test_remove_blank_lines_eliminates_whitespace_only_lines` — verifica que líneas con solo espacios/tabs se eliminan. **R4**
- [x] `test_remove_blank_lines_preserves_code_lines` — verifica que líneas con código se preservan.
- [x] `test_sanitize_files_keeps_files_with_content` — verifica que archivos no vacíos se conservan. **R5**
- [x] `test_sanitize_files_removes_empty_files` — verifica que archivos vacíos tras sanitizar se descartan. **R5**
- [x] `test_count_lines_single_file` — verifica conteo correcto en un archivo. **R6**
- [x] `test_count_lines_multiple_files_sums_all` — verifica suma de líneas en múltiples archivos. **R6**
- [x] `test_count_lines_empty_list_returns_zero` — verifica que lista vacía retorna 0.

**Cubre:** R4, R5, R6

---

## Task 9: Tests de `JSONLValidator` — `tests/application/loader/test_jsonl_validator.py`

- [x] Crear archivo `tests/application/loader/test_jsonl_validator.py`.
- [x] `test_is_valid_jsonl_empty_string_returns_false` — contenido vacío es inválido.
- [x] `test_is_valid_jsonl_valid_multiline_returns_true` — JSONL bien formado es válido. **R8**
- [x] `test_is_valid_jsonl_invalid_json_returns_false` — JSON malformado es inválido. **R8**
- [x] `test_extract_attribution_found_and_valid_extracts_content` — extrae contenido cuando es válido. **R8**
- [x] `test_extract_attribution_found_invalid_logs_warning_returns_none` — registra WARNING y no extrae si JSONL inválido. **R9**
- [x] `test_extract_attribution_not_found_returns_none` — retorna `None` cuando no existe el archivo.
- [x] `test_extract_attribution_removes_file_from_list` — el archivo `.devcore-attribution.jsonl` no queda en la lista retornada.

**Cubre:** R8, R9

---

## Task 10: Tests de `GithubMetadataReader` — `tests/infra/adapters/github/test_metadata_reader.py`

- [x] Crear archivo `tests/infra/adapters/github/test_metadata_reader.py`.
- [x] `test_extract_from_repository_parses_owner_from_url` — verifica extracción de `owner` desde URL. **R7**
- [x] `test_extract_from_repository_parses_repo_name_from_url` — verifica extracción de `repo_name`. **R7**
- [x] `test_extract_from_repository_maps_target_to_branch` — verifica que `target` → `branch`.
- [x] `test_extract_from_repository_copies_commit_sha` — verifica copia de `commit_sha`.
- [x] `test_extract_from_repository_uses_default_author_name` — verifica valor por defecto cuando falta `author_name`.
- [x] `test_extract_from_repository_returns_repository_metadata_instance` — retorna instancia de `RepositoryMetadata`.

**Cubre:** R7

---

## Task 11: Tests del nodo — `tests/infra/adapters/workflow/test_loader_node.py`

- [x] Crear archivo `tests/infra/adapters/workflow/test_loader_node.py`.
- [x] `test_simple_route_when_only_files_content` — `load_to="simple"` cuando solo `files_content`. **R1**
- [x] `test_clone_route_when_only_repository` — `load_to="clone"` cuando solo `repository`. **R2**
- [x] `test_clone_route_takes_priority_when_both_present` — `load_to="clone"` cuando ambos presentes. **R3**
- [x] `test_raises_loader_node_error_when_no_inputs` — lanza `LoaderNodeError` si ninguno presente. **R12**
- [x] `test_simple_route_sanitizes_files_content` — `files_content` sanitizado en resultado. **R4, R5**
- [x] `test_simple_route_writes_total_lines` — `total_lines` escrito correctamente. **R6**
- [x] `test_simple_route_extracts_valid_attribution` — `ai_attribution_jsonl` escrito si válido. **R8**
- [x] `test_clone_route_writes_metadata` — `metadata` escrito cuando ruta clone. **R7**
- [x] `test_simple_route_passes_repository_unchanged` — `repository` no se modifica. **R11**
- [x] `test_clone_route_passes_files_content_unchanged` — `files_content` no se modifica. **R10**
- [x] `test_node_is_decorated_with_logging` — función tiene decorador `@with_logging()`. **R13**

**Cubre:** R1, R2, R3, R4, R5, R6, R7, R8, R10, R11, R12, R13

---

## Task 12: Tests de integración del grafo — `tests/infra/adapters/workflow/test_builder_with_loader.py`

- [x] Crear o extender `tests/infra/adapters/workflow/test_builder_with_loader.py`.
- [x] `test_builder_includes_loader_node` — nodo `"loader"` existe en el grafo compilado.
- [x] `test_loader_is_entry_point` — `"loader"` está establecido como punto de entrada.
- [x] `test_loader_connects_to_next_node` — existe edge desde `"loader"` al nodo siguiente.

**Cubre:** Integración en workflow.

---

## Notas de implementación

- **Capas:** Respetar el orden Domain → Application → Infra. Las capas superiores no importan de capas inferiores.
- **Estado seguro:** Usar `state.get()` con default; nunca acceder por índice directo al estado.
- **Logging:** Usar `logger` de stdlib; nivel `INFO` para decisiones de ruta, `ERROR` para fallos, `WARNING` para JSONL inválido.
- **Trazabilidad:** `@with_logging()` en `node_loader_task` es obligatorio (R13).
- **Pydantic:** Usar `.model_dump()` para convertir `RepositoryMetadata` a dict antes de escribir al estado.
- **Excepciones:** Lanzar explícitamente con mensaje descriptivo; no retornar `None` ni swallow errors.
- **Directorios nuevos:** Todos los nuevos paquetes requieren `__init__.py` vacío para ser importables.
