# Requirements: workflow_start

## Overview

El sistema Guardian necesita la capacidad de iniciar un flujo de trabajo (workflow) en respuesta a solicitudes entrantes via el endpoint `POST /manual-chat`. Este workflow debe cumplir un contrato explícito definido en términos de entrada, nodos, transiciones de estado y salida. El cliente recibirá el progreso del workflow en tiempo real mediante un stream.

## Contrato del Workflow

Un workflow en el contexto de Guardian es una ejecución dirigida por grafo de nodos:

- **Entrada:** JSON con estructura definida para procesar solicitudes.
- **Nodo:** Unidad de procesamiento discreta.
- **Estado del Nodo:** `Error`, `InProgress`, `Done`.
- **Salida:** Server-Sent Events (SSE) stream con eventos de estado del workflow:
  - `event: keepalive` - Mantiene la conexión viva durante procesamiento largo
  - `event: node_update` - Evento cuando un nodo cambia de estado
  - `event: complete` - Flujo completado exitosamente
  - `event: error` - Error durante ejecución

## Requirements

### R1
El sistema DEBE aceptar una solicitud POST al endpoint `/manual-chat` con un body JSON.

### R2
CUANDO se recibe una solicitud POST `/manual-chat` CON un body JSON válido, el sistema DEBE instanciar un nuevo workflow e iniciar su ejecución.

### R3
El sistema DEBE retornar un stream (HTTP 200 OK, Content-Type: text/event-stream; charset=utf-8) que emite eventos de progreso del workflow.

### R4
CUANDO un nodo del workflow cambia de estado, el sistema DEBE emitir un evento al stream indicando el nodo actual y su estado (InProgress, Done, o Error).

### R5
CUANDO un nodo falla (lanza excepción), el sistema DEBE emitir un evento con estado Error y detener la ejecución del workflow.

### R6
CUANDO todos los nodos del workflow han completado exitosamente, el sistema DEBE detener el stream indicando que el workflow ha finalizado.

### R7
El sistema DEBE preservar la trazabilidad de la ejecución del workflow mediante logs INFO para transiciones y ERROR para fallos.

### R8
CUANDO se recibe una solicitud POST `/manual-chat` CON un body JSON inválido, el sistema DEBE rechazar la solicitud con código HTTP 400 Bad Request.

### R9
El sistema DEBE definir explícitamente el contrato de entrada del workflow. Este contrato DEBE especificar qué campos son obligatorios y cuáles opcionales.

### R10
El sistema DEBE integrar el workflow con la estructura existente de `infra/entrypoints/http/app.py` sin modificar el middleware de validación de API Key.

### R11
El sistema DEBE permitir al desarrollador definir nuevos nodos especificando un identificador único y la lógica de ejecución.

### R12
CUANDO un nodo depende de nodos previos, el sistema DEBE ejecutar las dependencias antes de ejecutar el nodo actual.

### R13
El workflow DEBE implementarse como un **LangGraph StateGraph** con un estado tipado que incluya al menos: `user_input`, `processing_state`, `current_node`, `result`, y `errors`.

### R14
El StateGraph DEBE tener al menos dos nodos de ejecución (además del nodo de entrada/salida): uno para procesar la solicitud inicial y otro para validar o finalizar el resultado.

### R15
El StateGraph DEBE definir transiciones entre nodos que respondan al estado actual. CUANDO un nodo completa, el sistema DEBE evaluar la siguiente transición según el estado y dirigir la ejecución al nodo correspondiente.

### R16
CUANDO el workflow se ejecuta, el sistema DEBE streamear el estado del nodo actual (node output) en tiempo real mediante el mecanismo `event_mode` de LangGraph, emitiendo eventos que incluyen: `event_type`, `node`, `data` (contenido del estado del nodo).
