"""Small deterministic detector for educational narrative presentation intent."""
from __future__ import annotations

import re
import unicodedata


def is_story_request(question: str) -> bool:
    """Detect narrative wording without consulting the model or changing evidence policy."""
    value = unicodedata.normalize("NFKD", question.casefold())
    value = "".join(char for char in value if not unicodedata.category(char).startswith("M"))
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    patterns = (
        "tell me the story", "tell the story", "story of", "what happened here",
        "what happened at ", "what happened in ", "what happened when ",
        "narrate", "narrative", "احك", "احكي", "احكوا", "وش صار",
        "ماذا حدث", "ما الذي حدث", "القصة", "قصة", "كيف بدأ", "كيف بدأت",
    )
    return any(pattern in value for pattern in patterns)
