"""Unit tests for Dependency Manager."""

import pytest
from dataclasses import dataclass
import json

from src.tata.session import ModuleType
from src.tata.memory import ArtifactType, InMemoryMemoryManager
from src.tata.dependency import (
    MODULE_DEPENDENCIES,
    MODULE_TO_ARTIFACT,
    DependencyCheck,
    InMemoryDependencyManager,
    EmptySessionIDError,
)


@dataclass
class MockArtifact:
    """Mock artifact for testing purposes."""
    name: str
    _artifact_type: ArtifactType
    
    @property
    def artifact_type(self) -> ArtifactType:
        return self._artifact_type
    
    def to_json(self) -> str:
        return json.dumps({"name": self.name})


class TestModuleDependencies:
    """Tests for MODULE_DEPENDENCIES constant."""

    def test_requirement_profile_has_no_dependencies(self):
        """Module A (Requirement Profile) should have no dependencies."""
        assert MODULE_DEPENDENCIES[ModuleType.REQUIREMENT_PROFILE] == []

    def test_job_ad_requires_requirement_profile(self):
        """Module B (Job Ad) should require Module A."""
        assert MODULE_DEPENDENCIES[ModuleType.JOB_AD] == [ModuleType.REQUIREMENT_PROFILE]

    def test_ta_screening_requires_requirement_profile(self):
        """Module C (TA Screening) should require Module A."""
        assert MODULE_DEPENDENCIES[ModuleType.TA_SCREENING] == [ModuleType.REQUIREMENT_PROFILE]

    def test_hm_screening_requires_requirement_profile(self):
        """Module D (HM Screening) should require Module A."""
        assert MODULE_DEPENDENCIES[ModuleType.HM_SCREENING] == [ModuleType.REQUIREMENT_PROFILE]

    def test_headhunting_requires_requirement_profile(self):
        """Module E (Headhunting) should require Module A."""
        assert MODULE_DEPENDENCIES[ModuleType.HEADHUNTING] == [ModuleType.REQUIREMENT_PROFILE]

    def test_candidate_report_requires_profile_and_screening(self):
        """Module F (Candidate Report) should require Modules A and C."""
        deps = MODULE_DEPENDENCIES[ModuleType.CANDIDATE_REPORT]
        assert ModuleType.REQUIREMENT_PROFILE in deps
        assert ModuleType.TA_SCREENING in deps
        assert len(deps) == 2

    def test_funnel_report_is_standalone(self):
        """Module G (Funnel Report) should have no dependencies."""
        assert MODULE_DEPENDENCIES[ModuleType.FUNNEL_REPORT] == []

    def test_job_ad_review_is_standalone(self):
        """Module H (Job Ad Review) should have no dependencies."""
        assert MODULE_DEPENDENCIES[ModuleType.JOB_AD_REVIEW] == []

    def test_di_review_is_standalone(self):
        """Module I (D&I Review) should have no dependencies."""
        assert MODULE_DEPENDENCIES[ModuleType.DI_REVIEW] == []

    def test_calendar_invite_is_standalone(self):
        """Module J (Calendar Invite) should have no dependencies."""
        assert MODULE_DEPENDENCIES[ModuleType.CALENDAR_INVITE] == []


