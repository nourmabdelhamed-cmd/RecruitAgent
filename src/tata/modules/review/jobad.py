"""Job Ad Review module for Tata recruitment assistant.

This module implements Module H: Job Ad Review.
Reviews existing job ads for structure, completeness, and quality,
providing a scorecard and improvement recommendations.

Requirements covered:
- Module H specification: Review existing job ads
- Section mapping and gap analysis
- Identify missing or duplicated content
- Provide structured feedback with scorecard
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Tuple
import json
import re

from src.tata.session.session import SupportedLanguage
from src.tata.memory.memory import ArtifactType
from src.tata.language.checker import (
    check_banned_words,
    has_emojis,
    has_dash_bullets,
    BannedWordCheck,
)


class JobAdSection(Enum):
    """Expected sections in a job ad."""
    HEADLINE = "headline"
    INTRO = "intro"
    ROLE_DESCRIPTION = "role_description"
    RESPONSIBILITIES = "responsibilities"
    REQUIREMENTS = "requirements"
    SOFT_SKILLS = "soft_skills"
    GOOD_TO_HAVES = "good_to_haves"
    TEAM_INFO = "team_info"
    COMPANY_INFO = "company_info"
    BENEFITS = "benefits"
    PROCESS = "process"
    CALL_TO_ACTION = "call_to_action"


class IssueSeverity(Enum):
    """Severity level for review issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SectionAnalysis:
    """Analysis result for a single section.
    
    Attributes:
        section: The section being analyzed
        found: Whether the section was found
        quality_score: Quality score 0-100
        word_count: Number of words in the section
        issues: List of issues found
        suggestions: Improvement suggestions
    """
    section: JobAdSection
    found: bool
    quality_score: int
    word_count: int = 0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ReviewIssue:
    """A single issue found during review.
    
    Attributes:
        category: Category of the issue
        severity: Severity level
        description: Description of the issue
        location: Where in the text the issue was found
        suggestion: How to fix the issue
    """
    category: str
    severity: IssueSeverity
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class JobAdReviewInput:
    """Input for job ad review.
    
    Attributes:
        job_ad_text: The job ad text to review
        language: The language of the job ad
        position_title: Optional position title for context
    """
    job_ad_text: str
    language: SupportedLanguage = SupportedLanguage.ENGLISH
    position_title: Optional[str] = None


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


