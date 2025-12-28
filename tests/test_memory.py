"""Unit tests for Memory Manager."""

import pytest
from dataclasses import dataclass
import json

from src.tata.memory import (
    ArtifactType,
    Artifact,
    InMemoryMemoryManager,
    EmptySessionIDError,
)


@dataclass
class MockArtifact:
    """Mock artifact for testing purposes."""
    name: str
    data: str
    _artifact_type: ArtifactType
    
    @property
    def artifact_type(self) -> ArtifactType:
        return self._artifact_type
    
    def to_json(self) -> str:
        return json.dumps({"name": self.name, "data": self.data})


class TestArtifactType:
    """Tests for ArtifactType enum."""

    def test_all_artifact_types_defined(self):
        """All artifact types should be defined with correct values."""
        assert ArtifactType.REQUIREMENT_PROFILE.value == "requirement_profile"
        assert ArtifactType.JOB_AD.value == "job_ad"
        assert ArtifactType.TA_SCREENING_TEMPLATE.value == "ta_screening_template"
        assert ArtifactType.HM_SCREENING_TEMPLATE.value == "hm_screening_template"
        assert ArtifactType.HEADHUNTING_MESSAGES.value == "headhunting_messages"
        assert ArtifactType.CANDIDATE_REPORTS.value == "candidate_reports"
        assert ArtifactType.FUNNEL_REPORT.value == "funnel_report"
        assert ArtifactType.JOB_AD_REVIEW.value == "job_ad_review"
        assert ArtifactType.DI_REVIEW.value == "di_review"
        assert ArtifactType.CALENDAR_INVITE.value == "calendar_invite"


