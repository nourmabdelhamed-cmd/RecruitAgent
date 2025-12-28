"""Session management for Tata recruitment assistant.

This module provides session lifecycle management for recruitment chat sessions.
Each session represents one recruitment project with persistent memory.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Protocol, Dict
from abc import abstractmethod
import threading
import uuid


class SupportedLanguage(Enum):
    """Languages Tata can output."""
    ENGLISH = "en"
    SWEDISH = "sv"
    DANISH = "da"
    NORWEGIAN = "no"
    GERMAN = "de"


class ModuleType(Enum):
    """Different modules in Tata."""
    REQUIREMENT_PROFILE = "A"
    JOB_AD = "B"
    TA_SCREENING = "C"
    HM_SCREENING = "D"
    HEADHUNTING = "E"
    CANDIDATE_REPORT = "F"
    FUNNEL_REPORT = "G"
    JOB_AD_REVIEW = "H"
    DI_REVIEW = "I"
    CALENDAR_INVITE = "J"


@dataclass
class Session:
    """Represents a recruitment chat session.
    
    Each session corresponds to one recruitment project and maintains
    state across the entire recruitment lifecycle.
    
    Attributes:
        id: Unique session identifier
        position_name: The job position name (used as chat title per Req 12.2)
        language: Output language for the session (default English per Req 12.1)
        created_at: When the session was created
        last_activity: Last activity timestamp
        current_module: Currently active module, if any
    """
    id: str
    position_name: str = ""
    language: SupportedLanguage = SupportedLanguage.ENGLISH
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    current_module: Optional[ModuleType] = None


class SessionNotFoundError(Exception):
    """Raised when a session cannot be found."""
    pass


class EmptyRecruiterIDError(Exception):
    """Raised when recruiter ID is empty."""
    pass


class EmptySessionIDError(Exception):
    """Raised when session ID is empty."""
    pass


class SessionManager(Protocol):
    """Protocol for managing recruitment chat sessions.
    
    Implementations must be thread-safe as sessions may be accessed
    concurrently from multiple requests.
    """
    
    @abstractmethod
    def create_session(self, recruiter_id: str) -> Session:
        """Create a new session for a recruiter.
        
        Args:
            recruiter_id: Identifier for the recruiter
            
        Returns:
            A new Session instance
            
        Raises:
            EmptyRecruiterIDError: If recruiter_id is empty
        """
        ...
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve an existing session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            The Session if found, None otherwise
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        ...
    
    @abstractmethod
    def set_position_name(self, session_id: str, position_name: str) -> None:
        """Set the position name for a session.
        
        The position name is used as the chat title per Requirement 12.2.
        
        Args:
            session_id: The session identifier
            position_name: The job position name
            
        Raises:
            EmptySessionIDError: If session_id is empty
            SessionNotFoundError: If session doesn't exist
        """
        ...
    
    @abstractmethod
    def set_language(self, session_id: str, language: SupportedLanguage) -> None:
        """Set the output language for a session.
        
        Args:
            session_id: The session identifier
            language: The target language
            
        Raises:
            EmptySessionIDError: If session_id is empty
            SessionNotFoundError: If session doesn't exist
        """
        ...
    
    @abstractmethod
    def get_active_module(self, session_id: str) -> Optional[ModuleType]:
        """Get the currently active module for a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            The active ModuleType if set, None otherwise
            
        Raises:
            EmptySessionIDError: If session_id is empty
            SessionNotFoundError: If session doesn't exist
        """
        ...
    
    @abstractmethod
    def set_active_module(self, session_id: str, module: ModuleType) -> None:
        """Set the currently active module for a session.
        
        Args:
            session_id: The session identifier
            module: The module to set as active
            
        Raises:
            EmptySessionIDError: If session_id is empty
            SessionNotFoundError: If session doesn't exist
        """
        ...


class InMemorySessionManager:
    """Thread-safe in-memory implementation of SessionManager.
    
    Uses a dictionary with threading.Lock for thread safety.
    Suitable for single-instance deployments.
    """
    
    def __init__(self, id_generator: Optional[callable] = None):
        """Initialize the session manager.
        
        Args:
            id_generator: Optional custom ID generator function.
                         Defaults to uuid4 string generation.
        """
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()
        self._id_generator = id_generator or (lambda: str(uuid.uuid4()))
    
    def create_session(self, recruiter_id: str) -> Session:
        """Create a new session for a recruiter.
        
        Args:
            recruiter_id: Identifier for the recruiter
            
        Returns:
            A new Session instance with default English language
            
        Raises:
            EmptyRecruiterIDError: If recruiter_id is empty
        """
        if not recruiter_id:
            raise EmptyRecruiterIDError("Recruiter ID cannot be empty")
        
        now = datetime.now()
        session = Session(
            id=self._id_generator(),
            position_name="",
            language=SupportedLanguage.ENGLISH,  # Default per Requirement 12.1
            created_at=now,
            last_activity=now,
            current_module=None,
        )
        
        with self._lock:
            self._sessions[session.id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve an existing session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            The Session if found, None otherwise
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            return self._sessions.get(session_id)
    
    def set_position_name(self, session_id: str, position_name: str) -> None:
        """Set the position name for a session.
        
        Args:
            session_id: The session identifier
            position_name: The job position name
            
        Raises:
            EmptySessionIDError: If session_id is empty
            SessionNotFoundError: If session doesn't exist
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session not found: {session_id}")
            
            session.position_name = position_name
            session.last_activity = datetime.now()
    
    def set_language(self, session_id: str, language: SupportedLanguage) -> None:
        """Set the output language for a session.
        
        Args:
            session_id: The session identifier
            language: The target language
            
        Raises:
            EmptySessionIDError: If session_id is empty
            SessionNotFoundError: If session doesn't exist
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session not found: {session_id}")
            
            session.language = language
            session.last_activity = datetime.now()
    
    def get_active_module(self, session_id: str) -> Optional[ModuleType]:
        """Get the currently active module for a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            The active ModuleType if set, None otherwise
            
        Raises:
            EmptySessionIDError: If session_id is empty
            SessionNotFoundError: If session doesn't exist
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session not found: {session_id}")
            
            return session.current_module
    
    def set_active_module(self, session_id: str, module: ModuleType) -> None:
        """Set the currently active module for a session.
        
        Args:
            session_id: The session identifier
            module: The module to set as active
            
        Raises:
            EmptySessionIDError: If session_id is empty
            SessionNotFoundError: If session doesn't exist
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session not found: {session_id}")
            
            session.current_module = module
            session.last_activity = datetime.now()