@dataclass
class JobAdReview:
    """Complete job ad review result.
    
    Attributes:
        overall_score: Overall quality score (0-100)
        section_analyses: Analysis for each expected section
        issues: All issues found
        recommendations: Prioritized improvement recommendations
        structure_score: Score for structure/organization
        content_score: Score for content quality
        compliance_score: Score for language compliance
        original_text: The original text, preserved unchanged
        created_at: When the review was created
    """
    overall_score: int
    section_analyses: List[SectionAnalysis]
    issues: List[ReviewIssue]
    recommendations: List[str]
    structure_score: int
    content_score: int
    compliance_score: int
    original_text: str
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type for memory storage."""
        return ArtifactType.JOB_AD_REVIEW
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "overall_score": self.overall_score,
            "section_analyses": [
                {
                    "section": sa.section.value,
                    "found": sa.found,
                    "quality_score": sa.quality_score,
                    "word_count": sa.word_count,
                    "issues": sa.issues,
                    "suggestions": sa.suggestions,
                }
                for sa in self.section_analyses
            ],
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                }
                for issue in self.issues
            ],
            "recommendations": self.recommendations,
            "structure_score": self.structure_score,
            "content_score": self.content_score,
            "compliance_score": self.compliance_score,
            "original_text": self.original_text,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data, indent=2)


# Section detection patterns for different languages
SECTION_PATTERNS: Dict[SupportedLanguage, Dict[JobAdSection, List[str]]] = {
    SupportedLanguage.ENGLISH: {
        JobAdSection.HEADLINE: [],  # First line or title
        JobAdSection.INTRO: ["about", "introduction", "overview", "we are looking"],
        JobAdSection.ROLE_DESCRIPTION: ["about the role", "the role", "position", "what you'll do"],
        JobAdSection.RESPONSIBILITIES: ["responsibilities", "duties", "what you will", "key tasks", "your role"],
        JobAdSection.REQUIREMENTS: ["requirements", "qualifications", "what we need", "must have", "you bring"],
        JobAdSection.SOFT_SKILLS: ["soft skills", "personal qualities", "who you are", "personality"],
        JobAdSection.GOOD_TO_HAVES: ["nice to have", "good to have", "bonus", "preferred", "plus"],
        JobAdSection.TEAM_INFO: ["team", "department", "who we are", "about us"],
        JobAdSection.COMPANY_INFO: ["company", "about globalconnect", "our company", "who we are"],
        JobAdSection.BENEFITS: ["benefits", "perks", "what we offer", "compensation", "we offer"],
        JobAdSection.PROCESS: ["process", "how to apply", "application", "next steps", "recruitment"],
        JobAdSection.CALL_TO_ACTION: ["apply", "join us", "interested", "ready to"],
    },
    SupportedLanguage.SWEDISH: {
        JobAdSection.HEADLINE: [],
        JobAdSection.INTRO: ["om", "introduktion", "vi söker"],
        JobAdSection.ROLE_DESCRIPTION: ["om rollen", "rollen", "tjänsten", "vad du kommer göra"],
        JobAdSection.RESPONSIBILITIES: ["ansvar", "arbetsuppgifter", "du kommer att"],
        JobAdSection.REQUIREMENTS: ["krav", "kvalifikationer", "vi söker dig som", "du har"],
        JobAdSection.SOFT_SKILLS: ["personliga egenskaper", "vem du är"],
        JobAdSection.GOOD_TO_HAVES: ["meriterande", "önskvärt", "bonus"],
        JobAdSection.TEAM_INFO: ["teamet", "avdelningen", "vilka vi är"],
        JobAdSection.COMPANY_INFO: ["företaget", "om globalconnect", "om oss"],
        JobAdSection.BENEFITS: ["förmåner", "vi erbjuder", "ersättning"],
        JobAdSection.PROCESS: ["process", "ansökan", "nästa steg", "rekrytering"],
        JobAdSection.CALL_TO_ACTION: ["ansök", "sök tjänsten", "intresserad"],
    },
    SupportedLanguage.GERMAN: {
        JobAdSection.HEADLINE: [],
        JobAdSection.INTRO: ["über", "einleitung", "wir suchen"],
        JobAdSection.ROLE_DESCRIPTION: ["über die rolle", "die rolle", "position", "ihre aufgaben"],
        JobAdSection.RESPONSIBILITIES: ["aufgaben", "verantwortlichkeiten", "tätigkeiten"],
        JobAdSection.REQUIREMENTS: ["anforderungen", "qualifikationen", "ihr profil", "sie bringen mit"],
        JobAdSection.SOFT_SKILLS: ["soft skills", "persönliche eigenschaften"],
        JobAdSection.GOOD_TO_HAVES: ["wünschenswert", "von vorteil", "nice to have"],
        JobAdSection.TEAM_INFO: ["team", "abteilung", "wer wir sind"],
        JobAdSection.COMPANY_INFO: ["unternehmen", "über globalconnect", "über uns"],
        JobAdSection.BENEFITS: ["benefits", "vorteile", "wir bieten", "vergütung"],
        JobAdSection.PROCESS: ["prozess", "bewerbung", "nächste schritte"],
        JobAdSection.CALL_TO_ACTION: ["bewerben", "interesse", "bereit"],
    },
}

# Add Danish and Norwegian with similar patterns
SECTION_PATTERNS[SupportedLanguage.DANISH] = {
    JobAdSection.HEADLINE: [],
    JobAdSection.INTRO: ["om", "introduktion", "vi søger"],
    JobAdSection.ROLE_DESCRIPTION: ["om rollen", "rollen", "stillingen"],
    JobAdSection.RESPONSIBILITIES: ["ansvar", "arbejdsopgaver", "du vil"],
    JobAdSection.REQUIREMENTS: ["krav", "kvalifikationer", "vi søger dig som"],
    JobAdSection.SOFT_SKILLS: ["personlige egenskaber", "hvem du er"],
    JobAdSection.GOOD_TO_HAVES: ["ønskeligt", "bonus", "en fordel"],
    JobAdSection.TEAM_INFO: ["teamet", "afdelingen", "hvem vi er"],
    JobAdSection.COMPANY_INFO: ["virksomheden", "om globalconnect", "om os"],
    JobAdSection.BENEFITS: ["fordele", "vi tilbyder", "kompensation"],
    JobAdSection.PROCESS: ["proces", "ansøgning", "næste skridt"],
    JobAdSection.CALL_TO_ACTION: ["ansøg", "interesseret", "klar til"],
}

SECTION_PATTERNS[SupportedLanguage.NORWEGIAN] = {
    JobAdSection.HEADLINE: [],
    JobAdSection.INTRO: ["om", "introduksjon", "vi søker"],
    JobAdSection.ROLE_DESCRIPTION: ["om rollen", "rollen", "stillingen"],
    JobAdSection.RESPONSIBILITIES: ["ansvar", "arbeidsoppgaver", "du vil"],
    JobAdSection.REQUIREMENTS: ["krav", "kvalifikasjoner", "vi søker deg som"],
    JobAdSection.SOFT_SKILLS: ["personlige egenskaper", "hvem du er"],
    JobAdSection.GOOD_TO_HAVES: ["ønskelig", "bonus", "en fordel"],
    JobAdSection.TEAM_INFO: ["teamet", "avdelingen", "hvem vi er"],
    JobAdSection.COMPANY_INFO: ["selskapet", "om globalconnect", "om oss"],
    JobAdSection.BENEFITS: ["fordeler", "vi tilbyr", "kompensasjon"],
    JobAdSection.PROCESS: ["prosess", "søknad", "neste steg"],
    JobAdSection.CALL_TO_ACTION: ["søk", "interessert", "klar til"],
}

# Required sections for a complete job ad
REQUIRED_SECTIONS = [
    JobAdSection.HEADLINE,
    JobAdSection.ROLE_DESCRIPTION,
    JobAdSection.RESPONSIBILITIES,
    JobAdSection.REQUIREMENTS,
]

# Recommended sections for a high-quality job ad
RECOMMENDED_SECTIONS = [
    JobAdSection.INTRO,
    JobAdSection.TEAM_INFO,
    JobAdSection.BENEFITS,
    JobAdSection.CALL_TO_ACTION,
]

# Minimum word counts for quality
MIN_WORD_COUNTS = {
    JobAdSection.ROLE_DESCRIPTION: 30,
    JobAdSection.RESPONSIBILITIES: 20,
    JobAdSection.REQUIREMENTS: 20,
    JobAdSection.TEAM_INFO: 15,
    JobAdSection.BENEFITS: 15,
}

# Maximum word counts (to avoid overly long sections)
MAX_WORD_COUNTS = {
    JobAdSection.INTRO: 100,
    JobAdSection.ROLE_DESCRIPTION: 200,
    JobAdSection.RESPONSIBILITIES: 300,
    JobAdSection.REQUIREMENTS: 250,
}


def detect_sections(
    text: str,
    language: SupportedLanguage
) -> Dict[JobAdSection, Tuple[int, int, str]]:
    """Detect sections in the job ad text.
    
    Args:
        text: The job ad text
        language: The language of the text
        
    Returns:
        Dict mapping section to (start_pos, end_pos, content)
    """
    patterns = SECTION_PATTERNS.get(language, SECTION_PATTERNS[SupportedLanguage.ENGLISH])
    text_lower = text.lower()
    lines = text.split('\n')
    
    detected: Dict[JobAdSection, Tuple[int, int, str]] = {}
    
    # Detect headline (first non-empty line)
    for i, line in enumerate(lines):
        if line.strip():
            # Find position in original text
            pos = text.find(line.strip())
            detected[JobAdSection.HEADLINE] = (pos, pos + len(line.strip()), line.strip())
            break
    
    # Detect other sections by patterns
    for section, keywords in patterns.items():
        if section == JobAdSection.HEADLINE:
            continue
            
        for keyword in keywords:
            keyword_lower = keyword.lower()
            pos = text_lower.find(keyword_lower)
            if pos != -1:
                # Find the end of this section (next section or end of text)
                section_start = pos
                section_end = len(text)
                
                # Look for next section header
                for other_section, other_keywords in patterns.items():
                    if other_section == section:
                        continue
                    for other_keyword in other_keywords:
                        other_pos = text_lower.find(other_keyword.lower(), pos + len(keyword))
                        if other_pos != -1 and other_pos < section_end:
                            section_end = other_pos
                
                content = text[section_start:section_end].strip()
                if section not in detected:
                    detected[section] = (section_start, section_end, content)
                break
    
    return detected


def analyze_section(
    section: JobAdSection,
    content: str,
    language: SupportedLanguage
) -> SectionAnalysis:
    """Analyze a single section for quality.
    
    Args:
        section: The section type
        content: The section content
        language: The language
        
    Returns:
        SectionAnalysis with quality assessment
    """
    issues: List[str] = []
    suggestions: List[str] = []
    word_count = len(content.split())
    quality_score = 100
    
    # Check minimum word count
    min_words = MIN_WORD_COUNTS.get(section, 0)
    if min_words > 0 and word_count < min_words:
        quality_score -= 20
        issues.append(f"Section is too short ({word_count} words, minimum {min_words})")
        suggestions.append(f"Add more detail to reach at least {min_words} words")
    
    # Check maximum word count
    max_words = MAX_WORD_COUNTS.get(section, float('inf'))
    if word_count > max_words:
        quality_score -= 10
        issues.append(f"Section is too long ({word_count} words, maximum {max_words})")
        suggestions.append("Consider condensing this section for better readability")
    
    # Check for bullet points in responsibilities/requirements
    if section in [JobAdSection.RESPONSIBILITIES, JobAdSection.REQUIREMENTS]:
        bullet_patterns = [r'•', r'\*', r'\d+\.', r'-\s']
        has_bullets = any(re.search(p, content) for p in bullet_patterns)
        if not has_bullets and word_count > 30:
            quality_score -= 10
            issues.append("No bullet points found")
            suggestions.append("Use bullet points for better readability")
    
    # Check for vague language
    vague_words = ["various", "different", "some", "many", "etc", "and more"]
    vague_count = sum(1 for w in vague_words if w in content.lower())
    if vague_count > 2:
        quality_score -= 5 * vague_count
        issues.append(f"Contains {vague_count} vague terms")
        suggestions.append("Replace vague terms with specific details")
    
    return SectionAnalysis(
        section=section,
        found=True,
        quality_score=max(0, quality_score),
        word_count=word_count,
        issues=issues,
        suggestions=suggestions,
    )


def check_content_duplication(text: str) -> List[ReviewIssue]:
    """Check for duplicated content in the job ad.
    
    Args:
        text: The job ad text
        
    Returns:
        List of duplication issues found
    """
    issues: List[ReviewIssue] = []
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip().lower() for s in sentences if len(s.strip()) > 20]
    
    # Check for duplicate sentences
    seen = set()
    for sentence in sentences:
        if sentence in seen:
            issues.append(ReviewIssue(
                category="duplication",
                severity=IssueSeverity.MEDIUM,
                description="Duplicate sentence found",
                location=sentence[:50] + "...",
                suggestion="Remove or rephrase duplicate content",
            ))
        seen.add(sentence)
    
    # Check for repeated phrases (3+ words)
    words = text.lower().split()
    phrase_counts: Dict[str, int] = {}
    for i in range(len(words) - 2):
        phrase = " ".join(words[i:i+3])
        if len(phrase) > 10:  # Skip very short phrases
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
    
    for phrase, count in phrase_counts.items():
        if count > 2:
            issues.append(ReviewIssue(
                category="duplication",
                severity=IssueSeverity.LOW,
                description=f"Phrase repeated {count} times: '{phrase}'",
                suggestion="Vary your language to avoid repetition",
            ))
    
    return issues


def check_language_compliance(
    text: str,
    language: SupportedLanguage
) -> Tuple[int, List[ReviewIssue]]:
    """Check text for language compliance issues.
    
    Args:
        text: The job ad text
        language: The language
        
    Returns:
        Tuple of (compliance_score, list of issues)
    """
    issues: List[ReviewIssue] = []
    score = 100
    
    # Check for emojis
    if has_emojis(text):
        score -= 15
        issues.append(ReviewIssue(
            category="compliance",
            severity=IssueSeverity.MEDIUM,
            description="Emojis found in job ad",
            suggestion="Remove all emojis from the job ad",
        ))
    
    # Check for dash bullets
    if has_dash_bullets(text):
        score -= 10
        issues.append(ReviewIssue(
            category="compliance",
            severity=IssueSeverity.LOW,
            description="Dash-style bullets found",
            suggestion="Use proper bullet points (•) instead of dashes",
        ))
    
    # Check for banned words
    banned_check = check_banned_words(text, language)
    if banned_check.has_banned_words:
        penalty = min(len(banned_check.violations) * 5, 30)
        score -= penalty
        for violation in banned_check.violations[:5]:  # Limit to first 5
            issues.append(ReviewIssue(
                category="banned_words",
                severity=IssueSeverity.HIGH,
                description=f"Banned word found: '{violation.word}'",
                location=f"Position {violation.position}",
                suggestion=f"Replace with: {violation.suggestion}",
            ))
    
    return max(0, score), issues


def generate_recommendations(
    section_analyses: List[SectionAnalysis],
    issues: List[ReviewIssue],
    overall_score: int
) -> List[str]:
    """Generate prioritized recommendations.
    
    Args:
        section_analyses: Analysis of each section
        issues: All issues found
        overall_score: The overall score
        
    Returns:
        List of prioritized recommendations
    """
    recommendations: List[str] = []
    
    # Missing required sections (highest priority)
    missing_required = [
        sa.section for sa in section_analyses
        if sa.section in REQUIRED_SECTIONS and not sa.found
    ]
    for section in missing_required:
        recommendations.append(
            f"Add a {section.value.replace('_', ' ')} section - this is essential for a complete job ad"
        )
    
    # Critical issues
    critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
    for issue in critical_issues[:3]:
        recommendations.append(f"Critical: {issue.description}")
    
    # High severity issues
    high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]
    for issue in high_issues[:3]:
        if issue.suggestion:
            recommendations.append(issue.suggestion)
    
    # Missing recommended sections
    missing_recommended = [
        sa.section for sa in section_analyses
        if sa.section in RECOMMENDED_SECTIONS and not sa.found
    ]
    for section in missing_recommended[:2]:
        recommendations.append(
            f"Consider adding a {section.value.replace('_', ' ')} section to improve the job ad"
        )
    
    # Low quality sections
    low_quality = [
        sa for sa in section_analyses
        if sa.found and sa.quality_score < 70
    ]
    for sa in low_quality[:2]:
        if sa.suggestions:
            recommendations.append(
                f"Improve {sa.section.value.replace('_', ' ')}: {sa.suggestions[0]}"
            )
    
    # General recommendations based on score
    if overall_score < 50:
        recommendations.append(
            "This job ad needs significant improvement. Focus on structure and completeness first."
        )
    elif overall_score < 70:
        recommendations.append(
            "The job ad has a good foundation but could be enhanced with more detail and better structure."
        )
    
    return recommendations[:10]  # Limit to top 10 recommendations


class JobAdReviewProcessor:
    """Processor for reviewing job ads.
    
    Implements the ModuleProcessor pattern for Module H.
    Reviews job ads for structure, completeness, and quality,
    providing a scorecard and improvement recommendations.
    
    This is a standalone module with no dependencies.
    """
    
    def validate(self, input_data: JobAdReviewInput) -> ValidationResult:
        """Validate input data before processing.
        
        Args:
            input_data: The input to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # Check job ad text
        if not input_data.job_ad_text or not input_data.job_ad_text.strip():
            errors.append(ValidationError(
                field="job_ad_text",
                message="Job ad text is required"
            ))
        
        # Check minimum length
        if input_data.job_ad_text and len(input_data.job_ad_text.strip()) < 100:
            warnings.append(ValidationWarning(
                field="job_ad_text",
                message="Job ad text is very short; review may be limited"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def process(self, input_data: JobAdReviewInput) -> JobAdReview:
        """Process input and generate a job ad review.
        
        Args:
            input_data: The job ad review input
            
        Returns:
            A complete JobAdReview
            
        Raises:
            InvalidInputError: If input validation fails
        """
        # Validate first
        validation = self.validate(input_data)
        if not validation.is_valid:
            error_msgs = "; ".join(e.message for e in validation.errors)
            raise InvalidInputError(f"Input validation failed: {error_msgs}")
        
        text = input_data.job_ad_text
        language = input_data.language
        
        # Detect sections
        detected_sections = detect_sections(text, language)
        
        # Analyze each section
        section_analyses: List[SectionAnalysis] = []
        for section in JobAdSection:
            if section in detected_sections:
                _, _, content = detected_sections[section]
                analysis = analyze_section(section, content, language)
                section_analyses.append(analysis)
            else:
                section_analyses.append(SectionAnalysis(
                    section=section,
                    found=False,
                    quality_score=0,
                    issues=["Section not found"],
                    suggestions=[f"Add a {section.value.replace('_', ' ')} section"],
                ))
        
        # Collect all issues
        all_issues: List[ReviewIssue] = []
        
        # Check for duplication
        duplication_issues = check_content_duplication(text)
        all_issues.extend(duplication_issues)
        
        # Check language compliance
        compliance_score, compliance_issues = check_language_compliance(text, language)
        all_issues.extend(compliance_issues)
        
        # Add section-level issues
        for sa in section_analyses:
            if not sa.found and sa.section in REQUIRED_SECTIONS:
                all_issues.append(ReviewIssue(
                    category="structure",
                    severity=IssueSeverity.HIGH,
                    description=f"Missing required section: {sa.section.value.replace('_', ' ')}",
                    suggestion=f"Add a {sa.section.value.replace('_', ' ')} section",
                ))
        
        # Calculate scores
        structure_score = self._calculate_structure_score(section_analyses)
        content_score = self._calculate_content_score(section_analyses)
        overall_score = self._calculate_overall_score(
            structure_score, content_score, compliance_score
        )
        
        # Generate recommendations
        recommendations = generate_recommendations(
            section_analyses, all_issues, overall_score
        )
        
        return JobAdReview(
            overall_score=overall_score,
            section_analyses=section_analyses,
            issues=all_issues,
            recommendations=recommendations,
            structure_score=structure_score,
            content_score=content_score,
            compliance_score=compliance_score,
            original_text=text,
        )
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input fields."""
        return ["job_ad_text"]
    
    def get_optional_inputs(self) -> List[str]:
        """Get list of optional input fields."""
        return ["language", "position_title"]
    
    def _calculate_structure_score(
        self,
        section_analyses: List[SectionAnalysis]
    ) -> int:
        """Calculate structure score based on section presence.
        
        Args:
            section_analyses: Analysis of each section
            
        Returns:
            Structure score 0-100
        """
        score = 100
        
        # Penalty for missing required sections
        for sa in section_analyses:
            if sa.section in REQUIRED_SECTIONS and not sa.found:
                score -= 20
        
        # Penalty for missing recommended sections
        for sa in section_analyses:
            if sa.section in RECOMMENDED_SECTIONS and not sa.found:
                score -= 5
        
        return max(0, score)
    
    def _calculate_content_score(
        self,
        section_analyses: List[SectionAnalysis]
    ) -> int:
        """Calculate content score based on section quality.
        
        Args:
            section_analyses: Analysis of each section
            
        Returns:
            Content score 0-100
        """
        found_sections = [sa for sa in section_analyses if sa.found]
        
        if not found_sections:
            return 0
        
        # Average quality score of found sections
        total_quality = sum(sa.quality_score for sa in found_sections)
        return total_quality // len(found_sections)
    
    def _calculate_overall_score(
        self,
        structure_score: int,
        content_score: int,
        compliance_score: int
    ) -> int:
        """Calculate overall score.
        
        Args:
            structure_score: Score for structure
            content_score: Score for content quality
            compliance_score: Score for language compliance
            
        Returns:
            Overall score 0-100
        """
        # Weighted average: structure 30%, content 40%, compliance 30%
        return int(
            structure_score * 0.3 +
            content_score * 0.4 +
            compliance_score * 0.3
        )
