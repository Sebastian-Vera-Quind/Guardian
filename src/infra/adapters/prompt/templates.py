from pathlib import Path
from typing import Dict

from src.domain.models import PromptScope

_PROMPTS_DIR = Path(__file__).resolve().parents[4] / "prompts"

SCOPE_TEMPLATES: Dict[PromptScope, Path] = {
  PromptScope.CHECKLIST: _PROMPTS_DIR / "checklist.md.j2",
  PromptScope.ARCHITECTURE: _PROMPTS_DIR / "architecture.md.j2",
  PromptScope.BUSINESS_RULES: _PROMPTS_DIR / "bussinees_rules.md.j2",
}
