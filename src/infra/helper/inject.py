from __future__ import annotations
from typing import Any, Literal, Union, overload

from src.domain.ports.input import WorkflowExecutor
from src.domain.ports.output import MetadataReader
from .adapter_injector import OutPortType, OutPortInjector
from .usecase_injector import InPortType, UseCaseInjector

@overload
def inject(dependency_type: Literal[InPortType.WorkFlowExcecutor]) -> WorkflowExecutor: ...
@overload
def inject(dependency_type: Literal[OutPortType.MetadataReader]) -> MetadataReader: ...


def inject(dependency_type: Union[InPortType, OutPortType]) -> Any:
    if dependency_type in OutPortType.__members__.values():
        return OutPortInjector.get_out_port(dependency_type)  # type: ignore[arg-type]
    return UseCaseInjector.get_use_case(dependency_type)  # type: ignore[arg-type]
