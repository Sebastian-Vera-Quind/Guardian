# Design: workflow_start

## Arquitectura General

La integración de workflow en Guardian se construye sobre la arquitectura hexagonal existente, **usando LangGraph StateGraph como motor de grafo**:

- **Domain** (`./domain/models/`): Define contrato `WorkflowInput`, evento `WorkflowEvent`, estado `WorkflowState`.
- **Domain Ports** (`./domain/ports/`): Define protocolo `WorkflowExecutor`.
- **Application** (`./application/usecases/`): Contiene `WorkflowUseCase` para orquestar ejecución.
- **Infra Adapter** (`./infra/adapters/workflow/`): Implementa `WorkflowBuilder` que construye un `StateGraph` con nodos y transiciones, y `WorkflowEngine` que ejecuta el grafo.
- **Infra HTTP** (`./infra/entrypoints/http/app.py`): Integra workflow en endpoint `/manual-chat`, usando streaming de eventos del grafo.

## Archivos a crear/modificar

### Nuevos archivos:

1. `domain/models/workflow.py` — Define `WorkflowInput` (contrato base), `WorkflowEvent`, `WorkflowState` (TypedDict para StateGraph).
2. `domain/ports/workflow_executor.py` — Define protocolo `WorkflowExecutor`.
3. `infra/adapters/workflow/builder.py` — Clase `WorkflowBuilder` que construye un StateGraph con nodos y transiciones.
4. `infra/adapters/workflow/engine.py` — Clase `WorkflowEngine` que ejecuta el StateGraph e itera eventos con streaming.
5. `infra/adapters/workflow/nodes.py` — Nodos de base: entrada, procesamiento, finalización. Cada nodo es una función que modifica el estado.
6. `infra/entrypoints/http/errors.py` — Añade excepciones de validación de workflow.

### Archivos existentes a modificar:

1. `infra/entrypoints/http/app.py` — Reemplaza endpoint `/manual-chat` para crear StateGraph, ejecutar engine, y streamear eventos.
2. `domain/models/__init__.py` — Exporta `WorkflowInput`, `WorkflowEvent`, `WorkflowState`.
3. `domain/ports/__init__.py` — Exporta `WorkflowExecutor`.
4. `infra/adapters/workflow/__init__.py` — Exporta `WorkflowBuilder`, `WorkflowEngine`.

## Decisiones de diseño

### 0. Elección de LangGraph como motor de grafo (R13, R14, R15, R16)

**Opción elegida:** LangGraph `StateGraph` para orquestar nodos y transiciones.

```python
from langgraph.graph import StateGraph
from typing_extensions import TypedDict

class WorkflowState(TypedDict):
    user_input: str
    processing_state: str  # "pending", "processing", "done", "failed"
    current_node: str
    result: dict | None
    errors: list[str]

graph = StateGraph(WorkflowState)
# Añadir nodos:
graph.add_node("start", node_start)
graph.add_node("process", node_process)
graph.add_node("end", node_end)
# Definir transiciones:
graph.add_edge("start", "process")
graph.add_conditional_edges("process", route_next, {"end": "end"})
```

**Justificación:**
- LangGraph proporciona estado tipado, nodos, transiciones condicionales.
- `event_mode=True` en `StreamEvents` permite streamear estado en tiempo real.
- Grafo dirigido acíclico (DAG) nativo facilita dependencias entre nodos.
- Integración con LLMs y agentes es directa.

**Alternativa descartada:** Máquina de estados FSM simple o motor custom.
- FSM es rígida, LangGraph es flexible y soporta DAG dinámico.
- Motor custom añade overhead de mantenimiento sin valor.

### 1. Contrato de entrada (WorkflowInput)

**Opción elegida:** Clase abstracta en `domain/models/workflow.py` que el desarrollador hereda.

```python
from pydantic import BaseModel

class WorkflowInput(BaseModel):
    """Contrato base. El desarrollador hereda y especifica campos."""
    class Config:
        extra = "forbid"
```

**Justificación:**
- Pydantic proporciona validación automática.
- Flexible: cada endpoint puede tener su propio contrato.
- Coherente con la arquitectura existente.

**Alternativa descartada:** Esquema JSON dinámico sin validación.
- Complica testing y documentación.
- Dificulta detección de errores tempranos.

### 2. Ejecución de nodos en LangGraph (R14, R15)

**Opción elegida:** Nodos como funciones `async` que reciben `WorkflowState` y retornan actualizaciones de estado.

