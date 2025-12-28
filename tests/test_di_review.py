"""Tests for D&I Review module (Module I).

Tests the DIReviewProcessor for detecting biased language
and generating inclusive alternatives.

Requirements covered:
- 10.1: Assess job ad text for inclusivity, bias, gendered language
- 10.2: Highlight flagged terms, tone issues, or gaps
- 10.3: Suggest alternative wording
- 10.4: Never change the job ad automatically
- 10.5: Provide feedback report with flagged words, alternatives, score
- 10.6: Check against comprehensive word pools for all bias categories
"""

import pytest
from datetime import datetime

from src.tata.session.session import SupportedLanguage
from src.tata.memory.memory import ArtifactType
from src.tata.modules.review.di import (
    BiasCategory,
    Severity,
    FlaggedItem,
    CategoryScore,
    DIReviewInput,
    DIReview,
    DIReviewProcessor,
    InvalidInputError,
    scan_for_bias,
    scan_german_titles,
    calculate_readability_score,
    GENDER_BIAS_WORDS,
    AGE_BIAS_WORDS,
    DISABILITY_BIAS_WORDS,
)


class TestDIReviewTypes:
    """Tests for D&I Review data types."""
    
    def test_bias_category_enum_values(self):
        """Test BiasCategory enum has all required categories."""
        assert BiasCategory.GENDER.value == "gender"
        assert BiasCategory.AGE.value == "age"
        assert BiasCategory.DISABILITY.value == "disability"
        assert BiasCategory.NATIONALITY.value == "nationality"
        assert BiasCategory.FAMILY.value == "family"
        assert BiasCategory.SOCIOECONOMIC.value == "socioeconomic"
        assert BiasCategory.READABILITY.value == "readability"
        assert BiasCategory.REQUIREMENTS.value == "requirements"
        assert BiasCategory.GERMAN_TITLE.value == "german_title"
        assert BiasCategory.LOCATION.value == "location"
    
    def test_severity_enum_values(self):
        """Test Severity enum values."""
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
    
    def test_flagged_item_creation(self):
        """Test FlaggedItem dataclass creation."""
        item = FlaggedItem(
            text="aggressive",
            category=BiasCategory.GENDER,
            severity=Severity.HIGH,
            explanation="Masculine-coded term",
            alternatives=["driven", "ambitious"],
            position=10,
        )
        
        assert item.text == "aggressive"
        assert item.category == BiasCategory.GENDER
        assert item.severity == Severity.HIGH
        assert item.explanation == "Masculine-coded term"
        assert item.alternatives == ["driven", "ambitious"]
        assert item.position == 10
    
    def test_category_score_creation(self):
        """Test CategoryScore dataclass creation."""
        score = CategoryScore(
            category=BiasCategory.GENDER,
            score=85,
            issues_found=1,
        )
        
        assert score.category == BiasCategory.GENDER
        assert score.score == 85
        assert score.issues_found == 1
    
    def test_di_review_input_defaults(self):
        """Test DIReviewInput default values."""
        input_data = DIReviewInput(job_ad_text="Test job ad")
        
        assert input_data.job_ad_text == "Test job ad"
        assert input_data.language == SupportedLanguage.ENGLISH
    
    def test_di_review_artifact_type(self):
        """Test DIReview artifact_type property."""
        review = DIReview(
            overall_score=90,
            category_scores=[],
            flagged_items=[],
            suggested_alternatives=[],
            compliance_notes=[],
            original_text="Test",
        )
        
        assert review.artifact_type == ArtifactType.DI_REVIEW
    
    def test_di_review_to_json(self):
        """Test DIReview JSON serialization."""
        review = DIReview(
            overall_score=85,
            category_scores=[
                CategoryScore(BiasCategory.GENDER, 100, 0),
            ],
            flagged_items=[
                FlaggedItem(
                    text="ninja",
                    category=BiasCategory.GENDER,
                    severity=Severity.HIGH,
                    explanation="Gendered tech jargon",
                    alternatives=["expert"],
                    position=5,
                ),
            ],
            suggested_alternatives=[],
            compliance_notes=["Test note"],
            original_text="Test text",
        )
        
        json_str = review.to_json()
        assert "overall_score" in json_str
        assert "85" in json_str
        assert "ninja" in json_str
        assert "gender" in json_str


