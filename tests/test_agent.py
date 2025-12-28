"""Tests for TataAgent.

Tests the TataAgent class that orchestrates conversation flow between
the user, OpenAI API, and Tata module processors.

Requirements covered:
- 4.1: Send message plus conversation history and available tools to OpenAI
- 4.2: Return text response to user when OpenAI responds with text only
- 4.3: Execute each tool via Tool_Executor when OpenAI responds with tool calls
- 4.4: Send results back to OpenAI for natural language response generation
- 4.5: Support multiple sequential tool calls in a single conversation turn
- 4.6: Maintain session context across the conversation
- 6.1: Return user-friendly error message when OpenAI API call fails
- 6.2: Explain which prerequisites are needed when tool execution fails
- 6.3: Explain what input is required when tool execution fails
"""

import json
import pytest

from src.tata.agent.agent import TataAgent
from src.tata.agent.client import MockOpenAIClient, OpenAIAPIError
from src.tata.agent.conversation import InMemoryConversationManager
from src.tata.agent.executor import ToolExecutor
from src.tata.agent.models import (
    ChatCompletionResponse,
    Message,
    MessageRole,
    ToolCall,
)
from src.tata.agent.registry import InMemoryToolRegistry
from src.tata.dependency.dependency import InMemoryDependencyManager
from src.tata.memory.memory import InMemoryMemoryManager, ArtifactType


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
def conversation_manager():
    """Create a conversation manager."""
    return InMemoryConversationManager()


@pytest.fixture
def mock_client():
    """Create a mock OpenAI client."""
    return MockOpenAIClient()


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


@pytest.fixture
def agent(mock_client, tool_registry, executor, conversation_manager):
    """Create a TataAgent with all dependencies."""
    return TataAgent(
        openai_client=mock_client,
        tool_registry=tool_registry,
        tool_executor=executor,
        conversation_manager=conversation_manager,
    )


