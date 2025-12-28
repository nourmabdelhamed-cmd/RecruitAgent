"""Tests for the Validator module.

Tests cover:
- Profile alignment validation
- Language compliance validation
- Must-have visibility validation
- Banned words validation
- Requirements 13.1, 13.3, 13.4, 13.5
"""

import pytest
from datetime import datetime

from src.tata.validator.validator import (
    ValidationResult,
    ValidationError,
    ValidationWarning,
    validate_against_profile,
    validate_language_compliance,
    validate_must_have_visibility,
    validate_no_banned_words,
    validate_artifact_comprehensive,
)
from src.tata.modules.profile.profile import (
    RequirementProfile,
    ContentSource,
)
from src.tata.modules.jobad.jobad import (
    JobAd,
    RequirementsSection,
)
from src.tata.session.session import SupportedLanguage


@pytest.fixture
def sample_profile():
    """Create a sample requirement profile for testing."""
    return RequirementProfile(
        position_title="Software Engineer",
        must_have_skills=(
            "Python programming",
            "SQL databases",
            "REST APIs",
            "Git version control",
        ),
        must_have_sources=(
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
        ),
        primary_responsibilities=[
            "Develop new features",
            "Write tests",
            "Code reviews",
        ],
        responsibility_sources=[
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
        ],
    )


@pytest.fixture
def sample_job_ad():
    """Create a sample job ad for testing."""
    return JobAd(
        headline="Software Engineer",
        intro="Join our team as a Software Engineer.",
        role_description="You will develop features and write tests.",
        the_why="This role matters.",
        responsibilities=["Develop features", "Write tests", "Review code"],
        requirements=RequirementsSection(
            must_haves=(
                "Python programming",
                "SQL databases",
                "REST APIs",
                "Git version control",
            ),
            soft_skills="We value teamwork.",
            good_to_haves="Docker is a plus.",
        ),
        soft_skills_paragraph="We look for collaborative people.",
        team_and_why_gc="Join GlobalConnect.",
        process="Our process is smooth.",
        ending="Apply now!",
    )


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_create_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_create_invalid_result(self):
        """Test creating an invalid result."""
        result = ValidationResult(
            is_valid=False,
            errors=[ValidationError(field="test", message="Error")],
        )
        assert not result.is_valid
        assert len(result.errors) == 1
    
    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult(
            is_valid=True,
            warnings=[ValidationWarning(field="a", message="Warning 1")],
        )
        result2 = ValidationResult(
            is_valid=False,
            errors=[ValidationError(field="b", message="Error 1")],
        )
        merged = result1.merge(result2)
        assert not merged.is_valid
        assert len(merged.errors) == 1
        assert len(merged.warnings) == 1


class TestValidateAgainstProfile:
    """Tests for validate_against_profile function."""
    
    def test_valid_job_ad_passes(self, sample_profile, sample_job_ad):
        """Test that a valid job ad passes validation."""
        result = validate_against_profile(sample_job_ad, sample_profile)
        assert result.is_valid
    
    def test_missing_must_have_fails(self, sample_profile):
        """Test that missing must-have fails validation."""
        job_ad = JobAd(
            headline="Software Engineer",
            intro="Join us.",
            role_description="Develop.",
            the_why="Important.",
            responsibilities=["Develop"],
            requirements=RequirementsSection(
                must_haves=(
                    "Python programming",
                    "SQL databases",
                    "REST APIs",
                    "Different skill",  # Not matching profile
                ),
                soft_skills="Teamwork.",
                good_to_haves="",
            ),
            soft_skills_paragraph="Collaborative.",
            team_and_why_gc="GlobalConnect.",
            process="Smooth.",
            ending="Apply!",
        )
        result = validate_against_profile(job_ad, sample_profile)
        assert not result.is_valid
        assert any("Git version control" in e.message for e in result.errors)


