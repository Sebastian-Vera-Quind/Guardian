from abc import ABC, abstractmethod


class TestRepositoryPort(ABC):
  @abstractmethod
  async def get_agent_state(self, agent_id: str):
    pass

  @abstractmethod
  async def save_agent_state(self, agent_id: str, state):
    pass
