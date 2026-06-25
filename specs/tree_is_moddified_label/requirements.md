# Feature 6: tree_is_moddified_label
## Requirements

### R1: Actualizar estructura del project_tree para incluir is_modified
El project_tree debe incluir un atributo `is_modified` en cada archivo que indique si ha sido modificado en el diff.

### R2: is_modified es un booleano
El atributo `is_modified` debe ser de tipo booleano (true/false).

### R3: is_modified=true para archivos modificados
Un archivo debe tener `is_modified=true` si aparece en el diff y ha sido modificado (no es nuevo, no es eliminado).

### R4: is_modified=false para archivos sin cambios
Un archivo debe tener `is_modified=false` si no aparece en el diff o si no ha sido modificado.

### R5: Compatibilidad con is_new
La adición de `is_modified` no debe afectar la lógica existente de `is_new`. Ambos atributos deben coexistir sin conflicto.

### R6: El diff se utiliza como fuente de verdad
El atributo `diff` del estado debe ser la fuente de verdad para determinar si un archivo fue modificado.
