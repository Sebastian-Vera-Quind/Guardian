from enum import Enum
from typing import Any, Callable, Dict


class InPortType(str, Enum):
  WorkFlowExcecutor = "workflow_executor"
  CloneService = "clone_service"


def _create_workflow_engine() -> Any:
  from src.infra.adapters.workflow.engine import WorkflowEngine
  return WorkflowEngine()

def _create_clone_service() -> Any:
  from src.application.clone import CloneService
  from src.infra.helper import inject, OutPortType

  repository_cloner = inject(OutPortType.RepositoryCloner)
  return CloneService(repository_cloner)


_in_port_factories: Dict[InPortType, Callable[[], Any]] = {
  InPortType.WorkFlowExcecutor: _create_workflow_engine,
  InPortType.CloneService: _create_clone_service,
}


class UseCaseInjector:
  _instances: Dict[InPortType, Any] = {}

  def __init__(self) -> None:
    raise TypeError("UseCaseInjector cannot be instantiated")

  @classmethod
  def get_use_case(cls, use_case_type: InPortType) -> Any:
    if use_case_type not in cls._instances:
      cls._instances[use_case_type] = _in_port_factories[use_case_type]()
    return cls._instances[use_case_type]
