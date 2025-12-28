"""Tests for ToolExecutor.

Tests the ToolExecutor class that routes OpenAI tool calls to Tata processors,
handles dependency checking, and manages artifact storage.

Requirements covered:
- 3.1: Parse function name and arguments from tool calls
- 3.2: Validate that requested tool exists in Tool_Registry
- 3.3: Check module dependencies via DependencyManager before execution
- 3.4: Return error message describing missing prerequisites
- 3.5: Instantiate appropriate processor and execute with parsed arguments
- 3.6: Store resulting artifact in MemoryManager
- 3.7: Return artifact's JSON representation for inclusion in conversation
- 3.8: Return structured error message on failure
"""

import json
import pytest

from src.tata.agent.executor import ToolExecutor, ToolExecutionResult
from src.tata.agent.models import ToolCall
from src.tata.agent.registry import InMemoryToolRegistry
from src.tata.dependency.dependency import InMemoryDependencyManager
from src.tata.memory.memory import InMemoryMemoryManager, ArtifactType
from src.tata.session.session import ModuleType


@pytest.fixture
def memory_manager():
    """Create a fresh memory manager for each test."""
    return InMemoryMemoryManager()


@pytest.fixture
def dependency_manager(memory_manager):
    """Create a dependency manager with the memory manager."""
    return InMemoryDependencyManager(memory_manager)


@pytest.fixture
def tool_registry():
    """Create a tool registry."""
    return InMemoryToolRegistry()


@pytest.fixture
def session_id():
    """Create a test session ID."""
    return "test-session-123"


@pytest.fixture
def executor(tool_registry, dependency_manager, memory_manager, session_id):
    """Create a ToolExecutor with all dependencies."""
    return ToolExecutor(
        tool_registry=tool_registry,
        dependency_manager=dependency_manager,
        memory_manager=memory_manager,
        session_id=session_id,
    )


