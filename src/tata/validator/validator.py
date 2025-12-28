"""Comprehensive validator for Tata recruitment assistant.

This module provides validation capabilities for all Tata artifacts,
ensuring outputs meet quality standards and comply with requirements.

Requirements covered:
- 13.1: Always align outputs with the locked requirement profile
- 13.3: Ensure four must-have hard skills are clearly visible
- 13.4: Apply GlobalConnect terminology, tone, and brand per GC AI Language Guide
- 13.5: Enforce banned words list in job ads and candidate-facing texts
"""

from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Tuple, Union
from abc import abstractmethod
import re

from src.tata.memory.memory import Artifact, ArtifactType
from src.tata.modules.profile.profile import RequirementProfile
from src.tata.modules.jobad.jobad import JobAd, contains_module_naming
from src.tata.modules.screening.screening import ScreeningTemplate
from src.tata.modules.headhunting.headhunting import HeadhuntingMessages
from src.tata.modules.calendar.invite import CalendarInvite
from src.tata.session.session import SupportedLanguage
from src.tata.language.checker import (
    check_banned_words,
    has_emojis,
    has_dash_bullets,
    BannedWordCheck,
)


@dataclass
class ValidationError:
    """A validation error.
    
    Attributes:
        field: The field or section that failed validation
        message: Description of the error
        severity: Error severity (error, warning)
    """
    field: str
    message: str
    severity: str = "error"


@dataclass
class ValidationWarning:
    """A validation warning.
    
    Attributes:
        field: The field or section with a warning
        message: Description of the warning
    """
    field: str
    message: str


