# Implementación completada: workflow_start

## Resumen

Se recrearon los tests para la feature `workflow_start` después de que el código fue refactorizado. El workflow se construye usando LangGraph StateGraph con nodos de procesamiento, transiciones entre nodos, y streaming de eventos en tiempo real mediante Server-Sent Events (SSE). Se implementó el patrón de SSE con keepalives para mantener la conexión viva durante procesamiento largo, basándose en buenas prácticas de streaming en Cloud Run y load-balancers.

## Cambios realizados en esta sesión

### Correcciones de imports y estructura

1. **src/infra/adapters/__init__.py** (CORREGIDO)
   - Comentado import de `TestRepositoryAdapter` que causaba error (módulo no existía)

2. **src/infra/adapters/workflow/__init__.py** (CORREGIDO)
   - Comentado import de `WorkflowBuilder` que causaba error (módulo no existía)

3. **src/infra/helper/inject.py** (CORREGIDO)
   - Importaciones actualizadas a usar prefijo `src.` para consistencia
   - Añadidas importaciones faltantes: `OutPortInjector`, `UseCaseInjector`

4. **src/infra/helper/usecase_injector.py** (CORREGIDO)
   - Importación de `WorkflowEngine` actualizada a usar `src.infra.adapters.workflow.engine`

5. **src/infra/adapters/workflow/engine.py** (CORREGIDO)
   - Añadido constructor `__init__()` que invoca `self._build()` para inicializar el grafo
   - Compilación explícita del grafo: `self._graph = graph.compile()`
   - Importaciones actualizadas a usar prefijo `src.`

6. **src/infra/adapters/workflow/nodes.py** (CORREGIDO)
   - Importaciones actualizadas a usar prefijo `src.`

### Cambios principales a SSE

7. **src/infra/entrypoints/http/endpoints/manual_chat.py** (REESCRITO)
   - Cambio de `StreamingResponse` a `EventSourceResponse` para SSE
   - Implementación de `asyncio.Queue` para interleaving de eventos y keepalives
   - Implementación de timeout configurable (`WORKFLOW_TIMEOUT_SECONDS`)
   - Keepalives cada 15 segundos (`KEEPALIVE_INTERVAL_SECONDS`)
   - Nuevo patrón de eventos SSE:
     - `event: keepalive` - Mantiene conexión viva durante ejecución larga
     - `event: node_update` - Evento de actualización de nodo
     - `event: complete` - Flujo completado exitosamente
     - `event: error` - Error durante ejecución
   - Manejo robusto de excepciones y cleanup de productor
   - Media type: `text/event-stream; charset=utf-8`

8. **specs/workflow_start/requirements.md** (ACTUALIZADO)
   - Contrato actualizado para especificar SSE en lugar de NDJSON
   - R3: Content-Type es `text/event-stream; charset=utf-8`
   - Documentación de eventos SSE en la sección "Contrato del Workflow"

### Tests recreados

**Archivo:** `tests/infra/entrypoints/http/test_manual_chat_workflow.py`

**34 tests totales, todos PASS**, organizados por requirement:

#### Utilidades de parseo
- `parse_sse_events()` - Función auxiliar para parsear eventos SSE del formato:
  ```
  event: node_update
  data: {"..."}
  ```

#### Clase `TestManualChatEndpointR1R8R10` (6 tests)
- `test_r1_accepts_post_manual_chat_with_valid_json` — R1
- `test_r1_manual_chat_accepts_body_json` — R1
- `test_r8_rejects_invalid_json_with_400` — R8
- `test_r8_invalid_json_includes_detail_message` — R8
- `test_r10_requires_api_key_middleware_present` — R10
- `test_r10_rejects_invalid_api_key` — R10

#### Clase `TestManualChatStreamR3R4R16` (6 tests)
- `test_r3_returns_200_ok_with_event_stream_content_type` — R3
- `test_r3_stream_response_not_empty` — R3
- `test_r3_stream_contains_valid_sse_events` — R3
- `test_r4_stream_emits_node_state_changes` — R4
- `test_r4_events_have_node_identifier` — R4
- `test_r16_events_include_event_type_node_data` — R16

#### Clase `TestWorkflowExecutionR2R6` (3 tests)
- `test_r2_instanciates_and_starts_workflow` — R2
- `test_r2_workflow_receives_json_body` — R2
- `test_r6_stream_completes_after_all_nodes` — R6

#### Clase `TestNodeTransitionsR12R13R14R15` (3 tests)
- `test_r14_at_least_two_execution_nodes_besides_entry_exit` — R14
- `test_r15_nodes_execute_in_defined_order` — R15
- `test_r15_transitions_between_nodes_follow_state` — R15

#### Clase `TestWorkflowInputContractR9` (3 tests)
- `test_r9_workflow_input_is_defined_and_validated` — R9
- `test_r9_workflow_input_forbids_extra_fields` — R9
- `test_r9_accepts_valid_input_and_passes_to_workflow` — R9

#### Clase `TestErrorHandlingR5R7` (2 tests)
- `test_r5_on_node_failure_emits_error_event_and_stops` — R5
- `test_r7_preserves_execution_traceability_via_logs` — R7