class TestToolExecutorBasics:
    """Basic tests for ToolExecutor."""
    
    def test_executor_initializes(self, executor):
        """Executor should initialize with all dependencies."""
        assert executor is not None
        assert executor._registry is not None
        assert executor._deps is not None
        assert executor._memory is not None
        assert executor._session_id == "test-session-123"
    
    def test_unknown_tool_returns_error(self, executor):
        """Executing unknown tool should return error (Requirement 3.2)."""
        tool_call = ToolCall(
            id="call-1",
            name="unknown_tool",
            arguments="{}"
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is False
        assert "unknown_tool" in result.error.lower()
    
    def test_invalid_json_arguments_returns_error(self, executor):
        """Invalid JSON arguments should return error."""
        tool_call = ToolCall(
            id="call-1",
            name="create_funnel_report",
            arguments="not valid json"
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is False
        assert "invalid" in result.error.lower() or "json" in result.error.lower()


class TestDependencyChecking:
    """Tests for dependency checking (Requirements 3.3, 3.4)."""
    
    def test_standalone_module_executes_without_dependencies(self, executor, session_id, memory_manager):
        """Standalone modules should execute without dependencies."""
        # Funnel report is standalone (Module G)
        tool_call = ToolCall(
            id="call-1",
            name="create_funnel_report",
            arguments=json.dumps({
                "job_title": "Software Engineer",
                "number_of_positions": 2,
                "hiring_manager_name": "John Smith",
                "job_ad_views": 1000,
                "apply_clicks": 100,
                "applications_received": 50,
            })
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is True
        assert result.result is not None
        # Verify artifact was stored
        assert memory_manager.has_artifact(session_id, ArtifactType.FUNNEL_REPORT)
    
    def test_dependent_module_fails_without_prerequisite(self, executor):
        """Dependent modules should fail without prerequisites (Requirement 3.4)."""
        # Job ad requires requirement profile
        tool_call = ToolCall(
            id="call-1",
            name="create_job_ad",
            arguments=json.dumps({})
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is False
        assert "requirement profile" in result.error.lower()
    
    def test_ta_screening_fails_without_profile(self, executor):
        """TA screening should fail without requirement profile."""
        tool_call = ToolCall(
            id="call-1",
            name="create_ta_screening_template",
            arguments=json.dumps({})
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is False
        assert "requirement profile" in result.error.lower()
    
    def test_headhunting_fails_without_profile(self, executor):
        """Headhunting should fail without requirement profile."""
        tool_call = ToolCall(
            id="call-1",
            name="create_headhunting_messages",
            arguments=json.dumps({})
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is False
        assert "requirement profile" in result.error.lower()


class TestStandaloneModules:
    """Tests for standalone module execution."""
    
    def test_funnel_report_execution(self, executor, session_id, memory_manager):
        """Funnel report should execute and store artifact."""
        tool_call = ToolCall(
            id="call-1",
            name="create_funnel_report",
            arguments=json.dumps({
                "job_title": "Data Scientist",
                "number_of_positions": 1,
                "hiring_manager_name": "Jane Doe",
                "job_ad_views": 500,
                "applications_received": 25,
            })
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is True
        assert result.result is not None
        
        # Verify JSON is valid
        parsed = json.loads(result.result)
        assert "summary" in parsed
        assert "funnel_table" in parsed
        
        # Verify artifact stored
        assert memory_manager.has_artifact(session_id, ArtifactType.FUNNEL_REPORT)
    
    def test_calendar_invite_execution(self, executor, session_id, memory_manager):
        """Calendar invite should execute and store artifact."""
        tool_call = ToolCall(
            id="call-1",
            name="create_calendar_invite",
            arguments=json.dumps({
                "position_name": "Software Engineer",
                "hiring_manager_name": "John Smith",
                "hiring_manager_title": "Engineering Manager",
                "recruiter_name": "Sarah Johnson",
                "location_type": "teams",
                "interview_type": "hiring_manager",
                "duration": 60,
                "booking_method": "jobylon",
            })
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is True
        assert result.result is not None
        
        # Verify JSON is valid
        parsed = json.loads(result.result)
        assert "subject" in parsed
        assert "body" in parsed
        
        # Verify artifact stored
        assert memory_manager.has_artifact(session_id, ArtifactType.CALENDAR_INVITE)
    
    def test_job_ad_review_execution(self, executor, session_id, memory_manager):
        """Job ad review should execute and store artifact."""
        tool_call = ToolCall(
            id="call-1",
            name="review_job_ad",
            arguments=json.dumps({
                "job_ad_text": """
                    Senior Software Engineer
                    
                    We are looking for a talented engineer to join our team.
                    
                    Requirements:
                    - 5+ years of experience
                    - Python expertise
                    - Cloud experience
                    
                    Responsibilities:
                    - Build scalable systems
                    - Mentor junior developers
                """,
                "language": "en",
            })
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is True
        assert result.result is not None
        
        # Verify artifact stored
        assert memory_manager.has_artifact(session_id, ArtifactType.JOB_AD_REVIEW)
    
    def test_di_review_execution(self, executor, session_id, memory_manager):
        """D&I review should execute and store artifact."""
        tool_call = ToolCall(
            id="call-1",
            name="review_di_compliance",
            arguments=json.dumps({
                "job_ad_text": """
                    Software Developer
                    
                    We are looking for a rockstar developer to join our young team.
                    Must be a native English speaker.
                """,
                "language": "en",
            })
        )
        
        result = executor.execute(tool_call)
        
        assert result.success is True
        assert result.result is not None
        
        # Verify JSON is valid
        parsed = json.loads(result.result)
        assert "overall_score" in parsed
        assert "flagged_items" in parsed
        
        # Verify artifact stored
        assert memory_manager.has_artifact(session_id, ArtifactType.DI_REVIEW)


class TestToolExecutionResult:
    """Tests for ToolExecutionResult dataclass."""
    
    def test_success_result(self):
        """Success result should have success=True and result."""
        result = ToolExecutionResult(
            success=True,
            result='{"key": "value"}'
        )
        
        assert result.success is True
        assert result.result == '{"key": "value"}'
        assert result.error is None
    
    def test_failure_result(self):
        """Failure result should have success=False and error."""
        result = ToolExecutionResult(
            success=False,
            error="Something went wrong"
        )
        
        assert result.success is False
        assert result.result is None
        assert result.error == "Something went wrong"


class TestErrorMessages:
    """Tests for error message quality (Requirement 3.8)."""
    
    def test_unknown_tool_error_contains_tool_name(self, executor):
        """Unknown tool error should contain the tool name."""
        tool_call = ToolCall(
            id="call-1",
            name="nonexistent_tool",
            arguments="{}"
        )
        
        result = executor.execute(tool_call)
        
        assert "nonexistent_tool" in result.error
    
    def test_dependency_error_is_descriptive(self, executor):
        """Dependency error should describe what's missing."""
        tool_call = ToolCall(
            id="call-1",
            name="create_job_ad",
            arguments="{}"
        )
        
        result = executor.execute(tool_call)
        
        # Should mention what's required
        assert "requirement profile" in result.error.lower()
        # Should indicate it needs to be created first
        assert "first" in result.error.lower() or "required" in result.error.lower()
