"""Tests for the JobAd module (Module B).

Tests cover:
- JobAdInput validation
- JobAd creation and serialization
- Section generation
- Module naming filter
- Dependency checks
- Requirements 5.1, 5.2, 5.3, 13.3, 3.5
"""

import pytest
import json
from datetime import datetime

from src.tata.modules.jobad.jobad import (
    JobAd,
    JobAdInput,
    RequirementsSection,
    JobAdProcessor,
    MissingRequirementProfileError,
    InvalidJobAdInputError,
    ValidationError,
    ValidationWarning,
    ValidationResult,
    filter_module_naming,
    contains_module_naming,
)
from src.tata.modules.profile.profile import (
    RequirementProfile,
    TeamInfo,
    ContentSource,
)
from src.tata.memory.memory import ArtifactType, InMemoryMemoryManager
from src.tata.dependency.dependency import InMemoryDependencyManager
from src.tata.session.session import ModuleType


@pytest.fixture
def sample_profile():
    """Create a sample requirement profile for testing."""
    return RequirementProfile(
        position_title="Senior Software Engineer",
        must_have_skills=(
            "Python programming (5+ years)",
            "SQL and database design",
            "REST API development",
            "Git version control",
        ),
        must_have_sources=(
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.OLD_JOB_AD,
            ContentSource.HIRING_MANAGER_INPUT,
        ),
        primary_responsibilities=[
            "Develop new features for our platform",
            "Write unit tests and integration tests",
            "Participate in code reviews",
            "Collaborate with product team",
        ],
        responsibility_sources=[
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
        ],
        good_to_haves=["Docker", "Kubernetes", "AWS"],
        soft_skills=["Communication", "Problem-solving", "Teamwork"],
        motivations=["Build scalable systems", "Work with cutting-edge technology"],
        team_info=TeamInfo(
            size=8,
            location="Stockholm",
            collaboration_style="Agile and collaborative",
        ),
        bu_description="Part of the Platform Engineering team",
    )


@pytest.fixture
def sample_input(sample_profile):
    """Create a sample job ad input."""
    return JobAdInput(
        requirement_profile=sample_profile,
        startup_notes="Looking for a senior engineer to join our growing team.",
        company_context="GlobalConnect is the leading digital infrastructure provider in the Nordics.",
    )


class TestRequirementsSection:
    """Tests for RequirementsSection dataclass."""
    
    def test_create_requirements_section(self):
        """Test creating a requirements section."""
        section = RequirementsSection(
            must_haves=("Python", "SQL", "APIs", "Git"),
            soft_skills="We value collaborative team players.",
            good_to_haves="Docker experience is a plus.",
        )
        assert len(section.must_haves) == 4
        assert section.must_haves[0] == "Python"
        assert "collaborative" in section.soft_skills


class TestJobAdInput:
    """Tests for JobAdInput dataclass."""
    
    def test_create_with_profile_only(self, sample_profile):
        """Test creating input with only requirement profile."""
        input_data = JobAdInput(requirement_profile=sample_profile)
        assert input_data.requirement_profile == sample_profile
        assert input_data.startup_notes == ""
        assert input_data.old_job_ad is None
        assert input_data.company_context is None
    
    def test_create_with_all_fields(self, sample_profile):
        """Test creating input with all fields."""
        input_data = JobAdInput(
            requirement_profile=sample_profile,
            startup_notes="Notes from meeting",
            old_job_ad="Previous ad text",
            company_context="Company info",
        )
        assert input_data.startup_notes == "Notes from meeting"
        assert input_data.old_job_ad == "Previous ad text"
        assert input_data.company_context == "Company info"


class TestJobAd:
    """Tests for JobAd dataclass."""
    
    def test_artifact_type_is_job_ad(self, sample_profile):
        """Test artifact_type property returns correct type."""
        job_ad = JobAd(
            headline="Test Position",
            intro="Test intro.",
            role_description="Test description.",
            the_why="Test why.",
            responsibilities=["Task 1", "Task 2", "Task 3"],
            requirements=RequirementsSection(
                must_haves=("A", "B", "C", "D"),
                soft_skills="Soft skills.",
                good_to_haves="Nice to haves.",
            ),
            soft_skills_paragraph="Soft skills paragraph.",
            team_and_why_gc="Team info.",
            process="Process info.",
            ending="Ending.",
        )
        assert job_ad.artifact_type == ArtifactType.JOB_AD
    
    def test_to_json_serialization(self, sample_profile):
        """Test JSON serialization."""
        job_ad = JobAd(
            headline="Software Engineer",
            intro="Join our team.",
            role_description="Build great software.",
            the_why="Make an impact.",
            responsibilities=["Code", "Test", "Deploy"],
            requirements=RequirementsSection(
                must_haves=("Python", "SQL", "APIs", "Git"),
                soft_skills="Team player.",
                good_to_haves="Docker.",
            ),
            soft_skills_paragraph="We value collaboration.",
            team_and_why_gc="Great team.",
            process="Simple process.",
            ending="Apply now.",
        )
        json_str = job_ad.to_json()
        data = json.loads(json_str)
        
        assert data["headline"] == "Software Engineer"
        assert data["requirements"]["must_haves"] == ["Python", "SQL", "APIs", "Git"]
        assert len(data["responsibilities"]) == 3
    
    def test_to_text_generates_readable_output(self, sample_profile):
        """Test text generation produces readable output."""
        job_ad = JobAd(
            headline="Software Engineer",
            intro="Join our team.",
            role_description="Build great software.",
            the_why="Make an impact.",
            responsibilities=["Code", "Test", "Deploy"],
            requirements=RequirementsSection(
                must_haves=("Python", "SQL", "APIs", "Git"),
                soft_skills="Team player.",
                good_to_haves="Docker experience.",
            ),
            soft_skills_paragraph="We value collaboration.",
            team_and_why_gc="Great team.",
            process="Simple process.",
            ending="Apply now.",
        )
        text = job_ad.to_text()
        
        assert "# Software Engineer" in text
        assert "## About the Role" in text
        assert "## Key Responsibilities" in text
        assert "## Requirements" in text
        assert "• Python" in text
        assert "• Code" in text


