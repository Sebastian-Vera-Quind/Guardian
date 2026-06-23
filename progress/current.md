# Feature en curso: 3 — loader_node

## Plan: tasks T1..T12 de specs/loader_node/tasks.md

### Estado actual

Implementación completa. Pendiente de revisión.

### Tasks completadas

- [x] T1: Excepciones en `domain/models/errors/loader_errors.py`
- [x] T2: Contrato `MetadataReader` en `domain/ports/output/metadata/`
- [x] Modelos de estado: `domain/models/state/` (FileContent, RepositoryMetadata, AgentState)
- [x] Exportaciones actualizadas en `domain/models/__init__.py`
- [x] T3: CodeSanitizer (application layer)
- [x] T4: JSONLValidator (application layer)
- [x] T5: GithubMetadataReader adapter (infra layer)
- [x] T6: node_loader_task + nodes/base.py + nodes/__init__.py (conflicto estructural resuelto)
- [x] T7: builder.py creado con loader como entry point
- [x] T8: Tests de CodeSanitizer
- [x] T9: Tests de JSONLValidator
- [x] T10: Tests de GithubMetadataReader
- [x] T11: Tests de node_loader_task
- [x] T12: Tests de integración del grafo
