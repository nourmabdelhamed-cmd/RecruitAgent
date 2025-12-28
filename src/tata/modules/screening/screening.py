"""Screening Template module for Tata recruitment assistant.

This module implements Module C (TA Screening) and Module D (HM Screening).
Creates structured interview templates based on the requirement profile.

Requirements covered:
- 6.1: Extract the 4 must-have skills and good-to-haves from the requirement profile
- 6.3: Generate 1 main question plus 2-3 follow-ups for each skill
- 6.4: Adapt question style based on skill type (Technical, Leadership, Functional, Good-to-haves)
- 6.5: Structure template with: Motivation, Skills/Requirement Profile Match, Practical, Closing
- 6.7: For HM templates, include space for notes after every question
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple, Dict
import json

from src.tata.memory.memory import ArtifactType
from src.tata.modules.profile.profile import RequirementProfile


class SkillType(Enum):
    """Categorizes skills for question generation.
    
    Different skill types require different questioning approaches
    per Requirement 6.4.
    """
    TECHNICAL = "technical"
    LEADERSHIP = "leadership"
    FUNCTIONAL = "functional"
    GOOD_TO_HAVE = "good_to_have"


@dataclass
class Question:
    """An interview question.
    
    Attributes:
        text: The question text
        notes_space: Whether to include notes space after (for HM templates)
    """
    text: str
    notes_space: bool = False


@dataclass
class SkillQuestionSet:
    """Questions for a specific skill.
    
    Contains 1 main question and 2-3 follow-ups per Requirement 6.3.
    
    Attributes:
        skill_name: The skill being assessed
        skill_type: Category of the skill for question styling
        main_question: The primary question for this skill
        follow_up_questions: 2-3 follow-up questions
        include_notes_space: Whether to include notes space (for HM templates)
    """
    skill_name: str
    skill_type: SkillType
    main_question: str
    follow_up_questions: List[str]  # 2-3 follow-ups per Req 6.3
    include_notes_space: bool = False
    
    def get_all_questions(self) -> List[Question]:
        """Get all questions as Question objects.
        
        Returns:
            List of Question objects with notes_space set appropriately
        """
        questions = [Question(text=self.main_question, notes_space=self.include_notes_space)]
        for follow_up in self.follow_up_questions:
            questions.append(Question(text=follow_up, notes_space=self.include_notes_space))
        return questions



@dataclass
class ScreeningTemplateInput:
    """Input for creating screening templates.
    
    Attributes:
        requirement_profile: The requirement profile to base questions on
        is_hm_template: True for HM template (Module D), False for TA (Module C)
        include_good_to_haves: Whether to include good-to-have skill questions
        skills_to_include: Specific skills to include (if None, uses all must-haves)
        additional_areas: Additional areas to cover beyond the profile
        include_role_intro: Whether to include a role introduction section
    """
    requirement_profile: RequirementProfile
    is_hm_template: bool = False
    include_good_to_haves: bool = False
    skills_to_include: Optional[List[str]] = None
    additional_areas: List[str] = field(default_factory=list)
    include_role_intro: bool = False


@dataclass
class ScreeningTemplate:
    """Interview template artifact.
    
    Structured per Requirement 6.5:
    - Motivation section
    - Skills/Requirement Profile Match
    - Practical Questions
    - Closing
    
    Attributes:
        position_title: The job position title
        role_intro: Optional role introduction
        motivation_questions: Questions about candidate motivation
        skill_questions: Questions for each skill (main + follow-ups)
        practical_questions: Questions about practical matters
        closing_guidance: Guidance for closing the interview
        is_hm_template: True if this is an HM template (includes notes space)
        created_at: When the template was created
    """
    position_title: str
    role_intro: Optional[str]
    motivation_questions: List[Question]
    skill_questions: List[SkillQuestionSet]
    practical_questions: List[Question]
    closing_guidance: str
    is_hm_template: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type for memory storage."""
        return ArtifactType.HM_SCREENING_TEMPLATE if self.is_hm_template else ArtifactType.TA_SCREENING_TEMPLATE
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "position_title": self.position_title,
            "role_intro": self.role_intro,
            "motivation_questions": [
                {"text": q.text, "notes_space": q.notes_space}
                for q in self.motivation_questions
            ],
            "skill_questions": [
                {
                    "skill_name": sq.skill_name,
                    "skill_type": sq.skill_type.value,
                    "main_question": sq.main_question,
                    "follow_up_questions": sq.follow_up_questions,
                    "include_notes_space": sq.include_notes_space,
                }
                for sq in self.skill_questions
            ],
            "practical_questions": [
                {"text": q.text, "notes_space": q.notes_space}
                for q in self.practical_questions
            ],
            "closing_guidance": self.closing_guidance,
            "is_hm_template": self.is_hm_template,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data, indent=2)
    
    def get_total_question_count(self) -> int:
        """Get total number of questions in the template.
        
        Returns:
            Total count of all questions
        """
        count = len(self.motivation_questions)
        for skill_set in self.skill_questions:
            count += 1 + len(skill_set.follow_up_questions)  # main + follow-ups
        count += len(self.practical_questions)
        return count



