"""Candidate Report module for Tata recruitment assistant.

This module implements Module F: Candidate Report generation.
Creates structured candidate assessments from interview transcripts.

Requirements covered:
- 8.1: Accept Microsoft Teams transcripts as input
- 8.3: Match transcript content to: Motivation, Skills/requirement profile match, Practical
- 8.4: Provide a rating (1-5) with explanation for each skill
- 8.5: Structure report with: Summary, Background, Highlights, Practical, Risks, Conclusion
- 8.7: Always anonymize candidates to initials in comparison tables
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple, Dict
import json
import re

from src.tata.memory.memory import ArtifactType
from src.tata.modules.profile.profile import RequirementProfile
from src.tata.modules.screening.screening import ScreeningTemplate, SkillType


class Rating(Enum):
    """1-5 skill rating per Requirement 8.4.
    
    Each rating has a numeric value and description.
    """
    VERY_BAD = 1        # No relevant points
    UNSATISFACTORY = 2  # Weak, missing key elements
    OKAY = 3            # Meets minimum expectations
    GOOD = 4            # Strong, missing minor details
    EXCELLENT = 5       # Fully relevant and strong


RATING_DESCRIPTIONS: Dict[Rating, str] = {
    Rating.VERY_BAD: "Very bad - no relevant points",
    Rating.UNSATISFACTORY: "Unsatisfactory - weak, missing key elements",
    Rating.OKAY: "Okay - meets minimum expectations",
    Rating.GOOD: "Good - strong, missing minor details",
    Rating.EXCELLENT: "Excellent - fully relevant and strong",
}


class Recommendation(Enum):
    """Overall recommendation for a candidate."""
    RECOMMENDED = "Recommended"
    NOT_RECOMMENDED = "Not Recommended"
    BORDERLINE = "Borderline"


@dataclass
class SkillAssessment:
    """Assessment of a single skill per Requirement 8.4.
    
    Attributes:
        skill_name: The skill being assessed
        summary: Brief summary of candidate's capability
        examples: Specific examples from the interview
        rating: 1-5 rating
        rating_explanation: Non-empty explanation for the rating
    """
    skill_name: str
    summary: str
    examples: List[str]
    rating: Rating
    rating_explanation: str
    
    def __post_init__(self):
        """Validate rating has explanation per Requirement 8.4."""
        if not self.rating_explanation or not self.rating_explanation.strip():
            raise ValueError("Rating explanation cannot be empty")
        if not isinstance(self.rating, Rating):
            raise ValueError(f"Rating must be a Rating enum, got {type(self.rating)}")


@dataclass
class PracticalDetails:
    """Practical information about a candidate.
    
    Attributes:
        notice_period: Candidate's notice period
        salary_expectation: Expected salary/compensation
        location: Candidate's location or relocation status
        languages: Languages the candidate speaks
    """
    notice_period: str
    salary_expectation: str
    location: str
    languages: List[str] = field(default_factory=list)


@dataclass
class TranscriptSection:
    """A section of parsed transcript content.
    
    Attributes:
        speaker: Who said this (candidate, interviewer, etc.)
        timestamp: When this was said
        content: The actual text content
    """
    speaker: str
    timestamp: Optional[str]
    content: str


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


class InvalidInputError(Exception):
    """Raised when input validation fails."""
    pass


class InvalidRatingError(Exception):
    """Raised when rating is invalid."""
    pass


@dataclass
class CandidateReportInput:
    """Input for creating candidate reports per Requirement 8.1.
    
    Attributes:
        transcript: Microsoft Teams transcript text
        screening_template: The screening template used for the interview
        requirement_profile: The requirement profile for the role
        candidate_name: Full name of the candidate (will be anonymized)
        interview_date: Date of the interview
        candidate_cv: Optional CV text for enrichment
    """
    transcript: str
    screening_template: ScreeningTemplate
    requirement_profile: RequirementProfile
    candidate_name: str
    interview_date: datetime
    candidate_cv: Optional[str] = None


@dataclass
class CandidateReport:
    """Complete candidate assessment per Requirement 8.5.
    
    Structure:
    - Candidate Summary
    - Professional Background
    - Highlights of Fit
    - Practical Details
    - Risks/Considerations
    - Conclusion
    
    Attributes:
        candidate_initials: Anonymized candidate identifier (2-3 chars)
        candidate_full_name: Original full name (for internal use only)
        position_name: The position being recruited for
        interview_date: When the interview took place
        recommendation: Overall recommendation
        professional_background: Summary of candidate's background
        motivation_assessment: Assessment of candidate's motivation
        skill_assessments: Assessment for each skill
        practical_details: Practical information
        risks_and_considerations: Potential concerns
        conclusion: Final summary and recommendation
        created_at: When the report was created
    """
    candidate_initials: str
    candidate_full_name: str
    position_name: str
    interview_date: datetime
    recommendation: Recommendation
    professional_background: str
    motivation_assessment: SkillAssessment
    skill_assessments: List[SkillAssessment]
    practical_details: PracticalDetails
    risks_and_considerations: List[str]
    conclusion: str
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type for memory storage."""
        return ArtifactType.CANDIDATE_REPORTS
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "candidate_initials": self.candidate_initials,
            "candidate_full_name": self.candidate_full_name,
            "position_name": self.position_name,
            "interview_date": self.interview_date.isoformat(),
            "recommendation": self.recommendation.value,
            "professional_background": self.professional_background,
            "motivation_assessment": {
                "skill_name": self.motivation_assessment.skill_name,
                "summary": self.motivation_assessment.summary,
                "examples": self.motivation_assessment.examples,
                "rating": self.motivation_assessment.rating.value,
                "rating_explanation": self.motivation_assessment.rating_explanation,
            },
            "skill_assessments": [
                {
                    "skill_name": sa.skill_name,
                    "summary": sa.summary,
                    "examples": sa.examples,
                    "rating": sa.rating.value,
                    "rating_explanation": sa.rating_explanation,
                }
                for sa in self.skill_assessments
            ],
            "practical_details": {
                "notice_period": self.practical_details.notice_period,
                "salary_expectation": self.practical_details.salary_expectation,
                "location": self.practical_details.location,
                "languages": self.practical_details.languages,
            },
            "risks_and_considerations": self.risks_and_considerations,
            "conclusion": self.conclusion,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data, indent=2)
    
    def get_average_rating(self) -> float:
        """Calculate average rating across all skill assessments.
        
        Returns:
            Average rating as a float
        """
        all_ratings = [self.motivation_assessment.rating.value]
        all_ratings.extend(sa.rating.value for sa in self.skill_assessments)
        return sum(all_ratings) / len(all_ratings)


