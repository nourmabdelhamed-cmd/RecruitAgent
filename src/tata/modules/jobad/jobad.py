"""Job Ad module for Tata recruitment assistant.

This module implements Module B: Job Ad creation.
The job ad is created from the requirement profile and follows
GlobalConnect's language guidelines.

Requirements covered:
- 5.1: Require a requirement profile before creating a job ad
- 5.2: Structure the job ad with all required sections
- 5.3: Verify each section is based on defined inputs
- 13.3: Ensure four must-have hard skills are clearly visible
- 3.5: Never expose module naming (A, B, C) to the recruiter
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple
import json
import re

from src.tata.memory.memory import ArtifactType, Artifact, MemoryManager
from src.tata.modules.profile.profile import RequirementProfile
from src.tata.dependency.dependency import (
    DependencyManager,
    DependencyCheck,
    MODULE_DEPENDENCIES,
)
from src.tata.session.session import ModuleType


class MissingRequirementProfileError(Exception):
    """Raised when job ad creation is attempted without a requirement profile."""
    pass


class InvalidJobAdInputError(Exception):
    """Raised when job ad input validation fails."""
    pass


@dataclass
class ValidationError:
    """A validation error for input data."""
    field: str
    message: str


@dataclass
class ValidationWarning:
    """A validation warning for input data."""
    field: str
    message: str


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)


@dataclass
class RequirementsSection:
    """Requirements part of a job ad.
    
    Contains the four must-have skills prominently displayed,
    plus soft skills and good-to-haves.
    
    Attributes:
        must_haves: Exactly 4 must-have skills (tuple enforces count)
        soft_skills: Paragraph describing soft skills
        good_to_haves: Paragraph describing nice-to-have qualifications
    """
    must_haves: Tuple[str, str, str, str]
    soft_skills: str
    good_to_haves: str


@dataclass
class JobAdInput:
    """Input for creating a job ad.
    
    Requires a requirement profile as the foundation.
    Additional context can be provided through startup notes
    and old job ads.
    
    Attributes:
        requirement_profile: The requirement profile (required)
        startup_notes: Notes from recruitment start-up meeting
        old_job_ad: Previous job advertisement for reference
        company_context: Additional company/team context
    """
    requirement_profile: RequirementProfile
    startup_notes: str = ""
    old_job_ad: Optional[str] = None
    company_context: Optional[str] = None


@dataclass
class JobAd:
    """Complete job advertisement.
    
    Structured according to Requirement 5.2 with all required sections.
    The four must-have skills are clearly visible in the requirements section.
    
    Attributes:
        headline: Job title/headline
        intro: Introduction (max 2 sentences)
        role_description: Description of the role
        the_why: Why this role matters
        responsibilities: 3-5 key responsibilities
        requirements: Requirements section with must-haves visible
        soft_skills_paragraph: Soft skills description
        team_and_why_gc: Team info and why GlobalConnect
        process: Recruitment process description
        ending: Closing statement
        created_at: When the job ad was created
    """
    headline: str
    intro: str
    role_description: str
    the_why: str
    responsibilities: List[str]
    requirements: RequirementsSection
    soft_skills_paragraph: str
    team_and_why_gc: str
    process: str
    ending: str
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type for memory storage."""
        return ArtifactType.JOB_AD
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "headline": self.headline,
            "intro": self.intro,
            "role_description": self.role_description,
            "the_why": self.the_why,
            "responsibilities": self.responsibilities,
            "requirements": {
                "must_haves": list(self.requirements.must_haves),
                "soft_skills": self.requirements.soft_skills,
                "good_to_haves": self.requirements.good_to_haves,
            },
            "soft_skills_paragraph": self.soft_skills_paragraph,
            "team_and_why_gc": self.team_and_why_gc,
            "process": self.process,
            "ending": self.ending,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data, indent=2)
    
    def to_text(self) -> str:
        """Generate plain text version of the job ad."""
        sections = [
            f"# {self.headline}",
            "",
            self.intro,
            "",
            "## About the Role",
            self.role_description,
            "",
            "## Why This Role Matters",
            self.the_why,
            "",
            "## Key Responsibilities",
        ]
        
        for resp in self.responsibilities:
            sections.append(f"• {resp}")
        
        sections.extend([
            "",
            "## Requirements",
            "What you bring:",
        ])
        
        for must_have in self.requirements.must_haves:
            sections.append(f"• {must_have}")
        
        if self.requirements.good_to_haves:
            sections.extend([
                "",
                "Nice to have:",
                self.requirements.good_to_haves,
            ])
        
        sections.extend([
            "",
            self.soft_skills_paragraph,
            "",
            "## The Team & Why GlobalConnect",
            self.team_and_why_gc,
            "",
            "## Recruitment Process",
            self.process,
            "",
            self.ending,
        ])
        
        return "\n".join(sections)


