from src.domain.ports.in_ports import TestUseCasePort
from src.domain.ports.out_ports import TestRepositoryPort


class TestUseCaseService(TestUseCasePort):
    def __init__(self, test_repository: TestRepositoryPort) -> None:
        self._test_repository = test_repository

    def execute(self) -> str:
        return self._test_repository.get_data()