@dataclass
class ValidationResult:
    """Result of validation.
    
    Attributes:
        is_valid: True if validation passed (no errors)
        errors: List of validation errors
        warnings: List of validation warnings
    """
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    
    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one.
        
        Args:
            other: Another validation result to merge
            
        Returns:
            New ValidationResult with combined errors and warnings
        """
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


class Validator(Protocol):
    """Protocol for artifact validation.
    
    Implementations ensure outputs meet quality standards.
    """
    
    @abstractmethod
    def validate_against_profile(
        self,
        artifact: Artifact,
        profile: RequirementProfile
    ) -> ValidationResult:
        """Validate artifact against requirement profile.
        
        Args:
            artifact: The artifact to validate
            profile: The requirement profile to validate against
            
        Returns:
            ValidationResult with any errors or warnings
        """
        ...
    
    @abstractmethod
    def validate_language_compliance(
        self,
        text: str,
        language: SupportedLanguage
    ) -> ValidationResult:
        """Validate text for language compliance.
        
        Args:
            text: The text to validate
            language: The expected language
            
        Returns:
            ValidationResult with any errors or warnings
        """
        ...
    
    @abstractmethod
    def validate_must_have_visibility(
        self,
        artifact: Artifact,
        must_haves: Tuple[str, str, str, str]
    ) -> ValidationResult:
        """Validate that must-haves are visible in artifact.
        
        Args:
            artifact: The artifact to validate
            must_haves: The four must-have skills
            
        Returns:
            ValidationResult with any errors or warnings
        """
        ...
    
    @abstractmethod
    def validate_no_banned_words(
        self,
        text: str,
        language: SupportedLanguage
    ) -> ValidationResult:
        """Validate text contains no banned words.
        
        Args:
            text: The text to validate
            language: The language for banned word checking
            
        Returns:
            ValidationResult with any errors or warnings
        """
        ...



def validate_against_profile(
    artifact: Artifact,
    profile: RequirementProfile
) -> ValidationResult:
    """Validate artifact against requirement profile.
    
    Ensures the artifact aligns with the locked requirement profile
    per Requirement 13.1.
    
    Args:
        artifact: The artifact to validate
        profile: The requirement profile to validate against
        
    Returns:
        ValidationResult with any errors or warnings
    """
    errors: List[ValidationError] = []
    warnings: List[ValidationWarning] = []
    
    artifact_type = artifact.artifact_type
    
    if artifact_type == ArtifactType.JOB_AD:
        job_ad: JobAd = artifact  # type: ignore
        
        # Check position title matches
        if profile.position_title.lower() not in job_ad.headline.lower():
            warnings.append(ValidationWarning(
                field="headline",
                message=f"Headline may not match position title '{profile.position_title}'"
            ))
        
        # Check must-haves are present
        for i, must_have in enumerate(profile.must_have_skills):
            if must_have not in job_ad.requirements.must_haves:
                errors.append(ValidationError(
                    field=f"requirements.must_haves[{i}]",
                    message=f"Must-have skill '{must_have}' not found in job ad requirements"
                ))
        
        # Check responsibilities are derived from profile
        if profile.primary_responsibilities:
            profile_resp_words = set()
            for resp in profile.primary_responsibilities:
                profile_resp_words.update(
                    word.lower() for word in resp.split() if len(word) > 4
                )
            
            job_ad_resp_text = " ".join(job_ad.responsibilities).lower()
            matches = sum(1 for word in profile_resp_words if word in job_ad_resp_text)
            
            if matches < len(profile_resp_words) * 0.3:
                warnings.append(ValidationWarning(
                    field="responsibilities",
                    message="Job ad responsibilities may not align well with profile"
                ))
    
    elif artifact_type in (ArtifactType.TA_SCREENING_TEMPLATE, ArtifactType.HM_SCREENING_TEMPLATE):
        template: ScreeningTemplate = artifact  # type: ignore
        
        # Check that skill questions cover must-haves
        template_skills = {sq.skill_name.lower() for sq in template.skill_questions}
        
        for must_have in profile.must_have_skills:
            must_have_lower = must_have.lower()
            # Check if any template skill matches
            found = any(
                must_have_lower in skill or skill in must_have_lower
                for skill in template_skills
            )
            if not found:
                warnings.append(ValidationWarning(
                    field="skill_questions",
                    message=f"Must-have skill '{must_have}' may not have questions in template"
                ))
    
    elif artifact_type == ArtifactType.HEADHUNTING_MESSAGES:
        messages: HeadhuntingMessages = artifact  # type: ignore
        
        # Check that messages reference the role
        position_words = set(
            word.lower() for word in profile.position_title.split() if len(word) > 3
        )
        
        # Check English message as representative
        en_text = messages.short_direct.en.lower()
        matches = sum(1 for word in position_words if word in en_text)
        
        if matches < len(position_words) * 0.5:
            warnings.append(ValidationWarning(
                field="short_direct.en",
                message="Headhunting message may not clearly reference the position"
            ))
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_language_compliance(
    text: str,
    language: SupportedLanguage
) -> ValidationResult:
    """Validate text for language compliance.
    
    Checks for:
    - No emojis (Requirement 2.5)
    - No dash bullets (Requirement 2.6)
    - No module naming exposure (Requirement 3.5)
    - GlobalConnect terminology compliance (Requirement 13.4)
    
    Args:
        text: The text to validate
        language: The expected language
        
    Returns:
        ValidationResult with any errors or warnings
    """
    errors: List[ValidationError] = []
    warnings: List[ValidationWarning] = []
    
    if not text:
        return ValidationResult(is_valid=True, errors=[], warnings=[])
    
    # Check for emojis (Requirement 2.5)
    if has_emojis(text):
        errors.append(ValidationError(
            field="text",
            message="Text contains emojis which are not allowed"
        ))
    
    # Check for dash bullets (Requirement 2.6)
    if has_dash_bullets(text):
        warnings.append(ValidationWarning(
            field="text",
            message="Text contains dash-style bullets which should be avoided"
        ))
    
    # Check for module naming exposure (Requirement 3.5)
    if contains_module_naming(text):
        errors.append(ValidationError(
            field="text",
            message="Text contains module naming (Module A, B, etc.) which should not be exposed"
        ))
    
    # Check for GlobalConnect terminology
    gc_terms = {
        "globalconnect": ["GlobalConnect", "Global Connect"],
        "gc": ["GC"],
    }
    
    text_lower = text.lower()
    for term, correct_forms in gc_terms.items():
        if term in text_lower:
            # Check if it's in correct form
            found_correct = any(form in text for form in correct_forms)
            if not found_correct and term == "globalconnect":
                warnings.append(ValidationWarning(
                    field="text",
                    message="GlobalConnect should be written as one word with capital G and C"
                ))
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_must_have_visibility(
    artifact: Artifact,
    must_haves: Tuple[str, str, str, str]
) -> ValidationResult:
    """Validate that must-haves are visible in artifact.
    
    Ensures four must-have hard skills are clearly visible
    per Requirement 13.3.
    
    Args:
        artifact: The artifact to validate
        must_haves: The four must-have skills
        
    Returns:
        ValidationResult with any errors or warnings
    """
    errors: List[ValidationError] = []
    warnings: List[ValidationWarning] = []
    
    artifact_type = artifact.artifact_type
    
    # Get text representation of artifact
    artifact_text = ""
    
    if artifact_type == ArtifactType.JOB_AD:
        job_ad: JobAd = artifact  # type: ignore
        artifact_text = job_ad.to_text()
        
        # Also check that must-haves are in the requirements section specifically
        for i, must_have in enumerate(must_haves):
            if must_have not in job_ad.requirements.must_haves:
                errors.append(ValidationError(
                    field=f"requirements.must_haves[{i}]",
                    message=f"Must-have '{must_have}' not in requirements section"
                ))
    
    elif artifact_type in (ArtifactType.TA_SCREENING_TEMPLATE, ArtifactType.HM_SCREENING_TEMPLATE):
        template: ScreeningTemplate = artifact  # type: ignore
        artifact_text = " ".join(
            sq.skill_name + " " + sq.main_question
            for sq in template.skill_questions
        )
    
    elif artifact_type == ArtifactType.HEADHUNTING_MESSAGES:
        messages: HeadhuntingMessages = artifact  # type: ignore
        artifact_text = (
            messages.short_direct.en + " " +
            messages.value_proposition.en + " " +
            messages.call_to_action.en
        )
    
    else:
        # For other artifact types, use JSON representation
        artifact_text = artifact.to_json()
    
    # Check visibility of each must-have
    artifact_text_lower = artifact_text.lower()
    visible_count = 0
    
    for must_have in must_haves:
        # Check if key words from must-have appear in artifact
        must_have_words = [
            word.lower() for word in must_have.split() if len(word) > 3
        ]
        
        if must_have_words:
            matches = sum(1 for word in must_have_words if word in artifact_text_lower)
            if matches >= len(must_have_words) * 0.5:
                visible_count += 1
            else:
                warnings.append(ValidationWarning(
                    field="must_haves",
                    message=f"Must-have '{must_have}' may not be clearly visible"
                ))
    
    # All 4 must-haves should be visible
    if visible_count < 4:
        errors.append(ValidationError(
            field="must_haves",
            message=f"Only {visible_count}/4 must-have skills are clearly visible"
        ))
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_no_banned_words(
    text: str,
    language: SupportedLanguage = SupportedLanguage.ENGLISH
) -> ValidationResult:
    """Validate text contains no banned words.
    
    Enforces the banned words list per Requirement 13.5.
    
    Args:
        text: The text to validate
        language: The language for banned word checking
        
    Returns:
        ValidationResult with any errors or warnings
    """
    errors: List[ValidationError] = []
    warnings: List[ValidationWarning] = []
    
    if not text:
        return ValidationResult(is_valid=True, errors=[], warnings=[])
    
    # Check for banned words
    banned_check: BannedWordCheck = check_banned_words(text, language)
    
    if banned_check.has_banned_words:
        for violation in banned_check.violations:
            errors.append(ValidationError(
                field="text",
                message=f"Banned word '{violation.word}' found at position {violation.position}. "
                        f"Suggestion: {violation.suggestion}"
            ))
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_artifact_comprehensive(
    artifact: Artifact,
    profile: Optional[RequirementProfile] = None,
    language: SupportedLanguage = SupportedLanguage.ENGLISH
) -> ValidationResult:
    """Perform comprehensive validation on an artifact.
    
    Combines all validation checks:
    - Profile alignment (if profile provided)
    - Language compliance
    - Must-have visibility (if profile provided)
    - Banned words check
    
    Args:
        artifact: The artifact to validate
        profile: Optional requirement profile for alignment checks
        language: The language for validation
        
    Returns:
        Combined ValidationResult
    """
    result = ValidationResult(is_valid=True, errors=[], warnings=[])
    
    # Get text representation for language checks
    artifact_text = artifact.to_json()
    
    # For specific artifact types, get better text representation
    if artifact.artifact_type == ArtifactType.JOB_AD:
        job_ad: JobAd = artifact  # type: ignore
        artifact_text = job_ad.to_text()
    
    # Language compliance check
    lang_result = validate_language_compliance(artifact_text, language)
    result = result.merge(lang_result)
    
    # Banned words check
    banned_result = validate_no_banned_words(artifact_text, language)
    result = result.merge(banned_result)
    
    # Profile-dependent checks
    if profile:
        # Profile alignment
        profile_result = validate_against_profile(artifact, profile)
        result = result.merge(profile_result)
        
        # Must-have visibility
        must_have_result = validate_must_have_visibility(
            artifact, profile.must_have_skills
        )
        result = result.merge(must_have_result)
    
    return result