```python
async def node_start(state: WorkflowState) -> dict:
    """Nodo inicial: valida entrada y prepara estado."""
    state["processing_state"] = "processing"
    state["current_node"] = "start"
    return {"processing_state": "processing", "current_node": "start"}

async def node_process(state: WorkflowState) -> dict:
    """Nodo de procesamiento: ejecuta lógica de negocio."""
    state["current_node"] = "process"
    state["result"] = {"data": "processed"}
    state["processing_state"] = "done"
    return {"current_node": "process", "result": state["result"]}

async def node_end(state: WorkflowState) -> dict:
    """Nodo final: retorna resultado."""
    state["current_node"] = "end"
    return {"current_node": "end"}
```

**Justificación:**
- Funciones puras son más fáciles de testear que clases.
- LangGraph espera funciones con firma `(state) -> dict | None`.
- Retornar `dict` actualiza el estado automáticamente.
- Compatible con async/await.

### 3. Streaming de eventos con LangGraph (R16)

**Opción elegida:** Usar `graph.stream()` con `mode="updates"` o `"values"` para emitir eventos en tiempo real.

```python
async def stream_workflow_events(graph: StateGraph, input_data: WorkflowState):
    """Itera eventos del grafo y emite como JSONL."""
    async for event in graph.astream(input_data):
        # event es (node_id, node_output)
        node_id, output = event
        payload = {
            "event_type": "node_updated",
            "node": node_id,
            "data": output
        }
        yield json.dumps(payload) + "\n"
```

Alternativa (más granular):

```python
async for event in graph.astream_events(input_data, config={"recursion_limit": 25}):
    if event["event"] == "on_chain_end":
        payload = {
            "event_type": event["event"],
            "node": event.get("name"),
            "data": event.get("data", {})
        }
        yield json.dumps(payload) + "\n"
```

**Justificación:**
- `astream()` es simple y eficiente, emite una tupla por nodo.
- `astream_events()` es granular, permite capturar eventos intermedios.
- FastAPI maneja ambos nativamente como iterables async.
- Eventos se envían sin buffering; cliente recibe en tiempo real.
- Compatible con clientes que leen streaming.

### 4. Validación de entrada

**Opción elegida:** Pydantic en `WorkflowInput`. El endpoint captura excepciones.

```python
try:
    input_data = WorkflowInput(**request_body)
except ValidationError as e:
    return JSONResponse(status_code=400, content={"detail": str(e)})
```

**Justificación:**
- Coherente con `docs/conventions.md`: errores explícitos.
- Mensajes claros y específicos.
- Centralizado en un lugar.

### 5. Orquestación y DAG

**Opción elegida:** Motor de workflow que:
- Mantiene diccionario de estado mutable.
- Ordena nodos topológicamente.
- Ejecuta nodos secuencialmente (futuro: paralelo).
- Emite eventos de transición.

**Justificación:**
- Separa orquestación de lógica de nodos.
- Facilita testing por separado.
- Permite extensión a ejecución paralela.

## Firmas nuevas

### Domain Models

```python
# domain/models/workflow.py
from pydantic import BaseModel
from typing_extensions import TypedDict

class WorkflowInput(BaseModel):
    """Contrato base para entrada del workflow."""
    pass

class WorkflowState(TypedDict):
    """Estado del StateGraph. Tipado estrictamente."""
    user_input: str
    processing_state: str  # "pending", "processing", "done", "failed"
    current_node: str
    result: dict | None
    errors: list[str]

class WorkflowEvent(TypedDict):
    """Evento emitido durante ejecución del grafo."""
    event_type: str  # "node_updated", "error", "completed"
    node: str
    data: dict  # Salida del nodo
```

### Domain Ports

```python
# domain/ports/workflow_executor.py
from typing import Protocol, AsyncGenerator
from langgraph.graph import StateGraph

class WorkflowExecutor(Protocol):
    """Protocolo para ejecutar workflows (StateGraph)."""
    
    graph: StateGraph
    
    async def execute_and_stream(
        self, input_data: WorkflowState
    ) -> AsyncGenerator[WorkflowEvent, None]:
        """Ejecuta grafo e itera eventos."""
        ...
```

### Infra Adapter

