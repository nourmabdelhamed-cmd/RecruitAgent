"""Unit tests for OpenAI integration data models."""

import pytest
import json

from src.tata.agent.models import (
    MessageRole,
    Message,
    ToolCall,
    ToolDefinition,
    ChatCompletionResponse,
)
from src.tata.session.session import ModuleType


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_all_roles_defined(self):
        """All OpenAI message roles should be defined."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"


class TestToolCall:
    """Tests for ToolCall dataclass."""

    def test_to_dict_format(self):
        """to_dict should return OpenAI tool_calls format."""
        tool_call = ToolCall(
            id="call_123",
            name="create_requirement_profile",
            arguments='{"position_title": "Python Developer"}'
        )
        
        result = tool_call.to_dict()
        
        assert result == {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "create_requirement_profile",
                "arguments": '{"position_title": "Python Developer"}'
            }
        }

    def test_parse_arguments_valid_json(self):
        """parse_arguments should parse valid JSON arguments."""
        tool_call = ToolCall(
            id="call_123",
            name="create_job_ad",
            arguments='{"tone": "formal", "include_salary": true}'
        )
        
        result = tool_call.parse_arguments()
        
        assert result == {"tone": "formal", "include_salary": True}

    def test_parse_arguments_empty_object(self):
        """parse_arguments should handle empty JSON object."""
        tool_call = ToolCall(
            id="call_123",
            name="some_tool",
            arguments='{}'
        )
        
        result = tool_call.parse_arguments()
        
        assert result == {}

    def test_parse_arguments_invalid_json_raises(self):
        """parse_arguments should raise JSONDecodeError for invalid JSON."""
        tool_call = ToolCall(
            id="call_123",
            name="some_tool",
            arguments='not valid json'
        )
        
        with pytest.raises(json.JSONDecodeError):
            tool_call.parse_arguments()


class TestMessage:
    """Tests for Message dataclass."""

    def test_system_message_to_openai_format(self):
        """System message should convert to correct format."""
        msg = Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant."
        )
        
        result = msg.to_openai_format()
        
        assert result == {
            "role": "system",
            "content": "You are a helpful assistant."
        }

    def test_user_message_to_openai_format(self):
        """User message should convert to correct format."""
        msg = Message(
            role=MessageRole.USER,
            content="Hello, I need help."
        )
        
        result = msg.to_openai_format()
        
        assert result == {
            "role": "user",
            "content": "Hello, I need help."
        }

    def test_assistant_message_to_openai_format(self):
        """Assistant text message should convert to correct format."""
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="I can help you with that."
        )
        
        result = msg.to_openai_format()
        
        assert result == {
            "role": "assistant",
            "content": "I can help you with that."
        }

    def test_assistant_tool_calls_to_openai_format(self):
        """Assistant message with tool calls should convert correctly."""
        tool_call = ToolCall(
            id="call_abc",
            name="create_profile",
            arguments='{"title": "Developer"}'
        )
        msg = Message(
            role=MessageRole.ASSISTANT,
            content=None,
            tool_calls=[tool_call]
        )
        
        result = msg.to_openai_format()
        
        assert result["role"] == "assistant"
        assert "content" not in result
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["id"] == "call_abc"

    def test_tool_result_message_to_openai_format(self):
        """Tool result message should convert to correct format."""
        msg = Message(
            role=MessageRole.TOOL,
            content='{"result": "success"}',
            tool_call_id="call_abc",
            name="create_profile"
        )
        
        result = msg.to_openai_format()
        
        assert result == {
            "role": "tool",
            "content": '{"result": "success"}',
            "tool_call_id": "call_abc",
            "name": "create_profile"
        }

    def test_from_openai_format_user_message(self):
        """from_openai_format should parse user message."""
        data = {
            "role": "user",
            "content": "Hello"
        }
        
        msg = Message.from_openai_format(data)
        
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.tool_calls is None

    def test_from_openai_format_assistant_with_tool_calls(self):
        """from_openai_format should parse assistant message with tool calls."""
        data = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_xyz",
                    "type": "function",
                    "function": {
                        "name": "create_job_ad",
                        "arguments": '{"tone": "casual"}'
                    }
                }
            ]
        }
        
        msg = Message.from_openai_format(data)
        
        assert msg.role == MessageRole.ASSISTANT
        assert msg.content is None
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].id == "call_xyz"
        assert msg.tool_calls[0].name == "create_job_ad"
        assert msg.tool_calls[0].arguments == '{"tone": "casual"}'

    def test_from_openai_format_tool_result(self):
        """from_openai_format should parse tool result message."""
        data = {
            "role": "tool",
            "content": '{"status": "ok"}',
            "tool_call_id": "call_xyz",
            "name": "create_job_ad"
        }
        
        msg = Message.from_openai_format(data)
        
        assert msg.role == MessageRole.TOOL
        assert msg.content == '{"status": "ok"}'
        assert msg.tool_call_id == "call_xyz"
        assert msg.name == "create_job_ad"

    def test_round_trip_user_message(self):
        """User message should survive round-trip conversion."""
        original = Message(
            role=MessageRole.USER,
            content="Test message"
        )
        
        openai_format = original.to_openai_format()
        restored = Message.from_openai_format(openai_format)
        
        assert restored.role == original.role
        assert restored.content == original.content

    def test_round_trip_assistant_with_tool_calls(self):
        """Assistant message with tool calls should survive round-trip."""
        tool_call = ToolCall(
            id="call_test",
            name="test_tool",
            arguments='{"key": "value"}'
        )
        original = Message(
            role=MessageRole.ASSISTANT,
            content=None,
            tool_calls=[tool_call]
        )
        
        openai_format = original.to_openai_format()
        restored = Message.from_openai_format(openai_format)
        
        assert restored.role == original.role
        assert restored.content == original.content
        assert len(restored.tool_calls) == 1
        assert restored.tool_calls[0].id == tool_call.id
        assert restored.tool_calls[0].name == tool_call.name
        assert restored.tool_calls[0].arguments == tool_call.arguments


class TestToolDefinition:
    """Tests for ToolDefinition dataclass."""

    def test_to_openai_format(self):
        """to_openai_format should return correct structure."""
        tool = ToolDefinition(
            name="create_requirement_profile",
            description="Create a requirement profile for a job position",
            parameters={
                "type": "object",
                "properties": {
                    "position_title": {
                        "type": "string",
                        "description": "The job position title"
                    }
                },
                "required": ["position_title"]
            },
            module_type=ModuleType.REQUIREMENT_PROFILE
        )
        
        result = tool.to_openai_format()
        
        assert result == {
            "type": "function",
            "function": {
                "name": "create_requirement_profile",
                "description": "Create a requirement profile for a job position",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "position_title": {
                            "type": "string",
                            "description": "The job position title"
                        }
                    },
                    "required": ["position_title"]
                }
            }
        }

    def test_to_openai_format_has_required_fields(self):
        """to_openai_format should include all required OpenAI fields."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            module_type=ModuleType.JOB_AD
        )
        
        result = tool.to_openai_format()
        
        assert result["type"] == "function"
        assert "function" in result
        assert "name" in result["function"]
        assert "description" in result["function"]
        assert "parameters" in result["function"]


class TestChatCompletionResponse:
    """Tests for ChatCompletionResponse dataclass."""

    def test_text_response(self):
        """ChatCompletionResponse should hold text content."""
        response = ChatCompletionResponse(
            content="Here is my response.",
            tool_calls=None,
            finish_reason="stop"
        )
        
        assert response.content == "Here is my response."
        assert response.tool_calls is None
        assert response.finish_reason == "stop"

    def test_tool_calls_response(self):
        """ChatCompletionResponse should hold tool calls."""
        tool_call = ToolCall(
            id="call_123",
            name="create_profile",
            arguments='{}'
        )
        response = ChatCompletionResponse(
            content=None,
            tool_calls=[tool_call],
            finish_reason="tool_calls"
        )
        
        assert response.content is None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "create_profile"
        assert response.finish_reason == "tool_calls"
