from typing import TypedDict, List
from .file import FileContent


class AgentState(TypedDict, total=False):
    # WorkflowState fields (backwards compat con nodos existentes)
    user_input: str
    processing_state: str
    current_node: str
    result: dict
    errors: list

    # Tracing (usados por with_logging)
    project_code: str
    scan_id: str
    commit_sha: str

    # Loader inputs
    files_content: List[FileContent]
    repository: dict

    # Loader outputs
    load_to: str
    total_lines: int
    metadata: dict
    ai_attribution_jsonl: str
