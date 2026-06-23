# Impl: loader_node — GitHub adapter (T5)

## Archivos creados

- `src/infra/adapters/github/__init__.py` — exporta `GithubMetadataReader`
- `src/infra/adapters/github/metadata_reader.py` — implementa `GithubMetadataReader`

## Contrato implementado

`GithubMetadataReader` implementa `MetadataReader` (ABC de `src/domain/ports/output/metadata/metadata_reader.py`).

Método `extract_from_repository(repo_data: dict) -> RepositoryMetadata`:
- Normaliza URL: strip `/` y `.git`, split por `/`
- `owner` = `parts[-2]` si hay al menos 2 segmentos, sino `"Unknown"`
- `repo_name` = `parts[-1]` si existe y no vacío, sino `"Unknown"`
- `branch` = `repo_data.get("target", "main")`
- `commit_sha`, `author_name` (default `"Unknown Author"`), `author_email` mapeados directamente
- `commit_message` = `None` (requiere GitHub API, fuera de scope)
- `timestamp` = `datetime.now(timezone.utc)`

## Trazabilidad

R7 (contrato MetadataReader / extracción de metadata de repositorio) cubierto por:
- Tests pendientes en `tests/infra/adapters/github/test_metadata_reader.py` (T10 del spec)

## Estado

T5 completada. Pendiente: T10 (tests de `GithubMetadataReader`).
