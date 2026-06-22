from src.domain.ports.out_ports import TestRepositoryPort


class TestRepositoryAdapter(TestRepositoryPort):
    def get_data(self) -> str:
        return "data from test adapter"