class TestBiasDetection:
    """Tests for bias detection functions."""
    
    def test_scan_for_gender_bias_english(self):
        """Test scanning for gender-biased words in English."""
        text = "We need an aggressive ninja to join our team."
        flagged = scan_for_bias(
            text,
            SupportedLanguage.ENGLISH,
            BiasCategory.GENDER,
            GENDER_BIAS_WORDS,
        )
        
        assert len(flagged) == 2
        words_found = {f.text for f in flagged}
        assert "aggressive" in words_found
        assert "ninja" in words_found
    
    def test_scan_for_age_bias_english(self):
        """Test scanning for age-biased words in English."""
        text = "Looking for a young and dynamic digital native."
        flagged = scan_for_bias(
            text,
            SupportedLanguage.ENGLISH,
            BiasCategory.AGE,
            AGE_BIAS_WORDS,
        )
        
        assert len(flagged) >= 2
        words_found = {f.text.lower() for f in flagged}
        assert "young and dynamic" in words_found or "digital native" in words_found
    
    def test_scan_for_disability_bias_english(self):
        """Test scanning for disability-biased words in English."""
        text = "Must be able-bodied and physically fit."
        flagged = scan_for_bias(
            text,
            SupportedLanguage.ENGLISH,
            BiasCategory.DISABILITY,
            DISABILITY_BIAS_WORDS,
        )
        
        assert len(flagged) >= 1
        words_found = {f.text.lower() for f in flagged}
        assert "able-bodied" in words_found or "physically fit" in words_found
    
    def test_scan_no_bias_found(self):
        """Test scanning text with no bias words."""
        text = "We are looking for a skilled professional to join our team."
        flagged = scan_for_bias(
            text,
            SupportedLanguage.ENGLISH,
            BiasCategory.GENDER,
            GENDER_BIAS_WORDS,
        )
        
        assert len(flagged) == 0
    
    def test_scan_word_boundaries(self):
        """Test that partial word matches are not flagged."""
        text = "We need someone with programming skills."
        flagged = scan_for_bias(
            text,
            SupportedLanguage.ENGLISH,
            BiasCategory.GENDER,
            GENDER_BIAS_WORDS,
        )
        
        # "programming" should not match "man" or similar
        assert len(flagged) == 0
    
    def test_scan_case_insensitive(self):
        """Test that scanning is case-insensitive."""
        text = "We need an AGGRESSIVE NINJA."
        flagged = scan_for_bias(
            text,
            SupportedLanguage.ENGLISH,
            BiasCategory.GENDER,
            GENDER_BIAS_WORDS,
        )
        
        assert len(flagged) == 2
    
    def test_scan_swedish_bias(self):
        """Test scanning for bias in Swedish."""
        text = "Vi söker en aggressiv och dominant person."
        flagged = scan_for_bias(
            text,
            SupportedLanguage.SWEDISH,
            BiasCategory.GENDER,
            GENDER_BIAS_WORDS,
        )
        
        assert len(flagged) >= 1