# Question templates by skill type per Requirement 6.4
QUESTION_TEMPLATES: Dict[SkillType, Dict[str, List[str]]] = {
    SkillType.TECHNICAL: {
        "main": [
            "Can you describe your experience with {skill}?",
            "Tell me about a project where you used {skill} extensively.",
            "How have you applied {skill} in your previous roles?",
        ],
        "follow_ups": [
            "What challenges did you face and how did you overcome them?",
            "How do you stay current with developments in {skill}?",
            "Can you walk me through a specific technical problem you solved using {skill}?",
            "What best practices do you follow when working with {skill}?",
            "How would you explain {skill} to someone non-technical?",
            "What tools or frameworks do you prefer when working with {skill}?",
        ],
    },
    SkillType.LEADERSHIP: {
        "main": [
            "Tell me about a time when you demonstrated {skill}.",
            "How have you applied {skill} to lead or influence others?",
            "Describe a situation where {skill} was critical to your success.",
        ],
        "follow_ups": [
            "What was the outcome and what did you learn?",
            "How did you handle any resistance or challenges?",
            "How do you adapt your approach based on different team dynamics?",
            "What feedback have you received about your {skill}?",
            "How do you continue to develop this skill?",
        ],
    },
    SkillType.FUNCTIONAL: {
        "main": [
            "How have you applied {skill} in a business context?",
            "Describe your experience with {skill} and its impact on business outcomes.",
            "Tell me about a time when {skill} helped you achieve a business goal.",
        ],
        "follow_ups": [
            "How did you measure the success of your approach?",
            "What stakeholders were involved and how did you collaborate with them?",
            "What would you do differently if you could do it again?",
            "How do you balance {skill} with other business priorities?",
            "Can you give an example of how you've improved processes using {skill}?",
        ],
    },
    SkillType.GOOD_TO_HAVE: {
        "main": [
            "Do you have any experience with {skill}?",
            "How familiar are you with {skill}?",
            "Have you had the opportunity to work with {skill}?",
        ],
        "follow_ups": [
            "How would you rate your proficiency level?",
            "Would you be interested in developing this skill further?",
            "How do you think {skill} could benefit this role?",
            "What resources would you use to learn more about {skill}?",
        ],
    },
}


# Standard motivation questions
MOTIVATION_QUESTIONS = [
    "What attracted you to this role at GlobalConnect?",
    "What are you looking for in your next position?",
    "Where do you see yourself in 2-3 years?",
    "What motivates you in your work?",
]


# Standard practical questions
PRACTICAL_QUESTIONS = [
    "What is your notice period?",
    "What are your salary expectations?",
    "Are you open to the location requirements for this role?",
    "Do you have any questions about the role or the team?",
]


# Standard closing guidance
CLOSING_GUIDANCE = """Thank the candidate for their time. Explain the next steps in the process:
- Timeline for feedback
- Next interview stages if applicable
- Who they can contact with questions

Ask if they have any final questions about the role, team, or company."""



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


