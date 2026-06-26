# Requirements: refactor_clonepath

Refactorización del nodo `clone_path` en cuatro nodos independientes con
responsabilidades desacopladas y soporte para múltiples flujos de entrada.

## R1
CUANDO se recibe `repository.url`, `repository.commit_sha` (obligatorio) y
`files_content` (obligatorio), el sistema DEBE clonar el repositorio,
hacer checkout al commit especificado, reemplazar el contenido de los
archivos indicados en `files_content`, y generar el diff y project_tree
entre los cambios realizados y el commit especificado en `commit_sha`.

## R2
CUANDO se recibe `repository.url` (obligatorio) y `files_content`
(obligatorio) sin `commit_sha` ni `target`, el sistema DEBE clonar el
repositorio, reemplazar el contenido de los archivos indicados en
`files_content`, y generar el diff y project_tree entre los cambios
realizados y el HEAD del repositorio clonado.

## R3
CUANDO se recibe `repository.url` (obligatorio), `repository.commit_sha`
(obligatorio) y `repository.target` (obligatorio) sin `files_content`,
el sistema DEBE clonar el repositorio, hacer checkout al commit
especificado en `commit_sha`, y generar el diff y project_tree entre
`commit_sha` y `target`.

## R4
CUANDO se recibe `repository.url` (obligatorio), `repository.commit_sha`
(obligatorio), `repository.target` (obligatorio) y `files_content`
(obligatorio), el sistema DEBE clonar el repositorio, hacer checkout al
commit especificado en `commit_sha`, reemplazar el contenido de los
archivos indicados en `files_content`, y generar el diff y project_tree
entre (`commit_sha` + cambios en `files_content`) y `target`.

## R5
El sistema DEBE separar el nodo monolítico `clone_path` en cuatro nodos
independientes: `clone_repository`, `checkout_commit`, `replace_files_content`,
y `generate_diff`.

## R6
El nodo `clone_repository` DEBE clonar el repositorio en un directorio
temporal bajo `/tmp/guardian/<uuid>/`, respetando la autenticación por
token si `repository.installation` está presente (repositorio privado),
y retornar la ruta absoluta del directorio clonado.

## R7
El nodo `checkout_commit` DEBE hacer checkout al commit especificado en
`repository.commit_sha` en la ruta del repositorio clonado, o lanzar una
excepción si el commit no existe.

## R8
El nodo `replace_files_content` DEBE reemplazar el contenido de cada
archivo en `files_content` dentro del repositorio clonado, creando el
archivo si no existe, y preservando la estructura de directorios.

## R9
El nodo `generate_diff` DEBE generar un diff en formato JSON entre dos
puntos de comparación (base y target), con la estructura especificada,
incluyendo información de adiciones, eliminaciones, estado de cambio
línea por línea, así como el árbol del proyecto.

## R10
El nodo `generate_diff` DEBE respetar las reglas de `.aiignore` si está
presente en el repositorio, excluyendo archivos que coincidan con dichas
reglas del diff y el project_tree.

## R11
El nodo `generate_diff` DEBE omitir archivos binarios que no sean de
código (imágenes, videos, markdown, lock files, etc.) del diff y
project_tree.

## R12
El nodo `generate_diff` DEBE incluir un atributo `is_modified` en cada
archivo del project_tree, indicando `true` si el archivo ha sido
modificado en el diff, y `false` si no ha sido modificado.

## R13
El workflow DEBE incluir conditional edges que dirijan el flujo a los
nodos apropiados según la presencia/ausencia de `files_content`,
`commit_sha` y `target` en el estado.

## R14
El workflow DEBE transicionar secuencialmente desde `loader` a
`clone_repository`, y de ahí ramificar a los nodos subsecuentes según
el caso de entrada (R1-R4).

## R15
El contrato `CloneService` en `src/domain/ports/input/clone/clone_service.py`
DEBE fragmentarse en al menos cuatro métodos especializados,
desligando responsabilidades de clonación, checkout, reemplazo de archivos
y generación de diff.

## R16
La implementación actual de `CloneService` en
`src/application/clone/clone_service.py` DEBE refactorizarse para
delegar operaciones a los servicios especializados que soporten los
nodos independientes.

## R17
SI se produce un error durante clonación, checkout, reemplazo de archivos
o generación de diff, el sistema DEBE lanzar una excepción nombrada
específica (`ClonePathError`, `CheckoutError`, `DiffGenerationError`,
`GitOperationError`) documentando la naturaleza del fallo.

## R18
Cada nodo DEBE estar decorado con `@with_logging()` según la convención
establecida en `src/infra/adapters/workflow/log.py`, permitiendo
trazabilidad y auditoría del flujo de ejecución.

## R19
El nodo del loader DEBE detectar cuál de los cuatro casos de entrada
se corresponde y establecer flags condicionales en el estado para que
el workflow pueda enrutar correctamente.

## R20
MIENTRAS el workflow ejecute los nodos refactorizados, cada nodo DEBE
mantener la interfaz estándar `async def node_<name>(state: AgentState) -> AgentState`
y respetar la estructura de entrada/salida del `AgentState`.
