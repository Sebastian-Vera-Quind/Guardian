# Tasks: workflow_start

## Implementación del Workflow con LangGraph

### Modelos y Puertos

- [x] T1 — Crear `domain/models/workflow.py` con clases `WorkflowInput`, `WorkflowState` (TypedDict), y `WorkflowEvent`. Cubre: R9, R13.
- [x] T2 — Crear `domain/ports/workflow_executor.py` con protocolo `WorkflowExecutor` que define `graph: StateGraph` y `execute_and_stream()`. Cubre: R10, R13.
- [x] T3 — Actualizar `domain/models/__init__.py` para exportar `WorkflowInput`, `WorkflowState`, y `WorkflowEvent`. Cubre: R9, R13.
- [x] T4 — Actualizar `domain/ports/__init__.py` para exportar `WorkflowExecutor`. Cubre: R10.

### StateGraph y Nodos

- [x] T5 — Crear `infra/adapters/workflow/nodes.py` con funciones async `node_start`, `node_process`, `node_end`. Cada función recibe `WorkflowState` y retorna dict con actualizaciones. Cubre: R13, R14.
- [x] T6 — Crear `infra/adapters/workflow/builder.py` con clase `WorkflowBuilder` que construye un `StateGraph` con los nodos, define transiciones (edges) y los retorna compilado. Cubre: R13, R15.
- [x] T7 — Crear `infra/adapters/workflow/engine.py` con clase `WorkflowEngine` que implementa `WorkflowExecutor`. El método `execute_and_stream()` itera el grafo con `graph.astream()` y emite eventos con estructura `{event_type, node, data}`. Cubre: R2, R3, R4, R6, R16.
- [x] T8 — Actualizar `infra/adapters/workflow/__init__.py` para exportar `WorkflowBuilder` y `WorkflowEngine`. Cubre: R13.

### Errores y Validación

- [x] T9 — Añadir excepciones `WorkflowValidationError` y `WorkflowExecutionError` en `infra/entrypoints/http/errors.py`. Cubre: R8, R5.

### Integración HTTP

- [x] T10 — Modificar `infra/entrypoints/http/app.py` para reemplazar endpoint `/manual-chat`. Debe recibir body, validar contrato, instanciar `WorkflowBuilder`, compilar el `StateGraph`, crear `WorkflowEngine` con el grafo, ejecutar `engine.execute_and_stream()`, y retornar `StreamingResponse` con eventos JSONL. Cubre: R1, R2, R3, R4, R8, R10, R16.

### Tests

- [x] T11 — Crear `tests/domain/test_workflow_models.py` para validar `WorkflowInput`, `WorkflowState`, y `WorkflowEvent`. Cubre: R9, R13.
- [x] T12 — Crear `tests/infra/adapters/test_workflow_builder.py` para validar que `WorkflowBuilder.build()` crea un `StateGraph` compilado con nodos y edges correctos. Cubre: R13, R15.
- [x] T13 — Crear `tests/infra/adapters/test_workflow_nodes.py` para validar que funciones de nodo (`node_start`, `node_process`, `node_end`) ejecutan correctamente y retornan actualizaciones de estado. Cubre: R14.
- [x] T14 — Crear `tests/infra/adapters/test_workflow_engine.py` para validar que `WorkflowEngine.execute_and_stream()` itera el grafo y emite eventos con estructura `{event_type, node, data}`. Cubre: R2, R3, R4, R6, R16.
- [x] T15 — Crear `tests/infra/entrypoints/http/test_manual_chat_workflow.py` para validar que endpoint `/manual-chat` recibe JSON válido, construye builder, compila grafo, ejecuta engine, y retorna stream JSONL. Cubre: R1, R3, R4, R10.
- [x] T16 — Crear test que valida que `/manual-chat` rechaza JSON inválido con código 400. Cubre: R8.
- [x] T17 — Crear test que valida que transiciones entre nodos ocurren en orden (grafo dirigido acíclico). Cubre: R15.
- [x] T18 — Crear test que valida manejo de errores en nodos, emitiendo evento Error en stream. Cubre: R5.

## Notas de implementación

- `WorkflowState` es un `TypedDict` que define el estado inmutable del grafo. LangGraph lo maneja automáticamente.
- Nodos son funciones `async` que reciben el estado completo y retornan un `dict` con claves a actualizar. LangGraph merge automáticamente.
- `WorkflowBuilder.build()` retorna `graph.compile()`, que es un grafo ejecutable (permite `astream()`, `astream_events()`, etc.).
- `WorkflowEngine.execute_and_stream()` itera `self.graph.astream(input_data)` que emite tuplas `(node_id, output_dict)`.
- Cada evento emitido debe tener estructura: `{"event_type": "node_updated", "node": str, "data": dict}`.
- Excepciones en nodos deben ser capturadas en el try-catch del engine, traducidas a evento Error, y propagadas al cliente.
- El endpoint `/manual-chat` valida body con Pydantic, captura excepciones, y retorna 400 si validación falla.
- El middleware de API Key se mantiene sin cambios (R10).
- LangGraph proporciona `astream_events()` para granularidad extra (e.g., on_chain_start, on_chain_end). Se puede explorar en futuras versiones.
- Futuras extensiones: condicionales complejos (router functions), ejecución paralela (parallel edges), persistencia en BD.