class TestGermanTitleScanning:
    """Tests for German job title gender notation scanning."""
    
    def test_scan_german_title_without_notation(self):
        """Test detecting German titles without gender notation."""
        text = "Wir suchen einen Entwickler für unser Team."
        flagged = scan_german_titles(text)
        
        assert len(flagged) == 1
        assert flagged[0].text == "entwickler"
        assert flagged[0].category == BiasCategory.GERMAN_TITLE
    
    def test_scan_german_title_with_mwd(self):
        """Test that titles with (m/w/d) are not flagged."""
        text = "Wir suchen einen Entwickler (m/w/d) für unser Team."
        flagged = scan_german_titles(text)
        
        assert len(flagged) == 0
    
    def test_scan_german_title_with_colon_in(self):
        """Test that titles with :in are not flagged."""
        text = "Wir suchen eine:n Entwickler:in für unser Team."
        flagged = scan_german_titles(text)
        
        assert len(flagged) == 0
    
    def test_scan_multiple_german_titles(self):
        """Test scanning multiple German titles."""
        text = "Wir suchen einen Manager und einen Ingenieur."
        flagged = scan_german_titles(text)
        
        assert len(flagged) == 2
        titles_found = {f.text for f in flagged}
        assert "manager" in titles_found
        assert "ingenieur" in titles_found


class TestReadabilityScore:
    """Tests for readability scoring."""
    
    def test_readability_good_text(self):
        """Test readability score for well-written text."""
        text = "We are looking for a developer. The role involves coding. You will work with a team."
        score, notes = calculate_readability_score(text)
        
        assert score >= 80
    
    def test_readability_long_sentences(self):
        """Test readability penalty for long sentences."""
        # Create a sentence with more than 25 words
        long_sentence = " ".join(["word"] * 30) + "."
        score, notes = calculate_readability_score(long_sentence)
        
        assert score < 100
        assert any("sentences" in note.lower() for note in notes)
    
    def test_readability_jargon(self):
        """Test readability penalty for business jargon."""
        text = "We leverage synergy to create a paradigm shift in our holistic ecosystem."
        score, notes = calculate_readability_score(text)
        
        assert score < 100
        assert any("jargon" in note.lower() for note in notes)
    
    def test_readability_empty_text(self):
        """Test readability score for empty text."""
        score, notes = calculate_readability_score("")
        
        assert score == 100
        assert len(notes) == 0


