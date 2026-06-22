from abc import ABC, abstractmethod


class TestUseCasePort(ABC):
  @abstractmethod
  async def wait_two_seconds(self) -> None:
    pass
