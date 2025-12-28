"""Banned words lists for all supported languages.

This module defines banned words, hype words, and exclusionary terms
that should not appear in candidate-facing outputs like job ads,
headhunting messages, and calendar invites.

Requirements covered:
- 2.7: Avoid hype words and banned terms in all outputs
- 7.5: Avoid generic hype phrases like "Exciting opportunity"
"""

from typing import Dict, List, Set
from src.tata.session.session import SupportedLanguage


# Hype words to avoid in all languages
# These are generic, overused phrases that lack substance
HYPE_WORDS: Dict[SupportedLanguage, List[str]] = {
    SupportedLanguage.ENGLISH: [
        "exciting opportunity",
        "amazing opportunity",
        "fantastic opportunity",
        "incredible opportunity",
        "unique opportunity",
        "once in a lifetime",
        "game changer",
        "game-changer",
        "world-class",
        "world class",
        "best in class",
        "best-in-class",
        "cutting edge",
        "cutting-edge",
        "state of the art",
        "state-of-the-art",
        "revolutionary",
        "groundbreaking",
        "disruptive",
        "synergy",
        "leverage",
        "paradigm shift",
        "think outside the box",
        "hit the ground running",
        "fast-paced environment",
        "dynamic environment",
        "rockstar",
        "rock star",
        "ninja",
        "guru",
        "wizard",
        "superstar",
        "unicorn",
    ],
    SupportedLanguage.SWEDISH: [
        "spännande möjlighet",
        "fantastisk möjlighet",
        "unik möjlighet",
        "världsklass",
        "banbrytande",
        "revolutionerande",
        "synergi",
        "paradigmskifte",
        "rockstjärna",
        "ninja",
        "guru",
    ],
    SupportedLanguage.DANISH: [
        "spændende mulighed",
        "fantastisk mulighed",
        "unik mulighed",
        "verdensklasse",
        "banebrydende",
        "revolutionerende",
        "synergi",
        "paradigmeskift",
        "rockstjerne",
        "ninja",
        "guru",
    ],
    SupportedLanguage.NORWEGIAN: [
        "spennende mulighet",
        "fantastisk mulighet",
        "unik mulighet",
        "verdensklasse",
        "banebrytende",
        "revolusjonerende",
        "synergi",
        "paradigmeskifte",
        "rockestjerne",
        "ninja",
        "guru",
    ],
    SupportedLanguage.GERMAN: [
        "spannende möglichkeit",
        "fantastische möglichkeit",
        "einzigartige möglichkeit",
        "weltklasse",
        "bahnbrechend",
        "revolutionär",
        "synergie",
        "paradigmenwechsel",
        "rockstar",
        "ninja",
        "guru",
    ],
}


# Exclusionary terms that may discourage diverse candidates
# These terms can create barriers or signal bias
EXCLUSIONARY_TERMS: Dict[SupportedLanguage, List[str]] = {
    SupportedLanguage.ENGLISH: [
        # Age-related
        "young and dynamic",
        "young team",
        "digital native",
        "recent graduate",
        "fresh graduate",
        "mature candidate",
        "seasoned professional",
        # Gender-coded (agentic)
        "aggressive",
        "dominant",
        "competitive",
        "assertive",
        # Ability-related
        "able-bodied",
        "physically fit",
        "clean driving license",
        # Cultural/background
        "native speaker",
        "mother tongue",
        "cultural fit",
        # Overqualification signals
        "overqualified",
        # Unnecessary requirements
        "must have car",
        "own transport required",
    ],
    SupportedLanguage.SWEDISH: [
        "ung och dynamisk",
        "ungt team",
        "digital inföding",
        "nyexaminerad",
        "aggressiv",
        "dominant",
        "konkurrensinriktad",
        "modersmål",
        "kulturell passform",
        "överkvalificerad",
        "måste ha bil",
    ],
    SupportedLanguage.DANISH: [
        "ung og dynamisk",
        "ungt team",
        "digital indfødt",
        "nyuddannet",
        "aggressiv",
        "dominant",
        "konkurrencepræget",
        "modersmål",
        "kulturel pasform",
        "overkvalificeret",
        "skal have bil",
    ],
    SupportedLanguage.NORWEGIAN: [
        "ung og dynamisk",
        "ungt team",
        "digital innfødt",
        "nyutdannet",
        "aggressiv",
        "dominant",
        "konkurranseorientert",
        "morsmål",
        "kulturell passform",
        "overkvalifisert",
        "må ha bil",
    ],
    SupportedLanguage.GERMAN: [
        "jung und dynamisch",
        "junges team",
        "digital native",
        "berufseinsteiger",
        "aggressiv",
        "dominant",
        "wettbewerbsorientiert",
        "muttersprache",
        "kulturelle passung",
        "überqualifiziert",
        "führerschein erforderlich",
        "eigenes fahrzeug erforderlich",
    ],
}


