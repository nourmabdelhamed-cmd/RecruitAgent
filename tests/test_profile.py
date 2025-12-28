"""Tests for the RequirementProfile module (Module A).

Tests cover:
- RequirementProfileInput validation
- RequirementProfile creation and serialization
- Skill extraction logic
- Content traceability
- Requirements 4.1, 4.2, 4.6, 13.2
"""

import pytest
import json
from datetime import datetime

from src.tata.modules.profile.profile import (
    RequirementProfileInput,
    RequirementProfile,
    TeamInfo,
    ContentSource,
    TrackedContent,
    ValidationError,
    ValidationWarning,
    ValidationResult,
    RequirementProfileProcessor,
    InvalidInputError,
    InsufficientSkillsError,
)
from src.tata.memory.memory import ArtifactType


class TestRequirementProfileInput:
    """Tests for RequirementProfileInput dataclass."""
    
    def test_create_with_required_field_only(self):
        """Test creating input with only startup_notes."""
        input_data = RequirementProfileInput(
            startup_notes="Looking for a Python developer"
        )
        assert input_data.startup_notes == "Looking for a Python developer"
        assert input_data.old_job_ad is None
        assert input_data.hiring_manager_input is None
    
    def test_create_with_all_fields(self):
        """Test creating input with all fields."""
        input_data = RequirementProfileInput(
            startup_notes="Looking for a Python developer",
            old_job_ad="Previous job ad text",
            hiring_manager_input="HM wants strong communication skills"
        )
        assert input_data.startup_notes == "Looking for a Python developer"
        assert input_data.old_job_ad == "Previous job ad text"
        assert input_data.hiring_manager_input == "HM wants strong communication skills"


class TestTeamInfo:
    """Tests for TeamInfo dataclass."""
    
    def test_create_team_info(self):
        """Test creating TeamInfo."""
        team = TeamInfo(
            size=5,
            location="Stockholm",
            collaboration_style="Agile"
        )
        assert team.size == 5
        assert team.location == "Stockholm"
        assert team.collaboration_style == "Agile"


class TestContentSource:
    """Tests for ContentSource enum."""
    
    def test_all_sources_defined(self):
        """Test all content sources are defined."""
        assert ContentSource.STARTUP_NOTES.value == "startup_notes"
        assert ContentSource.OLD_JOB_AD.value == "old_job_ad"
        assert ContentSource.HIRING_MANAGER_INPUT.value == "hiring_manager_input"
        assert ContentSource.RECRUITER_INPUT.value == "recruiter_input"


class TestRequirementProfile:
    """Tests for RequirementProfile dataclass."""
    
    def test_create_minimal_profile(self):
        """Test creating a profile with required fields only."""
        profile = RequirementProfile(
            position_title="Software Engineer",
            must_have_skills=("Python", "SQL", "REST APIs", "Git"),
            must_have_sources=(
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.OLD_JOB_AD,
                ContentSource.HIRING_MANAGER_INPUT,
            ),
            primary_responsibilities=["Develop features", "Write tests"],
            responsibility_sources=[ContentSource.STARTUP_NOTES, ContentSource.STARTUP_NOTES],
        )
        assert profile.position_title == "Software Engineer"
        assert len(profile.must_have_skills) == 4
        assert profile.must_have_skills[0] == "Python"
        assert profile.good_to_haves == []
        assert profile.soft_skills == []
    
    def test_artifact_type_is_requirement_profile(self):
        """Test artifact_type property returns correct type."""
        profile = RequirementProfile(
            position_title="Test",
            must_have_skills=("A", "B", "C", "D"),
            must_have_sources=(
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
            ),
            primary_responsibilities=[],
            responsibility_sources=[],
        )
        assert profile.artifact_type == ArtifactType.REQUIREMENT_PROFILE
    
    def test_to_json_serialization(self):
        """Test JSON serialization."""
        profile = RequirementProfile(
            position_title="Developer",
            must_have_skills=("Python", "SQL", "APIs", "Git"),
            must_have_sources=(
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.OLD_JOB_AD,
                ContentSource.HIRING_MANAGER_INPUT,
            ),
            primary_responsibilities=["Code", "Test"],
            responsibility_sources=[ContentSource.STARTUP_NOTES, ContentSource.STARTUP_NOTES],
            good_to_haves=["Docker"],
            soft_skills=["Communication"],
        )
        json_str = profile.to_json()
        data = json.loads(json_str)
        
        assert data["position_title"] == "Developer"
        assert data["must_have_skills"] == ["Python", "SQL", "APIs", "Git"]
        assert data["good_to_haves"] == ["Docker"]
        assert data["soft_skills"] == ["Communication"]
    
    def test_get_all_tracked_content(self):
        """Test getting all tracked content."""
        profile = RequirementProfile(
            position_title="Developer",
            must_have_skills=("Python", "SQL", "APIs", "Git"),
            must_have_sources=(
                ContentSource.STARTUP_NOTES,
                ContentSource.OLD_JOB_AD,
                ContentSource.HIRING_MANAGER_INPUT,
                ContentSource.STARTUP_NOTES,
            ),
            primary_responsibilities=["Develop features"],
            responsibility_sources=[ContentSource.STARTUP_NOTES],
        )
        tracked = profile.get_all_tracked_content()
        
        # 4 skills + 1 responsibility = 5 tracked items
        assert len(tracked) == 5
        assert all(isinstance(t, TrackedContent) for t in tracked)
        
        # Check sources are preserved
        sources = [t.source for t in tracked]
        assert ContentSource.STARTUP_NOTES in sources
        assert ContentSource.OLD_JOB_AD in sources
        assert ContentSource.HIRING_MANAGER_INPUT in sources


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
    
    def test_invalid_result_with_errors(self):
        """Test creating an invalid result with errors."""
        result = ValidationResult(
            is_valid=False,
            errors=[ValidationError(field="test", message="Error message")]
        )
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "test"