# Module naming patterns to filter out (Requirement 3.5)
MODULE_NAMING_PATTERNS = [
    r"\bModule\s+[A-J]\b",
    r"\bmodule\s+[a-j]\b",
    r"\bModule\s+A\b",
    r"\bModule\s+B\b",
    r"\bModule\s+C\b",
    r"\bModule\s+D\b",
    r"\bModule\s+E\b",
    r"\bModule\s+F\b",
    r"\bModule\s+G\b",
    r"\bModule\s+H\b",
    r"\bModule\s+I\b",
    r"\bModule\s+J\b",
]


def filter_module_naming(text: str) -> str:
    """Remove any module naming references from text.
    
    Implements Requirement 3.5: Never expose module naming (A, B, C)
    to the recruiter, using natural terms instead.
    
    Args:
        text: The text to filter
        
    Returns:
        Text with module naming removed
    """
    result = text
    for pattern in MODULE_NAMING_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    
    # Clean up any double spaces left behind
    result = re.sub(r"\s+", " ", result)
    result = result.strip()
    
    return result


def contains_module_naming(text: str) -> bool:
    """Check if text contains any module naming references.
    
    Args:
        text: The text to check
        
    Returns:
        True if module naming is found, False otherwise
    """
    for pattern in MODULE_NAMING_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


