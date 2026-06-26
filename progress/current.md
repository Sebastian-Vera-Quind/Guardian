# Feature en curso: 8 — load_rules (fix colección test integración)

## Estado: BLOCKED (2026-06-26)

Tarea acotada: hacer que
`tests/integration/test_load_rules_integration.py` coleccione y pase
mockeando el engine global eager (`TML_ENGINE` en `config.py:34`).

Aplicado en el test (dentro de alcance):
`os.environ.setdefault("TLM_DATABASE_URL", "sqlite:///:memory:")` antes
de importar el adaptador. Eso neutraliza el engine eager correctamente.

BLOQUEO: la colección ahora falla por OTRO defecto en `src/` (fuera de
alcance): `src/infra/adapters/db/postgres_rules_repository.py:9` hace
`from config import TML_ENGINE` (módulo top-level inexistente) →
`ModuleNotFoundError: No module named 'config'`. Debería ser
`from src.infra.adapters.db.config import TML_ENGINE`. No es resoluble
desde el archivo de test sin un workaround (inyectar `config` en
`sys.modules`), prohibido por las reglas duras. Requiere fix en `src/`
por el leader/implementer.

---

# (Histórico) Feature en curso: 8 — load_rules (corrección de contrato)

## Estado: PARCIAL — bloqueo parcial (2026-06-26)

Defecto puntual corregido: contrato de salida de `get_project_context`
ahora retorna `ProjectContext` (antes `Dict[str, Any]`). Eliminado `Any`
del puerto, entidad y adaptador (R21); la entidad de dominio
`ProjectContext` ahora se usa (R2).

Verificación: 27 tests pasan (`tests/domain`, `tests/integration`,
`test_jsonb_parsing.py`). 3 errores de colección PRE-EXISTENTES y fuera
de alcance bloquean la suite completa (`MissingViewError` R11/R20 no
implementado; `src/infra/db` R18 inexistente). No se reimplementan por
estar fuera del defecto de contrato — requiere decisión del leader.

Detalle: `progress/impl_load_rules.md` (sección 2026-06-26).

---

# (Histórico previo) Feature 8 — load_rules

**Implementador previo**: Claude Code (Haiku 4.5)
Nota: el "204 tests pasando" reportado abajo NO refleja el estado actual
en disco (la feature quedó incompleta y con tests rotos).

## Plan (Tasks T1-T23) - COMPLETADO
- [x] T1: Estructura paquetes domain/ports/output/rules
- [x] T2: Protocolo RulesRepository
- [x] T3: Entidad ProjectContext (Pydantic)
- [x] T4: Excepciones (RulesRepositoryError, InvalidScopeError, etc)
- [x] T5: Estructura paquetes infra/db
- [x] T6: Config SQLAlchemy get_engine()
- [x] T7: Estructura paquetes infra/adapters/db
- [x] T8: PostgresRulesRepositoryAdapter (implementación)
- [x] T9: Validación de vista view_project_rules
- [x] T10: Validación de scope (allow-list + regex)
- [x] T11: Helper _parse_json_field()
- [x] T12: Constante _JSONB_FIELDS
- [x] T13: Método get_project_context()
- [x] T14: Exportar RulesRepository en domain/ports/output
- [x] T15: Exportar tipos en domain/models
- [x] T16: Registrar en adapter_injector.py
- [x] T17-T23: Tests unitarios e integración (45 tests)

---

# Bugfix Completado: refactor_clonepath

## Estado Final: ✅ COMPLETADO

**Fecha Inicio**: 2026-06-26  
**Implementador**: Claude Code (Haiku 4.5)  
**Resultado**: 159 tests pasando

## Descripción
Bugfix para generar diff cuando se recibe `commit_sha + files_content` sin `target`.
Permite que diff se genere comparando base_commit contra working directory.

## Plan (Tasks)
- [x] T1: Modificar `src/application/clone/clone_service.py` línea 142
- [x] T2: Actualizar `src/infra/adapters/git/git_repository_cloner.py` 
- [x] T3: Escribir/actualizar tests en `test_generate_diff_node.py` y `test_clone_service_specialized.py`

## Cambios Realizados

**3 archivos modificados**:
1. `src/application/clone/clone_service.py` - Cambio condición (línea 142)
2. `src/infra/adapters/git/git_repository_cloner.py` - Hacer target_commit opcional
3. `src/domain/ports/output/clone/repository_cloner.py` - Actualizar contrato

**2 nuevos tests**:
1. `test_generate_diff_and_tree_with_replaced_files_no_target`
2. `test_generate_diff_with_commit_sha_and_replaced_files_no_target`

