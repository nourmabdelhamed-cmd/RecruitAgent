"""Tests for the language processing module.

Tests banned word checking, emoji detection, dash bullet detection,
and German formality selection.
"""

import pytest
from src.tata.session.session import SupportedLanguage
from src.tata.language.banned_words import (
    BANNED_WORDS,
    HYPE_WORDS,
    EXCLUSIONARY_TERMS,
    get_banned_words_for_language,
    get_all_banned_words,
    get_suggestion_for_word,
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


class TestBannedWords:
    """Tests for banned words lists."""
    
    def test_banned_words_exist_for_all_languages(self):
        """All supported languages should have banned words defined."""
        for lang in SupportedLanguage:
            words = get_banned_words_for_language(lang)
            assert isinstance(words, list)
            assert len(words) > 0, f"No banned words for {lang}"
    
    def test_hype_words_exist_for_all_languages(self):
        """All supported languages should have hype words defined."""
        for lang in SupportedLanguage:
            assert lang in HYPE_WORDS
            assert len(HYPE_WORDS[lang]) > 0
    
    def test_exclusionary_terms_exist_for_all_languages(self):
        """All supported languages should have exclusionary terms defined."""
        for lang in SupportedLanguage:
            assert lang in EXCLUSIONARY_TERMS
            assert len(EXCLUSIONARY_TERMS[lang]) > 0
    
    def test_get_all_banned_words_returns_set(self):
        """get_all_banned_words should return a non-empty set."""
        all_words = get_all_banned_words()
        assert isinstance(all_words, set)
        assert len(all_words) > 0
    
    def test_english_contains_exciting_opportunity(self):
        """English banned words should include 'exciting opportunity'."""
        words = get_banned_words_for_language(SupportedLanguage.ENGLISH)
        assert "exciting opportunity" in words
    
    def test_suggestion_for_exciting_opportunity(self):
        """Should suggest 'opportunity' for 'exciting opportunity'."""
        suggestion = get_suggestion_for_word(
            "exciting opportunity", 
            SupportedLanguage.ENGLISH
        )
        assert suggestion == "opportunity"


class TestBannedWordChecker:
    """Tests for the banned word checker function."""
    
    def test_empty_text_returns_no_violations(self):
        """Empty text should have no violations."""
        result = check_banned_words("", SupportedLanguage.ENGLISH)
        assert result.has_banned_words is False
        assert len(result.violations) == 0
    
    def test_clean_text_returns_no_violations(self):
        """Text without banned words should have no violations."""
        result = check_banned_words(
            "We are looking for a software engineer.",
            SupportedLanguage.ENGLISH
        )
        assert result.has_banned_words is False
        assert len(result.violations) == 0
    
    def test_detects_exciting_opportunity(self):
        """Should detect 'exciting opportunity' as banned."""
        result = check_banned_words(
            "This is an exciting opportunity to join our team.",
            SupportedLanguage.ENGLISH
        )
        assert result.has_banned_words is True
        assert len(result.violations) == 1
        assert result.violations[0].word == "exciting opportunity"
    
    def test_case_insensitive_detection(self):
        """Detection should be case-insensitive."""
        result = check_banned_words(
            "This is an EXCITING OPPORTUNITY!",
            SupportedLanguage.ENGLISH
        )
        assert result.has_banned_words is True
    
    def test_multiple_violations(self):
        """Should detect multiple banned words."""
        result = check_banned_words(
            "We need a rockstar ninja for this exciting opportunity.",
            SupportedLanguage.ENGLISH
        )
        assert result.has_banned_words is True
        assert len(result.violations) >= 3
    
    def test_violation_includes_position(self):
        """Violations should include the position in text."""
        text = "Join our exciting opportunity today."
        result = check_banned_words(text, SupportedLanguage.ENGLISH)
        assert result.has_banned_words is True
        assert result.violations[0].position == text.lower().find("exciting opportunity")
    
    def test_swedish_banned_words(self):
        """Should detect Swedish banned words."""
        result = check_banned_words(
            "Detta är en spännande möjlighet.",
            SupportedLanguage.SWEDISH
        )
        assert result.has_banned_words is True


class TestEmojiDetection:
    """Tests for emoji detection."""
    
    def test_empty_text_no_emojis(self):
        """Empty text should have no emojis."""
        assert has_emojis("") is False
    
    def test_plain_text_no_emojis(self):
        """Plain text should have no emojis."""
        assert has_emojis("Hello, this is plain text.") is False
    
    def test_detects_smiley(self):
        """Should detect smiley emoji."""
        assert has_emojis("Hello 😀") is True
    
    def test_detects_heart(self):
        """Should detect heart emoji."""
        assert has_emojis("We love our team ❤️") is True
    
    def test_detects_flag(self):
        """Should detect flag emoji."""
        assert has_emojis("Based in 🇸🇪") is True
    
    def test_detects_multiple_emojis(self):
        """Should detect multiple emojis."""
        assert has_emojis("Great job! 🎉🎊🎈") is True
    
    def test_special_characters_not_emojis(self):
        """Special characters like © should not be detected as emojis."""
        assert has_emojis("Copyright © 2024") is False


class TestDashBulletDetection:
    """Tests for dash bullet detection."""
    
    def test_empty_text_no_dash_bullets(self):
        """Empty text should have no dash bullets."""
        assert has_dash_bullets("") is False
    
    def test_plain_text_no_dash_bullets(self):
        """Plain text should have no dash bullets."""
        assert has_dash_bullets("This is plain text.") is False
    
    def test_detects_hyphen_bullet(self):
        """Should detect hyphen-minus bullet."""
        assert has_dash_bullets("- First item\n- Second item") is True
    
    def test_detects_en_dash_bullet(self):
        """Should detect en dash bullet."""
        assert has_dash_bullets("– First item") is True
    
    def test_detects_em_dash_bullet(self):
        """Should detect em dash bullet."""
        assert has_dash_bullets("— First item") is True
    
    def test_detects_indented_dash_bullet(self):
        """Should detect indented dash bullets."""
        assert has_dash_bullets("  - Indented item") is True
    
    def test_hyphen_in_word_not_bullet(self):
        """Hyphens within words should not be detected as bullets."""
        assert has_dash_bullets("This is a well-known fact.") is False
    
    def test_asterisk_bullets_allowed(self):
        """Asterisk bullets should not be detected as dash bullets."""
        assert has_dash_bullets("* First item\n* Second item") is False


class TestGermanFormality:
    """Tests for German formality selection."""
    
    def test_empty_context_returns_sie(self):
        """Empty context should default to formal (Sie)."""
        assert get_german_formality("") == GermanFormality.SIE
    
    def test_startup_context_returns_du(self):
        """Startup context should return informal (du)."""
        assert get_german_formality("We are a tech startup") == GermanFormality.DU
    
    def test_banking_context_returns_sie(self):
        """Banking context should return formal (Sie)."""
        assert get_german_formality("Leading bank in Europe") == GermanFormality.SIE
    
    def test_tech_company_returns_du(self):
        """Tech company context should return informal (du)."""
        assert get_german_formality("Innovative tech company with agile teams") == GermanFormality.DU
    
    def test_legal_context_returns_sie(self):
        """Legal context should return formal (Sie)."""
        assert get_german_formality("International law firm") == GermanFormality.SIE
    
    def test_mixed_context_prefers_formal(self):
        """When context is ambiguous, should prefer formal (Sie)."""
        # Equal informal and formal keywords
        result = get_german_formality("Modern banking")
        assert result == GermanFormality.SIE
    
    def test_case_insensitive(self):
        """Context matching should be case-insensitive."""
        assert get_german_formality("STARTUP") == GermanFormality.DU
        assert get_german_formality("BANKING") == GermanFormality.SIE
