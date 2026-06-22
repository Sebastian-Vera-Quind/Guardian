# Requirements: server_entry_point

## Overview

El sistema Guardian necesita un punto de entrada para recibir solicitudes HTTP desde clientes externos. Este punto de entrada debe:

- Ser implementado con FastAPI.
- Recibir solicitudes HTTP y enrutarlas a los módulos correspondientes.
- Validar credenciales antes de procesar solicitudes.
- Servir un endpoint `/manual-chat` que retorne un stream de texto.

## Requirements

### R1
El sistema DEBE utilizar FastAPI como framework web para exponer la API HTTP.

### R2
El sistema DEBE ser capaz de recibir solicitudes HTTP GET y POST.

### R3
CUANDO se realiza una solicitud al endpoint `POST /manual-chat`, el sistema DEBE retornar un stream de texto.

### R4
CUANDO se realiza una solicitud al endpoint `POST /manual-chat`, SI la cabezera `X-API-KEY` no está presente ENTONCES el sistema DEBE rechazar la solicitud y retornar un código de estado HTTP 401 Unauthorized.

### R5
CUANDO se realiza una solicitud al endpoint `POST /manual-chat`, SI la cabezera `X-API-KEY` está presente PERO su valor es diferente al valor de la variable de entorno `GUARDIAN_API_KEY` ENTONCES el sistema DEBE rechazar la solicitud y retornar un código de estado HTTP 403 Forbidden.

### R6
CUANDO se realiza una solicitud al endpoint `POST /manual-chat` CON una cabezera `X-API-KEY` válida, el sistema DEBE retornar un stream de texto con el contenido "Hello, World!".

### R7
El servidor DEBE ser configurable para iniciar en un puerto específico (por defecto 8000).

### R8
El sistema DEBE enrutar correctamente las solicitudes entrantes a los módulos correspondientes.
