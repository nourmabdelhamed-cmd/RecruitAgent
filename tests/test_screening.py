"""Tests for the Screening Template module (Module C & D).

Tests cover:
- ScreeningTemplateInput validation
- ScreeningTemplate creation and serialization
- Question generation by skill type
- HM template notes space
- Requirements 6.1, 6.3, 6.4, 6.5, 6.7
"""

import pytest
import json
from datetime import datetime

from src.tata.modules.screening.screening import (
    SkillType,
    Question,
    SkillQuestionSet,
    ScreeningTemplateInput,
    ScreeningTemplate,
    ScreeningTemplateProcessor,
    ValidationError,
    ValidationWarning,
    ValidationResult,
    InvalidInputError,
    QUESTION_TEMPLATES,
    MOTIVATION_QUESTIONS,
    PRACTICAL_QUESTIONS,
    CLOSING_GUIDANCE,
)
from src.tata.modules.profile.profile import (
    RequirementProfile,
    ContentSource,
    TeamInfo,
)
from src.tata.memory.memory import ArtifactType


@pytest.fixture
def sample_profile():
    """Create a sample requirement profile for testing."""
    return RequirementProfile(
        position_title="Senior Software Engineer",
        must_have_skills=("Python programming", "SQL databases", "REST API development", "Git version control"),
        must_have_sources=(
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.OLD_JOB_AD,
            ContentSource.HIRING_MANAGER_INPUT,
        ),
        primary_responsibilities=["Develop features", "Write tests", "Code reviews"],
        responsibility_sources=[
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
        ],
        good_to_haves=["Docker", "Kubernetes"],
        soft_skills=["Communication", "Teamwork"],
    )


@pytest.fixture
def profile_with_team_info():
    """Create a profile with team info for testing."""
    return RequirementProfile(
        position_title="Tech Lead",
        must_have_skills=("Leadership experience", "Python", "System design", "Mentoring"),
        must_have_sources=(
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
        ),
        primary_responsibilities=["Lead team", "Architecture decisions"],
        responsibility_sources=[ContentSource.STARTUP_NOTES, ContentSource.STARTUP_NOTES],
        team_info=TeamInfo(size=8, location="Stockholm", collaboration_style="Agile"),
        bu_description="Platform Engineering",
    )


class TestSkillType:
    """Tests for SkillType enum."""
    
    def test_all_skill_types_defined(self):
        """Test all skill types are defined."""
        assert SkillType.TECHNICAL.value == "technical"
        assert SkillType.LEADERSHIP.value == "leadership"
        assert SkillType.FUNCTIONAL.value == "functional"
        assert SkillType.GOOD_TO_HAVE.value == "good_to_have"


class TestQuestion:
    """Tests for Question dataclass."""
    
    def test_create_question_without_notes(self):
        """Test creating a question without notes space."""
        q = Question(text="What is your experience?")
        assert q.text == "What is your experience?"
        assert q.notes_space is False
    
    def test_create_question_with_notes(self):
        """Test creating a question with notes space (HM template)."""
        q = Question(text="Describe your leadership style.", notes_space=True)
        assert q.text == "Describe your leadership style."
        assert q.notes_space is True



class TestSkillQuestionSet:
    """Tests for SkillQuestionSet dataclass."""
    
    def test_create_skill_question_set(self):
        """Test creating a skill question set."""
        sqs = SkillQuestionSet(
            skill_name="Python",
            skill_type=SkillType.TECHNICAL,
            main_question="Tell me about your Python experience.",
            follow_up_questions=[
                "What frameworks have you used?",
                "How do you handle testing?",
            ],
        )
        assert sqs.skill_name == "Python"
        assert sqs.skill_type == SkillType.TECHNICAL
        assert len(sqs.follow_up_questions) == 2
        assert sqs.include_notes_space is False
    
    def test_get_all_questions(self):
        """Test getting all questions as Question objects."""
        sqs = SkillQuestionSet(
            skill_name="SQL",
            skill_type=SkillType.TECHNICAL,
            main_question="Main question?",
            follow_up_questions=["Follow-up 1?", "Follow-up 2?", "Follow-up 3?"],
            include_notes_space=True,
        )
        questions = sqs.get_all_questions()
        
        assert len(questions) == 4  # 1 main + 3 follow-ups
        assert all(isinstance(q, Question) for q in questions)
        assert all(q.notes_space is True for q in questions)
        assert questions[0].text == "Main question?"


