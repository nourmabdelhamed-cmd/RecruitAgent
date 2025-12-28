"""Language processing module for Tata recruitment assistant.

This module provides language guide processing, banned word checking,
and style validation for all supported languages.
"""

from src.tata.language.banned_words import (
    BANNED_WORDS,
    HYPE_WORDS,
    EXCLUSIONARY_TERMS,
    get_banned_words_for_language,
    get_all_banned_words,
)
from src.tata.language.checker import (
    BannedWordViolation,
    BannedWordCheck,
    check_banned_words,
    has_emojis,
    has_dash_bullets,
    GermanFormality,
    get_german_formality,
)

__all__ = [
    "BANNED_WORDS",
    "HYPE_WORDS",
    "EXCLUSIONARY_TERMS",
    "get_banned_words_for_language",
    "get_all_banned_words",
    "BannedWordViolation",
    "BannedWordCheck",
    "check_banned_words",
    "has_emojis",
    "has_dash_bullets",
    "GermanFormality",
    "get_german_formality",
]
