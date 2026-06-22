from .app import app


def create_app():
  """Crea y retorna instancia de FastAPI."""
  return app


__all__ = ["app", "create_app"]
