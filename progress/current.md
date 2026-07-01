# Feature en curso: 9 — prompt_builder

## Estado: IMPLEMENTADO — pendiente de review (2026-07-01)

Tasks T1..T25 completadas y marcadas `[x]`. pytest: 255 passed
(244 baseline + 11 nuevos). Detalle y trazabilidad R→test en
`progress/impl_prompt_builder.md`. NO se marca `done` (lo hace el
reviewer/leader).

Plan ejecutado: tasks T1..T25 de `specs/prompt_builder/tasks.md` en
orden. Baseline verde confirmado (244 passed) antes de empezar.

- Dominio (T1-T8): enum PromptScope, excepciones, puertos input/output,
  exports.
- Application (T9-T14): PromptBuilderService + saneamiento.
- Infra (T15-T19): plantillas Jinja2 y JinjaPromptRenderer.
- Inyección (T20-T22): registrar PromptRenderer (out) y
  PromptBuilderService (in).
- Tests (T23-T25): unitarios servicio, adaptador e inyección.
