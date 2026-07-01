# Requirements: prompt_builder

Servicio de construcción de prompts para el agente Guardian, con
saneamiento de contenido de entrada y renderizado de plantillas mediante
Jinja2, siguiendo la arquitectura hexagonal del repositorio.

## Overview

El sistema Guardian necesita una capa que construya los prompts que se
envían al agente a partir de:

- Un conjunto acotado de `scope`s de prompt (`checklist`, `architecture`,
  `business_rules`) definidos como enumerador en la capa de dominio.
- Atributos de entrada tipados (no `Any`), que son saneados antes de
  inyectarse en la plantilla.

La solución expone:

- Un **puerto de entrada** (`PromptBuilder`) implementado por un
  **servicio** de `application`.
- Un **puerto de salida** (`PromptRenderer`) implementado por un
  **adaptador** de `infra` que usa Jinja2.
- Un **enum de dominio** (`PromptScope`) con los scopes válidos.
- **Excepciones nombradas** que heredan de `AgenticError`.

El servicio ofrece tres capacidades: construir un prompt por `scope`,
sanear los atributos de entrada, y construir un prompt genérico a partir
de una plantilla en `string` y un diccionario de atributos.

## R1

El sistema DEBE definir un enumerador `PromptScope` en la capa de dominio
(`src/domain/models/`) con exactamente los miembros `CHECKLIST`,
`ARCHITECTURE` y `BUSINESS_RULES`, cuyos valores string sean `checklist`,
`architecture` y `business_rules` respectivamente.

## R2

El sistema DEBE definir un puerto de entrada `PromptBuilder` (protocolo
abstracto) en `src/domain/ports/input/` que declare el contrato del
servicio de construcción de prompts.

## R3

El sistema DEBE definir un puerto de salida `PromptRenderer` (protocolo
abstracto) en `src/domain/ports/output/` que declare el contrato del
adaptador que renderiza plantillas.

## R4

El sistema DEBE definir una excepción base `PromptBuilderError` que herede
de `AgenticError`, ubicada en `src/domain/models/errors/`.

## R5

CUANDO el servicio recibe un `scope` que NO es un miembro de `PromptScope`,
el sistema DEBE lanzar una excepción `UnknownPromptScopeError` que herede
de `PromptBuilderError`.

## R6

CUANDO se invoca el método de construcción por scope del servicio con un
`scope` válido de `PromptScope` y un objeto de atributos de entrada, el
sistema DEBE retornar un `string` con el prompt construido a partir de la
plantilla asociada a ese scope y los atributos provistos.

## R7

El servicio DEBE sanear el contenido de los atributos de entrada de tipo
`string` antes de construir el prompt, eliminando los caracteres de
control no imprimibles definidos en el saneador del proyecto.

## R8

El servicio DEBE sanear el contenido de los atributos de entrada de tipo
`string` eliminando las líneas en blanco (líneas cuyo contenido sea vacío
o compuesto solo por espacios) antes de construir el prompt.

## R9

El sistema DEBE exponer en el servicio un método público de saneamiento
que reciba un `string` y retorne el `string` saneado según R7 y R8, de
forma que el saneamiento sea invocable de manera independiente a la
construcción de prompts.

## R10

El sistema DEBE exponer en el servicio un método genérico de construcción
que reciba una plantilla como `string` y un diccionario de atributos, y
retorne el `string` del prompt construido renderizando la plantilla con
esos atributos.

## R11

CUANDO se invoca el método genérico de construcción (R10), el sistema DEBE
sanear (según R7 y R8) los valores de tipo `string` del diccionario de
atributos antes de renderizar la plantilla.

## R12

El adaptador `PromptRenderer` DEBE utilizar Jinja2 para renderizar las
plantillas a partir de un `string` de plantilla y un diccionario de
atributos.

## R13

El adaptador DEBE exponer un método genérico que reciba un `scope`
(`PromptScope`) y un diccionario de atributos, resuelva la plantilla
asociada al scope, y retorne el `string` del prompt renderizado.

## R14

SI la plantilla provista al adaptador contiene una sintaxis Jinja2
inválida o hace referencia a construcciones no resolubles ENTONCES el
sistema DEBE lanzar una excepción `PromptRenderError` que herede de
`PromptBuilderError`, sin propagar la excepción interna de Jinja2 tal cual.

## R15

El sistema DEBE registrar el servicio `PromptBuilder` como puerto de
entrada inyectable en `src/infra/helper/usecase_injector.py` y el adaptador
`PromptRenderer` como puerto de salida inyectable en
`src/infra/helper/adapter_injector.py`, siguiendo el patrón de inyección
existente.

## R16

El sistema DEBE estar completamente tipado con type hints, sin usar `Any`,
usando tipos concretos para los atributos de entrada conforme a
`docs/conventions.md`.

## R17

El sistema DEBE usar `logging` (nivel DEBUG para construcción, WARNING/ERROR
para fallos de renderizado) y NO DEBE usar `print()`, conforme a
`docs/conventions.md`.

## R18

El sistema NO DEBE definir lógica de renderizado con Jinja2 dentro de la
capa `application`; el servicio DEBE delegar la construcción al adaptador
`PromptRenderer` a través del puerto de salida.