class TestRequirementProfileProcessor:
    """Tests for RequirementProfileProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a processor instance."""
        return RequirementProfileProcessor()
    
    @pytest.fixture
    def valid_input(self):
        """Create valid input with enough skills."""
        return RequirementProfileInput(
            startup_notes="""
            We are looking for a Senior Software Engineer.
            
            Requirements:
            - Must have Python experience (5+ years)
            - Must have SQL and database design skills
            - Must have REST API development experience
            - Must have Git and version control knowledge
            
            Responsibilities:
            - Develop new features for our platform
            - Write unit tests and integration tests
            - Participate in code reviews
            """
        )
    
    def test_get_required_inputs(self, processor):
        """Test getting required inputs."""
        required = processor.get_required_inputs()
        assert "startup_notes" in required
    
    def test_get_optional_inputs(self, processor):
        """Test getting optional inputs."""
        optional = processor.get_optional_inputs()
        assert "old_job_ad" in optional
        assert "hiring_manager_input" in optional
    
    def test_validate_empty_startup_notes_fails(self, processor):
        """Test validation fails for empty startup notes."""
        input_data = RequirementProfileInput(startup_notes="")
        result = processor.validate(input_data)
        
        assert result.is_valid is False
        assert any(e.field == "startup_notes" for e in result.errors)
    
    def test_validate_whitespace_only_fails(self, processor):
        """Test validation fails for whitespace-only notes."""
        input_data = RequirementProfileInput(startup_notes="   \n\t  ")
        result = processor.validate(input_data)
        
        assert result.is_valid is False
    
    def test_validate_short_notes_warns(self, processor):
        """Test validation warns for very short notes."""
        input_data = RequirementProfileInput(startup_notes="Short notes")
        result = processor.validate(input_data)
        
        # Should be valid but with warnings
        assert result.is_valid is True
        assert len(result.warnings) > 0
    
    def test_validate_valid_input_passes(self, processor, valid_input):
        """Test validation passes for valid input."""
        result = processor.validate(valid_input)
        assert result.is_valid is True
    
    def test_process_creates_profile(self, processor, valid_input):
        """Test processing creates a valid profile."""
        profile = processor.process(valid_input, "Senior Software Engineer")
        
        assert profile.position_title == "Senior Software Engineer"
        assert len(profile.must_have_skills) == 4
        assert len(profile.primary_responsibilities) > 0
    
    def test_process_extracts_exactly_four_skills(self, processor, valid_input):
        """Test exactly 4 must-have skills are extracted (Req 4.1)."""
        profile = processor.process(valid_input, "Test Position")
        
        assert len(profile.must_have_skills) == 4
        assert len(profile.must_have_sources) == 4
    
    def test_process_tracks_skill_sources(self, processor, valid_input):
        """Test skill sources are tracked."""
        profile = processor.process(valid_input, "Test Position")
        
        # All skills should come from startup_notes in this case
        assert all(s == ContentSource.STARTUP_NOTES for s in profile.must_have_sources)
    
    def test_process_insufficient_skills_raises(self, processor):
        """Test processing raises when fewer than 4 skills found."""
        input_data = RequirementProfileInput(
            startup_notes="We need someone with Python skills. That's all."
        )
        
        with pytest.raises(InsufficientSkillsError):
            processor.process(input_data, "Test Position")
    
    def test_process_invalid_input_raises(self, processor):
        """Test processing raises for invalid input."""
        input_data = RequirementProfileInput(startup_notes="")
        
        with pytest.raises(InvalidInputError):
            processor.process(input_data, "Test Position")
    
    def test_process_extracts_responsibilities(self, processor, valid_input):
        """Test responsibilities are extracted (Req 4.2)."""
        profile = processor.process(valid_input, "Test Position")
        
        assert len(profile.primary_responsibilities) > 0
        # Check responsibilities are tracked
        assert len(profile.responsibility_sources) == len(profile.primary_responsibilities)
    
    def test_process_with_multiple_sources(self, processor):
        """Test processing with multiple input sources."""
        input_data = RequirementProfileInput(
            startup_notes="""
            Requirements:
            - Python programming
            - SQL databases
            """,
            old_job_ad="""
            Must have:
            - REST API experience
            - Git version control
            """,
            hiring_manager_input="Need strong communication skills"
        )
        
        profile = processor.process(input_data, "Developer")
        
        assert len(profile.must_have_skills) == 4
        # Should have sources from different inputs
        sources = set(profile.must_have_sources)
        assert len(sources) >= 1  # At least one source type
    
    def test_verify_no_invented_content_passes(self, processor, valid_input):
        """Test content verification passes for valid profile."""
        profile = processor.process(valid_input, "Test Position")
        
        result = processor.verify_no_invented_content(profile, valid_input)
        assert result is True
    
    def test_verify_no_invented_content_fails_for_invented(self, processor, valid_input):
        """Test content verification fails for invented content."""
        # Create a profile with invented content
        profile = RequirementProfile(
            position_title="Test",
            must_have_skills=(
                "Quantum Computing",  # Not in input
                "Blockchain",  # Not in input
                "Machine Learning",  # Not in input
                "Kubernetes",  # Not in input
            ),
            must_have_sources=(
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
            ),
            primary_responsibilities=[],
            responsibility_sources=[],
        )
        
        result = processor.verify_no_invented_content(profile, valid_input)
        assert result is False


