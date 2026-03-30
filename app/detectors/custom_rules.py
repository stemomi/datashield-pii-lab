"""Project-local custom detection rules."""

from __future__ import annotations

import re

CustomRulePattern = str | re.Pattern[str]

# Example:
# CUSTOM_ENTITY_RULES = {
#     "PERSON_NAME": r"(?i)operatore\s+alfa",
# }
CUSTOM_ENTITY_RULES: dict[str, CustomRulePattern] = {}