class TestMockArtifact:
    """Tests for MockArtifact to ensure it implements Artifact protocol."""

    def test_mock_artifact_implements_protocol(self):
        """MockArtifact should implement Artifact protocol."""
        artifact = MockArtifact(
            name="test",
            data="test data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        
        assert isinstance(artifact, Artifact)
        assert artifact.artifact_type == ArtifactType.REQUIREMENT_PROFILE
        assert artifact.to_json() == '{"name": "test", "data": "test data"}'


class TestInMemoryMemoryManager:
    """Tests for InMemoryMemoryManager."""

    def test_store_and_retrieve_artifact(self):
        """store should save artifact and retrieve should return it."""
        manager = InMemoryMemoryManager()
        artifact = MockArtifact(
            name="profile",
            data="test profile data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        
        manager.store("session-1", artifact)
        retrieved = manager.retrieve("session-1", ArtifactType.REQUIREMENT_PROFILE)
        
        assert retrieved is not None
        assert retrieved.name == "profile"
        assert retrieved.data == "test profile data"

    def test_retrieve_returns_none_for_unknown_session(self):
        """retrieve should return None for unknown session ID."""
        manager = InMemoryMemoryManager()
        
        result = manager.retrieve("unknown-session", ArtifactType.REQUIREMENT_PROFILE)
        
        assert result is None

    def test_retrieve_returns_none_for_unknown_artifact_type(self):
        """retrieve should return None for unknown artifact type."""
        manager = InMemoryMemoryManager()
        artifact = MockArtifact(
            name="profile",
            data="test data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        manager.store("session-1", artifact)
        
        result = manager.retrieve("session-1", ArtifactType.JOB_AD)
        
        assert result is None

    def test_store_empty_session_id_raises(self):
        """store should raise EmptySessionIDError for empty session ID."""
        manager = InMemoryMemoryManager()
        artifact = MockArtifact(
            name="test",
            data="data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        
        with pytest.raises(EmptySessionIDError):
            manager.store("", artifact)

    def test_retrieve_empty_session_id_raises(self):
        """retrieve should raise EmptySessionIDError for empty session ID."""
        manager = InMemoryMemoryManager()
        
        with pytest.raises(EmptySessionIDError):
            manager.retrieve("", ArtifactType.REQUIREMENT_PROFILE)

    def test_has_artifact_returns_true_when_exists(self):
        """has_artifact should return True when artifact exists."""
        manager = InMemoryMemoryManager()
        artifact = MockArtifact(
            name="profile",
            data="test data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        manager.store("session-1", artifact)
        
        result = manager.has_artifact("session-1", ArtifactType.REQUIREMENT_PROFILE)
        
        assert result is True

    def test_has_artifact_returns_false_when_not_exists(self):
        """has_artifact should return False when artifact doesn't exist."""
        manager = InMemoryMemoryManager()
        
        result = manager.has_artifact("session-1", ArtifactType.REQUIREMENT_PROFILE)
        
        assert result is False

    def test_has_artifact_returns_false_for_different_type(self):
        """has_artifact should return False for different artifact type."""
        manager = InMemoryMemoryManager()
        artifact = MockArtifact(
            name="profile",
            data="test data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        manager.store("session-1", artifact)
        
        result = manager.has_artifact("session-1", ArtifactType.JOB_AD)
        
        assert result is False

    def test_has_artifact_empty_session_id_raises(self):
        """has_artifact should raise EmptySessionIDError for empty session ID."""
        manager = InMemoryMemoryManager()
        
        with pytest.raises(EmptySessionIDError):
            manager.has_artifact("", ArtifactType.REQUIREMENT_PROFILE)

    def test_get_all_artifacts_returns_all_stored(self):
        """get_all_artifacts should return all artifacts for a session."""
        manager = InMemoryMemoryManager()
        profile = MockArtifact(
            name="profile",
            data="profile data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        job_ad = MockArtifact(
            name="job_ad",
            data="job ad data",
            _artifact_type=ArtifactType.JOB_AD
        )
        manager.store("session-1", profile)
        manager.store("session-1", job_ad)
        
        result = manager.get_all_artifacts("session-1")
        
        assert len(result) == 2
        assert ArtifactType.REQUIREMENT_PROFILE in result
        assert ArtifactType.JOB_AD in result
        assert result[ArtifactType.REQUIREMENT_PROFILE].name == "profile"
        assert result[ArtifactType.JOB_AD].name == "job_ad"

    def test_get_all_artifacts_returns_empty_dict_for_unknown_session(self):
        """get_all_artifacts should return empty dict for unknown session."""
        manager = InMemoryMemoryManager()
        
        result = manager.get_all_artifacts("unknown-session")
        
        assert result == {}

    def test_get_all_artifacts_empty_session_id_raises(self):
        """get_all_artifacts should raise EmptySessionIDError for empty session ID."""
        manager = InMemoryMemoryManager()
        
        with pytest.raises(EmptySessionIDError):
            manager.get_all_artifacts("")

    def test_store_overwrites_existing_artifact(self):
        """store should overwrite existing artifact of same type."""
        manager = InMemoryMemoryManager()
        artifact1 = MockArtifact(
            name="profile1",
            data="first data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        artifact2 = MockArtifact(
            name="profile2",
            data="second data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        
        manager.store("session-1", artifact1)
        manager.store("session-1", artifact2)
        
        retrieved = manager.retrieve("session-1", ArtifactType.REQUIREMENT_PROFILE)
        assert retrieved.name == "profile2"
        assert retrieved.data == "second data"

    def test_multiple_sessions_isolated(self):
        """Artifacts from different sessions should be isolated."""
        manager = InMemoryMemoryManager()
        artifact1 = MockArtifact(
            name="profile1",
            data="session 1 data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        artifact2 = MockArtifact(
            name="profile2",
            data="session 2 data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        
        manager.store("session-1", artifact1)
        manager.store("session-2", artifact2)
        
        retrieved1 = manager.retrieve("session-1", ArtifactType.REQUIREMENT_PROFILE)
        retrieved2 = manager.retrieve("session-2", ArtifactType.REQUIREMENT_PROFILE)
        
        assert retrieved1.name == "profile1"
        assert retrieved2.name == "profile2"

    def test_clear_session_removes_all_artifacts(self):
        """clear_session should remove all artifacts for a session."""
        manager = InMemoryMemoryManager()
        profile = MockArtifact(
            name="profile",
            data="profile data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        job_ad = MockArtifact(
            name="job_ad",
            data="job ad data",
            _artifact_type=ArtifactType.JOB_AD
        )
        manager.store("session-1", profile)
        manager.store("session-1", job_ad)
        
        manager.clear_session("session-1")
        
        assert manager.retrieve("session-1", ArtifactType.REQUIREMENT_PROFILE) is None
        assert manager.retrieve("session-1", ArtifactType.JOB_AD) is None
        assert manager.get_all_artifacts("session-1") == {}

    def test_clear_session_empty_session_id_raises(self):
        """clear_session should raise EmptySessionIDError for empty session ID."""
        manager = InMemoryMemoryManager()
        
        with pytest.raises(EmptySessionIDError):
            manager.clear_session("")

    def test_clear_session_does_not_affect_other_sessions(self):
        """clear_session should not affect other sessions."""
        manager = InMemoryMemoryManager()
        artifact1 = MockArtifact(
            name="profile1",
            data="session 1 data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        artifact2 = MockArtifact(
            name="profile2",
            data="session 2 data",
            _artifact_type=ArtifactType.REQUIREMENT_PROFILE
        )
        manager.store("session-1", artifact1)
        manager.store("session-2", artifact2)
        
        manager.clear_session("session-1")
        
        assert manager.retrieve("session-1", ArtifactType.REQUIREMENT_PROFILE) is None
        assert manager.retrieve("session-2", ArtifactType.REQUIREMENT_PROFILE) is not None
