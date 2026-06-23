# Trazabilidad: loader_node — capa Application

## Archivos creados

- `src/application/loader/__init__.py` — exporta CodeSanitizer y JSONLValidator
- `src/application/loader/sanitizer.py` — clase CodeSanitizer
- `src/application/loader/jsonl_validator.py` — clase JSONLValidator
- `tests/__init__.py`
- `tests/application/__init__.py`
- `tests/application/loader/__init__.py`
- `tests/application/loader/test_sanitizer.py` — tests de CodeSanitizer
- `tests/application/loader/test_jsonl_validator.py` — tests de JSONLValidator

## Mapa R<n> -> test

| Requirement | Test |
|-------------|------|
| R4 — eliminar líneas en blanco | `TestCodeSanitizerRemoveBlankLines::test_remove_blank_lines_eliminates_whitespace_only_lines` |
| R4 — preservar líneas con código | `TestCodeSanitizerRemoveBlankLines::test_remove_blank_lines_preserves_code_lines` |
| R5 — conservar archivos con contenido | `TestCodeSanitizerSanitizeFiles::test_sanitize_files_keeps_files_with_content` |
| R5 — descartar archivos vacíos tras sanitización | `TestCodeSanitizerSanitizeFiles::test_sanitize_files_removes_empty_files` |
| R6 — contar líneas en un archivo | `TestCodeSanitizerCountLines::test_count_lines_single_file` |
| R6 — sumar líneas de múltiples archivos | `TestCodeSanitizerCountLines::test_count_lines_multiple_files_sums_all` |
| R6 — lista vacía retorna 0 | `TestCodeSanitizerCountLines::test_count_lines_empty_list_returns_zero` |
| R8 — JSONL vacío inválido | `TestJSONLValidatorIsValidJsonl::test_is_valid_jsonl_empty_string_returns_false` |
| R8 — JSONL multilínea válido | `TestJSONLValidatorIsValidJsonl::test_is_valid_jsonl_valid_multiline_returns_true` |
| R8 — JSONL malformado inválido | `TestJSONLValidatorIsValidJsonl::test_is_valid_jsonl_invalid_json_returns_false` |
| R8 — extrae contenido attribution válido | `TestJSONLValidatorExtractAttributionFile::test_extract_attribution_found_and_valid_extracts_content` |
| R8 — archivo attribution no queda en lista | `TestJSONLValidatorExtractAttributionFile::test_extract_attribution_removes_file_from_list` |
| R9 — registra WARNING y no extrae si JSONL inválido | `TestJSONLValidatorExtractAttributionFile::test_extract_attribution_found_invalid_logs_warning_returns_none` |
| R9 — retorna None si no existe attribution | `TestJSONLValidatorExtractAttributionFile::test_extract_attribution_not_found_returns_none` |

## Notas

- Los requirements R1, R2, R3, R7, R10, R11, R12, R13 corresponden a la capa Infra (T5-T7, T10-T12) y no son cubiertos en esta sesión.
- Imports absolutos desde `src.domain.models.state.file`.
- `FileContent` es TypedDict; acceso por clave string (`file["path"]`).
- El logger de `JSONLValidator` usa el nombre del módulo (`src.application.loader.jsonl_validator`) para que `assertLogs` lo intercepte correctamente en los tests.