class TestScreeningTemplateInput:
    """Tests for ScreeningTemplateInput dataclass."""
    
    def test_create_minimal_input(self, sample_profile):
        """Test creating input with only required field."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        
        assert input_data.requirement_profile == sample_profile
        assert input_data.is_hm_template is False
        assert input_data.include_good_to_haves is False
        assert input_data.skills_to_include is None
        assert input_data.additional_areas == []
        assert input_data.include_role_intro is False
    
    def test_create_hm_template_input(self, sample_profile):
        """Test creating input for HM template."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            is_hm_template=True,
            include_good_to_haves=True,
        )
        
        assert input_data.is_hm_template is True
        assert input_data.include_good_to_haves is True


class TestScreeningTemplate:
    """Tests for ScreeningTemplate dataclass."""
    
    def test_create_ta_template(self, sample_profile):
        """Test creating a TA screening template."""
        template = ScreeningTemplate(
            position_title="Software Engineer",
            role_intro=None,
            motivation_questions=[Question(text="Why this role?")],
            skill_questions=[
                SkillQuestionSet(
                    skill_name="Python",
                    skill_type=SkillType.TECHNICAL,
                    main_question="Python experience?",
                    follow_up_questions=["Follow-up 1?", "Follow-up 2?"],
                )
            ],
            practical_questions=[Question(text="Notice period?")],
            closing_guidance="Thank the candidate.",
            is_hm_template=False,
        )
        
        assert template.position_title == "Software Engineer"
        assert template.is_hm_template is False
        assert template.artifact_type == ArtifactType.TA_SCREENING_TEMPLATE
    
    def test_create_hm_template(self, sample_profile):
        """Test creating an HM screening template."""
        template = ScreeningTemplate(
            position_title="Software Engineer",
            role_intro="Role intro text",
            motivation_questions=[Question(text="Why this role?", notes_space=True)],
            skill_questions=[],
            practical_questions=[],
            closing_guidance="Thank the candidate.",
            is_hm_template=True,
        )
        
        assert template.is_hm_template is True
        assert template.artifact_type == ArtifactType.HM_SCREENING_TEMPLATE
    
    def test_to_json_serialization(self, sample_profile):
        """Test JSON serialization."""
        template = ScreeningTemplate(
            position_title="Developer",
            role_intro="Intro",
            motivation_questions=[Question(text="Q1", notes_space=False)],
            skill_questions=[
                SkillQuestionSet(
                    skill_name="Python",
                    skill_type=SkillType.TECHNICAL,
                    main_question="Main?",
                    follow_up_questions=["F1?", "F2?"],
                    include_notes_space=False,
                )
            ],
            practical_questions=[Question(text="P1?")],
            closing_guidance="Closing",
            is_hm_template=False,
        )
        
        json_str = template.to_json()
        data = json.loads(json_str)
        
        assert data["position_title"] == "Developer"
        assert data["role_intro"] == "Intro"
        assert len(data["motivation_questions"]) == 1
        assert len(data["skill_questions"]) == 1
        assert data["skill_questions"][0]["skill_type"] == "technical"
        assert data["is_hm_template"] is False
    
    def test_get_total_question_count(self):
        """Test counting total questions."""
        template = ScreeningTemplate(
            position_title="Test",
            role_intro=None,
            motivation_questions=[Question(text="M1"), Question(text="M2")],  # 2
            skill_questions=[
                SkillQuestionSet(
                    skill_name="S1",
                    skill_type=SkillType.TECHNICAL,
                    main_question="Main1",
                    follow_up_questions=["F1", "F2", "F3"],  # 1 + 3 = 4
                ),
                SkillQuestionSet(
                    skill_name="S2",
                    skill_type=SkillType.FUNCTIONAL,
                    main_question="Main2",
                    follow_up_questions=["F1", "F2"],  # 1 + 2 = 3
                ),
            ],
            practical_questions=[Question(text="P1"), Question(text="P2")],  # 2
            closing_guidance="Close",
        )
        
        # Total: 2 + 4 + 3 + 2 = 11
        assert template.get_total_question_count() == 11



class TestQuestionTemplates:
    """Tests for question templates."""
    
    def test_all_skill_types_have_templates(self):
        """Test all skill types have question templates."""
        for skill_type in SkillType:
            assert skill_type in QUESTION_TEMPLATES
            assert "main" in QUESTION_TEMPLATES[skill_type]
            assert "follow_ups" in QUESTION_TEMPLATES[skill_type]
    
    def test_templates_have_skill_placeholder(self):
        """Test templates contain {skill} placeholder."""
        for skill_type, templates in QUESTION_TEMPLATES.items():
            for main in templates["main"]:
                assert "{skill}" in main, f"Missing {{skill}} in {skill_type} main template"
    
    def test_follow_ups_exist(self):
        """Test each skill type has at least 2 follow-ups."""
        for skill_type, templates in QUESTION_TEMPLATES.items():
            assert len(templates["follow_ups"]) >= 2


