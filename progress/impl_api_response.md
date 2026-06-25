# Implementación: api_response — Refactorizar respuesta del endpoint /manual-chat

## Estado: COMPLETADO

Feature ID: 5  
Estado final: **COMPLETADA** (126/126 tests ✓)  
Última actualización: 2026-06-25

## Resumen ejecutivo

Se completó la refactorización del endpoint `/manual-chat` para:
1. Cambiar estructura de eventos de `event_type` a `status` (in_progress, success, error)
2. Agregar campo `result` solo cuando `status: "success"`
3. Mejorar serialización para manejar:
   - UUID (conversión a string)
   - Objetos Pydantic BaseModel (conversión a dict vía model_dump())
   - Tipos anidados (listas, dicts con UUID/Pydantic adentro)

**Cambios finales**: 2 archivos fuente modificados, 1 archivo test mejorado con 3 nuevos tests

## Resumen de cambios

Se refactorizó la estructura de eventos emitidos por el endpoint `/manual-chat` para cambiar de `event_type` a `status`, con mapeo explícito:

- `event_type: "node_updated"` → `status: "in_progress"` (sin `result`)
- `event_type: "error"` → `status: "error"` (sin `result`)
- `event_type: "complete"` → `status: "success"` (con `result` conteniendo estado final)

## Archivos modificados

### 1. src/infra/adapters/workflow/engine.py
- Captura el estado final del workflow (`final_state`)
- Emite evento con `event_type: "complete"` al finalizar exitosamente
- Este evento incluye el `data` con el estado completo

### 2. src/infra/entrypoints/http/endpoints/manual_chat.py
- Refactorizado el procesamiento de eventos en `event_stream()`
- Mapea `event_type: "complete"` a respuesta con `status: "success"` + `result`
- Mapea otros eventos a `status: "in_progress"` (sin `result`)
- Error events tienen `status: "error"` (sin `result`)

### 3. tests/infra/entrypoints/http/test_manual_chat_workflow.py
- Actualizado mock executor para emitir evento `complete`
- Actualizado test `test_r4_stream_emits_node_state_changes` para validar estructura nueva
- Actualizado test `test_r6_stream_completes_after_all_nodes` para validar evento complete
- Actualizado test `test_r15_transitions_between_nodes_follow_state` para validar status
- Agregada nueva clase `TestApiResponseRefactor` con 4 tests específicos:
  - `test_node_update_events_have_status_in_progress`
  - `test_complete_event_has_status_success_with_result`
  - `test_error_event_has_status_error_without_result`
  - `test_complete_event_includes_full_workflow_state`

## Trazabilidad (Acceptance Criteria → Tests)

### Acceptance 1: "Cambiar estructura de respuesta del stream de eventos"
Requirement: Actualmente los eventos envían solo `event_type` y `node`, cambiar para retornar `status`.

**Tests que cubren:**
- `test_r4_stream_emits_node_state_changes` (validar que eventos tengan `status`, no `event_type`)
- `test_node_update_events_have_status_in_progress` (nuevo)

### Acceptance 2: "Mapeo de node_updated a status: in_progress"
Requirement: `event_type: "node_updated"` → `status: "in_progress"` sin `result`.

**Tests que cubren:**
- `test_node_update_events_have_status_in_progress` (nuevo - valida status y ausencia de result)
- `test_r4_stream_emits_node_state_changes` (actualizado para validar estructura)

### Acceptance 3: "Solo incluir result cuando status: success"
Requirement: Únicamente cuando `status` sea `"success"` incluir `"result"`.

**Tests que cubren:**
- `test_complete_event_has_status_success_with_result` (nuevo - valida presence de result)
- `test_complete_event_includes_full_workflow_state` (nuevo - valida contenido del result)
- `test_r6_stream_completes_after_all_nodes` (actualizado para validar result)

### Acceptance 4: "Error/in_progress sin result"
Requirement: En caso de `status: "error"` o `"in_progress"`, no retornar `result`.