class TestModuleNamingFilter:
    """Tests for module naming filter (Requirement 3.5)."""
    
    def test_filter_removes_module_a(self):
        """Test filtering removes 'Module A' references."""
        text = "This is from Module A output."
        result = filter_module_naming(text)
        assert "Module A" not in result
        assert "Module" not in result
    
    def test_filter_removes_module_b(self):
        """Test filtering removes 'Module B' references."""
        text = "Created by Module B processor."
        result = filter_module_naming(text)
        assert "Module B" not in result
    
    def test_filter_removes_all_module_letters(self):
        """Test filtering removes all module letter references."""
        for letter in "ABCDEFGHIJ":
            text = f"This is Module {letter} content."
            result = filter_module_naming(text)
            assert f"Module {letter}" not in result
    
    def test_filter_case_insensitive(self):
        """Test filtering is case insensitive."""
        text = "module a and MODULE B and Module C"
        result = filter_module_naming(text)
        assert "module" not in result.lower() or "module" in result.lower() and "module a" not in result.lower()
    
    def test_filter_preserves_other_content(self):
        """Test filtering preserves non-module content."""
        text = "This is a great job opportunity."
        result = filter_module_naming(text)
        assert "great job opportunity" in result
    
    def test_contains_module_naming_detects_patterns(self):
        """Test detection of module naming patterns."""
        assert contains_module_naming("Module A") is True
        assert contains_module_naming("Module B") is True
        assert contains_module_naming("module c") is True
        assert contains_module_naming("No modules here") is False
        assert contains_module_naming("This is a module for learning") is False


