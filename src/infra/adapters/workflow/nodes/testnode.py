import asyncio

from src.domain.models import AgentState
from src.infra.adapters.workflow.log import with_logging

@with_logging()
async def wait_two_seconds(state: AgentState) -> None:
  await asyncio.sleep(2)
