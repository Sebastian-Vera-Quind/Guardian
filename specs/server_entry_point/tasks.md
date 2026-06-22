# Tasks: server_entry_point

## Implementation Checklist

- [ ] T1 — Crear estructura de paquetes `src/infra/entrypoints/http/`. Cubre: R1, R8.

- [ ] T2 — Implementar `src/infra/entrypoints/http/errors.py` con excepciones `APIKeyMissingError` y `APIKeyInvalidError`. Cubre: R4, R5.

- [ ] T3 — Implementar `src/infra/entrypoints/http/middleware.py` con middleware `validate_api_key` para validar cabezera `X-API-KEY`. Cubre: R4, R5.

- [ ] T4 — Implementar `src/infra/entrypoints/http/app.py` con función `create_app()` que retorna una instancia de FastAPI configurada. Cubre: R1, R2, R8.

- [ ] T5 — Registrar endpoint `POST /manual-chat` en `src/infra/entrypoints/http/app.py` que retorna un `StreamingResponse`. Cubre: R3, R6.

- [ ] T6 — Implementar lógica de streaming en `/manual-chat` para retornar "Hello, World!". Cubre: R6.

- [ ] T7 — Implementar `src/main.py` como punto de entrada ejecutable que inicia el servidor FastAPI. Cubre: R7.

- [ ] T8 — Configurar variables de entorno `GUARDIAN_API_KEY` y `SERVER_PORT` en `src/main.py`. Cubre: R7.

- [ ] T9 — Escribir `tests/infra/test_http_app.py` para validar que FastAPI se crea correctamente. Cubre: R1.

- [ ] T10 — Escribir test para validar que `/manual-chat` rechaza solicitudes SIN cabezera `X-API-KEY`. Cubre: R4.

- [ ] T11 — Escribir test para validar que `/manual-chat` rechaza solicitudes CON `X-API-KEY` inválida. Cubre: R5.

- [ ] T12 — Escribir test para validar que `/manual-chat` CON `X-API-KEY` válida retorna stream "Hello, World!". Cubre: R3, R6.

- [ ] T13 — Escribir test para validar que el servidor escucha en puerto configurable. Cubre: R7.

- [ ] T14 — Escribir test para validar que `/manual-chat` es accesible vía POST. Cubre: R2.

## Orden de ejecución

La ejecución debe ser secuencial dentro de cada grupo:

1. **Estructura e infraestructura** (T1–T3): Crea paquetes, errores, middleware.
2. **Punto de entrada FastAPI** (T4–T6): Crea app y endpoint.
3. **Script de ejecución** (T7–T8): Configura variables de entorno y punto de entrada.
4. **Tests** (T9–T14): Valida comportamiento con tests unitarios e integración.

## Trazabilidad

| Requirement | Tasks |
|-------------|-------|
| R1          | T1, T4, T9 |
| R2          | T4, T14 |
| R3          | T5, T6, T12 |
| R4          | T2, T3, T10 |
| R5          | T2, T3, T11 |
| R6          | T5, T6, T12 |
| R7          | T7, T8, T13 |
| R8          | T1, T4 |
