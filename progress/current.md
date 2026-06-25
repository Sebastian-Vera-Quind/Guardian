# Feature en curso: 5 — api_response

## Plan: Refactorizar respuesta del endpoint /manual-chat

### Aceptación del feature
1. Cambiar estructura de eventos: de `event_type` + `node` a `status` + `node`
2. Mapeo: `event_type: "node_updated"` → `status: "in_progress"` (sin `result`)
3. Evento final `complete` → `status: "success"` con `result` (estado final)
4. Evento de error → `status: "error"` sin `result`

### Plan de tasks - FASE 1 (Completada)
- [x] T1: Modificar líneas 72-77 de manual_chat.py para cambiar estructura de `event_data`
- [x] T2: Modificar línea 80 de manual_chat.py para enviar evento `complete` con `status: "success"` e incluir `result`
- [x] T3: Modificar línea 84 para error event con `status: "error"` sin `result`
- [x] T4: Escribir tests validando estructura de eventos `node_update` con `status: "in_progress"`
- [x] T5: Escribir tests validando evento `complete` con `status: "success"` e `result`
- [x] T6: Escribir tests validando evento error con `status: "error"`
- [x] T7: Ejecutar pytest y verificar todos pasan (25 tests OK)
- [x] T8: Documentar trazabilidad en progress/impl_api_response.md

### Plan de tasks - FASE 2 (Completada - Fix UUID Serialization)
- [x] T9: Crear función helper `convert_state_to_json_safe()` para convertir UUIDs a strings recursivamente
- [x] T10: Aplicar función en línea 100 del event_stream() para el evento complete
- [x] T11: Escribir test `test_complete_event_with_uuid_serializes()` validando serialización de UUID
- [x] T12: Ejecutar pytest completo y verificar 124 tests pasan sin regresiones

### Plan de tasks - FASE 3 (Completada - Custom JSONEncoder)
- [x] T1: Crear clase `SafeJSONEncoder` en manual_chat.py que extienda JSONEncoder
- [x] T2: Actualizar todas las llamadas a json.dumps() para usar cls=SafeJSONEncoder
- [x] T3: Eliminar función helper `convert_state_to_json_safe()` ya que no es necesaria
- [x] T4: Escribir test `test_complete_event_with_datetime_serializes()` validando datetime
- [x] T5: Ejecutar pytest completo y verificar 127 tests pasan sin regresiones

### Plan de tasks - FASE 4 (Completada - Robust Enum Handling)
- [x] T1: Mejorar `SafeJSONEncoder` para manejar Enum usando `.value`
- [x] T2: Agregar fallback genérico para tipos desconocidos (convertir a string)
- [x] T3: Escribir test `test_complete_event_with_enum_serializes()` validando Enum
- [x] T4: Ejecutar pytest completo y verificar 128 tests pasan sin regresiones

### Cambios realizados
1. **engine.py**: Agregado evento final de tipo "complete" con estado final
2. **manual_chat.py**: 
   - Refactorizado evento_stream para mapear eventos con nuevo status
   - Agregada clase `SafeJSONEncoder` que maneja UUID, datetime, date, Enum, y Pydantic models
   - Reemplazados todos los json.dumps() con json.dumps(..., cls=SafeJSONEncoder)
   - Eliminada función helper `convert_state_to_json_safe()` (no necesaria)
   - Mejorado fallback genérico para tipos desconocidos
3. **test_manual_chat_workflow.py**: 
   - Actualizado todos los tests + múltiples tests de serialización
   - Agregados tests para UUID, Pydantic, tipos mixtos, datetime, y Enum

### Estado: COMPLETADA
✓ Todos 128 tests pasados (fue 127, ahora 128)
✓ Respuesta refactorizada según acceptance criteria
✓ JSON serialization mejorada con SafeJSONEncoder
✓ Maneja: UUID, datetime, date, Enum, Pydantic models, tipos desconocidos
✓ Trazabilidad documentada en progress/impl_api_response.md
✓ Robust Enum handling implementado con fallback seguro
