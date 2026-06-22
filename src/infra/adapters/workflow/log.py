import functools
import inspect
import logging
import time
from typing import Callable

from src.domain.models import AgentState


logger = logging.getLogger(__name__)

def _context_from_state(state: AgentState) -> str:
  """Extract identifying fields from AgentState for log lines."""
  if not isinstance(state, dict):
    return ""

  pieces: list[str] = []
  for key in ("project_code", "scan_id", "commit_sha"):
    val = state.get(key)
    if val:
      pieces.append(f"{key}={val}")

  return " ".join(pieces)


def with_logging[T, R](name: str | None = None) -> Callable[[Callable[[T], R]], Callable[[T], R]]:
  def decorator(func: Callable[[T], R]) -> Callable[[T], R]:
    is_async = inspect.iscoroutinefunction(func)
    _name = name or func.__name__
    
    if is_async:
      @functools.wraps(func)
      async def wrapper(*args: T, **kwargs: R) -> R:
        state = args[0] if args else kwargs.get('state')
        context = _context_from_state(state)
        logger.info(f"[START] node={_name} {context}")

        t0 = time.monotonic()
        
        try:
          result = await func(*args, **kwargs)
        except Exception as e:
          elapsed = (time.monotonic() - t0) * 1000
          logger.error(f"[ERROR] node={_name} {context} elapsed={elapsed:.2f}ms error={e}")
          raise
        
        elapsed = (time.monotonic() - t0) * 1000
        logger.info(f"[END] node={_name} {context} elapsed={elapsed:.2f}ms")
        return result
      return wrapper

    def sync_wrapper(*args: T, **kwargs: R) -> R:
      state = args[0] if args else kwargs.get('state')
      context = _context_from_state(state)
      logger.info(f"[START] node={_name} {context}")

      t0 = time.monotonic()
      
      try:
        result = func(*args, **kwargs)
      except Exception as e:
        elapsed = (time.monotonic() - t0) * 1000
        logger.error(f"[ERROR] node={_name} {context} elapsed={elapsed:.2f}ms error={e}")
        raise
      
      elapsed = (time.monotonic() - t0) * 1000
      logger.info(f"[END] node={_name} {context} elapsed={elapsed:.2f}ms")
      return result
    return sync_wrapper
  return decorator
  