class TestDIReviewProcessor:
    """Tests for DIReviewProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a DIReviewProcessor instance."""
        return DIReviewProcessor()
    
    def test_validate_valid_input(self, processor):
        """Test validation with valid input."""
        input_data = DIReviewInput(
            job_ad_text="We are looking for a software developer to join our team.",
            language=SupportedLanguage.ENGLISH,
        )
        
        result = processor.validate(input_data)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_empty_text(self, processor):
        """Test validation with empty text."""
        input_data = DIReviewInput(job_ad_text="")
        
        result = processor.validate(input_data)
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].field == "job_ad_text"
    
    def test_validate_short_text_warning(self, processor):
        """Test validation warning for short text."""
        input_data = DIReviewInput(job_ad_text="Short text")
        
        result = processor.validate(input_data)
        
        assert result.is_valid  # Still valid, just a warning
        assert len(result.warnings) == 1
        assert result.warnings[0].field == "job_ad_text"
    
    def test_process_clean_text(self, processor):
        """Test processing text with no bias issues."""
        input_data = DIReviewInput(
            job_ad_text="We are looking for a skilled professional to join our team. "
                       "The ideal candidate will have experience in software development.",
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        assert review.overall_score >= 80
        assert len(review.flagged_items) == 0
        assert review.original_text == input_data.job_ad_text
    
    def test_process_biased_text(self, processor):
        """Test processing text with bias issues."""
        input_data = DIReviewInput(
            job_ad_text="We need an aggressive ninja who is a digital native. "
                       "Must be young and dynamic with native English.",
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        # Score should be lower due to multiple bias issues
        assert review.overall_score <= 85
        assert len(review.flagged_items) > 0
        
        # Check that alternatives are provided (Requirement 10.3)
        for item in review.flagged_items:
            assert len(item.alternatives) > 0
    
    def test_process_preserves_original_text(self, processor):
        """Test that original text is preserved unchanged (Requirement 10.4)."""
        original = "We need an aggressive rockstar ninja."
        input_data = DIReviewInput(
            job_ad_text=original,
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        # Original text must be unchanged
        assert review.original_text == original
    
    def test_process_all_categories_checked(self, processor):
        """Test that all bias categories are checked (Requirement 10.6)."""
        input_data = DIReviewInput(
            job_ad_text="We are looking for a developer.",
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        # Should have scores for all categories
        categories_checked = {cs.category for cs in review.category_scores}
        
        assert BiasCategory.GENDER in categories_checked
        assert BiasCategory.AGE in categories_checked
        assert BiasCategory.DISABILITY in categories_checked
        assert BiasCategory.NATIONALITY in categories_checked
        assert BiasCategory.FAMILY in categories_checked
        assert BiasCategory.SOCIOECONOMIC in categories_checked
        assert BiasCategory.READABILITY in categories_checked
        assert BiasCategory.REQUIREMENTS in categories_checked
        assert BiasCategory.LOCATION in categories_checked
    
    def test_process_german_title_check(self, processor):
        """Test German title gender notation check."""
        input_data = DIReviewInput(
            job_ad_text="Wir suchen einen Entwickler und einen Manager für unser Team.",
            language=SupportedLanguage.GERMAN,
        )
        
        review = processor.process(input_data)
        
        # Should flag German titles without gender notation
        german_title_issues = [
            f for f in review.flagged_items
            if f.category == BiasCategory.GERMAN_TITLE
        ]
        assert len(german_title_issues) >= 1
    
    def test_process_invalid_input_raises(self, processor):
        """Test that invalid input raises InvalidInputError."""
        input_data = DIReviewInput(job_ad_text="")
        
        with pytest.raises(InvalidInputError):
            processor.process(input_data)
    
    def test_get_required_inputs(self, processor):
        """Test get_required_inputs method."""
        required = processor.get_required_inputs()
        
        assert "job_ad_text" in required
    
    def test_get_optional_inputs(self, processor):
        """Test get_optional_inputs method."""
        optional = processor.get_optional_inputs()
        
        assert "language" in optional
    
    def test_compliance_notes_generated(self, processor):
        """Test that compliance notes are generated (Requirement 10.5)."""
        input_data = DIReviewInput(
            job_ad_text="We need an aggressive ninja.",
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        assert len(review.compliance_notes) > 0
    
    def test_flagged_items_have_position(self, processor):
        """Test that flagged items include position information."""
        input_data = DIReviewInput(
            job_ad_text="We need a ninja developer.",
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        for item in review.flagged_items:
            assert item.position >= 0


class TestMultiLanguageSupport:
    """Tests for multi-language bias detection."""
    
    @pytest.fixture
    def processor(self):
        return DIReviewProcessor()
    
    def test_swedish_bias_detection(self, processor):
        """Test bias detection in Swedish."""
        input_data = DIReviewInput(
            job_ad_text="Vi söker en aggressiv och ung och dynamisk person.",
            language=SupportedLanguage.SWEDISH,
        )
        
        review = processor.process(input_data)
        
        assert len(review.flagged_items) >= 1
    
    def test_danish_bias_detection(self, processor):
        """Test bias detection in Danish."""
        input_data = DIReviewInput(
            job_ad_text="Vi søger en aggressiv og ung og dynamisk person.",
            language=SupportedLanguage.DANISH,
        )
        
        review = processor.process(input_data)
        
        assert len(review.flagged_items) >= 1
    
    def test_norwegian_bias_detection(self, processor):
        """Test bias detection in Norwegian."""
        input_data = DIReviewInput(
            job_ad_text="Vi søker en aggressiv og ung og dynamisk person.",
            language=SupportedLanguage.NORWEGIAN,
        )
        
        review = processor.process(input_data)
        
        assert len(review.flagged_items) >= 1
    
    def test_german_bias_detection(self, processor):
        """Test bias detection in German."""
        input_data = DIReviewInput(
            job_ad_text="Wir suchen eine aggressive und jung und dynamisch Person.",
            language=SupportedLanguage.GERMAN,
        )
        
        review = processor.process(input_data)
        
        assert len(review.flagged_items) >= 1