class TestJobAdProcessor:
    """Tests for JobAdProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a processor instance."""
        return JobAdProcessor()
    
    @pytest.fixture
    def processor_with_managers(self):
        """Create a processor with memory and dependency managers."""
        memory = InMemoryMemoryManager()
        dependency = InMemoryDependencyManager(memory)
        return JobAdProcessor(memory_manager=memory, dependency_manager=dependency)
    
    def test_get_required_inputs(self, processor):
        """Test getting required inputs."""
        required = processor.get_required_inputs()
        assert "requirement_profile" in required
    
    def test_get_optional_inputs(self, processor):
        """Test getting optional inputs."""
        optional = processor.get_optional_inputs()
        assert "startup_notes" in optional
        assert "old_job_ad" in optional
        assert "company_context" in optional
    
    def test_validate_missing_profile_fails(self, processor):
        """Test validation fails without requirement profile."""
        # Create input with None profile (simulating missing)
        input_data = JobAdInput.__new__(JobAdInput)
        input_data.requirement_profile = None
        input_data.startup_notes = ""
        input_data.old_job_ad = None
        input_data.company_context = None
        
        result = processor.validate(input_data)
        assert result.is_valid is False
        assert any("requirement_profile" in e.field for e in result.errors)
    
    def test_validate_valid_input_passes(self, processor, sample_input):
        """Test validation passes for valid input."""
        result = processor.validate(sample_input)
        assert result.is_valid is True
    
    def test_validate_warns_on_module_naming_in_notes(self, processor, sample_profile):
        """Test validation warns when module naming in startup notes."""
        input_data = JobAdInput(
            requirement_profile=sample_profile,
            startup_notes="This is from Module A output.",
        )
        result = processor.validate(input_data)
        assert result.is_valid is True
        assert any("module naming" in w.message.lower() for w in result.warnings)
    
    def test_process_creates_job_ad(self, processor, sample_input):
        """Test processing creates a valid job ad."""
        job_ad = processor.process(sample_input)
        
        assert job_ad.headline == "Senior Software Engineer"
        assert len(job_ad.responsibilities) >= 3
        assert len(job_ad.requirements.must_haves) == 4
    
    def test_process_without_profile_raises(self, processor):
        """Test processing raises without requirement profile (Req 5.1)."""
        input_data = JobAdInput.__new__(JobAdInput)
        input_data.requirement_profile = None
        input_data.startup_notes = ""
        input_data.old_job_ad = None
        input_data.company_context = None
        
        with pytest.raises(MissingRequirementProfileError):
            processor.process(input_data)
    
    def test_process_includes_four_must_haves(self, processor, sample_input):
        """Test job ad includes exactly 4 must-haves (Req 13.3)."""
        job_ad = processor.process(sample_input)
        
        assert len(job_ad.requirements.must_haves) == 4
        # Verify they match the profile
        for skill in sample_input.requirement_profile.must_have_skills:
            # Skills should be present (possibly filtered)
            assert any(
                filter_module_naming(skill) in mh or mh in filter_module_naming(skill)
                for mh in job_ad.requirements.must_haves
            )
    
    def test_process_generates_all_sections(self, processor, sample_input):
        """Test all required sections are generated (Req 5.2)."""
        job_ad = processor.process(sample_input)
        
        assert job_ad.headline  # Headline
        assert job_ad.intro  # Intro
        assert job_ad.role_description  # Role Description
        assert job_ad.the_why  # The Why
        assert len(job_ad.responsibilities) >= 3  # Responsibilities (3-5)
        assert len(job_ad.responsibilities) <= 5
        assert job_ad.requirements  # Requirements
        assert job_ad.soft_skills_paragraph  # Soft skills paragraph
        assert job_ad.team_and_why_gc  # Team & Why GC
        assert job_ad.process  # Process
        assert job_ad.ending  # Ending
    
    def test_process_filters_module_naming(self, processor, sample_profile):
        """Test module naming is filtered from output (Req 3.5)."""
        # Create input with module naming in various places
        profile_with_module = RequirementProfile(
            position_title="Module A Engineer",  # Has module naming
            must_have_skills=(
                "Python from Module B",
                "SQL",
                "APIs",
                "Git",
            ),
            must_have_sources=(
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
            ),
            primary_responsibilities=["Module C task"],
            responsibility_sources=[ContentSource.STARTUP_NOTES],
        )
        input_data = JobAdInput(
            requirement_profile=profile_with_module,
            company_context="Module D context",
        )
        
        job_ad = processor.process(input_data)
        
        # Check no module naming in output
        full_text = job_ad.to_text()
        assert not contains_module_naming(full_text)
    
    def test_process_responsibilities_between_3_and_5(self, processor, sample_input):
        """Test responsibilities count is between 3 and 5."""
        job_ad = processor.process(sample_input)
        
        assert len(job_ad.responsibilities) >= 3
        assert len(job_ad.responsibilities) <= 5
    
    def test_process_with_minimal_profile(self, processor):
        """Test processing with minimal profile data."""
        minimal_profile = RequirementProfile(
            position_title="Developer",
            must_have_skills=("Python", "SQL", "APIs", "Git"),
            must_have_sources=(
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
                ContentSource.STARTUP_NOTES,
            ),
            primary_responsibilities=[],
            responsibility_sources=[],
        )
        input_data = JobAdInput(requirement_profile=minimal_profile)
        
        job_ad = processor.process(input_data)
        
        # Should still generate all sections
        assert job_ad.headline == "Developer"
        assert len(job_ad.responsibilities) >= 3  # Should add generic ones
        assert len(job_ad.requirements.must_haves) == 4
    
    def test_check_dependencies_without_managers(self, processor):
        """Test dependency check without managers."""
        result = processor.check_dependencies("session-1")
        assert result.can_proceed is True
    
    def test_check_dependencies_with_profile_in_memory(self, processor_with_managers, sample_profile):
        """Test dependency check passes when profile exists."""
        # Store profile in memory
        processor_with_managers._memory_manager.store("session-1", sample_profile)
        
        result = processor_with_managers.check_dependencies("session-1")
        assert result.can_proceed is True
    
    def test_check_dependencies_without_profile_in_memory(self, processor_with_managers):
        """Test dependency check fails when profile missing."""
        result = processor_with_managers.check_dependencies("session-1")
        assert result.can_proceed is False
        assert ModuleType.REQUIREMENT_PROFILE in result.missing_dependencies


class TestJobAdIntegration:
    """Integration tests for job ad creation."""
    
    def test_full_workflow_with_memory(self, sample_profile):
        """Test full workflow with memory manager."""
        memory = InMemoryMemoryManager()
        dependency = InMemoryDependencyManager(memory)
        processor = JobAdProcessor(memory_manager=memory, dependency_manager=dependency)
        
        # Store profile
        memory.store("session-1", sample_profile)
        
        # Check dependencies
        dep_check = processor.check_dependencies("session-1")
        assert dep_check.can_proceed is True
        
        # Create job ad
        input_data = JobAdInput(requirement_profile=sample_profile)
        job_ad = processor.process(input_data)
        
        # Store job ad
        memory.store("session-1", job_ad)
        
        # Verify job ad is stored
        assert memory.has_artifact("session-1", ArtifactType.JOB_AD)
        retrieved = memory.retrieve("session-1", ArtifactType.JOB_AD)
        assert retrieved is not None