class TestValidateLanguageCompliance:
    """Tests for validate_language_compliance function."""
    
    def test_clean_text_passes(self):
        """Test that clean text passes validation."""
        result = validate_language_compliance(
            "This is clean text without issues.",
            SupportedLanguage.ENGLISH,
        )
        assert result.is_valid
    
    def test_emoji_fails(self):
        """Test that text with emojis fails validation."""
        result = validate_language_compliance(
            "Great opportunity! 🚀",
            SupportedLanguage.ENGLISH,
        )
        assert not result.is_valid
        assert any("emoji" in e.message.lower() for e in result.errors)
    
    def test_dash_bullets_warns(self):
        """Test that dash bullets generate warning."""
        result = validate_language_compliance(
            "Requirements:\n- Python\n- SQL",
            SupportedLanguage.ENGLISH,
        )
        assert any("dash" in w.message.lower() for w in result.warnings)
    
    def test_module_naming_fails(self):
        """Test that module naming fails validation."""
        result = validate_language_compliance(
            "Please complete Module A first.",
            SupportedLanguage.ENGLISH,
        )
        assert not result.is_valid
        assert any("module" in e.message.lower() for e in result.errors)
    
    def test_empty_text_passes(self):
        """Test that empty text passes validation."""
        result = validate_language_compliance("", SupportedLanguage.ENGLISH)
        assert result.is_valid


class TestValidateMustHaveVisibility:
    """Tests for validate_must_have_visibility function."""
    
    def test_all_must_haves_visible_passes(self, sample_profile, sample_job_ad):
        """Test that all must-haves visible passes."""
        result = validate_must_have_visibility(
            sample_job_ad,
            sample_profile.must_have_skills,
        )
        assert result.is_valid
    
    def test_missing_must_have_fails(self, sample_profile):
        """Test that missing must-have fails."""
        job_ad = JobAd(
            headline="Engineer",
            intro="Join us.",
            role_description="Work.",
            the_why="Important.",
            responsibilities=["Work"],
            requirements=RequirementsSection(
                must_haves=(
                    "Unrelated skill 1",
                    "Unrelated skill 2",
                    "Unrelated skill 3",
                    "Unrelated skill 4",
                ),
                soft_skills="",
                good_to_haves="",
            ),
            soft_skills_paragraph="",
            team_and_why_gc="",
            process="",
            ending="",
        )
        result = validate_must_have_visibility(
            job_ad,
            sample_profile.must_have_skills,
        )
        assert not result.is_valid


class TestValidateNoBannedWords:
    """Tests for validate_no_banned_words function."""
    
    def test_clean_text_passes(self):
        """Test that clean text passes."""
        result = validate_no_banned_words(
            "We are looking for a talented engineer.",
            SupportedLanguage.ENGLISH,
        )
        assert result.is_valid
    
    def test_empty_text_passes(self):
        """Test that empty text passes."""
        result = validate_no_banned_words("", SupportedLanguage.ENGLISH)
        assert result.is_valid


class TestValidateArtifactComprehensive:
    """Tests for validate_artifact_comprehensive function."""
    
    def test_comprehensive_validation_passes(self, sample_profile, sample_job_ad):
        """Test comprehensive validation on valid artifact."""
        result = validate_artifact_comprehensive(
            sample_job_ad,
            profile=sample_profile,
            language=SupportedLanguage.ENGLISH,
        )
        assert result.is_valid
    
    def test_comprehensive_without_profile(self, sample_job_ad):
        """Test comprehensive validation without profile."""
        result = validate_artifact_comprehensive(
            sample_job_ad,
            profile=None,
            language=SupportedLanguage.ENGLISH,
        )
        # Should still run language and banned word checks
        assert isinstance(result, ValidationResult)
    
    def test_comprehensive_catches_emoji(self, sample_profile):
        """Test comprehensive validation catches emojis."""
        job_ad = JobAd(
            headline="Software Engineer 🚀",
            intro="Join us!",
            role_description="Develop.",
            the_why="Important.",
            responsibilities=["Develop"],
            requirements=RequirementsSection(
                must_haves=sample_profile.must_have_skills,
                soft_skills="",
                good_to_haves="",
            ),
            soft_skills_paragraph="",
            team_and_why_gc="",
            process="",
            ending="",
        )
        result = validate_artifact_comprehensive(
            job_ad,
            profile=sample_profile,
            language=SupportedLanguage.ENGLISH,
        )
        assert not result.is_valid
        assert any("emoji" in e.message.lower() for e in result.errors)