class TestModuleToArtifact:
    """Tests for MODULE_TO_ARTIFACT mapping."""

    def test_all_modules_have_artifact_mapping(self):
        """All modules should have an artifact type mapping."""
        for module in ModuleType:
            assert module in MODULE_TO_ARTIFACT

    def test_correct_artifact_mappings(self):
        """Module to artifact mappings should be correct."""
        assert MODULE_TO_ARTIFACT[ModuleType.REQUIREMENT_PROFILE] == ArtifactType.REQUIREMENT_PROFILE
        assert MODULE_TO_ARTIFACT[ModuleType.JOB_AD] == ArtifactType.JOB_AD
        assert MODULE_TO_ARTIFACT[ModuleType.TA_SCREENING] == ArtifactType.TA_SCREENING_TEMPLATE
        assert MODULE_TO_ARTIFACT[ModuleType.HM_SCREENING] == ArtifactType.HM_SCREENING_TEMPLATE
        assert MODULE_TO_ARTIFACT[ModuleType.HEADHUNTING] == ArtifactType.HEADHUNTING_MESSAGES
        assert MODULE_TO_ARTIFACT[ModuleType.CANDIDATE_REPORT] == ArtifactType.CANDIDATE_REPORTS
        assert MODULE_TO_ARTIFACT[ModuleType.FUNNEL_REPORT] == ArtifactType.FUNNEL_REPORT
        assert MODULE_TO_ARTIFACT[ModuleType.JOB_AD_REVIEW] == ArtifactType.JOB_AD_REVIEW
        assert MODULE_TO_ARTIFACT[ModuleType.DI_REVIEW] == ArtifactType.DI_REVIEW
        assert MODULE_TO_ARTIFACT[ModuleType.CALENDAR_INVITE] == ArtifactType.CALENDAR_INVITE


class TestDependencyCheck:
    """Tests for DependencyCheck dataclass."""

    def test_dependency_check_can_proceed(self):
        """DependencyCheck should indicate when execution can proceed."""
        check = DependencyCheck(
            can_proceed=True,
            missing_dependencies=[],
            message="All dependencies satisfied."
        )
        
        assert check.can_proceed is True
        assert check.missing_dependencies == []
        assert check.message == "All dependencies satisfied."

    def test_dependency_check_cannot_proceed(self):
        """DependencyCheck should indicate when execution cannot proceed."""
        check = DependencyCheck(
            can_proceed=False,
            missing_dependencies=[ModuleType.REQUIREMENT_PROFILE],
            message="Missing requirement profile."
        )
        
        assert check.can_proceed is False
        assert check.missing_dependencies == [ModuleType.REQUIREMENT_PROFILE]

    def test_dependency_check_defaults(self):
        """DependencyCheck should have sensible defaults."""
        check = DependencyCheck(can_proceed=True)
        
        assert check.missing_dependencies == []
        assert check.message == ""


