# Feature 6: tree_is_moddified_label
## Design

### Arquitectura general
La modificación se realiza en el flujo de construcción del project_tree en `CloneService`. El diff se genera como un diccionario con estructura `{file_path: DiffFile}`, donde `DiffFile` contiene campos como `is_new`, `is_deleted`, `additions`, `deletions`, y `content`.

### Cambios en CloneService
En `src/application/clone/clone_service.py`:
1. El diff callback ya identifica archivos nuevos (is_new) y los agrega a `added_files`
2. Se debe pasar un conjunto adicional `modified_files` a TreeBuilder que contenga archivos que fueron modificados
3. Un archivo modificado es aquel en el diff que NO es nuevo (`is_new=false`) y NO es eliminado (`is_deleted=false`)

### Cambios en TreeBuilder
En `src/application/clone/tree_builder.py`:
1. El método `build_tree` debe recibir un parámetro adicional `modified_files_set` (similar a `added_files_set`)
2. En la función `_traverse`, al procesar archivos, si la ruta está en `modified_files_set`, se agrega `is_modified=true`
3. Si la ruta NO está en `modified_files_set`, se agrega `is_modified=false` para archivos que tienen un diff
4. Los archivos que no aparecen en el diff no incluyen el atributo (comportamiento por defecto)

### Estructura del nodo de archivo con is_modified
```json
{
  "name": "file.py",
  "type": "file",
  "is_new": true,
  "is_modified": false
}
```
O si es modificado:
```json
{
  "name": "file.py",
  "type": "file",
  "is_modified": true
}
```

### Integración con DiffFile
El tipo `DiffFile` (en models.py) ya contiene:
- `is_new`: boolean indicando si es nuevo
- `is_deleted`: boolean indicando si fue eliminado
- `additions`, `deletions`: conteos de líneas
- `content`: detalles de cambios

Se debe utilizar `is_new` e `is_deleted` para determinar si un archivo fue modificado.

### Lógica de determinación de is_modified
- `is_modified = not is_new and not is_deleted` (en el diff)
- Si el archivo no aparece en el diff, no se incluye `is_modified` (o se asume false)
