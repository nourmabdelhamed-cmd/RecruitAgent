"""Requirement Profile module for Tata recruitment assistant.

This module implements Module A: Requirement Profile creation.
The requirement profile is the foundational document containing must-have skills,
responsibilities, and role details that serves as the backbone for all outputs.

Requirements covered:
- 4.1: Extract four must-have skills/qualifications from recruiter input
- 4.2: Extract primary responsibilities and key tasks written simply
- 4.6: Never invent requirements or responsibilities not provided by recruiter
- 13.2: Never invent responsibilities or requirements not provided
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple, Protocol, Dict, Set
from abc import abstractmethod
import json
import re

from src.tata.memory.memory import ArtifactType, Artifact


class ContentSource(Enum):
    """Source of extracted content for traceability.
    
    Tracks where each piece of content originated to ensure
    no invented content per Requirements 4.6 and 13.2.
    """
    STARTUP_NOTES = "startup_notes"
    OLD_JOB_AD = "old_job_ad"
    HIRING_MANAGER_INPUT = "hiring_manager_input"
    RECRUITER_INPUT = "recruiter_input"


@dataclass
class TrackedContent:
    """Content with source tracking for traceability.
    
    Ensures all content can be traced back to recruiter-provided input.
    
    Attributes:
        content: The actual text content
        source: Where this content originated
        original_text: The original text this was extracted from
    """
    content: str
    source: ContentSource
    original_text: str


@dataclass
class TeamInfo:
    """Team-related information.
    
    Attributes:
        size: Number of team members
        location: Team location(s)
        collaboration_style: How the team works together
    """
    size: int
    location: str
    collaboration_style: str


@dataclass
class ValidationError:
    """A validation error for input data.
    
    Attributes:
        field: The field that failed validation
        message: Description of the error
    """
    field: str
    message: str


@dataclass
class ValidationWarning:
    """A validation warning for input data.
    
    Attributes:
        field: The field with a warning
        message: Description of the warning
    """
    field: str
    message: str


@dataclass
class ValidationResult:
    """Result of input validation.
    
    Attributes:
        is_valid: True if validation passed
        errors: List of validation errors
        warnings: List of validation warnings
    """
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)


class InvalidInputError(Exception):
    """Raised when input validation fails."""
    pass


class InsufficientSkillsError(Exception):
    """Raised when fewer than 4 must-have skills can be extracted."""
    pass


@dataclass
class RequirementProfileInput:
    """Input for creating a requirement profile.
    
    At least startup_notes must be provided. Additional sources
    (old_job_ad, hiring_manager_input) enrich the profile.
    
    Attributes:
        startup_notes: Notes from the recruitment start-up meeting (required)
        old_job_ad: Previous job advertisement for the role (optional)
        hiring_manager_input: Direct input from the hiring manager (optional)
    """
    startup_notes: str
    old_job_ad: Optional[str] = None
    hiring_manager_input: Optional[str] = None


@dataclass
class RequirementProfile:
    """Core artifact for a recruitment.
    
    The requirement profile is the foundational document that all other
    modules depend on. It contains exactly 4 must-have skills as required
    by Requirement 4.1.
    
    Attributes:
        position_title: The job title
        must_have_skills: Exactly 4 must-have skills (tuple enforces count)
        must_have_sources: Source tracking for each must-have skill
        primary_responsibilities: List of key responsibilities
        responsibility_sources: Source tracking for responsibilities
        good_to_haves: Optional nice-to-have skills
        soft_skills: Optional soft skills
        motivations: Optional motivations/USPs for the role
        team_info: Optional team information
        bu_description: Optional business unit description
        created_at: When the profile was created
    """
    position_title: str
    must_have_skills: Tuple[str, str, str, str]  # Exactly 4 must-haves
    must_have_sources: Tuple[ContentSource, ContentSource, ContentSource, ContentSource]
    primary_responsibilities: List[str]
    responsibility_sources: List[ContentSource]
    good_to_haves: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    motivations: List[str] = field(default_factory=list)
    team_info: Optional[TeamInfo] = None
    bu_description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type for memory storage."""
        return ArtifactType.REQUIREMENT_PROFILE
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "position_title": self.position_title,
            "must_have_skills": list(self.must_have_skills),
            "must_have_sources": [s.value for s in self.must_have_sources],
            "primary_responsibilities": self.primary_responsibilities,
            "responsibility_sources": [s.value for s in self.responsibility_sources],
            "good_to_haves": self.good_to_haves,
            "soft_skills": self.soft_skills,
            "motivations": self.motivations,
            "team_info": {
                "size": self.team_info.size,
                "location": self.team_info.location,
                "collaboration_style": self.team_info.collaboration_style,
            } if self.team_info else None,
            "bu_description": self.bu_description,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data, indent=2)
    
    def get_all_tracked_content(self) -> List[TrackedContent]:
        """Get all content with source tracking.
        
        Returns a list of all content items with their sources,
        useful for verifying no invented content.
        """
        tracked = []
        
        # Track must-have skills
        for skill, source in zip(self.must_have_skills, self.must_have_sources):
            tracked.append(TrackedContent(
                content=skill,
                source=source,
                original_text=skill  # In real impl, would store original
            ))
        
        # Track responsibilities
        for resp, source in zip(self.primary_responsibilities, self.responsibility_sources):
            tracked.append(TrackedContent(
                content=resp,
                source=source,
                original_text=resp
            ))
        
        return tracked