class JobAdProcessor:
    """Processor for creating job ads from requirement profiles.
    
    Implements the ModuleProcessor pattern for Module B.
    Creates structured job ads based on the requirement profile
    while ensuring compliance with GlobalConnect's guidelines.
    
    Requirements covered:
    - 5.1: Require a requirement profile before creating a job ad
    - 5.2: Structure the job ad with all required sections
    - 5.3: Verify each section is based on defined inputs
    - 13.3: Ensure four must-have hard skills are clearly visible
    - 3.5: Never expose module naming to the recruiter
    """
    
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        dependency_manager: Optional[DependencyManager] = None,
    ):
        """Initialize the job ad processor.
        
        Args:
            memory_manager: Optional memory manager for artifact storage
            dependency_manager: Optional dependency manager for checks
        """
        self._memory_manager = memory_manager
        self._dependency_manager = dependency_manager
    
    def check_dependencies(self, session_id: str) -> DependencyCheck:
        """Check if job ad creation can proceed.
        
        Verifies that the requirement profile exists in the session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            DependencyCheck indicating if creation can proceed
        """
        if self._dependency_manager:
            return self._dependency_manager.can_execute(
                session_id, ModuleType.JOB_AD
            )
        
        # If no dependency manager, check memory directly
        if self._memory_manager:
            has_profile = self._memory_manager.has_artifact(
                session_id, ArtifactType.REQUIREMENT_PROFILE
            )
            if has_profile:
                return DependencyCheck(
                    can_proceed=True,
                    missing_dependencies=[],
                    message="Requirement profile found. Ready to create job ad."
                )
            else:
                return DependencyCheck(
                    can_proceed=False,
                    missing_dependencies=[ModuleType.REQUIREMENT_PROFILE],
                    message="Requirement profile is required before creating a job ad."
                )
        
        # No managers available, assume can proceed if profile provided directly
        return DependencyCheck(
            can_proceed=True,
            missing_dependencies=[],
            message="No dependency check available."
        )
    
    def validate(self, input_data: JobAdInput) -> ValidationResult:
        """Validate input data before processing.
        
        Args:
            input_data: The input to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # Check requirement profile
        if input_data.requirement_profile is None:
            errors.append(ValidationError(
                field="requirement_profile",
                message="Requirement profile is required"
            ))
        else:
            # Validate profile has required fields
            profile = input_data.requirement_profile
            
            if not profile.position_title:
                errors.append(ValidationError(
                    field="requirement_profile.position_title",
                    message="Position title is required"
                ))
            
            if len(profile.must_have_skills) != 4:
                errors.append(ValidationError(
                    field="requirement_profile.must_have_skills",
                    message="Exactly 4 must-have skills are required"
                ))
            
            if not profile.primary_responsibilities:
                warnings.append(ValidationWarning(
                    field="requirement_profile.primary_responsibilities",
                    message="No responsibilities provided; job ad may be incomplete"
                ))
        
        # Check for module naming in inputs
        if input_data.startup_notes and contains_module_naming(input_data.startup_notes):
            warnings.append(ValidationWarning(
                field="startup_notes",
                message="Module naming detected in startup notes; will be filtered"
            ))
        
        if input_data.old_job_ad and contains_module_naming(input_data.old_job_ad):
            warnings.append(ValidationWarning(
                field="old_job_ad",
                message="Module naming detected in old job ad; will be filtered"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def process(self, input_data: JobAdInput) -> JobAd:
        """Process input and generate a job ad.
        
        Args:
            input_data: The job ad input with requirement profile
            
        Returns:
            A complete JobAd
            
        Raises:
            MissingRequirementProfileError: If no requirement profile provided
            InvalidJobAdInputError: If input validation fails
        """
        # Validate input
        validation = self.validate(input_data)
        if not validation.is_valid:
            error_msgs = "; ".join(e.message for e in validation.errors)
            if "requirement profile" in error_msgs.lower():
                raise MissingRequirementProfileError(error_msgs)
            raise InvalidJobAdInputError(f"Input validation failed: {error_msgs}")
        
        profile = input_data.requirement_profile
        
        # Generate each section
        headline = self._generate_headline(profile)
        intro = self._generate_intro(profile, input_data.company_context)
        role_description = self._generate_role_description(profile)
        the_why = self._generate_the_why(profile, input_data.company_context)
        responsibilities = self._generate_responsibilities(profile)
        requirements = self._generate_requirements_section(profile)
        soft_skills_paragraph = self._generate_soft_skills_paragraph(profile)
        team_and_why_gc = self._generate_team_and_why_gc(
            profile, input_data.company_context
        )
        process = self._generate_process()
        ending = self._generate_ending(profile)
        
        # Create job ad
        job_ad = JobAd(
            headline=headline,
            intro=intro,
            role_description=role_description,
            the_why=the_why,
            responsibilities=responsibilities,
            requirements=requirements,
            soft_skills_paragraph=soft_skills_paragraph,
            team_and_why_gc=team_and_why_gc,
            process=process,
            ending=ending,
        )
        
        # Filter any module naming from the output
        job_ad = self._filter_module_naming_from_job_ad(job_ad)
        
        return job_ad
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input fields."""
        return ["requirement_profile"]
    
    def get_optional_inputs(self) -> List[str]:
        """Get list of optional input fields."""
        return ["startup_notes", "old_job_ad", "company_context"]
    
    def _generate_headline(self, profile: RequirementProfile) -> str:
        """Generate the job ad headline.
        
        Args:
            profile: The requirement profile
            
        Returns:
            Job headline string
        """
        return filter_module_naming(profile.position_title)
    
    def _generate_intro(
        self,
        profile: RequirementProfile,
        company_context: Optional[str]
    ) -> str:
        """Generate the intro section (max 2 sentences).
        
        Args:
            profile: The requirement profile
            company_context: Optional company context
            
        Returns:
            Intro paragraph (max 2 sentences)
        """
        position = profile.position_title
        
        # Build intro based on available context
        if company_context:
            intro = f"We are looking for a {position} to join our team. {filter_module_naming(company_context[:200])}"
        else:
            intro = f"We are looking for a {position} to join GlobalConnect. This is an opportunity to make a real impact."
        
        return filter_module_naming(intro)
    
    def _generate_role_description(self, profile: RequirementProfile) -> str:
        """Generate the role description section.
        
        Args:
            profile: The requirement profile
            
        Returns:
            Role description paragraph
        """
        position = profile.position_title
        
        # Build description from responsibilities
        if profile.primary_responsibilities:
            resp_summary = ", ".join(profile.primary_responsibilities[:3])
            description = f"As a {position}, you will be responsible for {resp_summary.lower()}."
        else:
            description = f"As a {position}, you will play a key role in our organization."
        
        if profile.bu_description:
            description += f" {filter_module_naming(profile.bu_description)}"
        
        return filter_module_naming(description)
    
    def _generate_the_why(
        self,
        profile: RequirementProfile,
        company_context: Optional[str]
    ) -> str:
        """Generate the 'why this role matters' section.
        
        Args:
            profile: The requirement profile
            company_context: Optional company context
            
        Returns:
            The why paragraph
        """
        if profile.motivations:
            motivations_text = " ".join(profile.motivations[:2])
            the_why = f"This role matters because {motivations_text.lower()}"
        else:
            the_why = "This role is crucial to our continued growth and success."
        
        if company_context:
            the_why += f" {filter_module_naming(company_context[:150])}"
        
        return filter_module_naming(the_why)
    
    def _generate_responsibilities(self, profile: RequirementProfile) -> List[str]:
        """Generate the responsibilities list (3-5 items).
        
        Args:
            profile: The requirement profile
            
        Returns:
            List of 3-5 responsibility strings
        """
        responsibilities = profile.primary_responsibilities[:5]
        
        # Ensure we have at least 3 responsibilities
        if len(responsibilities) < 3:
            # Add generic responsibilities based on role
            generic = [
                "Collaborate with cross-functional teams",
                "Contribute to continuous improvement initiatives",
                "Support team goals and objectives",
            ]
            while len(responsibilities) < 3:
                responsibilities.append(generic[len(responsibilities)])
        
        # Filter module naming from each responsibility
        return [filter_module_naming(r) for r in responsibilities]
    
    def _generate_requirements_section(
        self,
        profile: RequirementProfile
    ) -> RequirementsSection:
        """Generate the requirements section with 4 must-haves visible.
        
        Implements Requirement 13.3: Ensure four must-have hard skills
        are clearly visible.
        
        Args:
            profile: The requirement profile
            
        Returns:
            RequirementsSection with must-haves, soft skills, good-to-haves
        """
        # Must-haves are directly from profile (exactly 4)
        must_haves = tuple(
            filter_module_naming(skill) for skill in profile.must_have_skills
        )
        
        # Soft skills paragraph
        if profile.soft_skills:
            soft_skills = "We value candidates who are " + ", ".join(
                s.lower() for s in profile.soft_skills[:4]
            ) + "."
        else:
            soft_skills = "We value candidates who are collaborative and proactive."
        
        # Good-to-haves
        if profile.good_to_haves:
            good_to_haves = "It would be great if you also have experience with " + ", ".join(
                g.lower() for g in profile.good_to_haves[:3]
            ) + "."
        else:
            good_to_haves = ""
        
        return RequirementsSection(
            must_haves=must_haves,  # type: ignore
            soft_skills=filter_module_naming(soft_skills),
            good_to_haves=filter_module_naming(good_to_haves),
        )
    
    def _generate_soft_skills_paragraph(self, profile: RequirementProfile) -> str:
        """Generate the soft skills paragraph.
        
        Args:
            profile: The requirement profile
            
        Returns:
            Soft skills paragraph
        """
        if profile.soft_skills:
            skills_list = ", ".join(s.lower() for s in profile.soft_skills)
            paragraph = f"Beyond technical skills, we're looking for someone who is {skills_list}. These qualities will help you thrive in our collaborative environment."
        else:
            paragraph = "We're looking for someone who thrives in a collaborative environment and brings a positive attitude to their work."
        
        return filter_module_naming(paragraph)
    
    def _generate_team_and_why_gc(
        self,
        profile: RequirementProfile,
        company_context: Optional[str]
    ) -> str:
        """Generate the team and why GlobalConnect section.
        
        Args:
            profile: The requirement profile
            company_context: Optional company context
            
        Returns:
            Team and why GC paragraph
        """
        parts = []
        
        # Team info
        if profile.team_info:
            team = profile.team_info
            parts.append(
                f"You'll be joining a team of {team.size} people based in {team.location}. "
                f"Our team culture is {team.collaboration_style.lower()}."
            )
        
        # Why GlobalConnect
        parts.append(
            "At GlobalConnect, we're building the digital infrastructure of the Nordics. "
            "We offer a dynamic work environment where you can grow and make an impact."
        )
        
        if company_context:
            parts.append(filter_module_naming(company_context[:200]))
        
        return filter_module_naming(" ".join(parts))
    
    def _generate_process(self) -> str:
        """Generate the recruitment process section.
        
        Returns:
            Process description
        """
        return (
            "Our recruitment process typically includes an initial screening call, "
            "followed by interviews with the hiring manager and team. "
            "We aim to make the process smooth and transparent."
        )
    
    def _generate_ending(self, profile: RequirementProfile) -> str:
        """Generate the closing statement.
        
        Args:
            profile: The requirement profile
            
        Returns:
            Ending paragraph
        """
        position = profile.position_title
        return filter_module_naming(
            f"Ready to take the next step in your career as a {position}? "
            "We'd love to hear from you. Apply now and let's start the conversation."
        )
    
    def _filter_module_naming_from_job_ad(self, job_ad: JobAd) -> JobAd:
        """Filter module naming from all job ad fields.
        
        Implements Requirement 3.5: Never expose module naming.
        
        Args:
            job_ad: The job ad to filter
            
        Returns:
            Job ad with module naming removed
        """
        return JobAd(
            headline=filter_module_naming(job_ad.headline),
            intro=filter_module_naming(job_ad.intro),
            role_description=filter_module_naming(job_ad.role_description),
            the_why=filter_module_naming(job_ad.the_why),
            responsibilities=[filter_module_naming(r) for r in job_ad.responsibilities],
            requirements=RequirementsSection(
                must_haves=tuple(
                    filter_module_naming(m) for m in job_ad.requirements.must_haves
                ),  # type: ignore
                soft_skills=filter_module_naming(job_ad.requirements.soft_skills),
                good_to_haves=filter_module_naming(job_ad.requirements.good_to_haves),
            ),
            soft_skills_paragraph=filter_module_naming(job_ad.soft_skills_paragraph),
            team_and_why_gc=filter_module_naming(job_ad.team_and_why_gc),
            process=filter_module_naming(job_ad.process),
            ending=filter_module_naming(job_ad.ending),
            created_at=job_ad.created_at,
        )