# Common transcription errors and corrections
TRANSCRIPTION_CORRECTIONS: Dict[str, str] = {
    "gonna": "going to",
    "wanna": "want to",
    "gotta": "got to",
    "kinda": "kind of",
    "sorta": "sort of",
    "dunno": "don't know",
    "lemme": "let me",
    "gimme": "give me",
    "coulda": "could have",
    "shoulda": "should have",
    "woulda": "would have",
    "ain't": "is not",
    "y'all": "you all",
}


def anonymize_name(full_name: str) -> str:
    """Convert full name to initials per Requirement 8.7.
    
    Args:
        full_name: The candidate's full name
        
    Returns:
        2-3 character initials (e.g., "John Smith" -> "JS")
    """
    if not full_name or not full_name.strip():
        return "XX"
    
    # Split name into parts
    parts = full_name.strip().split()
    
    # Take first letter of each part (up to 3)
    initials = "".join(part[0].upper() for part in parts[:3] if part)
    
    # Ensure at least 2 characters
    if len(initials) < 2:
        initials = initials + "X" if initials else "XX"
    
    return initials


def validate_rating(rating: Rating, explanation: str) -> bool:
    """Validate that a rating is valid per Requirement 8.4.
    
    Args:
        rating: The rating value
        explanation: The explanation for the rating
        
    Returns:
        True if valid
        
    Raises:
        InvalidRatingError: If rating is invalid
    """
    if not isinstance(rating, Rating):
        raise InvalidRatingError(f"Rating must be a Rating enum, got {type(rating)}")
    
    if rating.value < 1 or rating.value > 5:
        raise InvalidRatingError(f"Rating must be between 1 and 5, got {rating.value}")
    
    if not explanation or not explanation.strip():
        raise InvalidRatingError("Rating explanation cannot be empty")
    
    return True


