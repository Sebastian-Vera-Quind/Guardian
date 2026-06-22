from enum import Enum
from typing import Any, Callable, Dict

from src.infra.adapters.test_adapter import TestRepositoryAdapter


class OutPortType(str, Enum):
    TestRepository = "testRepository"


_out_port_factories: Dict[OutPortType, Callable[[], Any]] = {
    OutPortType.TestRepository: lambda: TestRepositoryAdapter(),
}


class OutPortInjector:
    _instances: Dict[OutPortType, Any] = {}

    def __init__(self) -> None:
        raise TypeError("OutPortInjector cannot be instantiated")

    @classmethod
    def get_out_port(cls, port_type: OutPortType) -> Any:
        if port_type not in cls._instances:
            cls._instances[port_type] = _out_port_factories[port_type]()
        return cls._instances[port_type]
