# Requirements: clone_path

## Overview

El nodo `clone_path` del workflow LangGraph clona repositorios de GitHub en una ubicación temporal, efectúa checkout a un commit específico, y genera análisis de diferencias entre commits cuando es requerido. El nodo es responsable de autenticar con GitHub para repositorios privados, clonar en `/tmp/guardian/` con UUID único, y producir una proyección del árbol de archivos respetando exclusiones de `.aiignore`.

El nodo recibe estado del workflow con `load_to="clone"`, `repository` (metadatos), y opcionalmente `target` (rama/commit comparación). Produce `clone_path` (ruta local), `diff` (cambios línea por línea), `modified_lines` (cantidad), y `project_tree` (estructura jerárquica).

## Entradas

El nodo recibe estado del workflow (`AgentState`) con presentes:
- `load_to`: debe ser `"clone"` (determinado por `loader_node`)
- `repository`: diccionario con estructura `{"url": str, "installation": Optional[str], "commit_sha": str, "target": str}`
- `metadata`: objeto con `owner`, `repo_name`, `branch`, `commit_sha` (populado por `loader_node`)

## Salidas

El nodo escribe en el estado del workflow:
- `clone_path`: ruta absoluta al directorio clonado (p. ej. `/tmp/guardian/<uuid>/`)
- `diff`: (opcional) lista de cambios línea por línea entre `commit_sha` y `target` (respetando `.aiignore`)
- `modified_lines`: cantidad total de líneas modificadas en el diff
- `project_tree`: árbol jerárquico de directorios y archivos del repositorio clonado (excluyendo binarios, imágenes, markdown, lock files)

## Requirements

### R1
CUANDO `load_to="clone"` ENTONCES el sistema DEBE clonar el repositorio especificado en `repository.url` en un directorio temporal bajo `/tmp/guardian/` con nombre de directorio UUID único (v4), y escribir la ruta absoluta en `clone_path`.

### R2
SI `repository.installation` está presente (indicando repositorio privado) ENTONCES el sistema DEBE usar el valor de `installation` como token GitHub para autenticarse durante la clonación.

### R3
SI `repository.installation` está ausente (indicando repositorio público) ENTONCES el sistema DEBE clonar sin autenticación.

### R4
CUANDO la clonación es exitosa, el sistema DEBE hacer checkout al commit especificado en `commit_sha` del estado.

### R5
SI `target` está especificado en `repository` (p. ej. una rama o commit diferente al de `commit_sha`) ENTONCES el sistema DEBE generar un diff JSON comparando `commit_sha` (base) contra `target` (rama/commit de comparación), respetando reglas de exclusión de `.aiignore` si existe, y escribir el resultado en el estado como atributo `diff`.

### R6
El diff JSON DEBE tener la estructura especificada:
```json
[
  {
    "/path/to/file": {
      "additions": int,
      "deletions": int,
      "content": [
        {
          "status": "added" | "modified" | "deleted",
          "line_number": int,
          "content": str
        }
      ]
    }
  }
]
```
donde `additions` es cantidad de líneas añadidas, `deletions` es cantidad de líneas eliminadas, `content` es lista de cambios línea por línea con status (`added`, `modified`, `deleted`), número de línea, y contenido de la línea.

### R7
SI existe un archivo `.aiignore` en la raíz del repositorio clonado, el sistema DEBE parsear las reglas de exclusión (formato gitignore standard) y NO incluir archivos que coincidan con esas reglas en el diff JSON.

### R8
El sistema DEBE escribir en el estado un atributo `modified_lines` (entero >= 0) que contenga la cantidad total de líneas modificadas (adiciones + eliminaciones) en el diff.

### R9
El sistema DEBE generar un atributo `project_tree` que sea un árbol jerárquico de directorios y archivos del repositorio clonado, con la siguiente estructura:
```json
{
  "name": "root",
  "type": "directory",
  "children": [
    {
      "name": "file1.py",
      "type": "file"
    },
    {
      "name": "subdir",
      "type": "directory",
      "children": [
        {
          "name": "file2.py",
          "type": "file",
          "is_new": true
        }
      ]
    }
  ]
}
```
donde `name` es el nombre del archivo/directorio, `type` es `"file"` o `"directory"`, `children` (opcional) lista subcarpetas/archivos, e `is_new` (opcional, booleano) marca archivos nuevos en el diff.

### R10
El sistema DEBE excluir del `project_tree` Y del `diff` archivos binarios que no sean código (imágenes: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`; vídeos: `.mp4`, `.avi`, `.mkv`, `.mov`; markdown: `.md`; lock files: `package-lock.json`, `yarn.lock`, `Pipfile.lock`, `poetry.lock`, `*.lock`, etc.) y otros artefactos no esenciales.

### R11
MIENTRAS se genera el `project_tree`, el sistema DEBE marcar con `"is_new": true` los archivos que fueron añadidos en el diff (status `"added"`).

### R12
SI la clonación falla (p. ej. URL inválida, autenticación rechazada, red no disponible), el sistema DEBE registrar un error (nivel ERROR) y lanzar una excepción `ClonePathError`.

### R13
SI el checkout al `commit_sha` falla (p. ej. commit no existe), el sistema DEBE registrar un error (nivel ERROR) y lanzar una excepción `ClonePathError`.

### R14
SI la generación del diff falla (p. ej. `target` no existe o commit especificado no es válido), el sistema DEBE registrar un error (nivel ERROR) y lanzar una excepción `DiffGenerationError`.

### R15
El nodo DEBE decorarse con `@with_logging()` conforme a `src/infra/adapters/workflow/log.py` para asegurar trazabilidad de cada operación (clonación, checkout, diff generación).

### R16
El sistema DEBE limpiar correctamente el directorio temporal (via context manager o similar) en caso de error durante clonación, para evitar acumulación de directorios huérfanos en `/tmp/guardian/`.

### R17
SI no está presente `load_to="clone"` en el estado (indicando que este nodo fue invocado incorrectamente), el sistema DEBE registrar un error (nivel ERROR) y lanzar una excepción `ClonePathError`.

### R18
El nodo DEBE inyectar todas sus dependencias (clonador de repositorio, generador de diff) vía el patrón de inyección definido en `src/infra/helper/` (usando `inject()` o abstractos en `domain/ports/`), y NO DEBE instanciar directamente clases de `infra/adapters/` o `application/`.
