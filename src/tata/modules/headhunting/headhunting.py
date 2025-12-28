"""Headhunting Messages module for Tata recruitment assistant.

This module implements Module E: Headhunting Messages creation.
Generates LinkedIn outreach messages in multiple styles and languages
for sourcing passive candidates.

Requirements covered:
- 7.1: Create three message versions (Short & Direct, Value-Proposition, Call-to-Action)
- 7.2: Make all versions available in EN, SV, DA, NO, DE (du and Sie)
- 7.3: Keep first contact messages under 100 words
- 7.4: Personalize with one detail from candidate LinkedIn profile when provided
- 7.5: Avoid generic hype phrases like "Exciting opportunity"
- 7.6: Include role hook, one value proposition, and call to action in each message
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple
from enum import Enum
import json
import re

from src.tata.memory.memory import ArtifactType
from src.tata.modules.profile.profile import RequirementProfile
from src.tata.modules.jobad.jobad import JobAd
from src.tata.session.session import SupportedLanguage
from src.tata.language.banned_words import get_banned_words_for_language
from src.tata.language.checker import (
    check_banned_words,
    GermanFormality,
    get_german_formality,
)


# Maximum word count for first contact messages (Requirement 7.3)
MAX_MESSAGE_WORDS = 100


class MessageTooLongError(Exception):
    """Raised when a message exceeds the word limit."""
    pass


class MissingRequirementProfileError(Exception):
    """Raised when headhunting message creation is attempted without a requirement profile."""
    pass


class InvalidHeadhuntingInputError(Exception):
    """Raised when headhunting input validation fails."""
    pass


class MessageVersion(Enum):
    """Types of headhunting message versions (Requirement 7.1)."""
    SHORT_DIRECT = "short_direct"
    VALUE_PROPOSITION = "value_proposition"
    CALL_TO_ACTION = "call_to_action"


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
class MessageStructure:
    """Structure validation for a message (Requirement 7.6).
    
    Each message must contain:
    - role_hook: A hook about the role to grab attention
    - value_proposition: One value proposition
    - call_to_action: A clear call to action
    
    Attributes:
        has_role_hook: Whether the message has a role hook
        has_value_proposition: Whether the message has a value proposition
        has_call_to_action: Whether the message has a call to action
        is_complete: Whether all required elements are present
    """
    has_role_hook: bool
    has_value_proposition: bool
    has_call_to_action: bool
    
    @property
    def is_complete(self) -> bool:
        """Check if all required elements are present."""
        return self.has_role_hook and self.has_value_proposition and self.has_call_to_action


@dataclass
class MultiLanguageMessage:
    """Message in all supported languages (Requirement 7.2).
    
    Contains the same message translated into all five supported languages,
    with German having both informal (du) and formal (Sie) variants.
    
    Attributes:
        en: English version
        sv: Swedish version
        da: Danish version
        no: Norwegian version
        de_du: German informal (du) version
        de_sie: German formal (Sie) version
    """
    en: str
    sv: str
    da: str
    no: str
    de_du: str
    de_sie: str
    
    def get_for_language(
        self,
        language: SupportedLanguage,
        german_formality: Optional[GermanFormality] = None
    ) -> str:
        """Get the message for a specific language.
        
        Args:
            language: The target language
            german_formality: For German, whether to use du or Sie
            
        Returns:
            The message in the requested language
        """
        if language == SupportedLanguage.ENGLISH:
            return self.en
        elif language == SupportedLanguage.SWEDISH:
            return self.sv
        elif language == SupportedLanguage.DANISH:
            return self.da
        elif language == SupportedLanguage.NORWEGIAN:
            return self.no
        elif language == SupportedLanguage.GERMAN:
            if german_formality == GermanFormality.DU:
                return self.de_du
            return self.de_sie
        return self.en  # Default to English
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "en": self.en,
            "sv": self.sv,
            "da": self.da,
            "no": self.no,
            "de_du": self.de_du,
            "de_sie": self.de_sie,
        }


@dataclass
class HeadhuntingInput:
    """Input for creating headhunting messages.
    
    Requires a requirement profile as the foundation.
    Optional job ad and candidate profile for enrichment.
    
    Attributes:
        requirement_profile: The requirement profile (required)
        job_ad: Optional job ad for additional context
        candidate_profile: Optional LinkedIn profile text for personalization
        company_context: Optional company/team context
    """
    requirement_profile: RequirementProfile
    job_ad: Optional[JobAd] = None
    candidate_profile: Optional[str] = None
    company_context: Optional[str] = None


@dataclass
class HeadhuntingMessages:
    """All three message versions in all languages (Requirements 7.1, 7.2).
    
    Contains three distinct message versions, each available in all
    supported languages. The versions are:
    - short_direct: Brief, to-the-point message
    - value_proposition: Focuses on what the candidate gains
    - call_to_action: Emphasizes the next step
    
    Attributes:
        short_direct: Short & direct message version
        value_proposition: Value-proposition focused version
        call_to_action: Clear call-to-action version
        personalization_detail: The detail used for personalization (if any)
        created_at: When the messages were created
    """
    short_direct: MultiLanguageMessage
    value_proposition: MultiLanguageMessage
    call_to_action: MultiLanguageMessage
    personalization_detail: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type for memory storage."""
        return ArtifactType.HEADHUNTING_MESSAGES
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "short_direct": self.short_direct.to_dict(),
            "value_proposition": self.value_proposition.to_dict(),
            "call_to_action": self.call_to_action.to_dict(),
            "personalization_detail": self.personalization_detail,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data, indent=2)
    
    def get_version(self, version: MessageVersion) -> MultiLanguageMessage:
        """Get a specific message version.
        
        Args:
            version: The message version to retrieve
            
        Returns:
            The MultiLanguageMessage for that version
        """
        if version == MessageVersion.SHORT_DIRECT:
            return self.short_direct
        elif version == MessageVersion.VALUE_PROPOSITION:
            return self.value_proposition
        elif version == MessageVersion.CALL_TO_ACTION:
            return self.call_to_action
        return self.short_direct