# Combined banned words dictionary
# Merges hype words and exclusionary terms for each language
BANNED_WORDS: Dict[SupportedLanguage, List[str]] = {
    lang: HYPE_WORDS.get(lang, []) + EXCLUSIONARY_TERMS.get(lang, [])
    for lang in SupportedLanguage
}


# Suggestions for banned words (word -> suggested replacement)
BANNED_WORD_SUGGESTIONS: Dict[SupportedLanguage, Dict[str, str]] = {
    SupportedLanguage.ENGLISH: {
        "exciting opportunity": "opportunity",
        "amazing opportunity": "opportunity",
        "fantastic opportunity": "opportunity",
        "unique opportunity": "opportunity",
        "rockstar": "skilled professional",
        "ninja": "expert",
        "guru": "specialist",
        "wizard": "expert",
        "superstar": "high performer",
        "young and dynamic": "energetic",
        "young team": "collaborative team",
        "digital native": "digitally proficient",
        "native speaker": "fluent",
        "mother tongue": "fluent",
        "aggressive": "driven",
        "dominant": "confident",
        "competitive": "motivated",
        "cultural fit": "team alignment",
        "fast-paced environment": "dynamic workplace",
        "hit the ground running": "quick to contribute",
        "game changer": "impactful",
        "game-changer": "impactful",
        "cutting edge": "innovative",
        "cutting-edge": "innovative",
        "world-class": "excellent",
        "world class": "excellent",
        "best in class": "leading",
        "best-in-class": "leading",
        "state of the art": "modern",
        "state-of-the-art": "modern",
        "revolutionary": "innovative",
        "groundbreaking": "pioneering",
        "disruptive": "transformative",
        "synergy": "collaboration",
        "leverage": "use",
        "paradigm shift": "significant change",
        "think outside the box": "creative thinking",
    },
    SupportedLanguage.SWEDISH: {
        "spännande möjlighet": "möjlighet",
        "fantastisk möjlighet": "möjlighet",
        "rockstjärna": "skicklig medarbetare",
        "ung och dynamisk": "energisk",
        "modersmål": "flytande",
    },
    SupportedLanguage.DANISH: {
        "spændende mulighed": "mulighed",
        "fantastisk mulighed": "mulighed",
        "rockstjerne": "dygtig medarbejder",
        "ung og dynamisk": "energisk",
        "modersmål": "flydende",
    },
    SupportedLanguage.NORWEGIAN: {
        "spennende mulighet": "mulighet",
        "fantastisk mulighet": "mulighet",
        "rockestjerne": "dyktig medarbeider",
        "ung og dynamisk": "energisk",
        "morsmål": "flytende",
    },
    SupportedLanguage.GERMAN: {
        "spannende möglichkeit": "möglichkeit",
        "fantastische möglichkeit": "möglichkeit",
        "rockstar": "kompetenter mitarbeiter",
        "jung und dynamisch": "engagiert",
        "muttersprache": "fließend",
    },
}


def get_banned_words_for_language(language: SupportedLanguage) -> List[str]:
    """Get the list of banned words for a specific language.
    
    Args:
        language: The target language
        
    Returns:
        List of banned words/phrases for that language
    """
    return BANNED_WORDS.get(language, [])


def get_all_banned_words() -> Set[str]:
    """Get all banned words across all languages.
    
    Returns:
        Set of all banned words/phrases from all languages
    """
    all_words: Set[str] = set()
    for words in BANNED_WORDS.values():
        all_words.update(words)
    return all_words


def get_suggestion_for_word(word: str, language: SupportedLanguage) -> str:
    """Get a suggested replacement for a banned word.
    
    Args:
        word: The banned word to get a suggestion for
        language: The language context
        
    Returns:
        Suggested replacement, or empty string if no suggestion available
    """
    suggestions = BANNED_WORD_SUGGESTIONS.get(language, {})
    return suggestions.get(word.lower(), "")