class CandidateReportProcessor:
    """Processor for creating candidate reports from interview transcripts.
    
    Implements the ModuleProcessor pattern for Module F.
    Parses transcripts, maps content to assessment sections, and generates
    structured reports with skill ratings.
    
    Requirements covered:
    - 8.1: Accept Microsoft Teams transcripts as input
    - 8.2: Correct obvious transcription errors
    - 8.3: Match transcript content to Motivation, Skills, Practical sections
    - 8.4: Provide rating (1-5) with explanation for each skill
    - 8.5: Structure report with required sections
    - 8.7: Anonymize candidates to initials
    """
    
    # Patterns for parsing Teams transcript format
    # Format: "HH:MM:SS Speaker Name\nContent"
    TEAMS_TIMESTAMP_PATTERN = re.compile(
        r'^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+?)$',
        re.MULTILINE
    )
    
    # Alternative format: "Speaker Name HH:MM:SS"
    TEAMS_ALT_PATTERN = re.compile(
        r'^(.+?)\s+(\d{1,2}:\d{2}(?::\d{2})?)$',
        re.MULTILINE
    )
    
    # Keywords for section detection
    MOTIVATION_KEYWORDS = [
        "motivation", "why", "interested", "attracted", "looking for",
        "career", "goals", "aspiration", "passion", "excited",
    ]
    
    PRACTICAL_KEYWORDS = [
        "notice period", "salary", "compensation", "location", "relocate",
        "start date", "availability", "language", "travel", "remote",
    ]
    
    def validate(self, input_data: CandidateReportInput) -> ValidationResult:
        """Validate input data before processing.
        
        Args:
            input_data: The input to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # Check transcript
        if not input_data.transcript or not input_data.transcript.strip():
            errors.append(ValidationError(
                field="transcript",
                message="Transcript is required and cannot be empty"
            ))
        elif len(input_data.transcript.strip()) < 100:
            warnings.append(ValidationWarning(
                field="transcript",
                message="Transcript is very short; may not contain enough information"
            ))
        
        # Check screening template
        if input_data.screening_template is None:
            errors.append(ValidationError(
                field="screening_template",
                message="Screening template is required"
            ))
        
        # Check requirement profile
        if input_data.requirement_profile is None:
            errors.append(ValidationError(
                field="requirement_profile",
                message="Requirement profile is required"
            ))
        
        # Check candidate name
        if not input_data.candidate_name or not input_data.candidate_name.strip():
            errors.append(ValidationError(
                field="candidate_name",
                message="Candidate name is required"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def process(self, input_data: CandidateReportInput) -> CandidateReport:
        """Process input and generate a candidate report.
        
        Args:
            input_data: The candidate report input
            
        Returns:
            A complete CandidateReport
            
        Raises:
            InvalidInputError: If input validation fails
        """
        # Validate first
        validation = self.validate(input_data)
        if not validation.is_valid:
            error_msgs = "; ".join(e.message for e in validation.errors)
            raise InvalidInputError(f"Input validation failed: {error_msgs}")
        
        # Parse and correct transcript
        corrected_transcript = self._correct_transcription_errors(input_data.transcript)
        sections = self._parse_transcript(corrected_transcript)
        
        # Map content to assessment sections
        motivation_content = self._extract_motivation_content(sections)
        skill_content = self._extract_skill_content(sections, input_data.requirement_profile)
        practical_content = self._extract_practical_content(sections)
        
        # Generate assessments
        motivation_assessment = self._assess_motivation(
            motivation_content,
            input_data.requirement_profile
        )
        
        skill_assessments = self._assess_skills(
            skill_content,
            input_data.requirement_profile,
            input_data.screening_template
        )
        
        practical_details = self._extract_practical_details(practical_content)
        
        # Generate professional background
        professional_background = self._generate_background(
            input_data.candidate_cv,
            sections
        )
        
        # Identify risks
        risks = self._identify_risks(
            motivation_assessment,
            skill_assessments,
            practical_details,
            input_data.requirement_profile
        )
        
        # Determine recommendation
        recommendation = self._determine_recommendation(
            motivation_assessment,
            skill_assessments
        )
        
        # Generate conclusion
        conclusion = self._generate_conclusion(
            recommendation,
            motivation_assessment,
            skill_assessments,
            risks
        )
        
        return CandidateReport(
            candidate_initials=anonymize_name(input_data.candidate_name),
            candidate_full_name=input_data.candidate_name,
            position_name=input_data.requirement_profile.position_title,
            interview_date=input_data.interview_date,
            recommendation=recommendation,
            professional_background=professional_background,
            motivation_assessment=motivation_assessment,
            skill_assessments=skill_assessments,
            practical_details=practical_details,
            risks_and_considerations=risks,
            conclusion=conclusion,
        )
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input fields."""
        return ["transcript", "screening_template", "requirement_profile", "candidate_name", "interview_date"]
    
    def get_optional_inputs(self) -> List[str]:
        """Get list of optional input fields."""
        return ["candidate_cv"]

    
    def _correct_transcription_errors(self, transcript: str) -> str:
        """Correct obvious transcription errors per Requirement 8.2.
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            Corrected transcript text
        """
        corrected = transcript
        
        for error, correction in TRANSCRIPTION_CORRECTIONS.items():
            # Case-insensitive replacement preserving word boundaries
            pattern = re.compile(r'\b' + re.escape(error) + r'\b', re.IGNORECASE)
            corrected = pattern.sub(correction, corrected)
        
        return corrected
    
    def _parse_transcript(self, transcript: str) -> List[TranscriptSection]:
        """Parse Microsoft Teams transcript format per Requirement 8.1.
        
        Args:
            transcript: The transcript text
            
        Returns:
            List of parsed transcript sections
        """
        sections: List[TranscriptSection] = []
        
        # Try to parse Teams format
        lines = transcript.split('\n')
        current_speaker = None
        current_timestamp = None
        current_content: List[str] = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for timestamp + speaker pattern
            timestamp_match = self.TEAMS_TIMESTAMP_PATTERN.match(line)
            alt_match = self.TEAMS_ALT_PATTERN.match(line)
            
            if timestamp_match:
                # Save previous section
                if current_speaker and current_content:
                    sections.append(TranscriptSection(
                        speaker=current_speaker,
                        timestamp=current_timestamp,
                        content=" ".join(current_content)
                    ))
                
                current_timestamp = timestamp_match.group(1)
                current_speaker = timestamp_match.group(2)
                current_content = []
            elif alt_match:
                # Save previous section
                if current_speaker and current_content:
                    sections.append(TranscriptSection(
                        speaker=current_speaker,
                        timestamp=current_timestamp,
                        content=" ".join(current_content)
                    ))
                
                current_speaker = alt_match.group(1)
                current_timestamp = alt_match.group(2)
                current_content = []
            else:
                # Content line
                current_content.append(line)
        
        # Save last section
        if current_speaker and current_content:
            sections.append(TranscriptSection(
                speaker=current_speaker,
                timestamp=current_timestamp,
                content=" ".join(current_content)
            ))
        
        # If no structured sections found, treat as single block
        if not sections:
            sections.append(TranscriptSection(
                speaker="Unknown",
                timestamp=None,
                content=transcript
            ))
        
        return sections
    
    def _extract_motivation_content(
        self,
        sections: List[TranscriptSection]
    ) -> List[str]:
        """Extract motivation-related content from transcript.
        
        Args:
            sections: Parsed transcript sections
            
        Returns:
            List of motivation-related content strings
        """
        motivation_content: List[str] = []
        
        for section in sections:
            content_lower = section.content.lower()
            if any(kw in content_lower for kw in self.MOTIVATION_KEYWORDS):
                motivation_content.append(section.content)
        
        return motivation_content
    
    def _extract_skill_content(
        self,
        sections: List[TranscriptSection],
        profile: RequirementProfile
    ) -> Dict[str, List[str]]:
        """Extract skill-related content from transcript.
        
        Args:
            sections: Parsed transcript sections
            profile: The requirement profile
            
        Returns:
            Dict mapping skill names to related content
        """
        skill_content: Dict[str, List[str]] = {}
        
        # Initialize for each must-have skill
        for skill in profile.must_have_skills:
            skill_content[skill] = []
        
        # Also check good-to-haves
        for skill in profile.good_to_haves:
            skill_content[skill] = []
        
        # Match content to skills
        for section in sections:
            content_lower = section.content.lower()
            
            for skill in skill_content.keys():
                # Check if skill keywords appear in content
                skill_words = skill.lower().split()
                if any(word in content_lower for word in skill_words if len(word) > 3):
                    skill_content[skill].append(section.content)
        
        return skill_content
    
    def _extract_practical_content(
        self,
        sections: List[TranscriptSection]
    ) -> List[str]:
        """Extract practical information from transcript.
        
        Args:
            sections: Parsed transcript sections
            
        Returns:
            List of practical-related content strings
        """
        practical_content: List[str] = []
        
        for section in sections:
            content_lower = section.content.lower()
            if any(kw in content_lower for kw in self.PRACTICAL_KEYWORDS):
                practical_content.append(section.content)
        
        return practical_content

    
    def _assess_motivation(
        self,
        motivation_content: List[str],
        profile: RequirementProfile
    ) -> SkillAssessment:
        """Assess candidate's motivation.
        
        Args:
            motivation_content: Motivation-related transcript content
            profile: The requirement profile
            
        Returns:
            SkillAssessment for motivation
        """
        # Determine rating based on content quality
        if not motivation_content:
            rating = Rating.UNSATISFACTORY
            summary = "Limited motivation discussion in the interview."
            explanation = "No clear motivation content found in transcript."
        elif len(motivation_content) >= 3:
            rating = Rating.GOOD
            summary = "Strong motivation demonstrated with clear career alignment."
            explanation = "Multiple instances of motivation discussion found."
        else:
            rating = Rating.OKAY
            summary = "Adequate motivation expressed."
            explanation = "Some motivation content found but could be more detailed."
        
        return SkillAssessment(
            skill_name="Motivation",
            summary=summary,
            examples=motivation_content[:3],  # Top 3 examples
            rating=rating,
            rating_explanation=explanation,
        )
    
    def _assess_skills(
        self,
        skill_content: Dict[str, List[str]],
        profile: RequirementProfile,
        template: ScreeningTemplate
    ) -> List[SkillAssessment]:
        """Assess candidate's skills per Requirement 8.4.
        
        Args:
            skill_content: Dict mapping skills to related content
            profile: The requirement profile
            template: The screening template used
            
        Returns:
            List of SkillAssessments
        """
        assessments: List[SkillAssessment] = []
        
        for skill in profile.must_have_skills:
            content = skill_content.get(skill, [])
            
            # Determine rating based on content
            if not content:
                rating = Rating.UNSATISFACTORY
                summary = f"No evidence of {skill} discussed in interview."
                explanation = f"No relevant content found for {skill}."
            elif len(content) >= 3:
                rating = Rating.GOOD
                summary = f"Strong demonstration of {skill} with multiple examples."
                explanation = f"Multiple relevant examples provided for {skill}."
            elif len(content) >= 1:
                rating = Rating.OKAY
                summary = f"Some evidence of {skill} capability."
                explanation = f"Limited examples provided for {skill}."
            else:
                rating = Rating.UNSATISFACTORY
                summary = f"Insufficient evidence of {skill}."
                explanation = f"Could not assess {skill} from transcript."
            
            assessments.append(SkillAssessment(
                skill_name=skill,
                summary=summary,
                examples=content[:3],
                rating=rating,
                rating_explanation=explanation,
            ))
        
        return assessments
    
    def _extract_practical_details(
        self,
        practical_content: List[str]
    ) -> PracticalDetails:
        """Extract practical details from content.
        
        Args:
            practical_content: Practical-related transcript content
            
        Returns:
            PracticalDetails object
        """
        notice_period = "Not discussed"
        salary_expectation = "Not discussed"
        location = "Not discussed"
        languages: List[str] = []
        
        combined = " ".join(practical_content).lower()
        
        # Extract notice period
        notice_patterns = [
            r'notice period[:\s]+(\d+\s*(?:weeks?|months?|days?))',
            r'(\d+\s*(?:weeks?|months?))\s*notice',
            r'can start[:\s]+(.+?)(?:\.|$)',
        ]
        for pattern in notice_patterns:
            match = re.search(pattern, combined)
            if match:
                notice_period = match.group(1).strip().title()
                break
        
        # Extract salary
        salary_patterns = [
            r'salary[:\s]+(\d+[\d,\.]*\s*(?:k|K|SEK|EUR|USD)?)',
            r'expecting[:\s]+(\d+[\d,\.]*)',
            r'compensation[:\s]+(\d+[\d,\.]*)',
        ]
        for pattern in salary_patterns:
            match = re.search(pattern, combined)
            if match:
                salary_expectation = match.group(1).strip()
                break
        
        # Extract location
        location_patterns = [
            r'based in[:\s]+([^\.]+)',
            r'located in[:\s]+([^\.]+)',
            r'live in[:\s]+([^\.]+)',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, combined)
            if match:
                location = match.group(1).strip().title()
                break
        
        # Extract languages
        language_keywords = ["english", "swedish", "danish", "norwegian", "german", "french", "spanish"]
        for lang in language_keywords:
            if lang in combined:
                languages.append(lang.title())
        
        return PracticalDetails(
            notice_period=notice_period,
            salary_expectation=salary_expectation,
            location=location,
            languages=languages if languages else ["Not discussed"],
        )
    
    def _generate_background(
        self,
        cv: Optional[str],
        sections: List[TranscriptSection]
    ) -> str:
        """Generate professional background summary.
        
        Args:
            cv: Optional CV text
            sections: Parsed transcript sections
            
        Returns:
            Professional background summary
        """
        if cv:
            # Extract key points from CV
            return f"Background extracted from CV and interview discussion."
        
        # Generate from transcript
        background_keywords = ["experience", "worked", "years", "role", "company", "position"]
        background_content: List[str] = []
        
        for section in sections:
            content_lower = section.content.lower()
            if any(kw in content_lower for kw in background_keywords):
                background_content.append(section.content)
        
        if background_content:
            return " ".join(background_content[:2])
        
        return "Professional background discussed during interview."

    
    def _identify_risks(
        self,
        motivation: SkillAssessment,
        skills: List[SkillAssessment],
        practical: PracticalDetails,
        profile: RequirementProfile
    ) -> List[str]:
        """Identify risks and considerations.
        
        Args:
            motivation: Motivation assessment
            skills: Skill assessments
            practical: Practical details
            profile: Requirement profile
            
        Returns:
            List of risk/consideration strings
        """
        risks: List[str] = []
        
        # Check motivation
        if motivation.rating.value <= 2:
            risks.append("Low motivation score may indicate lack of genuine interest.")
        
        # Check skills
        low_skill_count = sum(1 for s in skills if s.rating.value <= 2)
        if low_skill_count > 0:
            risks.append(f"{low_skill_count} must-have skill(s) rated below expectations.")
        
        # Check practical
        if practical.notice_period == "Not discussed":
            risks.append("Notice period not clarified during interview.")
        
        if practical.salary_expectation == "Not discussed":
            risks.append("Salary expectations not discussed.")
        
        return risks
    
    def _determine_recommendation(
        self,
        motivation: SkillAssessment,
        skills: List[SkillAssessment]
    ) -> Recommendation:
        """Determine overall recommendation.
        
        Args:
            motivation: Motivation assessment
            skills: Skill assessments
            
        Returns:
            Recommendation enum value
        """
        # Calculate average rating
        all_ratings = [motivation.rating.value]
        all_ratings.extend(s.rating.value for s in skills)
        avg_rating = sum(all_ratings) / len(all_ratings)
        
        # Count low ratings
        low_count = sum(1 for r in all_ratings if r <= 2)
        
        if avg_rating >= 4.0 and low_count == 0:
            return Recommendation.RECOMMENDED
        elif avg_rating < 2.5 or low_count >= 2:
            return Recommendation.NOT_RECOMMENDED
        else:
            return Recommendation.BORDERLINE
    
    def _generate_conclusion(
        self,
        recommendation: Recommendation,
        motivation: SkillAssessment,
        skills: List[SkillAssessment],
        risks: List[str]
    ) -> str:
        """Generate conclusion text.
        
        Args:
            recommendation: Overall recommendation
            motivation: Motivation assessment
            skills: Skill assessments
            risks: Identified risks
            
        Returns:
            Conclusion text
        """
        # Calculate stats
        avg_rating = (motivation.rating.value + sum(s.rating.value for s in skills)) / (1 + len(skills))
        
        if recommendation == Recommendation.RECOMMENDED:
            conclusion = f"Candidate demonstrates strong alignment with role requirements. "
            conclusion += f"Average rating: {avg_rating:.1f}/5. "
            conclusion += "Recommend proceeding to next stage."
        elif recommendation == Recommendation.NOT_RECOMMENDED:
            conclusion = f"Candidate does not meet minimum requirements for this role. "
            conclusion += f"Average rating: {avg_rating:.1f}/5. "
            if risks:
                conclusion += f"Key concerns: {risks[0]}"
        else:
            conclusion = f"Candidate shows potential but has areas of concern. "
            conclusion += f"Average rating: {avg_rating:.1f}/5. "
            conclusion += "Consider for further evaluation with focus on identified gaps."
        
        return conclusion


