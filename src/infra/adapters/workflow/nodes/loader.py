import logging
from src.infra.helper import inject, OutPortType
from src.domain.models.state import AgentState
from src.domain.models.errors import LoaderNodeError, MetadataExtractionError
from src.domain.models import FileContent
from src.application.loader import CodeSanitizer, JSONLValidator
from src.infra.adapters.workflow.log import with_logging

logger = logging.getLogger(__name__)


def determine_load_route(state: AgentState) -> str:
  has_repo = state.get("repository") is not None
  has_files = bool(state.get("files_content"))

  if has_repo:
    return "clone"
  elif has_files:
    return "simple"
  else:
    logger.error("No files_content or repository provided in state")
    raise LoaderNodeError("No files_content or repository provided")


@with_logging()
async def node_loader_task(state: AgentState) -> AgentState:
  load_route = determine_load_route(state)
  _reader = inject(OutPortType.MetadataReader)
  state["load_to"] = load_route

  if load_route == "simple":
    files_raw = list(state.get("files_content", []))
    files = [
      FileContent(**f) if isinstance(f, dict) else f
      for f in files_raw
    ]

    files, attribution = JSONLValidator.extract_attribution_file(files)
    if attribution is not None:
      state["ai_attribution_jsonl"] = attribution

    sanitized = CodeSanitizer.sanitize_files(files)
    state["files_content"] = sanitized
    state["total_lines"] = CodeSanitizer.count_lines(sanitized)

  elif load_route == "clone":
    repo_data = state.get("repository", {})
    try:
      metadata = _reader.extract_from_repository(repo_data)
      state["metadata"] = metadata
    except Exception as e:
      logger.error("Failed to extract metadata: %s", e)
      raise MetadataExtractionError(str(e)) from e
    state.pop("files_content", None)

  return state
