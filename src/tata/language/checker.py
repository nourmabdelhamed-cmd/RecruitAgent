"""Language style checking for Tata recruitment assistant.

This module provides functions for checking text against GlobalConnect's
language guidelines, including banned word detection, emoji detection,
dash bullet detection, and German formality selection.

Requirements covered:
- 2.5: No emojis in any output
- 2.6: No dash-style bullets in body text
- 2.7: Avoid hype words and banned terms
- 2.8: Match du/Sie appropriately for German
- 13.5: Enforce banned words list in candidate-facing texts
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import re

from src.tata.session.session import SupportedLanguage
from src.tata.language.banned_words import (
    get_banned_words_for_language,
    get_suggestion_for_word,
)


@dataclass
class BannedWordViolation:
    """A single banned word found in text.
    
    Attributes:
        word: The banned word/phrase that was found
        suggestion: Suggested replacement for the word
        position: Character position where the word starts in the text
    """
    word: str
    suggestion: str
    position: int


@dataclass
class BannedWordCheck:
    """Result of checking for banned words.
    
    Attributes:
        has_banned_words: True if any banned words were found
        violations: List of all violations found
    """
    has_banned_words: bool
    violations: List[BannedWordViolation] = field(default_factory=list)


def check_banned_words(text: str, language: SupportedLanguage) -> BannedWordCheck:
    """Check text for banned words in the specified language.
    
    Performs case-insensitive matching against the banned words list
    for the given language. Returns all violations found with their
    positions and suggested replacements.
    
    Args:
        text: The text to check
        language: The language to check against
        
    Returns:
        BannedWordCheck with has_banned_words flag and list of violations
    """
    if not text:
        return BannedWordCheck(has_banned_words=False, violations=[])
    
    banned_words = get_banned_words_for_language(language)
    violations: List[BannedWordViolation] = []
    text_lower = text.lower()
    
    for banned_word in banned_words:
        banned_lower = banned_word.lower()
        # Find all occurrences of the banned word
        start = 0
        while True:
            pos = text_lower.find(banned_lower, start)
            if pos == -1:
                break
            
            # Get suggestion for this word
            suggestion = get_suggestion_for_word(banned_word, language)
            
            violations.append(BannedWordViolation(
                word=banned_word,
                suggestion=suggestion,
                position=pos,
            ))
            start = pos + 1
    
    # Sort violations by position
    violations.sort(key=lambda v: v.position)
    
    return BannedWordCheck(
        has_banned_words=len(violations) > 0,
        violations=violations,
    )


# Emoji Unicode ranges for detection
# Covers most common emoji ranges
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    "\U0001F700-\U0001F77F"  # Alchemical Symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Enclosed characters
    "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
    "]+",
    flags=re.UNICODE
)


def has_emojis(text: str) -> bool:
    """Check if text contains any emoji characters.
    
    Uses Unicode range detection to find emojis including:
    - Emoticons (smileys, faces)
    - Misc symbols and pictographs
    - Transport and map symbols
    - Flags
    - Dingbats
    
    Args:
        text: The text to check
        
    Returns:
        True if any emoji is found, False otherwise
    """
    if not text:
        return False
    
    return bool(EMOJI_PATTERN.search(text))


# Pattern for dash-style bullets in body text
# Matches lines starting with - or – followed by space
DASH_BULLET_PATTERN = re.compile(
    r"^[\s]*[-–—][\s]+",  # Line start, optional whitespace, dash, space
    flags=re.MULTILINE
)


def has_dash_bullets(text: str) -> bool:
    """Check if text contains dash-style bullet points.
    
    Detects lines that start with:
    - Hyphen-minus (-)
    - En dash (–)
    - Em dash (—)
    
    followed by whitespace, which indicates a dash-style bullet.
    
    Args:
        text: The text to check
        
    Returns:
        True if dash bullets are found, False otherwise
    """
    if not text:
        return False
    
    return bool(DASH_BULLET_PATTERN.search(text))


class GermanFormality(Enum):
    """German formality level for du/Sie selection."""
    DU = "du"   # Informal
    SIE = "Sie"  # Formal


# Keywords that suggest informal (du) context
INFORMAL_CONTEXT_KEYWORDS = [
    "startup",
    "start-up",
    "tech",
    "digital",
    "creative",
    "young",
    "casual",
    "flat hierarchy",
    "agile",
    "scrum",
    "modern",
    "innovative",
]

# Keywords that suggest formal (Sie) context
FORMAL_CONTEXT_KEYWORDS = [
    "traditional",
    "corporate",
    "enterprise",
    "bank",
    "banking",
    "finance",
    "financial",
    "insurance",
    "legal",
    "law",
    "government",
    "public sector",
    "executive",
    "senior",
    "director",
    "management",
    "formal",
    "conservative",
]


def get_german_formality(context: str) -> GermanFormality:
    """Determine du/Sie formality based on context.
    
    Analyzes the context text to determine whether informal (du)
    or formal (Sie) address is more appropriate for German output.
    
    The decision is based on:
    - Industry keywords (tech/startup → du, banking/legal → Sie)
    - Company culture indicators
    - Role level indicators
    
    Args:
        context: Text describing the company, role, or culture
        
    Returns:
        GermanFormality.DU for informal, GermanFormality.SIE for formal
    """
    if not context:
        # Default to formal when no context
        return GermanFormality.SIE
    
    context_lower = context.lower()
    
    # Count matches for each formality level
    informal_score = sum(
        1 for keyword in INFORMAL_CONTEXT_KEYWORDS
        if keyword in context_lower
    )
    formal_score = sum(
        1 for keyword in FORMAL_CONTEXT_KEYWORDS
        if keyword in context_lower
    )
    
    # If more informal keywords, use du
    if informal_score > formal_score:
        return GermanFormality.DU
    
    # Default to formal (Sie) - safer choice
    return GermanFormality.SIE
