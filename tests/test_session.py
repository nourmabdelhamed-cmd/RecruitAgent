"""Unit tests for Session Manager."""

import pytest
from datetime import datetime

from src.tata.session import (
    Session,
    SupportedLanguage,
    ModuleType,
    InMemorySessionManager,
    SessionNotFoundError,
    EmptyRecruiterIDError,
    EmptySessionIDError,
)


class TestSession:
    """Tests for Session dataclass."""

    def test_session_creation_with_defaults(self):
        """Session should have sensible defaults."""
        session = Session(id="test-123")
        
        assert session.id == "test-123"
        assert session.position_name == ""
        assert session.language == SupportedLanguage.ENGLISH
        assert session.current_module is None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)

    def test_session_creation_with_all_fields(self):
        """Session should accept all fields."""
        now = datetime.now()
        session = Session(
            id="test-456",
            position_name="Senior Developer",
            language=SupportedLanguage.SWEDISH,
            created_at=now,
            last_activity=now,
            current_module=ModuleType.JOB_AD,
        )
        
        assert session.id == "test-456"
        assert session.position_name == "Senior Developer"
        assert session.language == SupportedLanguage.SWEDISH
        assert session.current_module == ModuleType.JOB_AD


class TestSupportedLanguage:
    """Tests for SupportedLanguage enum."""

    def test_all_languages_defined(self):
        """All five supported languages should be defined."""
        assert SupportedLanguage.ENGLISH.value == "en"
        assert SupportedLanguage.SWEDISH.value == "sv"
        assert SupportedLanguage.DANISH.value == "da"
        assert SupportedLanguage.NORWEGIAN.value == "no"
        assert SupportedLanguage.GERMAN.value == "de"


class TestModuleType:
    """Tests for ModuleType enum."""

    def test_all_modules_defined(self):
        """All ten modules should be defined with correct letters."""
        assert ModuleType.REQUIREMENT_PROFILE.value == "A"
        assert ModuleType.JOB_AD.value == "B"
        assert ModuleType.TA_SCREENING.value == "C"
        assert ModuleType.HM_SCREENING.value == "D"
        assert ModuleType.HEADHUNTING.value == "E"
        assert ModuleType.CANDIDATE_REPORT.value == "F"
        assert ModuleType.FUNNEL_REPORT.value == "G"
        assert ModuleType.JOB_AD_REVIEW.value == "H"
        assert ModuleType.DI_REVIEW.value == "I"
        assert ModuleType.CALENDAR_INVITE.value == "J"


