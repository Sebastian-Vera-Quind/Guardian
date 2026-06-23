from enum import Enum
from typing import Any, Callable, Dict


class InPortType(str, Enum):
  WorkFlowExcecutor = "workflow_executor"


def _create_workflow_engine() -> Any:
  from src.infra.adapters.workflow.engine import WorkflowEngine
  return WorkflowEngine()


_in_port_factories: Dict[InPortType, Callable[[], Any]] = {
  InPortType.WorkFlowExcecutor: _create_workflow_engine,
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