class TestTataAgentBasics:
    """Basic tests for TataAgent initialization and simple operations."""
    
    def test_agent_initializes(self, agent):
        """Agent should initialize with all dependencies."""
        assert agent is not None
        assert agent._client is not None
        assert agent._registry is not None
        assert agent._executor is not None
        assert agent._conversation is not None
    
    def test_text_only_response_returned(self, agent, mock_client):
        """Text-only response should be returned unchanged (Requirement 4.2)."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content="Hello! How can I help you today?",
                tool_calls=None,
                finish_reason="stop",
            )
        ])
        
        response = agent.chat("Hi there!")
        
        assert response == "Hello! How can I help you today?"
    
    def test_user_message_added_to_conversation(self, agent, mock_client, conversation_manager):
        """User message should be added to conversation history (Requirement 4.6)."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content="I can help with that.",
                tool_calls=None,
                finish_reason="stop",
            )
        ])
        
        agent.chat("I need help with recruitment")
        
        messages = conversation_manager.get_messages()
        # Should have: system prompt, user message, assistant response
        assert len(messages) >= 3
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        assert len(user_messages) == 1
        assert user_messages[0].content == "I need help with recruitment"
    
    def test_assistant_response_added_to_conversation(self, agent, mock_client, conversation_manager):
        """Assistant response should be added to conversation history."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content="I can help you create a job ad.",
                tool_calls=None,
                finish_reason="stop",
            )
        ])
        
        agent.chat("Help me write a job ad")
        
        messages = conversation_manager.get_messages()
        assistant_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]
        assert len(assistant_messages) == 1
        assert assistant_messages[0].content == "I can help you create a job ad."


class TestToolCallExecution:
    """Tests for tool call execution (Requirements 4.3, 4.4, 4.5)."""
    
    def test_single_tool_call_executed(self, agent, mock_client, memory_manager, session_id):
        """Single tool call should be executed (Requirement 4.3)."""
        # First response: tool call
        # Second response: text after tool execution
        mock_client.set_responses([
            ChatCompletionResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        name="create_funnel_report",
                        arguments=json.dumps({
                            "job_title": "Software Engineer",
                            "number_of_positions": 1,
                            "hiring_manager_name": "John Smith",
                            "job_ad_views": 100,
                            "applications_received": 50,
                        }),
                    )
                ],
                finish_reason="tool_calls",
            ),
            ChatCompletionResponse(
                content="I've created a funnel report for the Software Engineer position.",
                tool_calls=None,
                finish_reason="stop",
            ),
        ])
        
        response = agent.chat("Create a funnel report for Software Engineer")
        
        assert "funnel report" in response.lower()
        # Verify artifact was created
        assert memory_manager.has_artifact(session_id, ArtifactType.FUNNEL_REPORT)
    
    def test_tool_result_sent_back_to_openai(self, agent, mock_client, conversation_manager):
        """Tool result should be sent back to OpenAI (Requirement 4.4)."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        name="create_funnel_report",
                        arguments=json.dumps({
                            "job_title": "Data Analyst",
                            "number_of_positions": 2,
                            "hiring_manager_name": "Jane Doe",
                        }),
                    )
                ],
                finish_reason="tool_calls",
            ),
            ChatCompletionResponse(
                content="Done!",
                tool_calls=None,
                finish_reason="stop",
            ),
        ])
        
        agent.chat("Create a funnel report")
        
        # Check that tool result was added to conversation
        messages = conversation_manager.get_messages()
        tool_messages = [m for m in messages if m.role == MessageRole.TOOL]
        assert len(tool_messages) == 1
        assert tool_messages[0].tool_call_id == "call-1"
        assert tool_messages[0].name == "create_funnel_report"
    
    def test_multiple_sequential_tool_calls(self, agent, mock_client, memory_manager, session_id):
        """Multiple sequential tool calls should be supported (Requirement 4.5)."""
        mock_client.set_responses([
            # First tool call
            ChatCompletionResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        name="create_funnel_report",
                        arguments=json.dumps({
                            "job_title": "Engineer",
                            "number_of_positions": 1,
                            "hiring_manager_name": "Bob",
                            "job_ad_views": 100,
                            "applications_received": 50,
                        }),
                    )
                ],
                finish_reason="tool_calls",
            ),
            # Second tool call (after first completes)
            ChatCompletionResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-2",
                        name="create_calendar_invite",
                        arguments=json.dumps({
                            "position_name": "Engineer",
                            "hiring_manager_name": "Bob",
                            "hiring_manager_title": "Manager",
                            "recruiter_name": "Alice",
                            "location_type": "teams",
                            "interview_type": "hiring_manager",
                            "duration": 60,
                            "booking_method": "jobylon",
                        }),
                    )
                ],
                finish_reason="tool_calls",
            ),
            # Final text response
            ChatCompletionResponse(
                content="I've created both the funnel report and calendar invite.",
                tool_calls=None,
                finish_reason="stop",
            ),
        ])
        
        response = agent.chat("Create a funnel report and calendar invite")
        
        assert "created" in response.lower()
        # Both artifacts should exist
        assert memory_manager.has_artifact(session_id, ArtifactType.FUNNEL_REPORT)
        assert memory_manager.has_artifact(session_id, ArtifactType.CALENDAR_INVITE)
    
    def test_multiple_tool_calls_in_single_response(self, agent, mock_client, memory_manager, session_id):
        """Multiple tool calls in a single response should all be executed."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        name="create_funnel_report",
                        arguments=json.dumps({
                            "job_title": "Developer",
                            "number_of_positions": 1,
                            "hiring_manager_name": "Manager",
                            "job_ad_views": 100,
                            "applications_received": 50,
                        }),
                    ),
                    ToolCall(
                        id="call-2",
                        name="create_calendar_invite",
                        arguments=json.dumps({
                            "position_name": "Developer",
                            "hiring_manager_name": "Manager",
                            "hiring_manager_title": "Director",
                            "recruiter_name": "Recruiter",
                            "location_type": "teams",
                            "interview_type": "hiring_manager",
                            "duration": 60,
                            "booking_method": "jobylon",
                        }),
                    ),
                ],
                finish_reason="tool_calls",
            ),
            ChatCompletionResponse(
                content="Both tasks completed.",
                tool_calls=None,
                finish_reason="stop",
            ),
        ])
        
        response = agent.chat("Do both tasks")
        
        assert memory_manager.has_artifact(session_id, ArtifactType.FUNNEL_REPORT)
        assert memory_manager.has_artifact(session_id, ArtifactType.CALENDAR_INVITE)


class TestErrorHandling:
    """Tests for error handling (Requirements 6.1, 6.2, 6.3)."""
    
    def test_api_error_returns_user_friendly_message(self, agent, mock_client):
        """API error should return user-friendly message (Requirement 6.1)."""
        # Create a client that raises an error
        class FailingClient:
            def chat_completion(self, messages, tools=None):
                raise OpenAIAPIError("Connection failed", status_code=500)
        
        agent._client = FailingClient()
        
        response = agent.chat("Hello")
        
        # Should not expose technical details
        assert "500" not in response
        assert "Connection failed" not in response
        # Should be user-friendly
        assert "try again" in response.lower() or "trouble" in response.lower()
    
    def test_tool_execution_error_included_in_conversation(self, agent, mock_client, conversation_manager):
        """Tool execution error should be included in conversation (Requirement 6.2)."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        name="create_job_ad",  # Requires requirement profile
                        arguments=json.dumps({}),
                    )
                ],
                finish_reason="tool_calls",
            ),
            ChatCompletionResponse(
                content="I see that you need to create a requirement profile first.",
                tool_calls=None,
                finish_reason="stop",
            ),
        ])
        
        response = agent.chat("Create a job ad")
        
        # Check that error was added to conversation
        messages = conversation_manager.get_messages()
        tool_messages = [m for m in messages if m.role == MessageRole.TOOL]
        assert len(tool_messages) == 1
        assert "error" in tool_messages[0].content.lower()
        assert "requirement profile" in tool_messages[0].content.lower()
    
    def test_fallback_response_when_no_content(self, agent, mock_client):
        """Fallback response should be returned when OpenAI returns no content."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content=None,
                tool_calls=None,
                finish_reason="stop",
            )
        ])
        
        response = agent.chat("Hello")
        
        assert "apologize" in response.lower() or "try again" in response.lower()


class TestConversationManagement:
    """Tests for conversation management (Requirement 4.6)."""
    
    def test_clear_conversation(self, agent, mock_client, conversation_manager):
        """Clear conversation should reset to initial state."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content="First response",
                tool_calls=None,
                finish_reason="stop",
            ),
            ChatCompletionResponse(
                content="Second response",
                tool_calls=None,
                finish_reason="stop",
            ),
        ])
        
        agent.chat("First message")
        agent.clear_conversation()
        
        messages = conversation_manager.get_messages()
        # Should only have system prompt
        assert len(messages) == 1
        assert messages[0].role == MessageRole.SYSTEM
    
    def test_tools_sent_with_each_request(self, agent, mock_client):
        """Tools should be sent with each OpenAI request (Requirement 4.1)."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content="Response",
                tool_calls=None,
                finish_reason="stop",
            )
        ])
        
        agent.chat("Hello")
        
        # Check call history
        call_history = mock_client.get_call_history()
        assert len(call_history) == 1
        messages, tools = call_history[0]
        
        # Tools should be provided
        assert tools is not None
        assert len(tools) > 0
        # Should have all 10 Tata module tools
        tool_names = [t["function"]["name"] for t in tools]
        assert "create_requirement_profile" in tool_names
        assert "create_job_ad" in tool_names
        assert "create_funnel_report" in tool_names


class TestOpenAIClientIntegration:
    """Tests for OpenAI client integration."""
    
    def test_messages_sent_in_openai_format(self, agent, mock_client):
        """Messages should be sent in OpenAI format."""
        mock_client.set_responses([
            ChatCompletionResponse(
                content="Response",
                tool_calls=None,
                finish_reason="stop",
            )
        ])
        
        agent.chat("Test message")
        
        call_history = mock_client.get_call_history()
        messages, _ = call_history[0]
        
        # Messages should be Message objects
        assert all(isinstance(m, Message) for m in messages)
        # Should include system prompt and user message
        roles = [m.role for m in messages]
        assert MessageRole.SYSTEM in roles
        assert MessageRole.USER in roles