class TestInMemorySessionManager:
    """Tests for InMemorySessionManager."""

    def test_create_session(self):
        """create_session should create a new session with defaults."""
        manager = InMemorySessionManager()
        session = manager.create_session("recruiter-1")
        
        assert session.id is not None
        assert session.position_name == ""
        assert session.language == SupportedLanguage.ENGLISH
        assert session.current_module is None

    def test_create_session_empty_recruiter_id_raises(self):
        """create_session should raise EmptyRecruiterIDError for empty ID."""
        manager = InMemorySessionManager()
        
        with pytest.raises(EmptyRecruiterIDError):
            manager.create_session("")

    def test_create_session_with_custom_id_generator(self):
        """create_session should use custom ID generator."""
        counter = [0]
        def custom_id():
            counter[0] += 1
            return f"session-{counter[0]}"
        
        manager = InMemorySessionManager(id_generator=custom_id)
        session1 = manager.create_session("recruiter-1")
        session2 = manager.create_session("recruiter-2")
        
        assert session1.id == "session-1"
        assert session2.id == "session-2"

    def test_get_session_returns_created_session(self):
        """get_session should return a previously created session."""
        manager = InMemorySessionManager()
        created = manager.create_session("recruiter-1")
        
        retrieved = manager.get_session(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_session_returns_none_for_unknown(self):
        """get_session should return None for unknown session ID."""
        manager = InMemorySessionManager()
        
        result = manager.get_session("unknown-id")
        
        assert result is None

    def test_get_session_empty_id_raises(self):
        """get_session should raise EmptySessionIDError for empty ID."""
        manager = InMemorySessionManager()
        
        with pytest.raises(EmptySessionIDError):
            manager.get_session("")

    def test_set_position_name(self):
        """set_position_name should update the session's position name."""
        manager = InMemorySessionManager()
        session = manager.create_session("recruiter-1")
        
        manager.set_position_name(session.id, "Senior Developer")
        
        updated = manager.get_session(session.id)
        assert updated.position_name == "Senior Developer"

    def test_set_position_name_updates_last_activity(self):
        """set_position_name should update last_activity timestamp."""
        manager = InMemorySessionManager()
        session = manager.create_session("recruiter-1")
        original_activity = session.last_activity
        
        manager.set_position_name(session.id, "Developer")
        
        updated = manager.get_session(session.id)
        assert updated.last_activity >= original_activity

    def test_set_position_name_empty_session_id_raises(self):
        """set_position_name should raise EmptySessionIDError for empty ID."""
        manager = InMemorySessionManager()
        
        with pytest.raises(EmptySessionIDError):
            manager.set_position_name("", "Developer")

    def test_set_position_name_unknown_session_raises(self):
        """set_position_name should raise SessionNotFoundError for unknown session."""
        manager = InMemorySessionManager()
        
        with pytest.raises(SessionNotFoundError):
            manager.set_position_name("unknown-id", "Developer")

    def test_set_language(self):
        """set_language should update the session's language."""
        manager = InMemorySessionManager()
        session = manager.create_session("recruiter-1")
        
        manager.set_language(session.id, SupportedLanguage.GERMAN)
        
        updated = manager.get_session(session.id)
        assert updated.language == SupportedLanguage.GERMAN

    def test_set_language_empty_session_id_raises(self):
        """set_language should raise EmptySessionIDError for empty ID."""
        manager = InMemorySessionManager()
        
        with pytest.raises(EmptySessionIDError):
            manager.set_language("", SupportedLanguage.SWEDISH)

    def test_set_language_unknown_session_raises(self):
        """set_language should raise SessionNotFoundError for unknown session."""
        manager = InMemorySessionManager()
        
        with pytest.raises(SessionNotFoundError):
            manager.set_language("unknown-id", SupportedLanguage.SWEDISH)

    def test_get_active_module_returns_none_initially(self):
        """get_active_module should return None for new sessions."""
        manager = InMemorySessionManager()
        session = manager.create_session("recruiter-1")
        
        result = manager.get_active_module(session.id)
        
        assert result is None

    def test_get_active_module_empty_session_id_raises(self):
        """get_active_module should raise EmptySessionIDError for empty ID."""
        manager = InMemorySessionManager()
        
        with pytest.raises(EmptySessionIDError):
            manager.get_active_module("")

    def test_get_active_module_unknown_session_raises(self):
        """get_active_module should raise SessionNotFoundError for unknown session."""
        manager = InMemorySessionManager()
        
        with pytest.raises(SessionNotFoundError):
            manager.get_active_module("unknown-id")

    def test_set_active_module(self):
        """set_active_module should update the session's current module."""
        manager = InMemorySessionManager()
        session = manager.create_session("recruiter-1")
        
        manager.set_active_module(session.id, ModuleType.REQUIREMENT_PROFILE)
        
        result = manager.get_active_module(session.id)
        assert result == ModuleType.REQUIREMENT_PROFILE

    def test_set_active_module_empty_session_id_raises(self):
        """set_active_module should raise EmptySessionIDError for empty ID."""
        manager = InMemorySessionManager()
        
        with pytest.raises(EmptySessionIDError):
            manager.set_active_module("", ModuleType.JOB_AD)

    def test_set_active_module_unknown_session_raises(self):
        """set_active_module should raise SessionNotFoundError for unknown session."""
        manager = InMemorySessionManager()
        
        with pytest.raises(SessionNotFoundError):
            manager.set_active_module("unknown-id", ModuleType.JOB_AD)