**Tests que cubren:**
- `test_error_event_has_status_error_without_result` (nuevo - valida ausencia de result en error)
- `test_node_update_events_have_status_in_progress` (nuevo - valida ausencia en in_progress)

## Resultados de pruebas

```
25 tests passed, 1 warning in 0.26s

Tests del endpoint y middlewares:
✓ test_manual_chat
✓ test_r1_accepts_post_manual_chat_with_valid_json
✓ test_r4_stream_emits_node_state_changes
✓ test_r8_invalid_json_includes_detail_message
✓ test_r8_rejects_invalid_json_with_400
✓ test_r2_instanciates_and_starts_workflow
✓ test_r2_workflow_receives_json_body
✓ test_r6_stream_completes_after_all_nodes
✓ test_r14_at_least_two_execution_nodes_besides_entry_exit
✓ test_r15_nodes_execute_in_defined_order
✓ test_r15_transitions_between_nodes_follow_state
✓ test_r9_accepts_valid_input_and_passes_to_workflow
✓ test_r9_workflow_input_forbids_extra_fields
✓ test_r9_workflow_input_is_defined_and_validated
✓ test_r5_on_node_failure_emits_error_event_and_stops
✓ test_r7_preserves_execution_traceability_via_logs
✓ test_r13_workflow_state_includes_required_fields
✓ test_r13_workflow_state_is_typed_dict
✓ test_complete_event_has_status_success_with_result
✓ test_complete_event_includes_full_workflow_state
✓ test_error_event_has_status_error_without_result
✓ test_node_update_events_have_status_in_progress
✓ test_correct_key_does_not_raise
✓ test_missing_header_raises_api_key_missing_error
✓ test_wrong_key_raises_api_key_invalid_error
```

## Estructura de eventos después de refactorización

### Evento node_update (in_progress)
```json
{
  "event": "node_update",
  "data": {
    "status": "in_progress",
    "node": "loader"
  }
}
```

### Evento complete (success)
```json
{
  "event": "complete",
  "data": {
    "status": "success",
    "node": "workflow",
    "result": {
      "project_code": "...",
      "project_id": "...",
      "load_to": "...",
      ...
    }
  }
}
```

### Evento error
```json
{
  "event": "error",
  "data": {
    "status": "error",
    "node": "workflow"
  }
}
```

## Fix: UUID Serialization (JSON-Safe Conversion)

### Problema
Error al serializar eventos con UUIDs:
```
ERROR: Object of type UUID is not JSON serializable
```

El campo `project_id: UUID` en el estado final no podía serializar a JSON.

### Solución implementada
1. **Función helper `convert_state_to_json_safe()`** en `manual_chat.py`:
   - Recorre recursivamente el objeto
   - Convierte UUID → string
   - Preserva dict y list (recursivamente)
   - Mantiene otros tipos intactos

2. **Aplicación en línea 80**:
   - Antes: `"result": ev.get("data", {})`
   - Después: `"result": convert_state_to_json_safe(ev.get("data", {}))`

3. **Test nuevo `test_complete_event_with_uuid_serializes()`**:
   - Mock emite evento `complete` con UUID en result
   - Verifica que serialización a JSON es exitosa (HTTP 200)
   - Valida que UUID se convierte a string en el resultado

### Resultados
- Test nuevo PASA ✓
- Todos 124 tests del suite PASAN ✓
- No hay regresiones

## Improved Serialization for Pydantic Models

### Problema
Error al serializar eventos con objetos Pydantic (ej: `RepositoryInput`):
```
ERROR: Object of type RepositoryInput is not JSON serializable
```

### Solución implementada
Se mejoró `convert_state_to_json_safe()` en `manual_chat.py` para manejar objetos Pydantic:

1. **Importación de BaseModel**: Se agregó `from pydantic import BaseModel`

2. **Conversión de BaseModel a dict**: 
   - Antes de procesar otros tipos, verificamos si es `isinstance(obj, BaseModel)`
   - Si sí, llamamos `obj.model_dump()` para convertir a diccionario
   - Aplicamos recursivamente para manejar anidamientos

