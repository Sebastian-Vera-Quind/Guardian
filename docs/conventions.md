# Convenciones de código

> Homogeneidad extrema, El codigo debe parecer el mismo en todas partes, sin importar quien lo haya escrito.

## Estilo de python
- **Versión**: Python 3.10 o superior.
- **PEP 8**: Con lineas de maximo 79 caracteres, con 2espacios por indentación, y sin espacios alrededor de los operadores de asignación.
- **Imports**: librerias standard (stdlib) primero, luego librerias de terceros (third-party), y finalmente imports locales, cada grupo separado por una línea en blanco.
- **Modulos**: Si se necesita exportar una función o clase, se debe agregar a `__init__.py` del paquete correspondiente, unicamente con las funciones o clases que se necesiten exportar, y no todo el modulo. Si no hay nada que exportar, NO DEBE EXISTIR el archivo.
- **Strings**: Commillas dobles `"..."` siempre. Se debe utilizar f-strings para formatear, nada de `.format()` o concatenación con `+`.
- **Logs**: Se debe utilizar el módulo `logging` para registrar eventos, nada de `print()`. Se deben usar los niveles de log adecuados (DEBUG, INFO, WARNING, ERROR, CRITICAL) y configurar el formato del log para incluir información relevante como timestamp y nivel de log.
- **Idioma**: El código debe estar en inglés, incluyendo nombres de variables, funciones, clases y comentarios. Esto facilita la colaboración internacional y el mantenimiento a largo plazo del código.
- **Tipado**: Se debe utilizar tipado estático con `typing` para todas las funciones y métodos, incluyendo parámetros y valores de retorno. Esto mejora la legibilidad y ayuda a detectar errores en tiempo de desarrollo. Se debe evitar al maximo el uso de `Any`, y preferir tipos más específicos. Se debe utilizar `Optional` para parámetros que pueden ser `None`, y `Union` para parámetros que pueden ser de varios tipos.

## Nombres
| **Tipo**    | **Convención** | **Ejemplo**     |
| ----------- | -------------- | --------------- |
| Modulos     | snake_case     | `mi_modulo.py`  |
| Clases      | PascalCase     | `MiClase`       |
| Funciones   | snake_case     | `mi_funcion()`  |
| Variables   | snake_case     | `mi_variable`   |
| Constantes  | UPPER_SNAKE    | `MI_CONSTANTE`  |
| Privadas    | _snake_case    | `_mi_variable`  |
| Paquetes    | snake_case     | `mi_paquete/`   |

## Test
- Un archivo de test por módulo: tests/package/test_<módulo>.py.
- Una clase Test<Cosa>(unittest.TestCase) por unidad lógica.
- Cada test usa un tempfile.TemporaryDirectory() y limpia tras de sí.
- Nombres de test descriptivos: test_load_returns_empty_when_file_missing.
- No deberia haber test sobre entidades de dominio, solo sobre casos de uso y de ser necesario sobre entidades de infraestructura (p. ej. repositorios). El dominio se prueba indirectamente a través de los casos de uso, y las entidades de dominio no deberían tener lógica compleja que necesite ser testeada directamente.

## Comentarios

Por defecto los unicos comentarios que deben existir, deben ser informativos del codigo de la historia de usuario, de otra forma solo se permiten cuando explican un por qué no obvio (p. ej. workaround documentado, invariante sutil). Los nombres deben hacer el resto.

## Errores

- Todos los errores personalizados deben heredar de `AgenticError` (definida en `domain/models/__init__.py`) para facilitar su manejo centralizado.
- En la medida de lo posible, se deben evitar los errores genéricos (`Exception`) y en su lugar definir errores específicos que describan claramente la naturaleza del problema (p. ej. `FeatureNotFoundError`, `SpecNotApprovedError`).
- Los errores personalizados se deben definir segun la capa a la que corresponda, por ejemplo errores relacionados con respuestas HTTP en `./infra/entrypoints/http/errors.py`, errores relacionados con el dominio en `./domain/models/errors.py`, etc.