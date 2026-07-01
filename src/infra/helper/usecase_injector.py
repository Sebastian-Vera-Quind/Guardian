from enum import Enum
from typing import Callable, Dict, Union

from src.domain.ports.input import (
  CloneService,
  WorkflowExecutor,
  ContextRetriever,
  PromptBuilder,
)


class InPortType(str, Enum):
  WorkFlowExcecutor = "workflow_executor"
  CloneService = "clone_service"
  ContextRetrievalService = "context_retrieval_service"
  PromptBuilderService = "prompt_builder_service"

_InPort = Union[
  WorkflowExecutor,
  CloneService,
  ContextRetriever,
  PromptBuilder,
]

def _create_workflow_engine() -> WorkflowExecutor:
  from src.infra.adapters.workflow.engine import WorkflowEngine
  return WorkflowEngine()


def _create_clone_service() -> CloneService:
  from src.application.clone import CloneService as CloneServiceImpl
  from src.infra.helper.inject import inject, OutPortType

  repository_cloner = inject(OutPortType.RepositoryCloner)
  return CloneServiceImpl(repository_cloner)


def _create_context_retrieval_service() -> ContextRetriever:
  from src.application.context.context_retrieval_service import (
    ContextRetrievalService,
  )
  from src.infra.helper.inject import inject, OutPortType

  rules = inject(OutPortType.RulesRepository)
  vector = inject(OutPortType.VectorSearchRepository)
  standards = inject(OutPortType.CodingStandardsSearch)
  fields = inject(OutPortType.ProjectFieldsRepository)
  return ContextRetrievalService(
    rules=rules,
    vector=vector,
    standards=standards,
    fields=fields,
  )


def _create_prompt_builder_service() -> PromptBuilder:
  from src.application.prompt import PromptBuilderService
  from src.infra.helper.inject import inject, OutPortType

  renderer = inject(OutPortType.PromptRenderer)
  return PromptBuilderService(renderer)


_in_port_factories: Dict[InPortType, Callable[[], _InPort]] = {
  InPortType.WorkFlowExcecutor: _create_workflow_engine,
  InPortType.CloneService: _create_clone_service,
  InPortType.ContextRetrievalService: _create_context_retrieval_service,
  InPortType.PromptBuilderService: _create_prompt_builder_service,
}


class UseCaseInjector:
  _instances: Dict[InPortType, _InPort] = {}

  def __init__(self) -> None:
    raise TypeError("UseCaseInjector cannot be instantiated")

  @classmethod
  def get_use_case(cls, use_case_type: InPortType) -> _InPort:
    if use_case_type not in cls._instances:
      cls._instances[use_case_type] = _in_port_factories[
        use_case_type
      ]()
    return cls._instances[use_case_type]
