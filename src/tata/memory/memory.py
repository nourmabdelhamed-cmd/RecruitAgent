"""Memory management for Tata recruitment assistant.

This module provides artifact storage and retrieval for recruitment chat sessions.
All artifacts created during a session are stored and can be reused by subsequent modules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Protocol, Dict, Any, runtime_checkable
from abc import abstractmethod
import threading
import json


class ArtifactType(Enum):
    """Different artifact types stored in memory.
    
    Each artifact type corresponds to a module output that can be
    stored and reused within a session.
    """
    REQUIREMENT_PROFILE = "requirement_profile"
    JOB_AD = "job_ad"
    TA_SCREENING_TEMPLATE = "ta_screening_template"
    HM_SCREENING_TEMPLATE = "hm_screening_template"
    HEADHUNTING_MESSAGES = "headhunting_messages"
    CANDIDATE_REPORTS = "candidate_reports"
    FUNNEL_REPORT = "funnel_report"
    JOB_AD_REVIEW = "job_ad_review"
    DI_REVIEW = "di_review"
    CALENDAR_INVITE = "calendar_invite"


@runtime_checkable
class Artifact(Protocol):
    """Interface all storable artifacts must implement.
    
    Any data structure that needs to be stored in memory must
    implement this protocol to ensure consistent serialization
    and type identification.
    """
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type."""
        ...
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        ...


class SessionNotFoundError(Exception):
    """Raised when a session cannot be found."""
    pass


class EmptySessionIDError(Exception):
    """Raised when session ID is empty."""
    pass


class MemoryManager(Protocol):
    """Protocol for storing and retrieving artifacts for sessions.
    
    Implementations must be thread-safe as artifacts may be accessed
    concurrently from multiple requests.
    
    Requirements covered:
    - 1.1: Maintain memory of all created outputs within a session
    - 1.2: Reuse requirement profile automatically in subsequent outputs
    - 1.3: Store job ad for use in headhunting messages and reviews
    - 1.4: Store screening template for use in candidate reports
    - 1.5: Never lose information once created within a session
    """
    
    @abstractmethod
    def store(self, session_id: str, artifact: Artifact) -> None:
        """Store an artifact for a session.
        
        Args:
            session_id: The session identifier
            artifact: The artifact to store (must implement Artifact protocol)
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        ...
    
    @abstractmethod
    def retrieve(self, session_id: str, artifact_type: ArtifactType) -> Optional[Artifact]:
        """Retrieve an artifact from a session.
        
        Args:
            session_id: The session identifier
            artifact_type: The type of artifact to retrieve
            
        Returns:
            The Artifact if found, None otherwise
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        ...
    
    @abstractmethod
    def has_artifact(self, session_id: str, artifact_type: ArtifactType) -> bool:
        """Check if an artifact exists for a session.
        
        Args:
            session_id: The session identifier
            artifact_type: The type of artifact to check
            
        Returns:
            True if the artifact exists, False otherwise
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        ...
    
    @abstractmethod
    def get_all_artifacts(self, session_id: str) -> Dict[ArtifactType, Artifact]:
        """Get all artifacts for a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dictionary mapping artifact types to artifacts
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        ...


class InMemoryMemoryManager:
    """Thread-safe in-memory implementation of MemoryManager.
    
    Uses nested dictionaries with threading.Lock for thread safety.
    Structure: {session_id: {artifact_type: artifact}}
    
    Suitable for single-instance deployments.
    """
    
    def __init__(self):
        """Initialize the memory manager."""
        self._storage: Dict[str, Dict[ArtifactType, Artifact]] = {}
        self._lock = threading.Lock()
    
    def store(self, session_id: str, artifact: Artifact) -> None:
        """Store an artifact for a session.
        
        If an artifact of the same type already exists, it will be overwritten.
        
        Args:
            session_id: The session identifier
            artifact: The artifact to store
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            if session_id not in self._storage:
                self._storage[session_id] = {}
            
            self._storage[session_id][artifact.artifact_type] = artifact
    
    def retrieve(self, session_id: str, artifact_type: ArtifactType) -> Optional[Artifact]:
        """Retrieve an artifact from a session.
        
        Args:
            session_id: The session identifier
            artifact_type: The type of artifact to retrieve
            
        Returns:
            The Artifact if found, None otherwise
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            session_artifacts = self._storage.get(session_id, {})
            return session_artifacts.get(artifact_type)
    
    def has_artifact(self, session_id: str, artifact_type: ArtifactType) -> bool:
        """Check if an artifact exists for a session.
        
        Args:
            session_id: The session identifier
            artifact_type: The type of artifact to check
            
        Returns:
            True if the artifact exists, False otherwise
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            session_artifacts = self._storage.get(session_id, {})
            return artifact_type in session_artifacts
    
    def get_all_artifacts(self, session_id: str) -> Dict[ArtifactType, Artifact]:
        """Get all artifacts for a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dictionary mapping artifact types to artifacts.
            Returns empty dict if session has no artifacts.
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            # Return a copy to prevent external modification
            return dict(self._storage.get(session_id, {}))
    
    def clear_session(self, session_id: str) -> None:
        """Clear all artifacts for a session.
        
        Args:
            session_id: The session identifier
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        with self._lock:
            if session_id in self._storage:
                del self._storage[session_id]
