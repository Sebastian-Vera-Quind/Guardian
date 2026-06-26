from enum import Enum
import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

class DatabaseLabel(Enum):
  TML = "TLM"
  
class EngineManager:
  _intance = None
  _engines: dict[DatabaseLabel, Engine]
  
  def __new__(cls):
    if cls._intance is None:
      cls._intance = super().__new__(cls)
      cls._engines = {}
    return cls._intance
  
  def _engine_kwargs(self, url: str) -> dict:
    is_sqlite = url.startswith("sqlite") if url else False
    if is_sqlite:
      return {"echo": False}
    statement_timeout_ms = int(os.getenv("STATEMENT_TIMEOUT_MS", "30000"))
    return {
      "echo": False,
      "pool_pre_ping": True,
      "pool_recycle": int(os.getenv("SQLALCHEMY_POOL_RECYCLE", "300")),
      "pool_size": int(os.getenv("SQLALCHEMY_POOL_SIZE", "5")),
      "max_overflow": int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "10")),
      "connect_args": {"options": f"-c statement_timeout={statement_timeout_ms}"},
    }
  
  def _safe_create_engine(self, name: str, url: str) -> Engine:
    try:
      return create_engine(url, **self._engine_kwargs(url))
    except Exception as exc:  # pragma: no cover — defensive
      logger.error(
        "engine_create_failed db=%s err=%s — engine will be retried on first use",
        name,
        exc,
      )
      raise
    
  def get_engine(self, database: DatabaseLabel) -> Engine:
    if database not in self._engines:
      self._engines[database] = self._create_engine(database)

    return self._engines[database]
  