class TestScreeningTemplateProcessor:
    """Tests for ScreeningTemplateProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a processor instance."""
        return ScreeningTemplateProcessor()
    
    def test_get_required_inputs(self, processor):
        """Test getting required inputs."""
        required = processor.get_required_inputs()
        assert "requirement_profile" in required
    
    def test_get_optional_inputs(self, processor):
        """Test getting optional inputs."""
        optional = processor.get_optional_inputs()
        assert "is_hm_template" in optional
        assert "include_good_to_haves" in optional
        assert "skills_to_include" in optional
    
    def test_validate_missing_profile_fails(self, processor):
        """Test validation fails when profile is None."""
        input_data = ScreeningTemplateInput(requirement_profile=None)
        result = processor.validate(input_data)
        
        assert result.is_valid is False
        assert any(e.field == "requirement_profile" for e in result.errors)
    
    def test_validate_valid_input_passes(self, processor, sample_profile):
        """Test validation passes for valid input."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        result = processor.validate(input_data)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_warns_for_unknown_skill(self, processor, sample_profile):
        """Test validation warns when requested skill not in profile."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            skills_to_include=["Unknown Skill"],
        )
        result = processor.validate(input_data)
        
        assert result.is_valid is True  # Still valid, just warning
        assert len(result.warnings) > 0
    
    def test_process_creates_ta_template(self, processor, sample_profile):
        """Test processing creates a valid TA template."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            is_hm_template=False,
        )
        template = processor.process(input_data)
        
        assert template.position_title == "Senior Software Engineer"
        assert template.is_hm_template is False
        assert template.artifact_type == ArtifactType.TA_SCREENING_TEMPLATE
    
    def test_process_creates_hm_template(self, processor, sample_profile):
        """Test processing creates a valid HM template."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            is_hm_template=True,
        )
        template = processor.process(input_data)
        
        assert template.is_hm_template is True
        assert template.artifact_type == ArtifactType.HM_SCREENING_TEMPLATE
    
    def test_process_invalid_input_raises(self, processor):
        """Test processing raises for invalid input."""
        input_data = ScreeningTemplateInput(requirement_profile=None)
        
        with pytest.raises(InvalidInputError):
            processor.process(input_data)


