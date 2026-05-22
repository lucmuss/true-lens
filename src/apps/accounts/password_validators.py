from __future__ import annotations

import re

from django.core.exceptions import ValidationError


class SpecialCharacterValidator:
    def validate(self, password: str, user=None) -> None:  # noqa: ANN001
        if not re.search(r"[^A-Za-z0-9]", password or ""):
            raise ValidationError("Password must include at least one special character.")

    def get_help_text(self) -> str:
        return "Your password must include at least one special character."