class TestSkillExtraction:
    """Tests specifically for skill extraction logic."""
    
    @pytest.fixture
    def processor(self):
        return RequirementProfileProcessor()
    
    def test_extracts_from_bullet_points(self, processor):
        """Test extraction from bullet point lists."""
        input_data = RequirementProfileInput(
            startup_notes="""
            Requirements:
            - Python programming experience
            - SQL database knowledge
            - REST API development
            - Git version control
            """
        )
        profile = processor.process(input_data, "Test")
        
        assert len(profile.must_have_skills) == 4
    
    def test_extracts_from_numbered_lists(self, processor):
        """Test extraction from numbered lists."""
        input_data = RequirementProfileInput(
            startup_notes="""
            Must have skills:
            1. Python programming
            2. SQL databases
            3. REST APIs
            4. Git knowledge
            """
        )
        profile = processor.process(input_data, "Test")
        
        assert len(profile.must_have_skills) == 4
    
    def test_extracts_near_must_have_indicators(self, processor):
        """Test extraction near 'must have' keywords."""
        input_data = RequirementProfileInput(
            startup_notes="""
            The candidate must have Python experience.
            Required: SQL database skills.
            Essential: REST API knowledge.
            Must possess Git proficiency.
            """
        )
        profile = processor.process(input_data, "Test")
        
        assert len(profile.must_have_skills) == 4
    
    def test_deduplicates_skills(self, processor):
        """Test duplicate skills are removed."""
        input_data = RequirementProfileInput(
            startup_notes="""
            Requirements:
            - Python programming
            - Python experience
            - SQL databases
            - REST APIs
            - Git knowledge
            """
        )
        profile = processor.process(input_data, "Test")
        
        # Should deduplicate Python
        skills_lower = [s.lower() for s in profile.must_have_skills]
        # Check no exact duplicates
        assert len(skills_lower) == len(set(skills_lower))


class TestResponsibilityExtraction:
    """Tests specifically for responsibility extraction logic."""
    
    @pytest.fixture
    def processor(self):
        return RequirementProfileProcessor()
    
    def test_extracts_from_responsibilities_section(self, processor):
        """Test extraction from responsibilities section."""
        input_data = RequirementProfileInput(
            startup_notes="""
            Requirements:
            - Python
            - SQL
            - APIs
            - Git
            
            Responsibilities:
            - Develop new features
            - Write unit tests
            - Review code
            """
        )
        profile = processor.process(input_data, "Test")
        
        assert len(profile.primary_responsibilities) > 0
    
    def test_limits_responsibilities_to_five(self, processor):
        """Test responsibilities are limited to 5 (Req 5.2)."""
        input_data = RequirementProfileInput(
            startup_notes="""
            Requirements:
            - Python, SQL, APIs, Git
            
            Responsibilities:
            - Task 1
            - Task 2
            - Task 3
            - Task 4
            - Task 5
            - Task 6
            - Task 7
            """
        )
        profile = processor.process(input_data, "Test")
        
        assert len(profile.primary_responsibilities) <= 5