class TestQuestionGeneration:
    """Tests for question generation logic (Req 6.3, 6.4)."""
    
    @pytest.fixture
    def processor(self):
        return ScreeningTemplateProcessor()
    
    def test_generates_questions_for_all_must_haves(self, processor, sample_profile):
        """Test questions generated for all 4 must-have skills (Req 6.1)."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        template = processor.process(input_data)
        
        assert len(template.skill_questions) == 4
        skill_names = [sq.skill_name for sq in template.skill_questions]
        for skill in sample_profile.must_have_skills:
            assert skill in skill_names
    
    def test_generates_one_main_plus_follow_ups(self, processor, sample_profile):
        """Test each skill has 1 main + 2-3 follow-ups (Req 6.3)."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        template = processor.process(input_data)
        
        for skill_set in template.skill_questions:
            assert skill_set.main_question  # Has main question
            assert 2 <= len(skill_set.follow_up_questions) <= 3  # 2-3 follow-ups
    
    def test_classifies_technical_skills(self, processor, sample_profile):
        """Test technical skills are classified correctly (Req 6.4)."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        template = processor.process(input_data)
        
        # "Python programming" should be classified as technical
        python_skill = next(
            sq for sq in template.skill_questions
            if "Python" in sq.skill_name
        )
        assert python_skill.skill_type == SkillType.TECHNICAL
    
    def test_classifies_leadership_skills(self, processor, profile_with_team_info):
        """Test leadership skills are classified correctly (Req 6.4)."""
        input_data = ScreeningTemplateInput(requirement_profile=profile_with_team_info)
        template = processor.process(input_data)
        
        # "Leadership experience" should be classified as leadership
        leadership_skill = next(
            sq for sq in template.skill_questions
            if "Leadership" in sq.skill_name
        )
        assert leadership_skill.skill_type == SkillType.LEADERSHIP
    
    def test_includes_good_to_haves_when_requested(self, processor, sample_profile):
        """Test good-to-haves included when requested."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            include_good_to_haves=True,
        )
        template = processor.process(input_data)
        
        # Should have 4 must-haves + 2 good-to-haves = 6
        assert len(template.skill_questions) == 6
        
        # Good-to-haves should be classified as GOOD_TO_HAVE
        good_to_have_skills = [
            sq for sq in template.skill_questions
            if sq.skill_type == SkillType.GOOD_TO_HAVE
        ]
        assert len(good_to_have_skills) == 2
    
    def test_good_to_haves_have_fewer_follow_ups(self, processor, sample_profile):
        """Test good-to-have skills have 2 follow-ups (not 3)."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            include_good_to_haves=True,
        )
        template = processor.process(input_data)
        
        good_to_have_skills = [
            sq for sq in template.skill_questions
            if sq.skill_type == SkillType.GOOD_TO_HAVE
        ]
        for sq in good_to_have_skills:
            assert len(sq.follow_up_questions) == 2



class TestHMTemplateNotesSpace:
    """Tests for HM template notes space (Req 6.7)."""
    
    @pytest.fixture
    def processor(self):
        return ScreeningTemplateProcessor()
    
    def test_hm_template_has_notes_space_on_motivation(self, processor, sample_profile):
        """Test HM template has notes space on motivation questions."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            is_hm_template=True,
        )
        template = processor.process(input_data)
        
        for q in template.motivation_questions:
            assert q.notes_space is True
    
    def test_hm_template_has_notes_space_on_skills(self, processor, sample_profile):
        """Test HM template has notes space on skill questions."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            is_hm_template=True,
        )
        template = processor.process(input_data)
        
        for skill_set in template.skill_questions:
            assert skill_set.include_notes_space is True
            for q in skill_set.get_all_questions():
                assert q.notes_space is True
    
    def test_hm_template_has_notes_space_on_practical(self, processor, sample_profile):
        """Test HM template has notes space on practical questions."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            is_hm_template=True,
        )
        template = processor.process(input_data)
        
        for q in template.practical_questions:
            assert q.notes_space is True
    
    def test_ta_template_no_notes_space(self, processor, sample_profile):
        """Test TA template does NOT have notes space."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            is_hm_template=False,
        )
        template = processor.process(input_data)
        
        # Check motivation questions
        for q in template.motivation_questions:
            assert q.notes_space is False
        
        # Check skill questions
        for skill_set in template.skill_questions:
            assert skill_set.include_notes_space is False
        
        # Check practical questions
        for q in template.practical_questions:
            assert q.notes_space is False


class TestTemplateStructure:
    """Tests for template structure (Req 6.5)."""
    
    @pytest.fixture
    def processor(self):
        return ScreeningTemplateProcessor()
    
    def test_template_has_motivation_section(self, processor, sample_profile):
        """Test template has motivation questions."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        template = processor.process(input_data)
        
        assert len(template.motivation_questions) > 0
    
    def test_template_has_skills_section(self, processor, sample_profile):
        """Test template has skill questions."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        template = processor.process(input_data)
        
        assert len(template.skill_questions) > 0
    
    def test_template_has_practical_section(self, processor, sample_profile):
        """Test template has practical questions."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        template = processor.process(input_data)
        
        assert len(template.practical_questions) > 0
    
    def test_template_has_closing_guidance(self, processor, sample_profile):
        """Test template has closing guidance."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        template = processor.process(input_data)
        
        assert template.closing_guidance
        assert len(template.closing_guidance) > 0
    
    def test_template_includes_role_intro_when_requested(self, processor, profile_with_team_info):
        """Test role intro included when requested."""
        input_data = ScreeningTemplateInput(
            requirement_profile=profile_with_team_info,
            include_role_intro=True,
        )
        template = processor.process(input_data)
        
        assert template.role_intro is not None
        assert profile_with_team_info.position_title in template.role_intro
    
    def test_template_no_role_intro_by_default(self, processor, sample_profile):
        """Test role intro not included by default."""
        input_data = ScreeningTemplateInput(requirement_profile=sample_profile)
        template = processor.process(input_data)
        
        assert template.role_intro is None


class TestSpecificSkillsSelection:
    """Tests for selecting specific skills to include."""
    
    @pytest.fixture
    def processor(self):
        return ScreeningTemplateProcessor()
    
    def test_uses_specific_skills_when_provided(self, processor, sample_profile):
        """Test only specified skills are included."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            skills_to_include=["Python programming", "SQL databases"],
        )
        template = processor.process(input_data)
        
        assert len(template.skill_questions) == 2
        skill_names = [sq.skill_name for sq in template.skill_questions]
        assert "Python programming" in skill_names
        assert "SQL databases" in skill_names
    
    def test_uses_all_must_haves_when_no_specific_skills(self, processor, sample_profile):
        """Test all must-haves used when no specific skills provided."""
        input_data = ScreeningTemplateInput(
            requirement_profile=sample_profile,
            skills_to_include=None,
        )
        template = processor.process(input_data)
        
        assert len(template.skill_questions) == 4