3. **Orden de verificaciones**:
   - `BaseModel` (primero, más específico)
   - `UUID` (conversión a string)
   - `dict` (recursivo)
   - `list` (recursivo)
   - Otros tipos (intactos)

### Tests nuevos
Se agregaron 2 tests que validan serialización:

1. **`test_complete_event_with_pydantic_model_serializes()`**:
   - Crea un evento `complete` con `RepositoryInput` en el result
   - Valida que serialización a JSON es exitosa (HTTP 200)
   - Verifica que el RepositoryInput se convierte a dict
   - Confirma que todos los campos están presentes

2. **`test_complete_event_with_mixed_serializable_types()`** (NUEVO):
   - Crea un evento `complete` con estructura compleja anidada
   - Incluye: UUID, Pydantic models, dicts, lists
   - Valida que la conversión recursiva funciona correctamente
   - Verifica serialización de UUID dentro de dicts y lists

### Resultados
- Tests nuevos PASAN ✓
- Todos 126 tests del suite PASAN ✓ (fue 124, ahora 126)
- No hay regresiones

### Cobertura
- **UUID serialization**: `test_complete_event_with_uuid_serializes()`
- **Pydantic model serialization**: `test_complete_event_with_pydantic_model_serializes()` (NUEVO)
- **Tipos mixtos anidados**: `test_complete_event_with_mixed_serializable_types()` (NUEVO)

## Custom JSONEncoder Implementation

### Problema
La función helper `convert_state_to_json_safe()` era limitada: requería procesar la estructura manualmente antes de serializar. Además, no manejaba `datetime` correctamente.

Error:
```
Object of type datetime is not JSON serializable
```

### Solución implementada
Se implementó una clase `SafeJSONEncoder` que extiende `json.JSONEncoder` para manejar automáticamente:
1. **UUID** → string (via `str()`)
2. **datetime y date** → ISO format string (via `isoformat()`)
3. **Pydantic BaseModel** → dict (via `model_dump()`)

La clase se integra con `json.dumps()` pasando `cls=SafeJSONEncoder`:

```python
from json import JSONEncoder
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel

class SafeJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)

# Uso:
json.dumps(event_data, cls=SafeJSONEncoder)
```

### Cambios realizados

1. **src/infra/entrypoints/http/endpoints/manual_chat.py**:
   - Agregadas importaciones: `JSONEncoder`, `datetime`, `date`
   - Creada clase `SafeJSONEncoder` que extiende `JSONEncoder`
   - Eliminada función helper `convert_state_to_json_safe()` (ya no necesaria)
   - Actualizado `event_stream()` para usar `cls=SafeJSONEncoder` en todos los `json.dumps()`:
     - Línea ~103: Evento complete
     - Línea ~110: Evento node_update
     - Línea ~118: Evento error (timeout)
     - Línea ~125: Evento error (exception)

2. **tests/infra/entrypoints/http/test_manual_chat_workflow.py**:
   - Agregado test `test_complete_event_with_datetime_serializes()`
   - Valida que `datetime` y `date` se convierten a ISO format
   - Valida que `datetime` dentro de dicts anidados también se serializa correctamente

### Tests nuevos

**`test_complete_event_with_datetime_serializes()`**:
- Crea un evento complete con `datetime` y `date` en el result
- Valida serialización exitosa (HTTP 200)
- Verifica que `datetime` → ISO format string
- Verifica que `date` → ISO format string
- Valida que `datetime` dentro de dicts anidados se serializa correctamente

### Resultados
- Test nuevo PASA ✓
- Todos 127 tests del suite PASAN ✓ (fue 126, ahora 127)
- No hay regresiones

### Ventajas sobre la solución anterior
1. **Automático**: No requiere pre-procesar la estructura antes de serializar
2. **Centralizado**: Un único lugar donde manejar conversiones
3. **Mantenible**: Agregar nuevos tipos es trivial (solo extender `default()`)
4. **Transparente**: El código que emite eventos no necesita conocer sobre serialización
5. **Correcto**: Maneja todos los tipos que JSON no soporta nátivamente

