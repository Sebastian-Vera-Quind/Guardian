# Implementacion: loader_node — Capa Domain

## Archivos creados

### src/domain/models/state/
- `__init__.py` — exporta FileContent, RepositoryMetadata, AgentState
- `file.py` — TypedDict FileContent con campos path, content, extension
- `repository.py` — Pydantic BaseModel RepositoryMetadata con campos owner, repo_name, branch, commit_sha, author_name, author_email, commit_message, timestamp
- `state.py` — TypedDict AgentState (total=False) con todos los campos del workflow loader

### src/domain/models/errors/
- `__init__.py` — exporta las 4 excepciones
- `loader_errors.py` — LoaderNodeError, SanitizationError, MetadataExtractionError, InvalidJSONLError (todas heredan de AgenticError via cadena)

### src/domain/ports/output/
- `__init__.py` — archivo vacio de paquete
- `metadata/__init__.py` — exporta MetadataReader
- `metadata/metadata_reader.py` — ABC MetadataReader con metodo abstracto extract_from_repository(repo_data: dict) -> RepositoryMetadata

## Archivos modificados

### src/domain/models/__init__.py
Añadidas exportaciones de:
- AgentState, FileContent, RepositoryMetadata (desde .state)
- LoaderNodeError, SanitizationError, MetadataExtractionError, InvalidJSONLError (desde .errors)

AgenticError se mantiene definida inline antes de los imports de subpaquetes para evitar circular imports.

## Decisiones tomadas

1. **Orden de definicion en __init__.py**: AgenticError se define como clase inline ANTES de importar .errors, porque loader_errors.py importa AgenticError desde src.domain.models. Python permite esto porque el simbolo ya esta en el namespace parcialmente inicializado del modulo cuando se ejecuta la importacion de .errors.

2. **AgentState como TypedDict(total=False)**: Todos los campos son opcionales porque el estado del workflow se construye incrementalmente a lo largo de los nodos. Esto sigue el patron de LangGraph donde cada nodo solo escribe los campos que produce.

3. **RepositoryMetadata como Pydantic BaseModel**: Permite validacion de tipos en construccion y uso de .model_dump() para serializar a dict antes de escribir en el estado (que es un TypedDict simple).

4. **MetadataReader como ABC**: Sigue el patron de puerto de salida de la arquitectura hexagonal. La implementacion concreta (GithubMetadataReader) va en la capa infra, manteniendo el dominio libre de dependencias externas.

5. **No se modifico nada fuera de src/domain/**: Se respeto el scope indicado. Las capas application e infra quedan pendientes para tasks T3-T12.

## Trazabilidad (capa Domain)

Los requirements cubiertos por esta capa son contratos y tipos:
- R7 (contrato): MetadataReader ABC en ports/output/metadata/
- R12 (tipo de excepcion): LoaderNodeError disponible para lanzarse en node_loader_task
- R1-R6, R8-R11, R13: requieren implementacion en capas application e infra (tasks T3-T12 pendientes)