class RequirementProfileProcessor:
    """Processor for creating requirement profiles from recruiter input.
    
    Implements the ModuleProcessor pattern for Module A.
    Extracts skills, responsibilities, and other profile data from
    recruiter-provided input while ensuring no content is invented.
    
    Requirements covered:
    - 4.1: Extract four must-have skills/qualifications
    - 4.2: Extract primary responsibilities and key tasks
    - 4.6: Never invent requirements not provided by recruiter
    - 13.2: Never invent responsibilities or requirements not provided
    """
    
    # Keywords that indicate must-have skills in text
    MUST_HAVE_INDICATORS = [
        "must have", "required", "essential", "mandatory", "need to have",
        "necessary", "critical", "key requirement", "must possess",
        "required skill", "must be able to", "should have experience in",
    ]
    
    # Keywords that indicate responsibilities
    RESPONSIBILITY_INDICATORS = [
        "responsible for", "will be", "duties include", "tasks include",
        "you will", "the role involves", "key responsibilities",
        "main tasks", "day-to-day", "accountable for",
    ]
    
    # Keywords that indicate good-to-have skills
    GOOD_TO_HAVE_INDICATORS = [
        "nice to have", "good to have", "preferred", "bonus", "plus",
        "advantageous", "desirable", "ideally", "would be great",
    ]
    
    def validate(self, input_data: RequirementProfileInput) -> ValidationResult:
        """Validate input data before processing.
        
        Args:
            input_data: The input to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # Check required field
        if not input_data.startup_notes or not input_data.startup_notes.strip():
            errors.append(ValidationError(
                field="startup_notes",
                message="Startup notes are required and cannot be empty"
            ))
        elif len(input_data.startup_notes.strip()) < 50:
            warnings.append(ValidationWarning(
                field="startup_notes",
                message="Startup notes are very short; may not contain enough information for a complete profile"
            ))
        
        # Check for potential skill extraction
        if input_data.startup_notes:
            combined_text = self._combine_input_sources(input_data)
            potential_skills = self._extract_potential_skills(combined_text)
            if len(potential_skills) < 4:
                warnings.append(ValidationWarning(
                    field="startup_notes",
                    message=f"Only {len(potential_skills)} potential must-have skills detected; 4 are required"
                ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def process(
        self,
        input_data: RequirementProfileInput,
        position_title: str,
    ) -> RequirementProfile:
        """Process input and generate a requirement profile.
        
        Args:
            input_data: The recruiter-provided input
            position_title: The job position title
            
        Returns:
            A complete RequirementProfile
            
        Raises:
            InvalidInputError: If input validation fails
            InsufficientSkillsError: If fewer than 4 skills can be extracted
        """
        # Validate first
        validation = self.validate(input_data)
        if not validation.is_valid:
            error_msgs = "; ".join(e.message for e in validation.errors)
            raise InvalidInputError(f"Input validation failed: {error_msgs}")
        
        # Combine all input sources
        combined_text = self._combine_input_sources(input_data)
        
        # Extract must-have skills with sources
        skills_with_sources = self._extract_must_have_skills(input_data)
        if len(skills_with_sources) < 4:
            raise InsufficientSkillsError(
                f"Could only extract {len(skills_with_sources)} must-have skills; 4 are required"
            )
        
        # Take exactly 4 skills
        top_skills = skills_with_sources[:4]
        must_have_skills = tuple(s[0] for s in top_skills)
        must_have_sources = tuple(s[1] for s in top_skills)
        
        # Extract responsibilities with sources
        responsibilities_with_sources = self._extract_responsibilities(input_data)
        responsibilities = [r[0] for r in responsibilities_with_sources]
        responsibility_sources = [r[1] for r in responsibilities_with_sources]
        
        # Extract good-to-haves
        good_to_haves = self._extract_good_to_haves(combined_text)
        
        # Extract soft skills
        soft_skills = self._extract_soft_skills(combined_text)
        
        return RequirementProfile(
            position_title=position_title,
            must_have_skills=must_have_skills,  # type: ignore
            must_have_sources=must_have_sources,  # type: ignore
            primary_responsibilities=responsibilities,
            responsibility_sources=responsibility_sources,
            good_to_haves=good_to_haves,
            soft_skills=soft_skills,
        )
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input fields."""
        return ["startup_notes"]
    
    def get_optional_inputs(self) -> List[str]:
        """Get list of optional input fields."""
        return ["old_job_ad", "hiring_manager_input"]
    
    def _combine_input_sources(self, input_data: RequirementProfileInput) -> str:
        """Combine all input sources into a single text.
        
        Args:
            input_data: The input data with all sources
            
        Returns:
            Combined text from all sources
        """
        parts = [input_data.startup_notes]
        if input_data.old_job_ad:
            parts.append(input_data.old_job_ad)
        if input_data.hiring_manager_input:
            parts.append(input_data.hiring_manager_input)
        return "\n\n".join(parts)
    
    def _extract_potential_skills(self, text: str) -> List[str]:
        """Extract potential skills from text without source tracking.
        
        Used for validation to check if enough skills are present.
        
        Args:
            text: The text to extract from
            
        Returns:
            List of potential skill strings
        """
        skills: List[str] = []
        text_lower = text.lower()
        
        # Look for bullet points or numbered lists
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Check if line starts with bullet or number
            if re.match(r'^[\-\*\•\d\.]+\s*', line):
                # Extract the content after the bullet
                content = re.sub(r'^[\-\*\•\d\.]+\s*', '', line).strip()
                if content and len(content) > 5:
                    skills.append(content)
        
        # Look for skills near must-have indicators
        for indicator in self.MUST_HAVE_INDICATORS:
            if indicator in text_lower:
                # Find sentences containing the indicator
                sentences = re.split(r'[.!?]', text)
                for sentence in sentences:
                    if indicator in sentence.lower():
                        # Extract skill-like phrases
                        skill = self._clean_skill_text(sentence)
                        if skill and skill not in skills:
                            skills.append(skill)
        
        return skills
    
    def _extract_must_have_skills(
        self,
        input_data: RequirementProfileInput
    ) -> List[Tuple[str, ContentSource]]:
        """Extract must-have skills with source tracking.
        
        Ensures all extracted skills can be traced back to input.
        
        Args:
            input_data: The input data with all sources
            
        Returns:
            List of (skill, source) tuples
        """
        skills_with_sources: List[Tuple[str, ContentSource]] = []
        seen_skills: Set[str] = set()
        
        # Process each source in priority order
        sources = [
            (input_data.startup_notes, ContentSource.STARTUP_NOTES),
            (input_data.hiring_manager_input, ContentSource.HIRING_MANAGER_INPUT),
            (input_data.old_job_ad, ContentSource.OLD_JOB_AD),
        ]
        
        for text, source in sources:
            if not text:
                continue
            
            extracted = self._extract_skills_from_text(text)
            for skill in extracted:
                skill_normalized = skill.lower().strip()
                if skill_normalized not in seen_skills:
                    seen_skills.add(skill_normalized)
                    skills_with_sources.append((skill, source))
        
        return skills_with_sources
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skill phrases from a single text source.
        
        Args:
            text: The text to extract from
            
        Returns:
            List of skill strings
        """
        skills: List[str] = []
        text_lower = text.lower()
        
        # Strategy 1: Look for bullet points in requirements sections
        lines = text.split('\n')
        in_requirements_section = False
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Detect requirements section headers
            if any(kw in line_lower for kw in ['requirement', 'must have', 'qualifications', 'skills needed']):
                in_requirements_section = True
                continue
            
            # Detect end of requirements section
            if in_requirements_section and line_lower:
                if any(kw in line_lower for kw in ['responsibilities', 'about', 'we offer', 'benefits']):
                    in_requirements_section = False
                    continue
            
            # Extract from bullet points (-, *, •, or numbered)
            bullet_match = re.match(r'^[\-\*\•]\s+(.+)$', line_stripped)
            numbered_match = re.match(r'^\d+[\.\)]\s*(.+)$', line_stripped)
            
            if bullet_match:
                content = bullet_match.group(1).strip()
                if content and len(content) > 5:
                    cleaned = self._clean_skill_text(content)
                    if cleaned:
                        skills.append(cleaned)
            elif numbered_match:
                content = numbered_match.group(1).strip()
                if content and len(content) > 5:
                    cleaned = self._clean_skill_text(content)
                    if cleaned:
                        skills.append(cleaned)
        
        # Strategy 2: Look for skills near indicators
        for indicator in self.MUST_HAVE_INDICATORS:
            if indicator in text_lower:
                sentences = re.split(r'[.!?\n]', text)
                for sentence in sentences:
                    if indicator in sentence.lower():
                        cleaned = self._clean_skill_text(sentence)
                        if cleaned and cleaned not in skills:
                            skills.append(cleaned)
        
        return skills
    
    def _extract_responsibilities(
        self,
        input_data: RequirementProfileInput
    ) -> List[Tuple[str, ContentSource]]:
        """Extract responsibilities with source tracking.
        
        Args:
            input_data: The input data with all sources
            
        Returns:
            List of (responsibility, source) tuples
        """
        responsibilities: List[Tuple[str, ContentSource]] = []
        seen: Set[str] = set()
        
        sources = [
            (input_data.startup_notes, ContentSource.STARTUP_NOTES),
            (input_data.hiring_manager_input, ContentSource.HIRING_MANAGER_INPUT),
            (input_data.old_job_ad, ContentSource.OLD_JOB_AD),
        ]
        
        for text, source in sources:
            if not text:
                continue
            
            extracted = self._extract_responsibilities_from_text(text)
            for resp in extracted:
                resp_normalized = resp.lower().strip()
                if resp_normalized not in seen:
                    seen.add(resp_normalized)
                    responsibilities.append((resp, source))
        
        return responsibilities
    
    def _extract_responsibilities_from_text(self, text: str) -> List[str]:
        """Extract responsibility phrases from text.
        
        Args:
            text: The text to extract from
            
        Returns:
            List of responsibility strings
        """
        responsibilities: List[str] = []
        text_lower = text.lower()
        
        # Look for responsibilities section
        lines = text.split('\n')
        in_responsibilities_section = False
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Detect responsibilities section
            if any(kw in line_lower for kw in ['responsibilities', 'duties', 'tasks', 'you will', 'the role']):
                in_responsibilities_section = True
                continue
            
            # Detect end of section
            if in_responsibilities_section and line_lower:
                if any(kw in line_lower for kw in ['requirements', 'qualifications', 'we offer', 'about us']):
                    in_responsibilities_section = False
                    continue
            
            # Extract from bullet points in responsibilities section
            if in_responsibilities_section:
                bullet_match = re.match(r'^[\-\*\•]\s+(.+)$', line_stripped)
                numbered_match = re.match(r'^\d+[\.\)]\s*(.+)$', line_stripped)
                
                if bullet_match:
                    content = bullet_match.group(1).strip()
                    if content and len(content) > 10:
                        responsibilities.append(content)
                elif numbered_match:
                    content = numbered_match.group(1).strip()
                    if content and len(content) > 10:
                        responsibilities.append(content)
        
        # Also look for responsibility indicators anywhere
        for indicator in self.RESPONSIBILITY_INDICATORS:
            if indicator in text_lower:
                sentences = re.split(r'[.!?\n]', text)
                for sentence in sentences:
                    if indicator in sentence.lower():
                        cleaned = sentence.strip()
                        if cleaned and len(cleaned) > 15 and cleaned not in responsibilities:
                            responsibilities.append(cleaned)
        
        return responsibilities[:5]  # Limit to 5 per Requirement 5.2
    
    def _extract_good_to_haves(self, text: str) -> List[str]:
        """Extract good-to-have skills from text.
        
        Args:
            text: The text to extract from
            
        Returns:
            List of good-to-have skill strings
        """
        good_to_haves: List[str] = []
        text_lower = text.lower()
        
        for indicator in self.GOOD_TO_HAVE_INDICATORS:
            if indicator in text_lower:
                sentences = re.split(r'[.!?\n]', text)
                for sentence in sentences:
                    if indicator in sentence.lower():
                        cleaned = self._clean_skill_text(sentence)
                        if cleaned and cleaned not in good_to_haves:
                            good_to_haves.append(cleaned)
        
        return good_to_haves
    
    def _extract_soft_skills(self, text: str) -> List[str]:
        """Extract soft skills from text.
        
        Args:
            text: The text to extract from
            
        Returns:
            List of soft skill strings
        """
        # Common soft skills to look for
        soft_skill_keywords = [
            "communication", "teamwork", "leadership", "problem-solving",
            "analytical", "creative", "adaptable", "organized", "detail-oriented",
            "collaborative", "proactive", "self-motivated", "flexible",
        ]
        
        found_skills: List[str] = []
        text_lower = text.lower()
        
        for skill in soft_skill_keywords:
            if skill in text_lower:
                # Find the context around the skill
                sentences = re.split(r'[.!?\n]', text)
                for sentence in sentences:
                    if skill in sentence.lower():
                        # Just add the skill keyword, not the whole sentence
                        if skill.title() not in found_skills:
                            found_skills.append(skill.title())
                        break
        
        return found_skills
    
    def _clean_skill_text(self, text: str) -> str:
        """Clean and normalize skill text.
        
        Args:
            text: Raw skill text
            
        Returns:
            Cleaned skill text
        """
        # Remove common prefixes
        prefixes_to_remove = [
            "must have", "required:", "essential:", "you need",
            "we are looking for", "the ideal candidate has",
        ]
        
        cleaned = text.strip()
        cleaned_lower = cleaned.lower()
        
        for prefix in prefixes_to_remove:
            if cleaned_lower.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                cleaned_lower = cleaned.lower()
        
        # Remove leading punctuation
        cleaned = re.sub(r'^[\-\*\•\:\,]+\s*', '', cleaned)
        
        # Capitalize first letter
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
        
        # Limit length
        if len(cleaned) > 200:
            cleaned = cleaned[:200].rsplit(' ', 1)[0] + "..."
        
        return cleaned
    
    def verify_no_invented_content(
        self,
        profile: RequirementProfile,
        input_data: RequirementProfileInput
    ) -> bool:
        """Verify that all profile content exists in the input.
        
        Implements Requirements 4.6 and 13.2: never invent content.
        
        Args:
            profile: The generated profile
            input_data: The original input
            
        Returns:
            True if all content is traceable to input
        """
        combined_input = self._combine_input_sources(input_data).lower()
        
        # Check all must-have skills
        for skill in profile.must_have_skills:
            # Check if key words from skill exist in input
            skill_words = set(skill.lower().split())
            significant_words = {w for w in skill_words if len(w) > 3}
            
            if significant_words:
                matches = sum(1 for w in significant_words if w in combined_input)
                if matches < len(significant_words) * 0.5:  # At least 50% of words should match
                    return False
        
        # Check all responsibilities
        for resp in profile.primary_responsibilities:
            resp_words = set(resp.lower().split())
            significant_words = {w for w in resp_words if len(w) > 3}
            
            if significant_words:
                matches = sum(1 for w in significant_words if w in combined_input)
                if matches < len(significant_words) * 0.5:
                    return False
        
        return True