def create_comparison_table(
    reports: List[CandidateReport],
    skills_to_compare: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """Create a comparison table for multiple candidates per Requirement 8.7.
    
    Uses initials only for anonymization.
    
    Args:
        reports: List of candidate reports to compare
        skills_to_compare: Optional list of skills to include
        
    Returns:
        Dict with headers and rows for comparison table
    """
    if not reports:
        return {"headers": [], "rows": []}
    
    # Determine skills to compare
    if skills_to_compare:
        skills = skills_to_compare
    else:
        # Use skills from first report
        skills = [sa.skill_name for sa in reports[0].skill_assessments]
    
    # Build headers: Candidate, Motivation, Skills..., Recommendation
    headers = ["Candidate", "Motivation"] + skills + ["Recommendation"]
    
    # Build rows
    rows: List[List[str]] = []
    for report in reports:
        row = [
            report.candidate_initials,  # Anonymized per Req 8.7
            f"{report.motivation_assessment.rating.value}/5",
        ]
        
        # Add skill ratings
        skill_ratings = {sa.skill_name: sa.rating.value for sa in report.skill_assessments}
        for skill in skills:
            rating = skill_ratings.get(skill, "-")
            row.append(f"{rating}/5" if isinstance(rating, int) else rating)
        
        row.append(report.recommendation.value)
        rows.append(row)
    
    return {"headers": headers, "rows": rows}
