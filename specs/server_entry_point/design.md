# Design: server_entry_point

## Arquitectura General

El punto de entrada del servidor Guardian sigue la arquitectura hexagonal definida en `docs/architecture.md`:

- **Domain** (`./src/domain/`): Modelos de validación y contratos.
- **Infra** (`./src/infra/entrypoints/http/`): Punto de entrada HTTP con FastAPI.
- **Application** (`./src/application/`): Lógica de negocio para procesar solicitudes.

## Archivos a crear/modificar

### Nuevos archivos:
1. `src/infra/entrypoints/__init__.py` — Paquete raíz para puntos de entrada.
2. `src/infra/entrypoints/http/__init__.py` — Paquete para entrypoints HTTP.
3. `src/infra/entrypoints/http/app.py` — Aplicación FastAPI y configuración de rutas.
4. `src/infra/entrypoints/http/errors.py` — Excepciones y manejadores de errores HTTP.
5. `src/infra/entrypoints/http/middleware.py` — Middleware para validación de API Key.
6. `src/main.py` — Script de entrada para ejecutar el servidor.

### Archivos existentes a modificar:
1. `src/__init__.py` — Exportar punto de entrada.
2. `src/infra/__init__.py` — Exportar módulo de entrypoints.

## Decisiones de diseño

### 1. Validación de API Key

**Opción elegida:** Middleware de FastAPI para validar `X-API-KEY` en todas las rutas.

**Justificación:**
- Centraliza la lógica de validación.
- Aplica automáticamente a todas las rutas sin boilerplate repetido.
- Fácil de testear y mantener.

**Alternativa descartada:** Validación en cada endpoint con Depends().
- Más flexible pero requiere repetir la lógica en múltiples endpoints.
- Dificulta cambios futuros si se necesita aplicar a nuevas rutas.

### 2. Stream de respuesta

**Opción elegida:** `StreamingResponse` de FastAPI para retornar el stream de texto "Hello, World!".

**Justificación:**
- FastAPI proporciona soporte nativo para streaming.
- Permite iterar sobre datos sin cargar todo en memoria.
- Compatible con HTTP/1.1 y HTTP/2.

### 3. Manejo de errores

**Opción elegida:** Custom exception handlers en FastAPI para mapear excepciones a respuestas HTTP.

**Justificación:**
- Coherente con convención de `docs/conventions.md`: errores explícitos.
- Centraliza la traducción de excepciones a códigos HTTP.
- Permite registrar errores con `logging`.

### 4. Configuración del servidor

**Opción elegida:** Variables de entorno (ENV_VARS) para puerto y API Key.

**Justificación:**
- Estándar en aplicaciones web modernas.
- Facilita despliegue en diferentes entornos.
- No hardcodea credenciales.

## Firmas nuevas

### FastAPI Application
```python
# src/infra/entrypoints/http/app.py
def create_app() -> FastAPI:
    """Crear y configurar la aplicación FastAPI."""
```

### Middleware
```python
# src/infra/entrypoints/http/middleware.py
async def validate_api_key(request: Request, call_next: Callable) -> Response:
    """Validar cabezera X-API-KEY antes de procesar la solicitud."""
```

### Endpoint
```python
# src/infra/entrypoints/http/app.py
@app.post("/manual-chat")
async def manual_chat(request: Request) -> StreamingResponse:
    """Endpoint que retorna un stream de texto 'Hello, World!'."""
```

## Excepciones

Se crearán dos excepciones HTTP personalizadas en `src/infra/entrypoints/http/errors.py`:

1. `APIKeyMissingError` — Cuando falta la cabezera `X-API-KEY`.
2. `APIKeyInvalidError` — Cuando el valor de `X-API-KEY` no coincide con `GUARDIAN_API_KEY`.

Ambas heredan de `AgenticError` (conforme a `docs/conventions.md`).

## Rutas iniciales

- `POST /manual-chat` — Retorna stream con "Hello, World!".

Futuras rutas podrán agregarse al mismo servidor sin cambiar la estructura.

## Configuración de entorno

Se requieren dos variables de entorno:

1. `GUARDIAN_API_KEY` — Clave de API para validar solicitudes.
2. `SERVER_PORT` (opcional, por defecto: 8000) — Puerto en el que escucha el servidor.

## Inyección de dependencias

La inyección de dependencias se configura en `src/infra/helper/` según lo indicado en `docs/architecture.md`. Aquí se instancia la aplicación FastAPI.
