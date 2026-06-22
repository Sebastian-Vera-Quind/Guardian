# Requirements: loader_node

## Overview

El nodo inicial (`loader_node`) del workflow LangGraph debe orquestar la carga de datos para procesamiento posterior. El nodo actúa como puerta de entrada que determina la ruta del procesamiento (via archivos locales o clonación de repositorio), sanitiza contenido, y captura metadatos necesarios para análisis.

El nodo recibe dos posibles fuentes de entrada: `files_content[]` (archivos con contenido inline) o `repository` (metadatos para clonar un repo). La decisión de ruta se basará en prioridad explícita y se reflejará en el atributo `load_to` del estado. El nodo es responsable de sanitizar, contar líneas, extraer atribuciones de IA, y escribir metadatos en el estado del workflow.

## Entradas

El nodo recibe estado del workflow (`AgentState`) con potencialmente presentes:
- `files_content`: Lista de objetos con estructura `{"path": str, "content": str, "extension": str}`
- `repository`: Diccionario con estructura `{"url": str, "installation": str, "commit_sha": str, "target": str}`

## Salidas

El nodo escribe en el estado del workflow:
- `load_to`: `"simple"` (archivos) o `"clone"` (repositorio)
- `files_content` (si input simple): sanitizado, sin líneas en blanco
- `total_lines` (si input simple): cantidad de líneas de código
- `metadata` (si input clone): objeto con `owner`, `author_name`, `commit_message`, `repo_name`
- `ai_attribution_jsonl` (si presente `.devcore-attribution.jsonl`): contenido en formato JSONL validado

## Requirements

### R1
El sistema DEBE procesar el atributo `files_content[]` presente en el estado del workflow y determinar que la ruta de carga es `"simple"` cuando SOLO `files_content[]` está presente.

### R2
El sistema DEBE procesar el atributo `repository` presente en el estado del workflow y determinar que la ruta de carga es `"clone"` cuando SOLO `repository` está presente.

### R3
SI tanto `files_content[]` COMO `repository` están presentes en el estado, ENTONCES el sistema DEBE establecer `load_to = "clone"` dando prioridad a la ruta de repositorio sobre la ruta de archivos.

### R4
CUANDO `load_to` es `"simple"` (vía `files_content[]`), el sistema DEBE iterar cada archivo en `files_content[]` y eliminar líneas en blanco (líneas que contengan solo espacios o tabulaciones).

### R5
CUANDO `load_to` es `"simple"` (vía `files_content[]`), el sistema DEBE eliminar del atributo `files_content[]` todo archivo cuyo contenido sanitizado no contenga ninguna línea de código (archivos vacíos o solo comentarios/espacios).

### R6
CUANDO `load_to` es `"simple"` (vía `files_content[]`), el sistema DEBE contar el número total de líneas de código en todos los archivos sanitizados y escribir este valor en el estado como atributo `total_lines` (entero >= 0).

### R7
CUANDO `load_to` es `"clone"` (vía `repository`), el sistema DEBE extraer e escribir en el estado los metadatos: `owner` (propietario del repo), `author_name` (autor del commit), `commit_message` (mensaje del commit), y `repo_name` (nombre del repositorio) en un objeto `metadata` que cumpla el contrato `RepositoryMetadata`.

### R8
SI un archivo en `files_content[]` tiene nombre exacto `.devcore-attribution.jsonl`, ENTONCES el sistema DEBE extraerlo de la lista, validar que su contenido sea un JSONL válido (líneas separadas por `\n` donde cada línea es un JSON válido), y escribir el contenido en el estado como atributo `ai_attribution_jsonl` (string).

### R9
SI un archivo `.devcore-attribution.jsonl` está presente PERO su contenido no es JSONL válido, ENTONCES el sistema DEBE registrar un error (nivel WARNING) y NO escribir el atributo `ai_attribution_jsonl`.

### R10
El sistema DEBE pasar el atributo `files_content[]` sanitizado al siguiente nodo del workflow (cuando ruta es `"simple"`) sin adicionales transformaciones fuera de lo especificado en R4 y R5.

### R11
El sistema DEBE pasar el atributo `repository` sin modificación al siguiente nodo (cuando ruta es `"clone"`).

### R12
SI no están presentes ni `files_content[]` ni `repository` en el estado, ENTONCES el sistema DEBE registrar un error (nivel ERROR) y lanzar una excepción `LoaderNodeError`.

### R13
El nodo DEBE decorarse con `@with_logging()` conforme a `src/infra/adapters/workflow/log.py` para asegurar trazabilidad de cada decisión (ruta elegida, sanitización, extracción de metadatos).
