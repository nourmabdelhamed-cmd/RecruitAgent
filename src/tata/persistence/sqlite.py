"""SQLite-based persistence for Tata.

Provides persistent implementations of SessionManager and MemoryManager
using SQLite for data storage across application restarts.
"""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.tata.session.session import (
    Session,
    SupportedLanguage,
    ModuleType,
    SessionNotFoundError,
    EmptyRecruiterIDError,
    EmptySessionIDError,
)
from src.tata.memory.memory import (
    Artifact,
    ArtifactType,
    EmptySessionIDError as MemoryEmptySessionIDError,
)


DEFAULT_DB_PATH = Path("tata.db")


class SQLiteSessionManager:
    """SQLite-based implementation of SessionManager.
    
    Provides persistent session storage using SQLite.
    Thread-safe via connection-per-thread pattern.
    
    Attributes:
        _db_path: Path to SQLite database file
        _local: Thread-local storage for connections
    """
    
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        """Initialize the SQLite session manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = db_path
        self._local = threading.local()
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                recruiter_id TEXT NOT NULL,
                position_name TEXT DEFAULT '',
                language TEXT DEFAULT 'en',
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                current_module TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_recruiter 
            ON sessions(recruiter_id)
        """)
        conn.commit()
    
    def create_session(self, recruiter_id: str) -> Session:
        """Create a new session for a recruiter.
        
        Args:
            recruiter_id: Identifier for the recruiter
            
        Returns:
            A new Session instance
            
        Raises:
            EmptyRecruiterIDError: If recruiter_id is empty
        """
        if not recruiter_id:
            raise EmptyRecruiterIDError("Recruiter ID cannot be empty")
        
        import uuid
        now = datetime.now()
        session = Session(
            id=str(uuid.uuid4()),
            recruiter_id=recruiter_id,
            position_name="",
            language=SupportedLanguage.ENGLISH,
            created_at=now,
            last_activity=now,
            current_module=None,
        )
        
        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO sessions 
            (id, recruiter_id, position_name, language, created_at, last_activity, current_module)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.id,
                session.recruiter_id,
                session.position_name,
                session.language.value,
                session.created_at.isoformat(),
                session.last_activity.isoformat(),
                None,
            ),
        )
        conn.commit()
        return session
    
    def list_sessions(self, recruiter_id: str) -> list[Session]:
        """List all sessions for a recruiter.
        
        Args:
            recruiter_id: Identifier for the recruiter
            
        Returns:
            List of sessions ordered by last_activity descending
            
        Raises:
            EmptyRecruiterIDError: If recruiter_id is empty
        """
        if not recruiter_id:
            raise EmptyRecruiterIDError("Recruiter ID cannot be empty")
        
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT * FROM sessions 
            WHERE recruiter_id = ? 
            ORDER BY last_activity DESC
            """,
            (recruiter_id,),
        )
        return [self._row_to_session(row) for row in cursor.fetchall()]
    
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
        
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        return self._row_to_session(row) if row else None
    
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
        
        conn = self._get_connection()
        cursor = conn.execute(
            """
            UPDATE sessions 
            SET position_name = ?, last_activity = ?
            WHERE id = ?
            """,
            (position_name, datetime.now().isoformat(), session_id),
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise SessionNotFoundError(f"Session not found: {session_id}")
    
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
        
        conn = self._get_connection()
        cursor = conn.execute(
            """
            UPDATE sessions 
            SET language = ?, last_activity = ?
            WHERE id = ?
            """,
            (language.value, datetime.now().isoformat(), session_id),
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise SessionNotFoundError(f"Session not found: {session_id}")
    
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
        
        session = self.get_session(session_id)
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
        
        conn = self._get_connection()
        cursor = conn.execute(
            """
            UPDATE sessions 
            SET current_module = ?, last_activity = ?
            WHERE id = ?
            """,
            (module.value, datetime.now().isoformat(), session_id),
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise SessionNotFoundError(f"Session not found: {session_id}")
    
    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """Convert database row to Session object."""
        current_module = None
        if row["current_module"]:
            current_module = ModuleType(row["current_module"])
        
        return Session(
            id=row["id"],
            recruiter_id=row["recruiter_id"],
            position_name=row["position_name"],
            language=SupportedLanguage(row["language"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            last_activity=datetime.fromisoformat(row["last_activity"]),
            current_module=current_module,
        )



class SQLiteMemoryManager:
    """SQLite-based implementation of MemoryManager.
    
    Provides persistent artifact storage using SQLite.
    Artifacts are stored as JSON blobs with type information.
    
    Attributes:
        _db_path: Path to SQLite database file
        _local: Thread-local storage for connections
        _artifact_registry: Registry mapping artifact types to classes for deserialization
    """
    
    def __init__(
        self,
        db_path: Path = DEFAULT_DB_PATH,
        artifact_registry: Optional[Dict[ArtifactType, type]] = None,
    ):
        """Initialize the SQLite memory manager.
        
        Args:
            db_path: Path to SQLite database file
            artifact_registry: Optional mapping of ArtifactType to artifact classes
                              for deserialization. If not provided, retrieve() returns
                              raw JSON data wrapped in a generic artifact.
        """
        self._db_path = db_path
        self._local = threading.local()
        self._artifact_registry = artifact_registry or {}
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                session_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (session_id, artifact_type)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_artifacts_session 
            ON artifacts(session_id)
        """)
        conn.commit()
    
    def store(self, session_id: str, artifact: Artifact) -> None:
        """Store an artifact for a session.
        
        Args:
            session_id: The session identifier
            artifact: The artifact to store
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise MemoryEmptySessionIDError("Session ID cannot be empty")
        
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO artifacts 
            (session_id, artifact_type, data, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                artifact.artifact_type.value,
                artifact.to_json(),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
    
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
            raise MemoryEmptySessionIDError("Session ID cannot be empty")
        
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT data FROM artifacts 
            WHERE session_id = ? AND artifact_type = ?
            """,
            (session_id, artifact_type.value),
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # If we have a registered class for this type, deserialize properly
        if artifact_type in self._artifact_registry:
            artifact_class = self._artifact_registry[artifact_type]
            if hasattr(artifact_class, "from_json"):
                return artifact_class.from_json(row["data"])
        
        # Return a generic wrapper if no class registered
        return _StoredArtifact(artifact_type, row["data"])
    
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
            raise MemoryEmptySessionIDError("Session ID cannot be empty")
        
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT 1 FROM artifacts 
            WHERE session_id = ? AND artifact_type = ?
            """,
            (session_id, artifact_type.value),
        )
        return cursor.fetchone() is not None
    
    def get_all_artifacts(self, session_id: str) -> Dict[ArtifactType, Artifact]:
        """Get all artifacts for a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dictionary mapping artifact types to artifacts
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise MemoryEmptySessionIDError("Session ID cannot be empty")
        
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT artifact_type, data FROM artifacts WHERE session_id = ?",
            (session_id,),
        )
        
        result: Dict[ArtifactType, Artifact] = {}
        for row in cursor.fetchall():
            artifact_type = ArtifactType(row["artifact_type"])
            
            if artifact_type in self._artifact_registry:
                artifact_class = self._artifact_registry[artifact_type]
                if hasattr(artifact_class, "from_json"):
                    result[artifact_type] = artifact_class.from_json(row["data"])
                    continue
            
            result[artifact_type] = _StoredArtifact(artifact_type, row["data"])
        
        return result
    
    def clear_session(self, session_id: str) -> None:
        """Clear all artifacts for a session.
        
        Args:
            session_id: The session identifier
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise MemoryEmptySessionIDError("Session ID cannot be empty")
        
        conn = self._get_connection()
        conn.execute(
            "DELETE FROM artifacts WHERE session_id = ?",
            (session_id,),
        )
        conn.commit()


class _StoredArtifact:
    """Generic wrapper for stored artifacts when no class is registered.
    
    Used when retrieving artifacts without a registered deserializer.
    """
    
    def __init__(self, artifact_type: ArtifactType, json_data: str):
        self._artifact_type = artifact_type
        self._json_data = json_data
        self._data = json.loads(json_data)
    
    @property
    def artifact_type(self) -> ArtifactType:
        return self._artifact_type
    
    def to_json(self) -> str:
        return self._json_data
    
    @property
    def data(self) -> Dict[str, Any]:
        """Access the raw data dictionary."""
        return self._data
