from typing import Any, Literal, Union, overload

from src.domain.ports.in_ports import TestUseCasePort
from src.domain.ports.out_ports import TestRepositoryPort
from .adapter_injector import OutPortInjector, OutPortType
from .usecase_injector import InPortType, UseCaseInjector


@overload
def inject(dependency_type: Literal[InPortType.TestUseCase]) -> TestUseCasePort: ...
@overload
def inject(dependency_type: Literal[OutPortType.TestRepository]) -> TestRepositoryPort: ...


def inject(dependency_type: Union[InPortType, OutPortType]) -> Any:
    if dependency_type in OutPortType.__members__.values():
        return OutPortInjector.get_out_port(dependency_type)  # type: ignore[arg-type]
    return UseCaseInjector.get_use_case(dependency_type)  # type: ignore[arg-type]