```python
# infra/adapters/workflow/builder.py
from langgraph.graph import StateGraph
from infra.adapters.workflow.nodes import node_start, node_process, node_end

class WorkflowBuilder:
    """Construye un StateGraph con nodos y transiciones."""
    
    def build(self) -> StateGraph:
        """Retorna StateGraph completamente configurado."""
        graph = StateGraph(WorkflowState)
        graph.add_node("start", node_start)
        graph.add_node("process", node_process)
        graph.add_node("end", node_end)
        
        graph.add_edge("start", "process")
        graph.add_edge("process", "end")
        
        graph.set_entry_point("start")
        graph.set_finish_point("end")
        
        return graph.compile()

# infra/adapters/workflow/engine.py
class WorkflowEngine(WorkflowExecutor):
    """Motor que ejecuta StateGraph con streaming."""
    
    def __init__(self, graph: StateGraph):
        self.graph = graph
    
    async def execute_and_stream(
        self, input_data: WorkflowState
    ) -> AsyncGenerator[WorkflowEvent, None]:
        """Ejecuta grafo e itera eventos con astream()."""
        async for node_id, output in self.graph.astream(input_data):
            yield {
                "event_type": "node_updated",
                "node": node_id,
                "data": output
            }

# infra/adapters/workflow/nodes.py
async def node_start(state: WorkflowState) -> dict:
    """Nodo inicial: valida entrada."""
    return {"processing_state": "processing", "current_node": "start"}

async def node_process(state: WorkflowState) -> dict:
    """Nodo de procesamiento: ejecuta lógica."""
    result = {"processed": True}
    return {"current_node": "process", "result": result, "processing_state": "done"}

async def node_end(state: WorkflowState) -> dict:
    """Nodo final."""
    return {"current_node": "end"}
```

### Infra HTTP

```python
# infra/entrypoints/http/app.py (modificado)
from infra.adapters.workflow.builder import WorkflowBuilder
from infra.adapters.workflow.engine import WorkflowEngine

@app.post("/manual-chat")
async def manual_chat(request: Request) -> StreamingResponse:
    """Endpoint que ejecuta StateGraph y retorna stream."""
    body = await request.json()
    input_data = WorkflowInput(**body)
    
    builder = WorkflowBuilder()
    graph = builder.build()
    engine = WorkflowEngine(graph)
    
    async def event_generator():
        async for event in engine.execute_and_stream({
            "user_input": input_data.user_input,
            "processing_state": "pending",
            "current_node": "",
            "result": None,
            "errors": []
        }):
            yield json.dumps(event) + "\n"
    
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
```

## Excepciones

Se añaden en `infra/entrypoints/http/errors.py`:

1. `WorkflowValidationError(AgenticError)` — JSON no cumple contrato.
2. `WorkflowExecutionError(AgenticError)` — Nodo falla durante ejecución.

Ambas heredan de `AgenticError` conforme a `docs/conventions.md`.

## Extensión: Nuevos Nodos

Desarrollador define nodo personalizado:

```python
from infra.adapters.workflow import WorkflowNode

class MiNodo(WorkflowNode):
    node_id = "mi-nodo"
    
    async def execute(self, state: dict) -> None:
        state["resultado"] = "valor"
```

Registra en motor:

```python
engine = WorkflowEngine(nodes=[MiNodo(), OtroNodo()])
```

## Integración con FastAPI

El endpoint `/manual-chat` realiza los siguientes pasos:

1. Recibe body JSON y lo valida contra `WorkflowInput`.
2. Crea un `WorkflowBuilder` y lo compila a `StateGraph`.
3. Instancia `WorkflowEngine` con el grafo.
4. Llama `engine.execute_and_stream(initial_state)`.
5. Itera eventos del engine y los emite como JSONL en tiempo real.
6. Cliente recibe stream de eventos, cada línea es un JSON con `{event_type, node, data}`.

Ejemplo de evento emitido:
```json
{"event_type": "node_updated", "node": "start", "data": {"processing_state": "processing", "current_node": "start"}}
{"event_type": "node_updated", "node": "process", "data": {"current_node": "process", "result": {...}, "processing_state": "done"}}
{"event_type": "node_updated", "node": "end", "data": {"current_node": "end"}}
```

## Alternativa descartada: Motor custom sin LangGraph

Se consideró build custom del motor. Se descartó porque:
- LangGraph ya es estable, testeado y usado en producción.
- Implementar StateGraph, DAG, streaming desde cero es overhead innecesario.
- LangGraph es la referencia estándar en la comunidad de LLMs/agents.
