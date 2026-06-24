from typing import Dict, List, Optional
from uuid import UUID
from typing_extensions import TypedDict

from src.domain.models.repo import DiffFile, TreeObject
from src.domain.models.workflow import RepositoryInput 
from ..util import FileContent


class AgentState(TypedDict, total=False):
    project_code: str
    project_id: UUID
    # WorkflowState fields (backwards compat con nodos existentes)
    user_input: str
    result: dict
    errors: list

    # Loader inputs
    files_content: List[FileContent]
    repository: Optional[RepositoryInput]

    # Loader outputs
    load_to: str
    total_lines: int
    metadata: dict
    ai_attribution_jsonl: str

    # Clone outputs
    clone_path: str
    diff: Dict[str, DiffFile]
    project_tree: TreeObject