class ScreeningTemplateProcessor:
    """Processor for creating screening templates from requirement profiles.
    
    Implements the ModuleProcessor pattern for Module C (TA) and Module D (HM).
    Generates structured interview templates with skill-appropriate questions.
    
    Requirements covered:
    - 6.1: Extract 4 must-have skills and good-to-haves from profile
    - 6.3: Generate 1 main question + 2-3 follow-ups per skill
    - 6.4: Adapt question style based on skill type
    - 6.5: Structure with Motivation, Skills, Practical, Closing
    - 6.7: Include notes space for HM templates
    """
    
    # Keywords to detect skill types
    TECHNICAL_KEYWORDS = [
        "python", "java", "sql", "api", "database", "cloud", "aws", "azure",
        "programming", "coding", "software", "development", "engineering",
        "git", "docker", "kubernetes", "linux", "networking", "security",
        "data", "analytics", "machine learning", "ai", "devops", "ci/cd",
    ]
    
    LEADERSHIP_KEYWORDS = [
        "leadership", "management", "team lead", "mentor", "coach",
        "strategic", "vision", "influence", "stakeholder", "executive",
        "decision-making", "delegation", "motivation", "inspire",
    ]
    
    def validate(self, input_data: ScreeningTemplateInput) -> ValidationResult:
        """Validate input data before processing.
        
        Args:
            input_data: The input to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # Check requirement profile exists
        if input_data.requirement_profile is None:
            errors.append(ValidationError(
                field="requirement_profile",
                message="Requirement profile is required"
            ))
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Check must-have skills exist
        profile = input_data.requirement_profile
        if not profile.must_have_skills or len(profile.must_have_skills) < 4:
            errors.append(ValidationError(
                field="requirement_profile.must_have_skills",
                message="Requirement profile must have exactly 4 must-have skills"
            ))
        
        # Check if specific skills requested exist in profile
        if input_data.skills_to_include:
            all_skills = list(profile.must_have_skills) + profile.good_to_haves
            all_skills_lower = [s.lower() for s in all_skills]
            for skill in input_data.skills_to_include:
                if skill.lower() not in all_skills_lower:
                    warnings.append(ValidationWarning(
                        field="skills_to_include",
                        message=f"Skill '{skill}' not found in requirement profile"
                    ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def process(self, input_data: ScreeningTemplateInput) -> ScreeningTemplate:
        """Process input and generate a screening template.
        
        Args:
            input_data: The screening template input
            
        Returns:
            A complete ScreeningTemplate
            
        Raises:
            InvalidInputError: If input validation fails
        """
        # Validate first
        validation = self.validate(input_data)
        if not validation.is_valid:
            error_msgs = "; ".join(e.message for e in validation.errors)
            raise InvalidInputError(f"Input validation failed: {error_msgs}")
        
        profile = input_data.requirement_profile
        is_hm = input_data.is_hm_template
        
        # Generate role intro if requested
        role_intro = None
        if input_data.include_role_intro:
            role_intro = self._generate_role_intro(profile)
        
        # Generate motivation questions
        motivation_questions = self._generate_motivation_questions(is_hm)
        
        # Determine which skills to include
        skills_to_assess = self._determine_skills_to_assess(input_data)
        
        # Generate skill questions
        skill_questions = self._generate_skill_questions(skills_to_assess, is_hm)
        
        # Generate practical questions
        practical_questions = self._generate_practical_questions(is_hm)
        
        return ScreeningTemplate(
            position_title=profile.position_title,
            role_intro=role_intro,
            motivation_questions=motivation_questions,
            skill_questions=skill_questions,
            practical_questions=practical_questions,
            closing_guidance=CLOSING_GUIDANCE,
            is_hm_template=is_hm,
        )
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input fields."""
        return ["requirement_profile"]
    
    def get_optional_inputs(self) -> List[str]:
        """Get list of optional input fields."""
        return [
            "is_hm_template",
            "include_good_to_haves",
            "skills_to_include",
            "additional_areas",
            "include_role_intro",
        ]

    
    def _generate_role_intro(self, profile: RequirementProfile) -> str:
        """Generate a role introduction section.
        
        Args:
            profile: The requirement profile
            
        Returns:
            Role introduction text
        """
        intro_parts = [f"Position: {profile.position_title}"]
        
        if profile.team_info:
            intro_parts.append(f"Team: {profile.team_info.size} people in {profile.team_info.location}")
        
        if profile.bu_description:
            intro_parts.append(f"Business Unit: {profile.bu_description}")
        
        if profile.primary_responsibilities:
            intro_parts.append("Key Responsibilities:")
            for resp in profile.primary_responsibilities[:3]:  # Top 3
                intro_parts.append(f"  • {resp}")
        
        return "\n".join(intro_parts)
    
    def _generate_motivation_questions(self, is_hm: bool) -> List[Question]:
        """Generate motivation section questions.
        
        Args:
            is_hm: Whether this is an HM template
            
        Returns:
            List of motivation questions
        """
        return [
            Question(text=q, notes_space=is_hm)
            for q in MOTIVATION_QUESTIONS
        ]
    
    def _determine_skills_to_assess(
        self,
        input_data: ScreeningTemplateInput
    ) -> List[Tuple[str, SkillType]]:
        """Determine which skills to include and their types.
        
        Args:
            input_data: The screening template input
            
        Returns:
            List of (skill_name, skill_type) tuples
        """
        profile = input_data.requirement_profile
        skills: List[Tuple[str, SkillType]] = []
        
        # If specific skills requested, use those
        if input_data.skills_to_include:
            for skill in input_data.skills_to_include:
                skill_type = self._classify_skill(skill)
                skills.append((skill, skill_type))
        else:
            # Use all must-have skills (Req 6.1)
            for skill in profile.must_have_skills:
                skill_type = self._classify_skill(skill)
                skills.append((skill, skill_type))
            
            # Optionally include good-to-haves
            if input_data.include_good_to_haves:
                for skill in profile.good_to_haves:
                    skills.append((skill, SkillType.GOOD_TO_HAVE))
        
        return skills
    
    def _classify_skill(self, skill: str) -> SkillType:
        """Classify a skill into a skill type.
        
        Args:
            skill: The skill name
            
        Returns:
            The appropriate SkillType
        """
        skill_lower = skill.lower()
        
        # Check for technical keywords
        for keyword in self.TECHNICAL_KEYWORDS:
            if keyword in skill_lower:
                return SkillType.TECHNICAL
        
        # Check for leadership keywords
        for keyword in self.LEADERSHIP_KEYWORDS:
            if keyword in skill_lower:
                return SkillType.LEADERSHIP
        
        # Default to functional
        return SkillType.FUNCTIONAL
    
    def _generate_skill_questions(
        self,
        skills: List[Tuple[str, SkillType]],
        is_hm: bool
    ) -> List[SkillQuestionSet]:
        """Generate questions for each skill.
        
        Generates 1 main question + 2-3 follow-ups per Requirement 6.3.
        Adapts style based on skill type per Requirement 6.4.
        
        Args:
            skills: List of (skill_name, skill_type) tuples
            is_hm: Whether this is an HM template
            
        Returns:
            List of SkillQuestionSet objects
        """
        skill_question_sets: List[SkillQuestionSet] = []
        
        for skill_name, skill_type in skills:
            templates = QUESTION_TEMPLATES[skill_type]
            
            # Select main question (rotate through templates)
            main_idx = hash(skill_name) % len(templates["main"])
            main_question = templates["main"][main_idx].format(skill=skill_name)
            
            # Select 2-3 follow-up questions
            follow_ups = self._select_follow_ups(
                skill_name,
                templates["follow_ups"],
                num_follow_ups=3 if skill_type != SkillType.GOOD_TO_HAVE else 2
            )
            
            skill_question_sets.append(SkillQuestionSet(
                skill_name=skill_name,
                skill_type=skill_type,
                main_question=main_question,
                follow_up_questions=follow_ups,
                include_notes_space=is_hm,  # Req 6.7
            ))
        
        return skill_question_sets
    
    def _select_follow_ups(
        self,
        skill_name: str,
        templates: List[str],
        num_follow_ups: int
    ) -> List[str]:
        """Select follow-up questions for a skill.
        
        Args:
            skill_name: The skill name for formatting
            templates: Available follow-up templates
            num_follow_ups: Number of follow-ups to select (2-3)
            
        Returns:
            List of formatted follow-up questions
        """
        # Use skill name hash to get consistent but varied selection
        start_idx = hash(skill_name + "follow") % len(templates)
        
        selected = []
        for i in range(num_follow_ups):
            idx = (start_idx + i) % len(templates)
            question = templates[idx].format(skill=skill_name)
            selected.append(question)
        
        return selected
    
    def _generate_practical_questions(self, is_hm: bool) -> List[Question]:
        """Generate practical section questions.
        
        Args:
            is_hm: Whether this is an HM template
            
        Returns:
            List of practical questions
        """
        return [
            Question(text=q, notes_space=is_hm)
            for q in PRACTICAL_QUESTIONS
        ]
