"""D&I Review module for Tata recruitment assistant.

This module implements Module I: Diversity & Inclusion Review.
Checks job ads for biased or exclusionary language and suggests alternatives.

Requirements covered:
- 10.1: Assess job ad text for inclusivity, bias, gendered language, and accessibility
- 10.2: Highlight flagged terms, tone issues, or gaps
- 10.3: Suggest alternative wording aligned with GC AI Language Guide
- 10.4: Never change the job ad automatically - all edits must be recruiter approved
- 10.5: Provide feedback report with flagged words/phrases, inclusive alternatives, overall score
- 10.6: Check against comprehensive word pools for all bias categories in all supported languages
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Tuple
import json
import re

from src.tata.session.session import SupportedLanguage
from src.tata.memory.memory import ArtifactType


class BiasCategory(Enum):
    """Categories of bias to check per Requirement 10.6.
    
    Covers gender, age, disability, nationality, family, socioeconomic,
    readability, requirements, german_title, and location.
    """
    GENDER = "gender"
    AGE = "age"
    DISABILITY = "disability"
    NATIONALITY = "nationality"
    FAMILY = "family"
    SOCIOECONOMIC = "socioeconomic"
    READABILITY = "readability"
    REQUIREMENTS = "requirements"
    GERMAN_TITLE = "german_title"
    LOCATION = "location"


class Severity(Enum):
    """Severity level for flagged items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class FlaggedItem:
    """Biased term found in text per Requirement 10.2.
    
    Attributes:
        text: The flagged word or phrase
        category: The bias category it belongs to
        severity: Severity level of the issue
        explanation: Why this is problematic
        alternatives: List of suggested alternative wordings
        position: Character position in the original text
    """
    text: str
    category: BiasCategory
    severity: Severity
    explanation: str
    alternatives: List[str]
    position: int = 0


@dataclass
class CategoryScore:
    """Score for a single bias category per Requirement 10.5.
    
    Attributes:
        category: The bias category
        score: Score from 0-100 (100 = no issues found)
        issues_found: Number of issues found in this category
    """
    category: BiasCategory
    score: int
    issues_found: int = 0