# Hype phrases to avoid (Requirement 7.5)
HYPE_PHRASES = [
    "exciting opportunity",
    "amazing opportunity",
    "incredible opportunity",
    "fantastic opportunity",
    "unique opportunity",
    "once in a lifetime",
    "game-changing",
    "revolutionary",
    "world-class",
    "best in class",
    "cutting-edge",
    "state-of-the-art",
    "industry-leading",
    "market-leading",
    "top-tier",
    "elite",
    "rockstar",
    "ninja",
    "guru",
    "wizard",
]


def count_words(text: str) -> int:
    """Count the number of words in text.
    
    Args:
        text: The text to count words in
        
    Returns:
        Number of words
    """
    if not text:
        return 0
    # Split on whitespace and filter empty strings
    words = [w for w in text.split() if w.strip()]
    return len(words)


def contains_hype_phrases(text: str) -> bool:
    """Check if text contains any hype phrases.
    
    Args:
        text: The text to check
        
    Returns:
        True if hype phrases found, False otherwise
    """
    if not text:
        return False
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in HYPE_PHRASES)


def extract_personalization_detail(candidate_profile: str) -> Optional[str]:
    """Extract a personalization detail from candidate LinkedIn profile.
    
    Looks for specific details that can be used to personalize the message:
    - Current company/role
    - Notable skills or experience
    - Education
    - Recent achievements
    
    Args:
        candidate_profile: The LinkedIn profile text
        
    Returns:
        A personalization detail string, or None if none found
    """
    if not candidate_profile or not candidate_profile.strip():
        return None
    
    profile_lower = candidate_profile.lower()
    
    # Try to extract current role/company
    role_patterns = [
        r"(?:currently|presently|now)\s+(?:working\s+)?(?:as\s+)?(?:a\s+)?([^.]+?)(?:\s+at\s+|\s+@\s+)([^.]+)",
        r"([^.]+?)\s+at\s+([^.]+?)(?:\s|$|\.)",
        r"(?:senior|lead|principal|staff|junior)?\s*([a-zA-Z\s]+(?:engineer|developer|manager|designer|analyst|consultant))",
    ]
    
    for pattern in role_patterns:
        match = re.search(pattern, candidate_profile, re.IGNORECASE)
        if match:
            detail = match.group(0).strip()
            # Clean up the detail
            detail = re.sub(r'\s+', ' ', detail)
            if len(detail) > 10 and len(detail) < 100:
                return detail
    
    # Try to extract years of experience
    exp_match = re.search(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", candidate_profile, re.IGNORECASE)
    if exp_match:
        return f"{exp_match.group(1)}+ years of experience"
    
    # Try to extract a skill
    skill_patterns = [
        r"(?:expert|experienced|skilled|proficient)\s+(?:in|with)\s+([^.]+)",
        r"specializ(?:e|ing)\s+in\s+([^.]+)",
    ]
    
    for pattern in skill_patterns:
        match = re.search(pattern, candidate_profile, re.IGNORECASE)
        if match:
            skill = match.group(1).strip()
            if len(skill) > 5 and len(skill) < 50:
                return f"expertise in {skill}"
    
    # Fallback: extract first meaningful sentence
    sentences = candidate_profile.split('.')
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20 and len(sentence) < 100:
            return sentence
    
    return None


def validate_message_structure(message: str) -> MessageStructure:
    """Validate that a message has the required structure (Requirement 7.6).
    
    Checks for:
    - Role hook: Mention of the role/position
    - Value proposition: What the candidate gains
    - Call to action: Clear next step
    
    Args:
        message: The message to validate
        
    Returns:
        MessageStructure with validation results
    """
    if not message:
        return MessageStructure(
            has_role_hook=False,
            has_value_proposition=False,
            has_call_to_action=False,
        )
    
    message_lower = message.lower()
    
    # Check for role hook (mention of position/role)
    role_indicators = [
        "position", "role", "opportunity", "looking for", "seeking",
        "engineer", "developer", "manager", "designer", "analyst",
        "specialist", "consultant", "lead", "director", "coordinator",
    ]
    has_role_hook = any(indicator in message_lower for indicator in role_indicators)
    
    # Check for value proposition (what candidate gains)
    value_indicators = [
        "you will", "you'll", "you can", "you would",
        "offer", "provide", "benefit", "growth", "develop",
        "learn", "impact", "contribute", "join", "team",
        "work with", "collaborate", "build", "create",
        "competitive", "flexible", "remote", "hybrid",
    ]
    has_value_proposition = any(indicator in message_lower for indicator in value_indicators)
    
    # Check for call to action
    cta_indicators = [
        "let me know", "interested", "connect", "chat", "talk",
        "discuss", "reach out", "reply", "respond", "contact",
        "schedule", "call", "meet", "hear from you", "get in touch",
        "learn more", "find out", "apply", "send", "share",
        "?",  # Questions often serve as CTAs
    ]
    has_call_to_action = any(indicator in message_lower for indicator in cta_indicators)
    
    return MessageStructure(
        has_role_hook=has_role_hook,
        has_value_proposition=has_value_proposition,
        has_call_to_action=has_call_to_action,
    )



class HeadhuntingProcessor:
    """Processor for creating headhunting messages from requirement profiles.
    
    Implements the ModuleProcessor pattern for Module E.
    Creates three message versions in all supported languages,
    with optional personalization from candidate profiles.
    
    Requirements covered:
    - 7.1: Create three message versions
    - 7.2: All versions in EN, SV, DA, NO, DE (du and Sie)
    - 7.3: Keep messages under 100 words
    - 7.4: Personalize with candidate profile detail when provided
    - 7.5: Avoid hype phrases
    - 7.6: Include role hook, value prop, and CTA in each message
    """
    
    def validate(self, input_data: HeadhuntingInput) -> ValidationResult:
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
            profile = input_data.requirement_profile
            
            if not profile.position_title:
                errors.append(ValidationError(
                    field="requirement_profile.position_title",
                    message="Position title is required"
                ))
            
            if len(profile.must_have_skills) != 4:
                warnings.append(ValidationWarning(
                    field="requirement_profile.must_have_skills",
                    message="Profile should have exactly 4 must-have skills"
                ))
        
        # Check for candidate profile (optional but noted)
        if input_data.candidate_profile:
            if len(input_data.candidate_profile.strip()) < 20:
                warnings.append(ValidationWarning(
                    field="candidate_profile",
                    message="Candidate profile is very short; personalization may be limited"
                ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def process(self, input_data: HeadhuntingInput) -> HeadhuntingMessages:
        """Process input and generate headhunting messages.
        
        Args:
            input_data: The headhunting input with requirement profile
            
        Returns:
            HeadhuntingMessages with all three versions in all languages
            
        Raises:
            MissingRequirementProfileError: If no requirement profile provided
            InvalidHeadhuntingInputError: If input validation fails
        """
        # Validate input
        validation = self.validate(input_data)
        if not validation.is_valid:
            error_msgs = "; ".join(e.message for e in validation.errors)
            if "requirement profile" in error_msgs.lower():
                raise MissingRequirementProfileError(error_msgs)
            raise InvalidHeadhuntingInputError(f"Input validation failed: {error_msgs}")
        
        profile = input_data.requirement_profile
        
        # Extract personalization detail if candidate profile provided
        personalization_detail = None
        if input_data.candidate_profile:
            personalization_detail = extract_personalization_detail(
                input_data.candidate_profile
            )
        
        # Determine German formality from context
        context = input_data.company_context or ""
        if profile.bu_description:
            context += " " + profile.bu_description
        german_formality = get_german_formality(context)
        
        # Generate all three message versions
        short_direct = self._generate_short_direct(
            profile, personalization_detail, german_formality
        )
        value_proposition = self._generate_value_proposition(
            profile, input_data.job_ad, personalization_detail, german_formality
        )
        call_to_action = self._generate_call_to_action(
            profile, personalization_detail, german_formality
        )
        
        return HeadhuntingMessages(
            short_direct=short_direct,
            value_proposition=value_proposition,
            call_to_action=call_to_action,
            personalization_detail=personalization_detail,
        )
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input fields."""
        return ["requirement_profile"]
    
    def get_optional_inputs(self) -> List[str]:
        """Get list of optional input fields."""
        return ["job_ad", "candidate_profile", "company_context"]
    
    def _generate_short_direct(
        self,
        profile: RequirementProfile,
        personalization: Optional[str],
        german_formality: GermanFormality,
    ) -> MultiLanguageMessage:
        """Generate short & direct message version.
        
        Brief, to-the-point message that gets straight to the opportunity.
        
        Args:
            profile: The requirement profile
            personalization: Optional personalization detail
            german_formality: German du/Sie preference
            
        Returns:
            MultiLanguageMessage with all language versions
        """
        position = profile.position_title
        
        # Build personalization prefix
        personal_en = f"I noticed your {personalization}. " if personalization else ""
        personal_sv = f"Jag såg din {personalization}. " if personalization else ""
        personal_da = f"Jeg lagde mærke til din {personalization}. " if personalization else ""
        personal_no = f"Jeg la merke til din {personalization}. " if personalization else ""
        personal_de = f"Mir ist aufgefallen, dass Sie {personalization} haben. " if personalization else ""
        personal_de_du = f"Mir ist aufgefallen, dass du {personalization} hast. " if personalization else ""
        
        # English
        en = (
            f"Hi,\n\n"
            f"{personal_en}"
            f"We have an open {position} position at GlobalConnect. "
            f"The role involves {profile.primary_responsibilities[0].lower() if profile.primary_responsibilities else 'interesting challenges'}. "
            f"Would you be open to a quick chat?\n\n"
            f"Best regards"
        )
        
        # Swedish
        sv = (
            f"Hej,\n\n"
            f"{personal_sv}"
            f"Vi har en ledig {position}-tjänst på GlobalConnect. "
            f"Rollen innebär {profile.primary_responsibilities[0].lower() if profile.primary_responsibilities else 'intressanta utmaningar'}. "
            f"Skulle du vara öppen för ett kort samtal?\n\n"
            f"Vänliga hälsningar"
        )
        
        # Danish
        da = (
            f"Hej,\n\n"
            f"{personal_da}"
            f"Vi har en ledig {position}-stilling hos GlobalConnect. "
            f"Rollen indebærer {profile.primary_responsibilities[0].lower() if profile.primary_responsibilities else 'interessante udfordringer'}. "
            f"Ville du være åben for en kort snak?\n\n"
            f"Venlig hilsen"
        )
        
        # Norwegian
        no = (
            f"Hei,\n\n"
            f"{personal_no}"
            f"Vi har en ledig {position}-stilling hos GlobalConnect. "
            f"Rollen innebærer {profile.primary_responsibilities[0].lower() if profile.primary_responsibilities else 'interessante utfordringer'}. "
            f"Ville du være åpen for en kort prat?\n\n"
            f"Vennlig hilsen"
        )
        
        # German formal (Sie)
        de_sie = (
            f"Guten Tag,\n\n"
            f"{personal_de}"
            f"Wir haben eine offene {position}-Stelle bei GlobalConnect. "
            f"Die Rolle umfasst {profile.primary_responsibilities[0].lower() if profile.primary_responsibilities else 'interessante Herausforderungen'}. "
            f"Wären Sie offen für ein kurzes Gespräch?\n\n"
            f"Mit freundlichen Grüßen"
        )
        
        # German informal (du)
        de_du = (
            f"Hi,\n\n"
            f"{personal_de_du}"
            f"Wir haben eine offene {position}-Stelle bei GlobalConnect. "
            f"Die Rolle umfasst {profile.primary_responsibilities[0].lower() if profile.primary_responsibilities else 'interessante Herausforderungen'}. "
            f"Hättest du Lust auf ein kurzes Gespräch?\n\n"
            f"Viele Grüße"
        )
        
        return MultiLanguageMessage(
            en=self._ensure_under_word_limit(en),
            sv=self._ensure_under_word_limit(sv),
            da=self._ensure_under_word_limit(da),
            no=self._ensure_under_word_limit(no),
            de_du=self._ensure_under_word_limit(de_du),
            de_sie=self._ensure_under_word_limit(de_sie),
        )
    
    def _generate_value_proposition(
        self,
        profile: RequirementProfile,
        job_ad: Optional[JobAd],
        personalization: Optional[str],
        german_formality: GermanFormality,
    ) -> MultiLanguageMessage:
        """Generate value-proposition focused message version.
        
        Emphasizes what the candidate gains from the opportunity.
        
        Args:
            profile: The requirement profile
            job_ad: Optional job ad for additional context
            personalization: Optional personalization detail
            german_formality: German du/Sie preference
            
        Returns:
            MultiLanguageMessage with all language versions
        """
        position = profile.position_title
        
        # Extract value props from profile or job ad
        value_props = []
        if profile.motivations:
            value_props.extend(profile.motivations[:2])
        if profile.team_info:
            value_props.append(f"team of {profile.team_info.size} in {profile.team_info.location}")
        
        value_text_en = value_props[0] if value_props else "make a real impact"
        
        # Build personalization
        personal_en = f"Your background in {personalization} caught my attention. " if personalization else ""
        personal_sv = f"Din bakgrund inom {personalization} fångade min uppmärksamhet. " if personalization else ""
        personal_da = f"Din baggrund inden for {personalization} fangede min opmærksomhed. " if personalization else ""
        personal_no = f"Din bakgrunn innen {personalization} fanget min oppmerksomhet. " if personalization else ""
        personal_de = f"Ihr Hintergrund in {personalization} hat meine Aufmerksamkeit erregt. " if personalization else ""
        personal_de_du = f"Dein Hintergrund in {personalization} hat meine Aufmerksamkeit erregt. " if personalization else ""
        
        # English
        en = (
            f"Hi,\n\n"
            f"{personal_en}"
            f"I'm reaching out about a {position} role at GlobalConnect. "
            f"This is a chance to {value_text_en.lower()}. "
            f"You would join a team focused on building the digital infrastructure of the Nordics. "
            f"Interested in learning more?\n\n"
            f"Best regards"
        )
        
        # Swedish
        sv = (
            f"Hej,\n\n"
            f"{personal_sv}"
            f"Jag kontaktar dig angående en {position}-roll på GlobalConnect. "
            f"Det här är en chans att {value_text_en.lower()}. "
            f"Du skulle bli en del av ett team som bygger Nordens digitala infrastruktur. "
            f"Intresserad av att veta mer?\n\n"
            f"Vänliga hälsningar"
        )
        
        # Danish
        da = (
            f"Hej,\n\n"
            f"{personal_da}"
            f"Jeg kontakter dig vedrørende en {position}-rolle hos GlobalConnect. "
            f"Dette er en chance for at {value_text_en.lower()}. "
            f"Du vil blive en del af et team, der bygger Nordens digitale infrastruktur. "
            f"Interesseret i at høre mere?\n\n"
            f"Venlig hilsen"
        )
        
        # Norwegian
        no = (
            f"Hei,\n\n"
            f"{personal_no}"
            f"Jeg kontakter deg angående en {position}-rolle hos GlobalConnect. "
            f"Dette er en sjanse til å {value_text_en.lower()}. "
            f"Du vil bli en del av et team som bygger Nordens digitale infrastruktur. "
            f"Interessert i å høre mer?\n\n"
            f"Vennlig hilsen"
        )
        
        # German formal (Sie)
        de_sie = (
            f"Guten Tag,\n\n"
            f"{personal_de}"
            f"Ich kontaktiere Sie bezüglich einer {position}-Position bei GlobalConnect. "
            f"Dies ist eine Gelegenheit, {value_text_en.lower()}. "
            f"Sie würden einem Team beitreten, das die digitale Infrastruktur Skandinaviens aufbaut. "
            f"Haben Sie Interesse, mehr zu erfahren?\n\n"
            f"Mit freundlichen Grüßen"
        )
        
        # German informal (du)
        de_du = (
            f"Hi,\n\n"
            f"{personal_de_du}"
            f"Ich kontaktiere dich bezüglich einer {position}-Position bei GlobalConnect. "
            f"Dies ist eine Gelegenheit, {value_text_en.lower()}. "
            f"Du würdest einem Team beitreten, das die digitale Infrastruktur Skandinaviens aufbaut. "
            f"Hast du Interesse, mehr zu erfahren?\n\n"
            f"Viele Grüße"
        )
        
        return MultiLanguageMessage(
            en=self._ensure_under_word_limit(en),
            sv=self._ensure_under_word_limit(sv),
            da=self._ensure_under_word_limit(da),
            no=self._ensure_under_word_limit(no),
            de_du=self._ensure_under_word_limit(de_du),
            de_sie=self._ensure_under_word_limit(de_sie),
        )
    
    def _generate_call_to_action(
        self,
        profile: RequirementProfile,
        personalization: Optional[str],
        german_formality: GermanFormality,
    ) -> MultiLanguageMessage:
        """Generate call-to-action focused message version.
        
        Emphasizes the next step and makes it easy to respond.
        
        Args:
            profile: The requirement profile
            personalization: Optional personalization detail
            german_formality: German du/Sie preference
            
        Returns:
            MultiLanguageMessage with all language versions
        """
        position = profile.position_title
        
        # Build personalization
        personal_en = f"Given your {personalization}, " if personalization else ""
        personal_sv = f"Med tanke på din {personalization}, " if personalization else ""
        personal_da = f"I betragtning af din {personalization}, " if personalization else ""
        personal_no = f"Med tanke på din {personalization}, " if personalization else ""
        personal_de = f"Angesichts Ihrer {personalization}, " if personalization else ""
        personal_de_du = f"Angesichts deiner {personalization}, " if personalization else ""
        
        # English
        en = (
            f"Hi,\n\n"
            f"{personal_en}"
            f"I think you could be a great fit for our {position} role at GlobalConnect. "
            f"I'd love to tell you more about the team and what we're building. "
            f"Would a 15-minute call this week work for you? "
            f"Just reply with a time that suits you.\n\n"
            f"Looking forward to hearing from you"
        )
        
        # Swedish
        sv = (
            f"Hej,\n\n"
            f"{personal_sv}"
            f"Jag tror att du skulle passa utmärkt för vår {position}-roll på GlobalConnect. "
            f"Jag skulle gärna berätta mer om teamet och vad vi bygger. "
            f"Skulle ett 15-minuters samtal denna vecka passa dig? "
            f"Svara bara med en tid som passar.\n\n"
            f"Ser fram emot att höra från dig"
        )
        
        # Danish
        da = (
            f"Hej,\n\n"
            f"{personal_da}"
            f"Jeg tror, du kunne passe godt til vores {position}-rolle hos GlobalConnect. "
            f"Jeg vil gerne fortælle dig mere om teamet og hvad vi bygger. "
            f"Ville et 15-minutters opkald i denne uge passe dig? "
            f"Svar bare med et tidspunkt, der passer.\n\n"
            f"Ser frem til at høre fra dig"
        )
        
        # Norwegian
        no = (
            f"Hei,\n\n"
            f"{personal_no}"
            f"Jeg tror du kunne passe godt til vår {position}-rolle hos GlobalConnect. "
            f"Jeg vil gjerne fortelle deg mer om teamet og hva vi bygger. "
            f"Ville en 15-minutters samtale denne uken passe deg? "
            f"Bare svar med et tidspunkt som passer.\n\n"
            f"Ser frem til å høre fra deg"
        )
        
        # German formal (Sie)
        de_sie = (
            f"Guten Tag,\n\n"
            f"{personal_de}"
            f"Ich denke, Sie könnten gut zu unserer {position}-Position bei GlobalConnect passen. "
            f"Ich würde Ihnen gerne mehr über das Team und unsere Arbeit erzählen. "
            f"Würde Ihnen ein 15-minütiges Gespräch diese Woche passen? "
            f"Antworten Sie einfach mit einer Zeit, die Ihnen passt.\n\n"
            f"Ich freue mich auf Ihre Rückmeldung"
        )
        
        # German informal (du)
        de_du = (
            f"Hi,\n\n"
            f"{personal_de_du}"
            f"Ich denke, du könntest gut zu unserer {position}-Position bei GlobalConnect passen. "
            f"Ich würde dir gerne mehr über das Team und unsere Arbeit erzählen. "
            f"Würde dir ein 15-minütiges Gespräch diese Woche passen? "
            f"Antworte einfach mit einer Zeit, die dir passt.\n\n"
            f"Ich freue mich auf deine Rückmeldung"
        )
        
        return MultiLanguageMessage(
            en=self._ensure_under_word_limit(en),
            sv=self._ensure_under_word_limit(sv),
            da=self._ensure_under_word_limit(da),
            no=self._ensure_under_word_limit(no),
            de_du=self._ensure_under_word_limit(de_du),
            de_sie=self._ensure_under_word_limit(de_sie),
        )
    
    def _ensure_under_word_limit(self, message: str) -> str:
        """Ensure message is under the word limit (Requirement 7.3).
        
        If message exceeds 100 words, truncate it intelligently.
        
        Args:
            message: The message to check/truncate
            
        Returns:
            Message under 100 words
        """
        word_count = count_words(message)
        
        if word_count <= MAX_MESSAGE_WORDS:
            return message
        
        # Truncate by removing sentences from the middle
        lines = message.split('\n')
        
        # Keep greeting and closing, trim middle
        if len(lines) >= 3:
            greeting = lines[0]
            closing = lines[-1]
            middle = '\n'.join(lines[1:-1])
            
            # Truncate middle content
            sentences = middle.split('. ')
            while count_words('\n'.join([greeting, '. '.join(sentences), closing])) > MAX_MESSAGE_WORDS and len(sentences) > 1:
                # Remove the longest sentence
                sentences.pop(len(sentences) // 2)
            
            return '\n'.join([greeting, '. '.join(sentences), closing])
        
        # Fallback: just truncate words
        words = message.split()
        return ' '.join(words[:MAX_MESSAGE_WORDS - 5]) + '...'