## Robust Enum Handling

### Problema
Error al serializar eventos con objetos Enum (ej: `ChangeType`):
```
ERROR: Object of type ChangeType is not JSON serializable
```

Los enums son tipos comunes en aplicaciones Python para representar valores discretos (estados, tipos de cambios, etc.), pero JSON no los soporta nativamente.

### Solución implementada
Se mejoró `SafeJSONEncoder` en `manual_chat.py` para manejar Enum:

1. **Importación de Enum**: Se agregó `from enum import Enum`

2. **Conversión de Enum a valor**:
   - Se agregó verificación `isinstance(obj, Enum)` 
   - Se retorna `obj.value` para obtener el valor del enum
   - Se coloca antes del fallback genérico

3. **Fallback genérico mejorado**:
   - Para tipos desconocidos no soportados, se intenta convertir a string con `str(obj)`
   - Si falla incluso eso, retorna `None`
   - Esto previene que la serialización se rompa con tipos inesperados

4. **Orden de verificaciones en `default()`**:
   - `UUID` (conversión a string)
   - `datetime, date` (conversión a ISO format)
   - `Enum` (conversión a .value) ← NUEVO
   - `BaseModel` (conversión a dict vía model_dump())
   - Fallback genérico: `str(obj)` con try/except ← MEJORADO

### Cambios realizados

**src/infra/entrypoints/http/endpoints/manual_chat.py**:
```python
from enum import Enum  # NUEVO

class SafeJSONEncoder(JSONEncoder):
    """Custom JSON encoder que maneja UUID, datetime, date, Enum, y Pydantic BaseModel."""

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Enum):  # NUEVO
            return obj.value
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        try:  # MEJORADO con fallback genérico
            return str(obj)
        except Exception:
            return None
```

### Test nuevo
**`test_complete_event_with_enum_serializes()`**:
- Crea un Enum `ChangeType` con valores "added", "modified", "deleted"
- Emite evento `complete` con Enum en la raíz del result y dentro de listas
- Valida que serialización a JSON es exitosa (HTTP 200)
- Verifica que Enum se convierte a su .value (string)
- Valida que Enum dentro de estructuras anidadas (listas) también se serializa correctamente

### Resultados
- Test nuevo PASA ✓
- Todos 128 tests del suite PASAN ✓ (fue 127, ahora 128)
- No hay regresiones

### Cobertura completa
El `SafeJSONEncoder` ahora maneja automáticamente:
- **UUID** → string (`test_complete_event_with_uuid_serializes`)
- **Pydantic BaseModel** → dict (`test_complete_event_with_pydantic_model_serializes`)
- **datetime / date** → ISO format string (`test_complete_event_with_datetime_serializes`)
- **Enum** → `.value` (`test_complete_event_with_enum_serializes`) ← NUEVO
- **Tipos mixtos anidados** → manejo recursivo (`test_complete_event_with_mixed_serializable_types`)
- **Tipos desconocidos** → fallback a string o `None` ← MEJORADO

## Conclusión

La refactorización está completa y verificada. La estructura de eventos es ahora más clara semánticamente:
- `status` indica el estado de la ejecución (error, in_progress, success)
- `result` está presente solo cuando el estado es final y exitoso
- `node` indica dónde estaba la ejecución cuando se emitió el evento
- **UUID se serializa correctamente a string en JSON**
- **Objetos Pydantic se serializan correctamente a dict vía model_dump()**
- **datetime y date se serializan correctamente a ISO format**
- **Enum se serializa correctamente a su valor (.value)**
- **Tipos desconocidos tienen fallback seguro a string o None**

Todos los acceptance criteria están cubiertos por tests concretos que validan la estructura correcta.

Se implementó un `SafeJSONEncoder` personalizado que maneja automáticamente la serialización de tipos no nativos de JSON, con manejo robusto de Enum y fallback genérico para tipos inesperados.