@dataclass
class DIReviewInput:
    """Input for D&I review per Requirement 10.1.
    
    Attributes:
        job_ad_text: The job ad text to review
        language: The language of the job ad
    """
    job_ad_text: str
    language: SupportedLanguage = SupportedLanguage.ENGLISH


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
class DIReview:
    """Complete D&I review result per Requirements 10.1-10.6.
    
    Attributes:
        overall_score: Overall inclusivity score (0-100)
        category_scores: Scores for each bias category
        flagged_items: All flagged items found
        suggested_alternatives: Flagged items with alternatives (same as flagged_items)
        compliance_notes: Additional compliance notes
        original_text: The original text, preserved unchanged per Requirement 10.4
        created_at: When the review was created
    """
    overall_score: int
    category_scores: List[CategoryScore]
    flagged_items: List[FlaggedItem]
    suggested_alternatives: List[FlaggedItem]
    compliance_notes: List[str]
    original_text: str
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type for memory storage."""
        return ArtifactType.DI_REVIEW
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "overall_score": self.overall_score,
            "category_scores": [
                {
                    "category": cs.category.value,
                    "score": cs.score,
                    "issues_found": cs.issues_found,
                }
                for cs in self.category_scores
            ],
            "flagged_items": [
                {
                    "text": fi.text,
                    "category": fi.category.value,
                    "severity": fi.severity.value,
                    "explanation": fi.explanation,
                    "alternatives": fi.alternatives,
                    "position": fi.position,
                }
                for fi in self.flagged_items
            ],
            "suggested_alternatives": [
                {
                    "text": fi.text,
                    "category": fi.category.value,
                    "severity": fi.severity.value,
                    "explanation": fi.explanation,
                    "alternatives": fi.alternatives,
                    "position": fi.position,
                }
                for fi in self.suggested_alternatives
            ],
            "compliance_notes": self.compliance_notes,
            "original_text": self.original_text,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data, indent=2)


# Bias word pools per Requirement 10.6
# Comprehensive word pools for gender, age, disability, etc. in all supported languages

# Gender-biased words (agentic vs communal)
GENDER_BIAS_WORDS: Dict[SupportedLanguage, Dict[str, Tuple[str, List[str]]]] = {
    SupportedLanguage.ENGLISH: {
        # Agentic (masculine-coded) words
        "aggressive": ("Masculine-coded term that may discourage female applicants", ["driven", "ambitious", "proactive"]),
        "dominant": ("Masculine-coded term", ["confident", "influential", "leading"]),
        "competitive": ("Masculine-coded term", ["motivated", "goal-oriented", "results-driven"]),
        "assertive": ("Masculine-coded term", ["confident", "self-assured", "decisive"]),
        "ambitious": ("Can be masculine-coded in some contexts", ["motivated", "goal-oriented", "driven"]),
        "fearless": ("Masculine-coded term", ["confident", "bold", "courageous"]),
        "ninja": ("Gendered tech jargon", ["expert", "specialist", "skilled professional"]),
        "rockstar": ("Gendered tech jargon", ["high performer", "top talent", "skilled professional"]),
        "guru": ("Gendered tech jargon", ["expert", "specialist", "authority"]),
        "hacker": ("Gendered tech jargon", ["developer", "engineer", "programmer"]),
        "manpower": ("Gendered term", ["workforce", "staff", "team members"]),
        "chairman": ("Gendered title", ["chairperson", "chair", "head"]),
        "salesman": ("Gendered title", ["salesperson", "sales representative", "sales professional"]),
        "businessman": ("Gendered title", ["businessperson", "professional", "executive"]),
        "mankind": ("Gendered term", ["humanity", "humankind", "people"]),
        "man-hours": ("Gendered term", ["work hours", "person-hours", "labor hours"]),
        # Communal (feminine-coded) words - can also create bias
        "nurturing": ("Feminine-coded term", ["supportive", "mentoring", "developing"]),
        "collaborative": ("Generally inclusive but can be feminine-coded", ["team-oriented", "cooperative"]),
    },
    SupportedLanguage.SWEDISH: {
        "aggressiv": ("Maskulint kodat ord", ["driven", "ambitiös", "proaktiv"]),
        "dominant": ("Maskulint kodat ord", ["självsäker", "inflytelserik", "ledande"]),
        "konkurrensinriktad": ("Maskulint kodat ord", ["motiverad", "målinriktad", "resultatdriven"]),
        "ninja": ("Könsstereotyp teknikjargong", ["expert", "specialist", "skicklig medarbetare"]),
        "rockstjärna": ("Könsstereotyp teknikjargong", ["topptalang", "skicklig medarbetare"]),
    },
    SupportedLanguage.DANISH: {
        "aggressiv": ("Maskulint kodet ord", ["drevet", "ambitiøs", "proaktiv"]),
        "dominant": ("Maskulint kodet ord", ["selvsikker", "indflydelsesrig", "ledende"]),
        "konkurrencepræget": ("Maskulint kodet ord", ["motiveret", "målorienteret", "resultatdrevet"]),
        "ninja": ("Kønsstereotyp teknisk jargon", ["ekspert", "specialist", "dygtig medarbejder"]),
        "rockstjerne": ("Kønsstereotyp teknisk jargon", ["toptalent", "dygtig medarbejder"]),
    },
    SupportedLanguage.NORWEGIAN: {
        "aggressiv": ("Maskulint kodet ord", ["drevet", "ambisiøs", "proaktiv"]),
        "dominant": ("Maskulint kodet ord", ["selvsikker", "innflytelsesrik", "ledende"]),
        "konkurranseorientert": ("Maskulint kodet ord", ["motivert", "målorientert", "resultatdrevet"]),
        "ninja": ("Kjønnsstereotyp teknisk sjargong", ["ekspert", "spesialist", "dyktig medarbeider"]),
        "rockestjerne": ("Kjønnsstereotyp teknisk sjargong", ["topptalent", "dyktig medarbeider"]),
    },
    SupportedLanguage.GERMAN: {
        "aggressiv": ("Maskulin kodiertes Wort", ["engagiert", "ambitioniert", "proaktiv"]),
        "dominant": ("Maskulin kodiertes Wort", ["selbstbewusst", "einflussreich", "führend"]),
        "wettbewerbsorientiert": ("Maskulin kodiertes Wort", ["motiviert", "zielorientiert", "ergebnisorientiert"]),
        "ninja": ("Geschlechtsstereotype Tech-Jargon", ["Experte", "Spezialist", "Fachkraft"]),
        "rockstar": ("Geschlechtsstereotype Tech-Jargon", ["Top-Talent", "Fachkraft"]),
    },
}


# Age-biased words
AGE_BIAS_WORDS: Dict[SupportedLanguage, Dict[str, Tuple[str, List[str]]]] = {
    SupportedLanguage.ENGLISH: {
        "young": ("Age-discriminatory term", ["energetic", "dynamic"]),
        "young and dynamic": ("Age-discriminatory phrase", ["energetic", "motivated"]),
        "young team": ("Age-discriminatory phrase", ["collaborative team", "dynamic team"]),
        "digital native": ("Age-coded term excluding older workers", ["digitally proficient", "tech-savvy"]),
        "recent graduate": ("Age-coded term", ["entry-level candidate", "early career professional"]),
        "fresh graduate": ("Age-coded term", ["entry-level candidate", "early career professional"]),
        "junior": ("Can be age-coded", ["entry-level", "early career"]),
        "mature": ("Age-coded term", ["experienced", "seasoned"]),
        "seasoned": ("Can be age-coded", ["experienced", "skilled"]),
        "energetic": ("Can be age-coded when combined with other terms", ["motivated", "enthusiastic"]),
        "youthful": ("Age-discriminatory term", ["dynamic", "vibrant"]),
        "years of experience": ("Can be age-discriminatory if excessive", ["relevant experience", "demonstrated expertise"]),
    },
    SupportedLanguage.SWEDISH: {
        "ung": ("Åldersdiskriminerande term", ["energisk", "dynamisk"]),
        "ung och dynamisk": ("Åldersdiskriminerande fras", ["energisk", "motiverad"]),
        "ungt team": ("Åldersdiskriminerande fras", ["samarbetsinriktat team", "dynamiskt team"]),
        "digital inföding": ("Ålderskodat uttryck", ["digitalt kunnig", "tekniskt skicklig"]),
        "nyexaminerad": ("Ålderskodat uttryck", ["nybörjare", "tidig karriär"]),
    },
    SupportedLanguage.DANISH: {
        "ung": ("Aldersdiskriminerende term", ["energisk", "dynamisk"]),
        "ung og dynamisk": ("Aldersdiskriminerende udtryk", ["energisk", "motiveret"]),
        "ungt team": ("Aldersdiskriminerende udtryk", ["samarbejdsorienteret team", "dynamisk team"]),
        "digital indfødt": ("Alderskodet udtryk", ["digitalt kompetent", "teknisk dygtig"]),
        "nyuddannet": ("Alderskodet udtryk", ["entry-level", "tidlig karriere"]),
    },
    SupportedLanguage.NORWEGIAN: {
        "ung": ("Aldersdiskriminerende term", ["energisk", "dynamisk"]),
        "ung og dynamisk": ("Aldersdiskriminerende uttrykk", ["energisk", "motivert"]),
        "ungt team": ("Aldersdiskriminerende uttrykk", ["samarbeidsorientert team", "dynamisk team"]),
        "digital innfødt": ("Alderskodet uttrykk", ["digitalt kompetent", "teknisk dyktig"]),
        "nyutdannet": ("Alderskodet uttrykk", ["entry-level", "tidlig karriere"]),
    },
    SupportedLanguage.GERMAN: {
        "jung": ("Altersdiskriminierender Begriff", ["energisch", "dynamisch"]),
        "jung und dynamisch": ("Altersdiskriminierende Phrase", ["engagiert", "motiviert"]),
        "junges team": ("Altersdiskriminierende Phrase", ["kooperatives Team", "dynamisches Team"]),
        "digital native": ("Alterskodierter Begriff", ["digital versiert", "technisch versiert"]),
        "berufseinsteiger": ("Alterskodierter Begriff", ["Einsteiger", "Berufsanfänger"]),
    },
}

# Disability-biased words
DISABILITY_BIAS_WORDS: Dict[SupportedLanguage, Dict[str, Tuple[str, List[str]]]] = {
    SupportedLanguage.ENGLISH: {
        "able-bodied": ("Ableist term", ["physically capable", "meets physical requirements"]),
        "physically fit": ("Can exclude people with disabilities", ["able to perform job duties"]),
        "stand for long periods": ("May exclude wheelchair users", ["work in various positions"]),
        "walk around": ("May exclude wheelchair users", ["move around the workspace"]),
        "normal": ("Ableist term implying disability is abnormal", ["typical", "standard"]),
        "handicapped": ("Outdated ableist term", ["person with disability", "disabled person"]),
        "suffering from": ("Negative framing of disability", ["living with", "has"]),
        "confined to wheelchair": ("Negative framing", ["wheelchair user", "uses a wheelchair"]),
        "clean driving license": ("May exclude people with certain disabilities", ["valid driving license if required for role"]),
    },
    SupportedLanguage.SWEDISH: {
        "fysiskt frisk": ("Kan utesluta personer med funktionsnedsättning", ["kan utföra arbetsuppgifterna"]),
        "stå långa perioder": ("Kan utesluta rullstolsanvändare", ["arbeta i olika positioner"]),
        "normal": ("Ableistisk term", ["typisk", "standard"]),
        "handikappad": ("Föråldrad ableistisk term", ["person med funktionsnedsättning"]),
    },
    SupportedLanguage.DANISH: {
        "fysisk fit": ("Kan udelukke personer med handicap", ["kan udføre arbejdsopgaverne"]),
        "stå i lange perioder": ("Kan udelukke kørestolsbrugere", ["arbejde i forskellige positioner"]),
        "normal": ("Ableistisk term", ["typisk", "standard"]),
        "handicappet": ("Forældet ableistisk term", ["person med handicap"]),
    },
    SupportedLanguage.NORWEGIAN: {
        "fysisk frisk": ("Kan ekskludere personer med funksjonshemming", ["kan utføre arbeidsoppgavene"]),
        "stå i lange perioder": ("Kan ekskludere rullestolbrukere", ["arbeide i ulike posisjoner"]),
        "normal": ("Ableistisk term", ["typisk", "standard"]),
        "handikappet": ("Utdatert ableistisk term", ["person med funksjonshemming"]),
    },
    SupportedLanguage.GERMAN: {
        "körperlich fit": ("Kann Menschen mit Behinderung ausschließen", ["kann die Arbeitsaufgaben erfüllen"]),
        "lange stehen": ("Kann Rollstuhlfahrer ausschließen", ["in verschiedenen Positionen arbeiten"]),
        "normal": ("Ableistischer Begriff", ["typisch", "standard"]),
        "behindert": ("Kann negativ konnotiert sein", ["Person mit Behinderung", "Mensch mit Behinderung"]),
    },
}


# Nationality/ethnicity-biased words
NATIONALITY_BIAS_WORDS: Dict[SupportedLanguage, Dict[str, Tuple[str, List[str]]]] = {
    SupportedLanguage.ENGLISH: {
        "native speaker": ("Excludes non-native speakers who may be fluent", ["fluent in", "proficient in"]),
        "mother tongue": ("Excludes non-native speakers", ["fluent in", "native-level proficiency"]),
        "native english": ("Excludes non-native speakers", ["fluent English", "excellent English skills"]),
        "cultural fit": ("Can mask discrimination based on background", ["team alignment", "values alignment"]),
        "local candidates only": ("Geographic discrimination", ["candidates in [location]", "able to work in [location]"]),
        "must be citizen": ("May exclude qualified immigrants", ["authorized to work in [country]"]),
    },
    SupportedLanguage.SWEDISH: {
        "modersmål": ("Utesluter icke-modersmålstalare", ["flytande i", "utmärkta kunskaper i"]),
        "kulturell passform": ("Kan dölja diskriminering", ["teamanpassning", "värderingsanpassning"]),
        "endast lokala kandidater": ("Geografisk diskriminering", ["kandidater i [plats]"]),
    },
    SupportedLanguage.DANISH: {
        "modersmål": ("Udelukker ikke-modersmålstalere", ["flydende i", "fremragende færdigheder i"]),
        "kulturel pasform": ("Kan skjule diskrimination", ["teamtilpasning", "værditilpasning"]),
        "kun lokale kandidater": ("Geografisk diskrimination", ["kandidater i [sted]"]),
    },
    SupportedLanguage.NORWEGIAN: {
        "morsmål": ("Ekskluderer ikke-morsmålstalere", ["flytende i", "utmerkede ferdigheter i"]),
        "kulturell passform": ("Kan skjule diskriminering", ["teamtilpasning", "verditilpasning"]),
        "kun lokale kandidater": ("Geografisk diskriminering", ["kandidater i [sted]"]),
    },
    SupportedLanguage.GERMAN: {
        "muttersprache": ("Schließt Nicht-Muttersprachler aus", ["fließend in", "ausgezeichnete Kenntnisse in"]),
        "muttersprachler": ("Schließt Nicht-Muttersprachler aus", ["fließend", "verhandlungssicher"]),
        "kulturelle passung": ("Kann Diskriminierung verbergen", ["Teamausrichtung", "Werteausrichtung"]),
        "nur lokale bewerber": ("Geografische Diskriminierung", ["Bewerber in [Ort]"]),
    },
}

# Family status-biased words
FAMILY_BIAS_WORDS: Dict[SupportedLanguage, Dict[str, Tuple[str, List[str]]]] = {
    SupportedLanguage.ENGLISH: {
        "family-oriented": ("May imply preference for certain family status", ["work-life balance focused"]),
        "no family commitments": ("Discriminates against parents/caregivers", ["flexible availability"]),
        "single": ("Marital status discrimination", ["available for travel"]),
        "married": ("Marital status discrimination", []),
        "childless": ("Family status discrimination", []),
        "willing to relocate family": ("Family status discrimination", ["open to relocation"]),
    },
    SupportedLanguage.SWEDISH: {
        "familjeorienterad": ("Kan antyda preferens för viss familjestatus", ["fokus på balans mellan arbete och privatliv"]),
        "inga familjeåtaganden": ("Diskriminerar föräldrar/vårdgivare", ["flexibel tillgänglighet"]),
    },
    SupportedLanguage.DANISH: {
        "familieorienteret": ("Kan antyde præference for bestemt familiestatus", ["fokus på work-life balance"]),
        "ingen familieforpligtelser": ("Diskriminerer forældre/omsorgspersoner", ["fleksibel tilgængelighed"]),
    },
    SupportedLanguage.NORWEGIAN: {
        "familieorientert": ("Kan antyde preferanse for bestemt familiestatus", ["fokus på balanse mellom arbeid og privatliv"]),
        "ingen familieforpliktelser": ("Diskriminerer foreldre/omsorgspersoner", ["fleksibel tilgjengelighet"]),
    },
    SupportedLanguage.GERMAN: {
        "familienorientiert": ("Kann Präferenz für bestimmten Familienstatus implizieren", ["Work-Life-Balance orientiert"]),
        "keine familiären verpflichtungen": ("Diskriminiert Eltern/Pflegende", ["flexible Verfügbarkeit"]),
    },
}

# Socioeconomic-biased words
SOCIOECONOMIC_BIAS_WORDS: Dict[SupportedLanguage, Dict[str, Tuple[str, List[str]]]] = {
    SupportedLanguage.ENGLISH: {
        "must have car": ("Excludes those without vehicle access", ["reliable transportation", "able to commute"]),
        "own transport required": ("Excludes those without vehicle access", ["able to commute to office"]),
        "own vehicle": ("Excludes those without vehicle access", ["reliable transportation"]),
        "prestigious university": ("Educational elitism", ["relevant degree", "qualified education"]),
        "top-tier university": ("Educational elitism", ["accredited university", "relevant degree"]),
        "ivy league": ("Educational elitism", ["accredited university"]),
        "unpaid internship": ("Excludes those who cannot work without pay", ["paid internship", "compensated position"]),
    },
    SupportedLanguage.SWEDISH: {
        "måste ha bil": ("Utesluter de utan tillgång till fordon", ["pålitlig transport", "kan pendla"]),
        "eget fordon krävs": ("Utesluter de utan tillgång till fordon", ["kan pendla till kontoret"]),
        "prestigefyllt universitet": ("Utbildningselitism", ["relevant examen"]),
    },
    SupportedLanguage.DANISH: {
        "skal have bil": ("Udelukker dem uden adgang til køretøj", ["pålidelig transport", "kan pendle"]),
        "eget køretøj påkrævet": ("Udelukker dem uden adgang til køretøj", ["kan pendle til kontoret"]),
        "prestigefyldt universitet": ("Uddannelseselitisme", ["relevant eksamen"]),
    },
    SupportedLanguage.NORWEGIAN: {
        "må ha bil": ("Ekskluderer de uten tilgang til kjøretøy", ["pålitelig transport", "kan pendle"]),
        "eget kjøretøy påkrevd": ("Ekskluderer de uten tilgang til kjøretøy", ["kan pendle til kontoret"]),
        "prestisjefylt universitet": ("Utdanningselitisme", ["relevant grad"]),
    },
    SupportedLanguage.GERMAN: {
        "führerschein erforderlich": ("Kann Menschen ohne Führerschein ausschließen", ["zuverlässige Transportmöglichkeit"]),
        "eigenes fahrzeug erforderlich": ("Schließt Menschen ohne Fahrzeug aus", ["kann zum Büro pendeln"]),
        "renommierte universität": ("Bildungselitismus", ["relevanter Abschluss"]),
    },
}


# German job title gender issues (specific to German language)
GERMAN_TITLE_BIAS: Dict[str, Tuple[str, List[str]]] = {
    "geschäftsführer": ("Male-only job title", ["Geschäftsführer (m/w/d)", "Geschäftsführung"]),
    "entwickler": ("Male-only job title", ["Entwickler (m/w/d)", "Entwickler:in"]),
    "manager": ("Should include gender notation", ["Manager (m/w/d)", "Manager:in"]),
    "ingenieur": ("Male-only job title", ["Ingenieur (m/w/d)", "Ingenieur:in"]),
    "berater": ("Male-only job title", ["Berater (m/w/d)", "Berater:in"]),
    "projektleiter": ("Male-only job title", ["Projektleiter (m/w/d)", "Projektleitung"]),
    "teamleiter": ("Male-only job title", ["Teamleiter (m/w/d)", "Teamleitung"]),
    "sachbearbeiter": ("Male-only job title", ["Sachbearbeiter (m/w/d)", "Sachbearbeitung"]),
    "verkäufer": ("Male-only job title", ["Verkäufer (m/w/d)", "Verkäufer:in"]),
    "kaufmann": ("Male-only job title", ["Kaufmann/-frau", "Kaufleute"]),
}

# Location-related bias words
LOCATION_BIAS_WORDS: Dict[SupportedLanguage, Dict[str, Tuple[str, List[str]]]] = {
    SupportedLanguage.ENGLISH: {
        "must live in": ("Geographic restriction", ["able to work from", "based in or willing to relocate to"]),
        "local candidates preferred": ("Geographic discrimination", ["candidates able to work in [location]"]),
        "no remote": ("May exclude candidates with disabilities or caregiving responsibilities", ["primarily office-based with flexibility"]),
    },
    SupportedLanguage.SWEDISH: {
        "måste bo i": ("Geografisk begränsning", ["kan arbeta från", "baserad i eller villig att flytta till"]),
        "lokala kandidater föredras": ("Geografisk diskriminering", ["kandidater som kan arbeta i [plats]"]),
    },
    SupportedLanguage.DANISH: {
        "skal bo i": ("Geografisk begrænsning", ["kan arbejde fra", "baseret i eller villig til at flytte til"]),
        "lokale kandidater foretrækkes": ("Geografisk diskrimination", ["kandidater der kan arbejde i [sted]"]),
    },
    SupportedLanguage.NORWEGIAN: {
        "må bo i": ("Geografisk begrensning", ["kan jobbe fra", "basert i eller villig til å flytte til"]),
        "lokale kandidater foretrekkes": ("Geografisk diskriminering", ["kandidater som kan jobbe i [sted]"]),
    },
    SupportedLanguage.GERMAN: {
        "muss wohnen in": ("Geografische Einschränkung", ["kann arbeiten von", "ansässig in oder umzugsbereit nach"]),
        "lokale bewerber bevorzugt": ("Geografische Diskriminierung", ["Bewerber die in [Ort] arbeiten können"]),
    },
}

# Requirements that may be unnecessarily exclusionary
REQUIREMENTS_BIAS_WORDS: Dict[SupportedLanguage, Dict[str, Tuple[str, List[str]]]] = {
    SupportedLanguage.ENGLISH: {
        "10+ years experience": ("May be unnecessarily exclusionary", ["extensive experience", "significant experience"]),
        "15+ years experience": ("May be unnecessarily exclusionary", ["extensive experience", "senior-level experience"]),
        "must have degree": ("May exclude qualified candidates without formal education", ["relevant education or equivalent experience"]),
        "degree required": ("May exclude qualified candidates", ["degree or equivalent experience"]),
        "perfect english": ("Unrealistic standard", ["excellent English", "strong English skills"]),
        "flawless": ("Unrealistic standard", ["excellent", "strong"]),
        "expert level": ("May be unnecessarily exclusionary", ["advanced", "proficient"]),
    },
    SupportedLanguage.SWEDISH: {
        "10+ års erfarenhet": ("Kan vara onödigt uteslutande", ["omfattande erfarenhet", "betydande erfarenhet"]),
        "måste ha examen": ("Kan utesluta kvalificerade kandidater", ["relevant utbildning eller motsvarande erfarenhet"]),
        "perfekt svenska": ("Orealistisk standard", ["utmärkt svenska", "starka svenskakunskaper"]),
    },
    SupportedLanguage.DANISH: {
        "10+ års erfaring": ("Kan være unødvendigt ekskluderende", ["omfattende erfaring", "betydelig erfaring"]),
        "skal have eksamen": ("Kan udelukke kvalificerede kandidater", ["relevant uddannelse eller tilsvarende erfaring"]),
        "perfekt dansk": ("Urealistisk standard", ["fremragende dansk", "stærke danskkundskaber"]),
    },
    SupportedLanguage.NORWEGIAN: {
        "10+ års erfaring": ("Kan være unødvendig ekskluderende", ["omfattende erfaring", "betydelig erfaring"]),
        "må ha grad": ("Kan ekskludere kvalifiserte kandidater", ["relevant utdanning eller tilsvarende erfaring"]),
        "perfekt norsk": ("Urealistisk standard", ["utmerket norsk", "sterke norskkunnskaper"]),
    },
    SupportedLanguage.GERMAN: {
        "10+ jahre erfahrung": ("Kann unnötig ausschließend sein", ["umfangreiche Erfahrung", "erhebliche Erfahrung"]),
        "abschluss erforderlich": ("Kann qualifizierte Kandidaten ausschließen", ["relevante Ausbildung oder gleichwertige Erfahrung"]),
        "perfektes deutsch": ("Unrealistischer Standard", ["ausgezeichnetes Deutsch", "sehr gute Deutschkenntnisse"]),
    },
}


# Category to word pool mapping
CATEGORY_WORD_POOLS: Dict[BiasCategory, Dict] = {
    BiasCategory.GENDER: GENDER_BIAS_WORDS,
    BiasCategory.AGE: AGE_BIAS_WORDS,
    BiasCategory.DISABILITY: DISABILITY_BIAS_WORDS,
    BiasCategory.NATIONALITY: NATIONALITY_BIAS_WORDS,
    BiasCategory.FAMILY: FAMILY_BIAS_WORDS,
    BiasCategory.SOCIOECONOMIC: SOCIOECONOMIC_BIAS_WORDS,
    BiasCategory.LOCATION: LOCATION_BIAS_WORDS,
    BiasCategory.REQUIREMENTS: REQUIREMENTS_BIAS_WORDS,
}

# Severity mapping based on category
CATEGORY_SEVERITY: Dict[BiasCategory, Severity] = {
    BiasCategory.GENDER: Severity.HIGH,
    BiasCategory.AGE: Severity.HIGH,
    BiasCategory.DISABILITY: Severity.HIGH,
    BiasCategory.NATIONALITY: Severity.MEDIUM,
    BiasCategory.FAMILY: Severity.MEDIUM,
    BiasCategory.SOCIOECONOMIC: Severity.MEDIUM,
    BiasCategory.READABILITY: Severity.LOW,
    BiasCategory.REQUIREMENTS: Severity.LOW,
    BiasCategory.GERMAN_TITLE: Severity.MEDIUM,
    BiasCategory.LOCATION: Severity.LOW,
}


def scan_for_bias(
    text: str,
    language: SupportedLanguage,
    category: BiasCategory,
    word_pool: Dict[SupportedLanguage, Dict[str, Tuple[str, List[str]]]]
) -> List[FlaggedItem]:
    """Scan text for bias words in a specific category.
    
    Args:
        text: The text to scan
        language: The language of the text
        category: The bias category being checked
        word_pool: The word pool for this category
        
    Returns:
        List of FlaggedItem for each bias word found
    """
    flagged: List[FlaggedItem] = []
    
    if language not in word_pool:
        return flagged
    
    words = word_pool[language]
    text_lower = text.lower()
    severity = CATEGORY_SEVERITY.get(category, Severity.MEDIUM)
    
    for word, (explanation, alternatives) in words.items():
        word_lower = word.lower()
        # Find all occurrences
        start = 0
        while True:
            pos = text_lower.find(word_lower, start)
            if pos == -1:
                break
            
            # Check word boundaries to avoid partial matches
            before_ok = pos == 0 or not text_lower[pos - 1].isalnum()
            after_pos = pos + len(word_lower)
            after_ok = after_pos >= len(text_lower) or not text_lower[after_pos].isalnum()
            
            if before_ok and after_ok:
                flagged.append(FlaggedItem(
                    text=word,
                    category=category,
                    severity=severity,
                    explanation=explanation,
                    alternatives=alternatives,
                    position=pos,
                ))
            
            start = pos + 1
    
    return flagged


def scan_german_titles(text: str) -> List[FlaggedItem]:
    """Scan German text for job titles without gender notation.
    
    Args:
        text: The German text to scan
        
    Returns:
        List of FlaggedItem for each problematic title found
    """
    flagged: List[FlaggedItem] = []
    text_lower = text.lower()
    
    for title, (explanation, alternatives) in GERMAN_TITLE_BIAS.items():
        title_lower = title.lower()
        start = 0
        while True:
            pos = text_lower.find(title_lower, start)
            if pos == -1:
                break
            
            # Check if already has gender notation (m/w/d) or :in
            context_end = min(pos + len(title) + 15, len(text))
            context = text_lower[pos:context_end]
            
            has_gender_notation = (
                "(m/w/d)" in context or
                "(m/w)" in context or
                "(w/m/d)" in context or
                ":in" in context or
                "*in" in context or
                "_in" in context
            )
            
            if not has_gender_notation:
                # Check word boundaries
                before_ok = pos == 0 or not text_lower[pos - 1].isalnum()
                after_pos = pos + len(title)
                after_ok = after_pos >= len(text_lower) or not text_lower[after_pos].isalnum()
                
                if before_ok and after_ok:
                    flagged.append(FlaggedItem(
                        text=title,
                        category=BiasCategory.GERMAN_TITLE,
                        severity=Severity.MEDIUM,
                        explanation=explanation,
                        alternatives=alternatives,
                        position=pos,
                    ))
            
            start = pos + 1
    
    return flagged


def calculate_readability_score(text: str) -> Tuple[int, List[str]]:
    """Calculate readability score and generate notes.
    
    Args:
        text: The text to analyze
        
    Returns:
        Tuple of (score 0-100, list of compliance notes)
    """
    notes: List[str] = []
    score = 100
    
    if not text:
        return score, notes
    
    # Check sentence length
    sentences = re.split(r'[.!?]+', text)
    long_sentences = [s for s in sentences if len(s.split()) > 25]
    if long_sentences:
        penalty = min(len(long_sentences) * 5, 20)
        score -= penalty
        notes.append(f"Found {len(long_sentences)} sentences with more than 25 words. Consider breaking them up.")
    
    # Check paragraph length
    paragraphs = text.split('\n\n')
    long_paragraphs = [p for p in paragraphs if len(p.split()) > 100]
    if long_paragraphs:
        penalty = min(len(long_paragraphs) * 5, 15)
        score -= penalty
        notes.append(f"Found {len(long_paragraphs)} paragraphs with more than 100 words. Consider adding more structure.")
    
    # Check for jargon density (rough heuristic)
    jargon_indicators = ["synergy", "leverage", "paradigm", "holistic", "ecosystem", "scalable", "robust"]
    jargon_count = sum(1 for j in jargon_indicators if j in text.lower())
    if jargon_count > 2:
        score -= 10
        notes.append("High density of business jargon detected. Consider using simpler language.")
    
    return max(0, score), notes


class DIReviewProcessor:
    """Processor for D&I reviews of job ads.
    
    Implements the ModuleProcessor pattern for Module I.
    Scans job ad text for biased or exclusionary language and
    provides suggestions for more inclusive alternatives.
    
    Requirements covered:
    - 10.1: Assess job ad text for inclusivity, bias, gendered language
    - 10.2: Highlight flagged terms, tone issues, or gaps
    - 10.3: Suggest alternative wording
    - 10.4: Never change the job ad automatically
    - 10.5: Provide feedback report with flagged words, alternatives, score
    - 10.6: Check against comprehensive word pools for all bias categories
    """
    
    def validate(self, input_data: DIReviewInput) -> ValidationResult:
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
        if input_data.job_ad_text and len(input_data.job_ad_text.strip()) < 50:
            warnings.append(ValidationWarning(
                field="job_ad_text",
                message="Job ad text is very short; review may be limited"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def process(self, input_data: DIReviewInput) -> DIReview:
        """Process input and generate a D&I review.
        
        Per Requirement 10.4, the original text is preserved unchanged.
        Only suggestions are provided separately.
        
        Args:
            input_data: The D&I review input
            
        Returns:
            A complete DIReview
            
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
        
        # Scan for all bias categories per Requirement 10.6
        all_flagged: List[FlaggedItem] = []
        category_issues: Dict[BiasCategory, int] = {cat: 0 for cat in BiasCategory}
        
        # Scan each category
        for category, word_pool in CATEGORY_WORD_POOLS.items():
            flagged = scan_for_bias(text, language, category, word_pool)
            all_flagged.extend(flagged)
            category_issues[category] = len(flagged)
        
        # Scan German titles if language is German
        if language == SupportedLanguage.GERMAN:
            german_flagged = scan_german_titles(text)
            all_flagged.extend(german_flagged)
            category_issues[BiasCategory.GERMAN_TITLE] = len(german_flagged)
        
        # Calculate readability
        readability_score, readability_notes = calculate_readability_score(text)
        if readability_score < 100:
            category_issues[BiasCategory.READABILITY] = 100 - readability_score
        
        # Sort flagged items by position
        all_flagged.sort(key=lambda f: f.position)
        
        # Calculate category scores
        category_scores = self._calculate_category_scores(category_issues)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(category_scores, len(all_flagged))
        
        # Generate compliance notes
        compliance_notes = self._generate_compliance_notes(
            all_flagged, readability_notes, language
        )
        
        # Per Requirement 10.4: original_text is preserved unchanged
        return DIReview(
            overall_score=overall_score,
            category_scores=category_scores,
            flagged_items=all_flagged,
            suggested_alternatives=all_flagged,  # Same list, each has alternatives
            compliance_notes=compliance_notes,
            original_text=text,  # Preserved unchanged
        )
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input fields."""
        return ["job_ad_text"]
    
    def get_optional_inputs(self) -> List[str]:
        """Get list of optional input fields."""
        return ["language"]
    
    def _calculate_category_scores(
        self,
        category_issues: Dict[BiasCategory, int]
    ) -> List[CategoryScore]:
        """Calculate scores for each bias category.
        
        Args:
            category_issues: Count of issues per category
            
        Returns:
            List of CategoryScore objects
        """
        scores: List[CategoryScore] = []
        
        for category in BiasCategory:
            issues = category_issues.get(category, 0)
            # Score decreases with more issues
            # Each issue reduces score by 15 points, minimum 0
            score = max(0, 100 - (issues * 15))
            
            scores.append(CategoryScore(
                category=category,
                score=score,
                issues_found=issues,
            ))
        
        return scores
    
    def _calculate_overall_score(
        self,
        category_scores: List[CategoryScore],
        total_issues: int
    ) -> int:
        """Calculate overall inclusivity score.
        
        Args:
            category_scores: Scores for each category
            total_issues: Total number of flagged items
            
        Returns:
            Overall score from 0-100
        """
        if not category_scores:
            return 100
        
        # Weight high-severity categories more heavily
        weighted_sum = 0
        total_weight = 0
        
        weights = {
            BiasCategory.GENDER: 2.0,
            BiasCategory.AGE: 2.0,
            BiasCategory.DISABILITY: 2.0,
            BiasCategory.NATIONALITY: 1.5,
            BiasCategory.FAMILY: 1.5,
            BiasCategory.SOCIOECONOMIC: 1.0,
            BiasCategory.READABILITY: 0.5,
            BiasCategory.REQUIREMENTS: 0.5,
            BiasCategory.GERMAN_TITLE: 1.0,
            BiasCategory.LOCATION: 0.5,
        }
        
        for cs in category_scores:
            weight = weights.get(cs.category, 1.0)
            weighted_sum += cs.score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 100
        
        base_score = weighted_sum / total_weight
        
        # Additional penalty for high total issue count
        if total_issues > 10:
            base_score -= 10
        elif total_issues > 5:
            base_score -= 5
        
        return max(0, min(100, int(base_score)))
    
    def _generate_compliance_notes(
        self,
        flagged_items: List[FlaggedItem],
        readability_notes: List[str],
        language: SupportedLanguage
    ) -> List[str]:
        """Generate compliance notes for the review.
        
        Args:
            flagged_items: All flagged items
            readability_notes: Notes from readability analysis
            language: The language of the job ad
            
        Returns:
            List of compliance notes
        """
        notes: List[str] = []
        
        # Summary of issues by category
        category_counts: Dict[BiasCategory, int] = {}
        for item in flagged_items:
            category_counts[item.category] = category_counts.get(item.category, 0) + 1
        
        if not flagged_items:
            notes.append("No bias issues detected. The job ad appears to use inclusive language.")
        else:
            notes.append(f"Found {len(flagged_items)} potential bias issues across {len(category_counts)} categories.")
            
            # High severity issues first
            high_severity = [f for f in flagged_items if f.severity == Severity.HIGH]
            if high_severity:
                notes.append(f"High priority: {len(high_severity)} items require immediate attention.")
            
            # Category breakdown
            for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
                notes.append(f"  - {category.value}: {count} issue(s)")
        
        # Add readability notes
        notes.extend(readability_notes)
        
        # Language-specific notes
        if language == SupportedLanguage.GERMAN:
            german_issues = [f for f in flagged_items if f.category == BiasCategory.GERMAN_TITLE]
            if german_issues:
                notes.append("German job titles should include gender notation (m/w/d) or use gender-neutral forms.")
        
        return notes
