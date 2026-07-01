from enum import Enum


class PromptScope(str, Enum):
  CHECKLIST = "checklist"
  ARCHITECTURE = "architecture"
  BUSINESS_RULES = "business_rules"
