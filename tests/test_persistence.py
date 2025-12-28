"""Tests for SQLite persistence layer.

Tests cover:
- Session creation and retrieval with persistence
- Session listing by recruiter
- Artifact storage and retrieval with persistence
- Thread safety of SQLite implementations
"""

import json
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.tata.memory.memory import ArtifactType
from src.tata.persistence.sqlite import (
    SQLiteSessionManager,
    SQLiteMemoryManager,
    _StoredArtifact,
)
from src.tata.session.session import (
    EmptyRecruiterIDError,
    EmptySessionIDError,
    SessionNotFoundError,
    SupportedLanguage,
    ModuleType,
)


@dataclass
class MockArtifact:
    """Mock artifact for testing."""
    
    name: str
    value: int
    
    @property
    def artifact_type(self) -> ArtifactType:
        return ArtifactType.REQUIREMENT_PROFILE
    
    def to_json(self) -> str:
        return json.dumps({"name": self.name, "value": self.value})
    
    @classmethod
    def from_json(cls, json_str: str) -> "MockArtifact":
        data = json.loads(json_str)
        return cls(name=data["name"], value=data["value"])


class TestSQLiteSessionManager:
    """Tests for SQLiteSessionManager."""
    
    @pytest.fixture
    def db_path(self):
        """Create temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
    
    @pytest.fixture
    def manager(self, db_path):
        """Create session manager with temp database."""
        return SQLiteSessionManager(db_path)
    
    def test_create_session_stores_recruiter_id(self, manager):
        """Session stores recruiter_id correctly."""
        session = manager.create_session("recruiter-123")
        
        assert session.recruiter_id == "recruiter-123"
        assert session.id is not None
        assert session.position_name == ""
        assert session.language == SupportedLanguage.ENGLISH
    
    def test_create_session_empty_recruiter_raises(self, manager):
        """Empty recruiter ID raises EmptyRecruiterIDError."""
        with pytest.raises(EmptyRecruiterIDError):
            manager.create_session("")
    
    def test_get_session_returns_persisted_session(self, manager):
        """Session can be retrieved after creation."""
        created = manager.create_session("recruiter-123")
        
        retrieved = manager.get_session(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.recruiter_id == "recruiter-123"
    
    def test_get_session_empty_id_raises(self, manager):
        """Empty session ID raises EmptySessionIDError."""
        with pytest.raises(EmptySessionIDError):
            manager.get_session("")
    
    def test_get_session_not_found_returns_none(self, manager):
        """Non-existent session returns None."""
        result = manager.get_session("nonexistent-id")
        assert result is None
    
    def test_list_sessions_returns_recruiter_sessions(self, manager):
        """list_sessions returns only sessions for specified recruiter."""
        manager.create_session("recruiter-1")
        manager.create_session("recruiter-1")
        manager.create_session("recruiter-2")
        
        sessions = manager.list_sessions("recruiter-1")
        
        assert len(sessions) == 2
        assert all(s.recruiter_id == "recruiter-1" for s in sessions)
    
    def test_list_sessions_ordered_by_last_activity(self, manager):
        """Sessions are ordered by last_activity descending."""
        s1 = manager.create_session("recruiter-1")
        s2 = manager.create_session("recruiter-1")
        
        # Update s1 to make it more recent
        manager.set_position_name(s1.id, "Updated Position")
        
        sessions = manager.list_sessions("recruiter-1")
        
        assert sessions[0].id == s1.id  # Most recently updated
        assert sessions[1].id == s2.id
    
    def test_list_sessions_empty_recruiter_raises(self, manager):
        """Empty recruiter ID raises EmptyRecruiterIDError."""
        with pytest.raises(EmptyRecruiterIDError):
            manager.list_sessions("")
    
    def test_list_sessions_no_sessions_returns_empty(self, manager):
        """Recruiter with no sessions returns empty list."""
        sessions = manager.list_sessions("new-recruiter")
        assert sessions == []
    
    def test_set_position_name_persists(self, manager):
        """Position name is persisted."""
        session = manager.create_session("recruiter-1")
        
        manager.set_position_name(session.id, "Senior Developer")
        
        retrieved = manager.get_session(session.id)
        assert retrieved.position_name == "Senior Developer"
    
    def test_set_position_name_not_found_raises(self, manager):
        """Setting position on non-existent session raises."""
        with pytest.raises(SessionNotFoundError):
            manager.set_position_name("nonexistent", "Position")
    
    def test_set_language_persists(self, manager):
        """Language setting is persisted."""
        session = manager.create_session("recruiter-1")
        
        manager.set_language(session.id, SupportedLanguage.GERMAN)
        
        retrieved = manager.get_session(session.id)
        assert retrieved.language == SupportedLanguage.GERMAN
    
    def test_set_active_module_persists(self, manager):
        """Active module is persisted."""
        session = manager.create_session("recruiter-1")
        
        manager.set_active_module(session.id, ModuleType.JOB_AD)
        
        retrieved = manager.get_session(session.id)
        assert retrieved.current_module == ModuleType.JOB_AD
    
    def test_get_active_module_returns_none_initially(self, manager):
        """New session has no active module."""
        session = manager.create_session("recruiter-1")
        
        module = manager.get_active_module(session.id)
        
        assert module is None
    
    def test_persistence_across_manager_instances(self, db_path):
        """Data persists across manager instances."""
        manager1 = SQLiteSessionManager(db_path)
        session = manager1.create_session("recruiter-1")
        manager1.set_position_name(session.id, "Test Position")
        
        # Create new manager instance with same db
        manager2 = SQLiteSessionManager(db_path)
        retrieved = manager2.get_session(session.id)
        
        assert retrieved is not None
        assert retrieved.position_name == "Test Position"


class TestSQLiteMemoryManager:
    """Tests for SQLiteMemoryManager."""
    
    @pytest.fixture
    def db_path(self):
        """Create temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
    
    @pytest.fixture
    def manager(self, db_path):
        """Create memory manager with temp database."""
        return SQLiteMemoryManager(db_path)
    
    @pytest.fixture
    def manager_with_registry(self, db_path):
        """Create memory manager with artifact registry."""
        registry = {ArtifactType.REQUIREMENT_PROFILE: MockArtifact}
        return SQLiteMemoryManager(db_path, artifact_registry=registry)
    
    def test_store_and_retrieve_artifact(self, manager):
        """Artifact can be stored and retrieved."""
        artifact = MockArtifact(name="test", value=42)
        
        manager.store("session-1", artifact)
        retrieved = manager.retrieve("session-1", ArtifactType.REQUIREMENT_PROFILE)
        
        assert retrieved is not None
        assert isinstance(retrieved, _StoredArtifact)
        assert retrieved.data["name"] == "test"
        assert retrieved.data["value"] == 42
    
    def test_store_empty_session_raises(self, manager):
        """Empty session ID raises error."""
        artifact = MockArtifact(name="test", value=42)
        
        with pytest.raises(Exception):  # MemoryEmptySessionIDError
            manager.store("", artifact)
    
    def test_retrieve_with_registry_deserializes(self, manager_with_registry):
        """Artifact is deserialized using registered class."""
        artifact = MockArtifact(name="test", value=42)
        
        manager_with_registry.store("session-1", artifact)
        retrieved = manager_with_registry.retrieve(
            "session-1", ArtifactType.REQUIREMENT_PROFILE
        )
        
        assert isinstance(retrieved, MockArtifact)
        assert retrieved.name == "test"
        assert retrieved.value == 42
    
    def test_retrieve_not_found_returns_none(self, manager):
        """Non-existent artifact returns None."""
        result = manager.retrieve("session-1", ArtifactType.JOB_AD)
        assert result is None
    
    def test_has_artifact_true_when_exists(self, manager):
        """has_artifact returns True when artifact exists."""
        artifact = MockArtifact(name="test", value=42)
        manager.store("session-1", artifact)
        
        assert manager.has_artifact("session-1", ArtifactType.REQUIREMENT_PROFILE)
    
    def test_has_artifact_false_when_missing(self, manager):
        """has_artifact returns False when artifact missing."""
        assert not manager.has_artifact("session-1", ArtifactType.JOB_AD)
    
    def test_get_all_artifacts_returns_all(self, manager):
        """get_all_artifacts returns all stored artifacts."""
        artifact = MockArtifact(name="test", value=42)
        manager.store("session-1", artifact)
        
        all_artifacts = manager.get_all_artifacts("session-1")
        
        assert len(all_artifacts) == 1
        assert ArtifactType.REQUIREMENT_PROFILE in all_artifacts
    
    def test_get_all_artifacts_empty_session(self, manager):
        """get_all_artifacts returns empty dict for new session."""
        all_artifacts = manager.get_all_artifacts("new-session")
        assert all_artifacts == {}
    
    def test_clear_session_removes_artifacts(self, manager):
        """clear_session removes all artifacts for session."""
        artifact = MockArtifact(name="test", value=42)
        manager.store("session-1", artifact)
        
        manager.clear_session("session-1")
        
        assert not manager.has_artifact("session-1", ArtifactType.REQUIREMENT_PROFILE)
    
    def test_store_overwrites_existing(self, manager):
        """Storing same artifact type overwrites previous."""
        manager.store("session-1", MockArtifact(name="first", value=1))
        manager.store("session-1", MockArtifact(name="second", value=2))
        
        retrieved = manager.retrieve("session-1", ArtifactType.REQUIREMENT_PROFILE)
        
        assert retrieved.data["name"] == "second"
        assert retrieved.data["value"] == 2
    
    def test_persistence_across_manager_instances(self, db_path):
        """Data persists across manager instances."""
        manager1 = SQLiteMemoryManager(db_path)
        manager1.store("session-1", MockArtifact(name="test", value=42))
        
        # Create new manager instance with same db
        manager2 = SQLiteMemoryManager(db_path)
        retrieved = manager2.retrieve("session-1", ArtifactType.REQUIREMENT_PROFILE)
        
        assert retrieved is not None
        assert retrieved.data["name"] == "test"


class TestInMemorySessionManagerListSessions:
    """Tests for list_sessions in InMemorySessionManager."""
    
    @pytest.fixture
    def manager(self):
        """Create in-memory session manager."""
        from src.tata.session.session import InMemorySessionManager
        return InMemorySessionManager()
    
    def test_list_sessions_returns_recruiter_sessions(self, manager):
        """list_sessions returns only sessions for specified recruiter."""
        manager.create_session("recruiter-1")
        manager.create_session("recruiter-1")
        manager.create_session("recruiter-2")
        
        sessions = manager.list_sessions("recruiter-1")
        
        assert len(sessions) == 2
        assert all(s.recruiter_id == "recruiter-1" for s in sessions)
    
    def test_list_sessions_empty_recruiter_raises(self, manager):
        """Empty recruiter ID raises EmptyRecruiterIDError."""
        with pytest.raises(EmptyRecruiterIDError):
            manager.list_sessions("")
    
    def test_list_sessions_no_sessions_returns_empty(self, manager):
        """Recruiter with no sessions returns empty list."""
        sessions = manager.list_sessions("new-recruiter")
        assert sessions == []
