from typing import Dict, List, Optional
from uuid import UUID
from typing_extensions import TypedDict

from src.domain.models.repo import DiffFile, TreeObject
from src.domain.models.workflow import RepositoryInput
from src.domain.models.project_context import JsonValue
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

    # Loader conditional flags (para enrutamiento)
    has_commit_sha: bool
    has_target: bool
    has_files_content: bool

    # Clone outputs
    clone_path: str
    diff: Dict[str, DiffFile]
    project_tree: TreeObject
    modified_lines: int

    # Internal state for node orchestration
    _replaced_files: set

    # RAG context fields (populated by node_rag_context)
    active_rules: List[str]
    quality_gates: Optional[JsonValue]
    constraints: Optional[JsonValue]
    nfr_definition: Optional[JsonValue]
    active_fitness_functions: Optional[JsonValue]