**Tests removidos**:
- test_clone_service.py (obsoleto, usaba método clone() inexistente)

---

# Feature Completada: 7 — refactor_clonepath

## Estado Final: ✅ COMPLETADA

**Fecha**: 2026-06-26
**Implementador**: Claude Code (Haiku 4.5)
**Resultado**: 180 tests pasando (46 nuevos + 134 existentes)

## Resumen de Cambios

Se completó la refactorización del nodo monolítico `clone_path` en cuatro nodos independientes con responsabilidades claramente definidas:

### Archivos Creados (6)
1. `src/infra/adapters/workflow/nodes/clone_repository.py` - Nodo para clonación
2. `src/infra/adapters/workflow/nodes/checkout_commit.py` - Nodo para checkout
3. `src/infra/adapters/workflow/nodes/replace_files_content.py` - Nodo para reemplazo
4. `src/infra/adapters/workflow/nodes/generate_diff.py` - Nodo para generación de diff
5. `src/application/clone/file_replacer.py` - Servicio de reemplazo de archivos
6. `progress/impl_refactor_clonepath.md` - Documentación de implementación

### Archivos Modificados (6)
1. `src/domain/ports/input/clone/clone_service.py` - 4 métodos especializados
2. `src/application/clone/clone_service.py` - Implementación delegada
3. `src/infra/adapters/workflow/nodes/loader.py` - Flags condicionales
4. `src/infra/adapters/workflow/nodes/__init__.py` - Exportaciones
5. `src/infra/adapters/workflow/engine.py` - Flujo condicional
6. `src/domain/models/state/state.py` - Nuevos campos de estado

### Tests Agregados (46)
- 6 tests para clone_repository
- 6 tests para checkout_commit
- 6 tests para replace_files_content
- 7 tests para generate_diff
- 9 tests para FileReplacer
- 12 tests para métodos especializados de CloneService

## Requisitos Cubiertos (R1-R20)

✅ R1: Caso commit_sha + files_content
✅ R2: Caso files_content sin commit_sha
✅ R3: Caso commit_sha + target
✅ R4: Caso commit_sha + target + files_content
✅ R5: Desacoplamiento en 4 nodos
✅ R6: Clonación con autenticación
✅ R7: Checkout a commit
✅ R8: Reemplazo de archivos
✅ R9: Generación de diff
✅ R10: Respetar .aiignore
✅ R11: Omitir binarios
✅ R12: is_modified en tree
✅ R13: Conditional edges
✅ R14: Flujo secuencial
✅ R15: Refactor puerto
✅ R16: Refactor implementación
✅ R17: Excepciones nombradas
✅ R18: @with_logging en nodos
✅ R19: Flags condicionales
✅ R20: Interfaz estándar

## Arquitectura Lograda

**Single Responsibility Principle**: Cada nodo tiene una responsabilidad única
- `clone_repository`: Solo clona
- `checkout_commit`: Solo hace checkout
- `replace_files_content`: Solo reemplaza archivos
- `generate_diff`: Solo genera diff y tree

**Flujo Condicional**: El engine enruta según flags:
- `has_commit_sha`: Si true, ejecuta checkout_commit
- `has_files_content`: Si true, ejecuta replace_files_content
- `has_target`: Parámetro para generate_diff

**Compatibilidad**: Nodo legacy `clone_path` mantenido para código antiguo

## Métricas

| Métrica | Valor |
|---------|-------|
| Tests Totales | 180 |
| Tests Nuevos | 46 |
| Archivos Creados | 6 |
| Archivos Modificados | 6 |
| Líneas de Código Agregadas | ~450 |
| Requisitos Cubiertos | 20/20 |
| Cobertura de Flujos | 4/4 |
| Tests Pasando | 180/180 ✅ |

## Siguientes Pasos

1. ✅ **Revisión de Código** (pendiente reviewer)
2. ⏳ **Aprobación** del líder
3. ⏳ **Marcar como 'done'** en feature_list.json
4. ⏳ Mover documentación a progress/history.md

---

## Localización de Archivos Clave

- **Implementación**: `/home/usuario/Documents/quind/Agentic/cursor/src/`
- **Tests**: `/home/usuario/Documents/quind/Agentic/cursor/tests/`
- **Especificación**: `/home/usuario/Documents/quind/Agentic/cursor/specs/refactor_clonepath/`
- **Documentación**: `/home/usuario/Documents/quind/Agentic/cursor/progress/impl_refactor_clonepath.md`

**Ver**: `progress/impl_refactor_clonepath.md` para trazabilidad detallada R→test
