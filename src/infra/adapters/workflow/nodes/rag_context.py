import logging
from typing import List

from src.application.context.query_builder import build_rag_query
from src.infra.adapters.workflow.log import with_logging
from src.infra.helper import inject, InPortType
from src.domain.models import AgentState

logger = logging.getLogger(__name__)


def _extract_contents(state: AgentState) -> List[str]:
  """Extract text contents from state to build the RAG query.

  For the simple path, reads files_content[*].content.
  For the clone path, reads added/modified lines from diff.

  Args:
    state: Current AgentState.

  Returns:
    List of content strings, possibly empty.
  """
  load_to = state.get("load_to", "")
  if load_to == "simple":
    files = state.get("files_content") or []
    result: List[str] = []
    for f in files:
      if isinstance(f, dict):
        content = f.get("content", "")
      else:
        content = getattr(f, "content", "")
      if content:
        result.append(content)
    return result

  diff = state.get("diff") or {}
  result = []
  for diff_file in diff.values():
    if isinstance(diff_file, dict):
      lines = diff_file.get("content") or []
    else:
      lines = getattr(diff_file, "content", []) or []
    for line in lines:
      if isinstance(line, dict):
        status = line.get("status")
        content = line.get("content", "")
      else:
        status = getattr(line, "status", None)
        content = getattr(line, "content", "")
      if status in ("added", "modified") and content:
        result.append(content)
  return result


@with_logging()
async def node_rag_context(state: AgentState) -> AgentState:
  """LangGraph node that populates RAG context fields in AgentState.

  Validates project_code, extracts contents from state, builds a
  query string and calls ContextRetrievalService.retrieve to populate
  active_rules, quality_gates, constraints, nfr_definition and
  active_fitness_functions.

  Args:
    state: Current AgentState.

  Returns:
    Updated AgentState with RAG context fields written.

  Raises:
    ValueError: When project_code is absent or empty.
  """
  project_code = state.get("project_code")
  if not project_code:
    raise ValueError("input must include valid 'project_code'")

  service = inject(InPortType.ContextRetrievalService)

  contents = _extract_contents(state)
  query_text = build_rag_query(contents)

  ctx = service.retrieve(
    project_code=project_code,
    query_text=query_text,
  )

  state["active_rules"] = ctx.active_rules
  state["quality_gates"] = ctx.quality_gates
  state["constraints"] = ctx.constraints
  state["nfr_definition"] = ctx.nfr_definition
  state["active_fitness_functions"] = ctx.fitness_functions
  return state