class TestInMemoryDependencyManager:
    """Tests for InMemoryDependencyManager."""

    def test_get_required_modules_for_standalone(self):
        """get_required_modules should return empty list for standalone modules."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        assert dep_manager.get_required_modules(ModuleType.REQUIREMENT_PROFILE) == []
        assert dep_manager.get_required_modules(ModuleType.FUNNEL_REPORT) == []
        assert dep_manager.get_required_modules(ModuleType.JOB_AD_REVIEW) == []
        assert dep_manager.get_required_modules(ModuleType.DI_REVIEW) == []
        assert dep_manager.get_required_modules(ModuleType.CALENDAR_INVITE) == []

    def test_get_required_modules_for_dependent(self):
        """get_required_modules should return dependencies for dependent modules."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        assert dep_manager.get_required_modules(ModuleType.JOB_AD) == [ModuleType.REQUIREMENT_PROFILE]
        assert dep_manager.get_required_modules(ModuleType.TA_SCREENING) == [ModuleType.REQUIREMENT_PROFILE]

    def test_is_standalone_returns_true_for_standalone_modules(self):
        """is_standalone should return True for modules with no dependencies."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        assert dep_manager.is_standalone(ModuleType.REQUIREMENT_PROFILE) is True
        assert dep_manager.is_standalone(ModuleType.FUNNEL_REPORT) is True
        assert dep_manager.is_standalone(ModuleType.JOB_AD_REVIEW) is True
        assert dep_manager.is_standalone(ModuleType.DI_REVIEW) is True
        assert dep_manager.is_standalone(ModuleType.CALENDAR_INVITE) is True

    def test_is_standalone_returns_false_for_dependent_modules(self):
        """is_standalone should return False for modules with dependencies."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        assert dep_manager.is_standalone(ModuleType.JOB_AD) is False
        assert dep_manager.is_standalone(ModuleType.TA_SCREENING) is False
        assert dep_manager.is_standalone(ModuleType.HM_SCREENING) is False
        assert dep_manager.is_standalone(ModuleType.HEADHUNTING) is False
        assert dep_manager.is_standalone(ModuleType.CANDIDATE_REPORT) is False

    def test_can_execute_standalone_module_always_succeeds(self):
        """can_execute should always succeed for standalone modules."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        result = dep_manager.can_execute("session-1", ModuleType.FUNNEL_REPORT)
        
        assert result.can_proceed is True
        assert result.missing_dependencies == []

    def test_can_execute_dependent_module_without_dependencies_fails(self):
        """can_execute should fail when dependencies are missing."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        result = dep_manager.can_execute("session-1", ModuleType.JOB_AD)
        
        assert result.can_proceed is False
        assert ModuleType.REQUIREMENT_PROFILE in result.missing_dependencies

    def test_can_execute_dependent_module_with_dependencies_succeeds(self):
        """can_execute should succeed when all dependencies are satisfied."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        # Store the required artifact
        profile = MockArtifact(
            name="profile",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        memory_manager.store("session-1", profile)
        
        result = dep_manager.can_execute("session-1", ModuleType.JOB_AD)
        
        assert result.can_proceed is True
        assert result.missing_dependencies == []

    def test_can_execute_candidate_report_requires_both_dependencies(self):
        """can_execute for Candidate Report should require both Profile and Screening."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        # No dependencies - should fail with both missing
        result = dep_manager.can_execute("session-1", ModuleType.CANDIDATE_REPORT)
        assert result.can_proceed is False
        assert len(result.missing_dependencies) == 2
        
        # Only profile - should still fail
        profile = MockArtifact(
            name="profile",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        memory_manager.store("session-1", profile)
        
        result = dep_manager.can_execute("session-1", ModuleType.CANDIDATE_REPORT)
        assert result.can_proceed is False
        assert ModuleType.TA_SCREENING in result.missing_dependencies
        
        # Both dependencies - should succeed
        screening = MockArtifact(
            name="screening",
            _artifact_type=ArtifactType.TA_SCREENING_TEMPLATE
        )
        memory_manager.store("session-1", screening)
        
        result = dep_manager.can_execute("session-1", ModuleType.CANDIDATE_REPORT)
        assert result.can_proceed is True
        assert result.missing_dependencies == []

    def test_can_execute_empty_session_id_raises(self):
        """can_execute should raise EmptySessionIDError for empty session ID."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        with pytest.raises(EmptySessionIDError):
            dep_manager.can_execute("", ModuleType.JOB_AD)

    def test_can_execute_returns_helpful_message(self):
        """can_execute should return a helpful message."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        # Standalone module
        result = dep_manager.can_execute("session-1", ModuleType.FUNNEL_REPORT)
        assert "no dependencies" in result.message.lower()
        
        # Missing single dependency
        result = dep_manager.can_execute("session-1", ModuleType.JOB_AD)
        assert "requirement profile" in result.message.lower()
        
        # All dependencies satisfied
        profile = MockArtifact(
            name="profile",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        memory_manager.store("session-1", profile)
        result = dep_manager.can_execute("session-1", ModuleType.JOB_AD)
        assert "satisfied" in result.message.lower()

    def test_sessions_are_isolated(self):
        """Dependencies should be checked per session."""
        memory_manager = InMemoryMemoryManager()
        dep_manager = InMemoryDependencyManager(memory_manager)
        
        # Store profile only in session-1
        profile = MockArtifact(
            name="profile",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        memory_manager.store("session-1", profile)
        
        # Session-1 should be able to execute Job Ad
        result1 = dep_manager.can_execute("session-1", ModuleType.JOB_AD)
        assert result1.can_proceed is True
        
        # Session-2 should not be able to execute Job Ad
        result2 = dep_manager.can_execute("session-2", ModuleType.JOB_AD)
        assert result2.can_proceed is False