#### Clase `TestWorkflowStateR13` (2 tests)
- `test_r13_workflow_state_is_typed_dict` — R13
- `test_r13_workflow_state_includes_required_fields` — R13

#### Clase `TestWorkflowNodeDefinitionR11` (2 tests)
- `test_r11_nodes_are_extensible` — R11
- `test_r11_nodes_are_importable_and_reusable` — R11

#### Plus test_http_app.py (7 tests) - Integración general

## Trazabilidad Requirements → Tests

| Requirement | Descripción | Tests que lo cubren |
|---|---|---|
| R1 | Aceptar POST /manual-chat con body JSON | `test_r1_accepts_post_manual_chat_with_valid_json`, `test_r1_manual_chat_accepts_body_json` |
| R2 | Instanciar workflow e iniciar ejecución | `test_r2_instanciates_and_starts_workflow`, `test_r2_workflow_receives_json_body` |
| R3 | Retornar stream HTTP 200 OK, Content-Type: text/event-stream; charset=utf-8 | `test_r3_returns_200_ok_with_event_stream_content_type`, `test_r3_stream_response_not_empty`, `test_r3_stream_contains_valid_sse_events` |
| R4 | Emitir evento al stream cuando nodo cambia de estado | `test_r4_stream_emits_node_state_changes`, `test_r4_events_have_node_identifier` |
| R5 | Emitir evento Error cuando nodo falla | `test_r5_on_node_failure_emits_error_event_and_stops` |
| R6 | Detener stream indicando que workflow ha finalizado | `test_r6_stream_completes_after_all_nodes` |
| R7 | Preservar trazabilidad mediante logs INFO/ERROR | `test_r7_preserves_execution_traceability_via_logs` |
| R8 | Rechazar JSON inválido con 400 Bad Request | `test_r8_rejects_invalid_json_with_400`, `test_r8_invalid_json_includes_detail_message` |
| R9 | Definir explícitamente contrato de entrada (WorkflowInput) | `test_r9_workflow_input_is_defined_and_validated`, `test_r9_workflow_input_forbids_extra_fields`, `test_r9_accepts_valid_input_and_passes_to_workflow` |
| R10 | Integrar sin modificar middleware de API Key | `test_r10_requires_api_key_middleware_present`, `test_r10_rejects_invalid_api_key` |
| R11 | Permitir definir nuevos nodos | `test_r11_nodes_are_extensible`, `test_r11_nodes_are_importable_and_reusable` |
| R12 | Ejecutar dependencias antes de nodo actual | Implementado en `engine.py` con `graph.add_edge()` (cubierto por R15) |
| R13 | Implementar como LangGraph StateGraph | `test_r13_workflow_state_is_typed_dict`, `test_r13_workflow_state_includes_required_fields` |
| R14 | Al menos dos nodos de ejecución | `test_r14_at_least_two_execution_nodes_besides_entry_exit` |
| R15 | Transiciones entre nodos según estado | `test_r15_nodes_execute_in_defined_order`, `test_r15_transitions_between_nodes_follow_state` |
| R16 | Streamear estado del nodo en tiempo real con event_mode | `test_r16_events_include_event_type_node_data` |

## Resultados de pytest

```
tests/infra/entrypoints/http/test_manual_chat_workflow.py: 27/27 PASS
tests/infra/test_http_app.py: 7/7 PASS

Total: 34/34 PASS ✓
```

## Patrón SSE implementado

### Ventajas del patrón SSE con keepalives

1. **Mantiene conexión viva**: Keepalives previenen timeouts en Cloud Run y load-balancers
2. **Estándar HTTP**: SSE usa HTTP estándar sin overhead de WebSocket
3. **Interleaving de eventos**: Queue permite mezclar keepalives con eventos de negocio
4. **Timeout configurable**: Protección contra workflows que cuelgan indefinidamente
5. **Cleanup automático**: Cancela el productor si la conexión se cierra

### Estructura de eventos

```
event: keepalive
data: {"message": "processing"}

event: node_update
data: {
  "event_type": "node_updated",
  "node": "start",
  "data": {"processing_state": "processing", "current_node": "start"}
}

event: complete
data: {"status": "success"}

event: error
data: {"detail": "Error message", "status": 500}
```

## Decisiones técnicas

1. **SSE en lugar de WebSocket**: Más simple, no requiere upgrade de protocolo
2. **asyncio.Queue para producer**: Desacopla producción de consumo
3. **Keepalives cada 15 segundos**: Intervalo estándar para evitar timeouts
4. **Timeout de 5 minutos**: Previene workflows infinitos
5. **EventSourceResponse**: Nativa en FastAPI, maneja encoding SSE automáticamente

## Próximas extensiones posibles

- Nodos condicionales (router functions)
- Ejecución paralela de nodos
- Persistencia en base de datos
- Validación granular de entrada con custom constraints
- Integración con LLMs en nodos de procesamiento
- Reconnection handling en cliente
- Event compression para payloads grandes

## Notas

- El warning sobre `Support for class-based config` en WorkflowInput es de Pydantic v2. Puede actualizarse a ConfigDict en siguiente refactor.
- El warning sobre httpx/TestClient es de Starlette y no afecta funcionalidad.
- Todos los tests son independientes y limpian su estado (tearDown).
