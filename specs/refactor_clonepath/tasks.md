# Tasks: refactor_clonepath

Checklist de tareas discretas y ordenadas para implementar el refactor
del nodo `clone_path` en cuatro nodos independientes.

## Fase 1: Refactorización de puertos y servicios

- [x] T1 — Refactorizar `src/domain/ports/input/clone/clone_service.py`
  para agregar métodos especializados `clone_repository()`,
  `checkout_commit()`, `replace_files_content()`, y `generate_diff_and_tree()`.
  Mantener el método `clone()` existente si se requiere compatibilidad.
  Cubre: R15.

- [x] T2 — Refactorizar `src/application/clone/clone_service.py` para
  implementar los cuatro métodos especializados. Si se mantiene `clone()`,
  hacerlo delegar a los métodos especializados.
  Cubre: R15, R16.

- [x] T3 — Crear nuevo archivo
  `src/application/clone/file_replacer.py` con lógica de reemplazo de
  archivos en el repositorio clonado (crear si no existen, reemplazar si
  existen, preservar estructura de directorios).
  Cubre: R8.

- [x] T4 — Actualizar `src/domain/models/errors/clone_errors.py` si es
  necesario para añadir excepciones especializadas (o reutilizar
  `ClonePathError`, `CheckoutError`, etc.).
  Cubre: R17.

## Fase 2: Creación de nodos independientes

- [x] T5 — Crear `src/infra/adapters/workflow/nodes/clone_repository.py`
  con nodo que clona el repositorio, respetando autenticación por token.
  Debe escribir `clone_path` en el estado.
  Cubre: R6, R18, R20.

- [x] T6 — Crear `src/infra/adapters/workflow/nodes/checkout_commit.py`
  con nodo que hace checkout al commit especificado. Debe lanzar excepción
  si el commit no existe.
  Cubre: R7, R18, R20.

- [x] T7 — Crear `src/infra/adapters/workflow/nodes/replace_files_content.py`
  con nodo que reemplaza archivos según `files_content`. Registra qué
  archivos fueron modificados para el paso posterior.
  Cubre: R8, R18, R20.

- [x] T8 — Crear `src/infra/adapters/workflow/nodes/generate_diff.py`
  con nodo que genera diff y project_tree. Debe:
    - Respetar `.aiignore`
    - Omitir binarios
    - Incluir `is_modified` en project_tree
    - Calcular `modified_lines`
  Cubre: R9, R10, R11, R12, R18, R20.

## Fase 3: Actualización del workflow y router

- [x] T9 — Refactorizar `src/infra/adapters/workflow/nodes/loader.py`
  para establecer flags condicionales:
    - `has_files_content: bool`
    - `has_commit_sha: bool`
    - `has_target: bool`
  Cubre: R19.

- [x] T10 — Actualizar `src/infra/adapters/workflow/nodes/__init__.py`
  para importar y exportar los cuatro nodos nuevos.
  Cubre: R5.

- [x] T11 — Refactorizar `src/infra/adapters/workflow/engine.py`:
    - Remover la arista `loader → clone_path → END`
    - Agregar nodo `clone_repository`
    - Agregar conditional edge desde `clone_repository` que dirija a:
      - `checkout_commit` SI `has_commit_sha == True`
      - O saltar directamente a siguiente nodo SI `has_commit_sha == False`
    - Agregar conditional edge que dirija a `replace_files_content` SI
      `has_files_content == True`, o saltarlo si `False`
    - Agregar nodo `generate_diff` que se ejecute después de todos los
      cambios (checkout y/o reemplazo)
    - Validar que todas las rutas lleven a `generate_diff` y luego a `END`
  Cubre: R13, R14.

## Fase 4: Validación de cobertura de casos de entrada

- [x] T12 — Verificar que el nuevo flujo cubre el **Caso 1** (R1):
  `repository.url + repository.commit_sha + files_content`.
  Flujo esperado: `loader → clone_repository → checkout_commit →
  replace_files_content → generate_diff → END`
  Cubre: R1, R13, R14.

- [x] T13 — Verificar que el nuevo flujo cubre el **Caso 2** (R2):
  `repository.url + files_content` (sin `commit_sha` ni `target`).
  Flujo esperado: `loader → clone_repository → replace_files_content →
  generate_diff (usando HEAD como base) → END`
  Cubre: R2, R13, R14.

- [x] T14 — Verificar que el nuevo flujo cubre el **Caso 3** (R3):
  `repository.url + repository.commit_sha + repository.target` (sin `files_content`).
  Flujo esperado: `loader → clone_repository → checkout_commit →
  generate_diff (comparando commit_sha vs target) → END`
  Cubre: R3, R13, R14.

- [x] T15 — Verificar que el nuevo flujo cubre el **Caso 4** (R4):
  `repository.url + repository.commit_sha + repository.target + files_content`.
  Flujo esperado: `loader → clone_repository → checkout_commit →
  replace_files_content → generate_diff (comparando commit_sha+cambios vs target) → END`
  Cubre: R4, R13, R14.

## Fase 5: Limpieza y documentación

- [x] T16 — Evaluar si mantener o eliminar `clone_path.py` según si hay
  código legacy que aún lo use. Si se mantiene, marcar como deprecated.
  Si se elimina, actualizar `__init__.py`.
  Cubre: R5.

- [x] T17 — Crear tests de integración para cada uno de los cuatro casos
  de entrada (R1-R4), validando que el workflow enruta correctamente y
  produce outputs esperados (clone_path, diff, project_tree, modified_lines).
  Cubre: R1, R2, R3, R4.

- [x] T18 — Crear tests unitarios para cada nodo refactorizado, simulando
  errores (commit inexistente, token inválido, archivo corrupto, etc.) y
  validando que se lancen excepciones nombradas.
  Cubre: R17, R18.

- [x] T19 — Actualizar documentación en `docs/architecture.md` o
  `docs/specs.md` (si aplica) para reflejar el nuevo flujo de workflow
  y los cuatro nodos independientes.
  Cubre: R5, R14.

- [x] T20 — Ejecutar suite de tests completa (unit + integration) para
  asegurar que no hay regresiones y que el refactor es funcional end-to-end.
  Cubre: R1-R20.
