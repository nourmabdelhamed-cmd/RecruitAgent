"""Unit tests for OpenAIClient implementations.

Tests the MockOpenAIClient implementation including response configuration,
call history tracking, and thread safety. Also tests OpenAIAPIError.

Requirements covered:
- 5.1: Protocol for chat completion with tools
- 5.2: Accept model name, messages, and tools as parameters
- 5.3: Return structured response containing text content or tool calls
- 5.4: Handle API errors and raise appropriate exceptions
- 5.5: Support configuration of API key, model, and timeout
- 7.1: Mock implementations for fast unit testing
- 7.2: Agent accepts OpenAI_Client instance via dependency injection
"""

import os
import pytest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from src.tata.agent.client import (
    OpenAIAPIError,
    RealOpenAIClient,
    MockOpenAIClient,
)
from src.tata.agent.models import (
    ChatCompletionResponse,
    Message,
    MessageRole,
    ToolCall,
)


class TestOpenAIAPIError:
    """Tests for OpenAIAPIError exception."""

    def test_error_with_message_only(self):
        """Should create error with message only."""
        error = OpenAIAPIError("API call failed")
        
        assert str(error) == "API call failed"
        assert error.message == "API call failed"
        assert error.status_code is None

    def test_error_with_status_code(self):
        """Should create error with message and status code."""
        error = OpenAIAPIError("Rate limited", status_code=429)
        
        assert error.message == "Rate limited"
        assert error.status_code == 429

    def test_error_is_exception(self):
        """OpenAIAPIError should be an Exception."""
        error = OpenAIAPIError("Test error")
        
        assert isinstance(error, Exception)

    def test_error_can_be_raised_and_caught(self):
        """Should be raisable and catchable."""
        with pytest.raises(OpenAIAPIError) as exc_info:
            raise OpenAIAPIError("Test error", status_code=500)
        
        assert exc_info.value.message == "Test error"
        assert exc_info.value.status_code == 500


class TestRealOpenAIClientInit:
    """Tests for RealOpenAIClient initialization."""

    def test_raises_without_api_key(self):
        """Should raise ValueError if no API key provided."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove OPENAI_API_KEY if it exists
            os.environ.pop("OPENAI_API_KEY", None)
            
            with pytest.raises(ValueError) as exc_info:
                RealOpenAIClient()
            
            assert "API key" in str(exc_info.value)

    def test_accepts_api_key_parameter(self):
        """Should accept API key as parameter."""
        client = RealOpenAIClient(api_key="test-key-123")
        
        assert client._api_key == "test-key-123"

    def test_reads_api_key_from_env(self):
        """Should read API key from environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key-456"}):
            client = RealOpenAIClient()
            
            assert client._api_key == "env-key-456"

    def test_parameter_overrides_env(self):
        """API key parameter should override environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            client = RealOpenAIClient(api_key="param-key")
            
            assert client._api_key == "param-key"

    def test_default_model(self):
        """Should use gpt-4o as default model."""
        client = RealOpenAIClient(api_key="test-key")
        
        assert client._model == "gpt-4o"

    def test_custom_model(self):
        """Should accept custom model parameter."""
        client = RealOpenAIClient(api_key="test-key", model="gpt-3.5-turbo")
        
        assert client._model == "gpt-3.5-turbo"

    def test_default_timeout(self):
        """Should use 30.0 as default timeout."""
        client = RealOpenAIClient(api_key="test-key")
        
        assert client._timeout == 30.0

    def test_custom_timeout(self):
        """Should accept custom timeout parameter."""
        client = RealOpenAIClient(api_key="test-key", timeout=60.0)
        
        assert client._timeout == 60.0


class TestMockOpenAIClientInit:
    """Tests for MockOpenAIClient initialization."""

    def test_initializes_empty(self):
        """Should initialize with empty responses and history."""
        client = MockOpenAIClient()
        
        assert client.get_call_history() == []

    def test_no_api_key_required(self):
        """Should not require API key."""
        client = MockOpenAIClient()
        
        assert client is not None


class TestMockOpenAIClientSetResponses:
    """Tests for MockOpenAIClient.set_responses method."""

    def test_set_single_response(self):
        """Should set a single response."""
        client = MockOpenAIClient()
        response = ChatCompletionResponse(
            content="Hello!",
            tool_calls=None,
            finish_reason="stop"
        )
        
        client.set_responses([response])
        
        result = client.chat_completion([])
        assert result.content == "Hello!"

    def test_set_multiple_responses(self):
        """Should return responses in order."""
        client = MockOpenAIClient()
        responses = [
            ChatCompletionResponse(content="First", tool_calls=None, finish_reason="stop"),
            ChatCompletionResponse(content="Second", tool_calls=None, finish_reason="stop"),
        ]
        
        client.set_responses(responses)
        
        assert client.chat_completion([]).content == "First"
        assert client.chat_completion([]).content == "Second"

    def test_responses_are_consumed(self):
        """Responses should be consumed after use."""
        client = MockOpenAIClient()
        client.set_responses([
            ChatCompletionResponse(content="Only one", tool_calls=None, finish_reason="stop")
        ])
        
        client.chat_completion([])
        result = client.chat_completion([])
        
        # Should return default response after queue is empty
        assert result.content == "Mock response"


class TestMockOpenAIClientAddResponse:
    """Tests for MockOpenAIClient.add_response method."""

    def test_add_response_to_queue(self):
        """Should add response to end of queue."""
        client = MockOpenAIClient()
        client.add_response(
            ChatCompletionResponse(content="Added", tool_calls=None, finish_reason="stop")
        )
        
        result = client.chat_completion([])
        assert result.content == "Added"

    def test_add_multiple_responses(self):
        """Should add multiple responses in order."""
        client = MockOpenAIClient()
        client.add_response(
            ChatCompletionResponse(content="First", tool_calls=None, finish_reason="stop")
        )
        client.add_response(
            ChatCompletionResponse(content="Second", tool_calls=None, finish_reason="stop")
        )
        
        assert client.chat_completion([]).content == "First"
        assert client.chat_completion([]).content == "Second"


class TestMockOpenAIClientChatCompletion:
    """Tests for MockOpenAIClient.chat_completion method."""

    def test_returns_default_response_when_empty(self):
        """Should return default response when no responses configured."""
        client = MockOpenAIClient()
        
        result = client.chat_completion([])
        
        assert result.content == "Mock response"
        assert result.tool_calls is None
        assert result.finish_reason == "stop"

    def test_returns_configured_response(self):
        """Should return configured response."""
        client = MockOpenAIClient()
        client.set_responses([
            ChatCompletionResponse(
                content="Configured response",
                tool_calls=None,
                finish_reason="stop"
            )
        ])
        
        result = client.chat_completion([])
        
        assert result.content == "Configured response"

    def test_returns_response_with_tool_calls(self):
        """Should return response with tool calls."""
        client = MockOpenAIClient()
        tool_call = ToolCall(
            id="call_123",
            name="test_tool",
            arguments='{"arg": "value"}'
        )
        client.set_responses([
            ChatCompletionResponse(
                content=None,
                tool_calls=[tool_call],
                finish_reason="tool_calls"
            )
        ])
        
        result = client.chat_completion([])
        
        assert result.content is None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "test_tool"
        assert result.finish_reason == "tool_calls"


class TestMockOpenAIClientCallHistory:
    """Tests for MockOpenAIClient call history tracking."""

    def test_records_messages(self):
        """Should record messages in call history."""
        client = MockOpenAIClient()
        messages = [
            Message(role=MessageRole.USER, content="Hello")
        ]
        
        client.chat_completion(messages)
        
        history = client.get_call_history()
        assert len(history) == 1
        assert len(history[0][0]) == 1
        assert history[0][0][0].content == "Hello"

    def test_records_tools(self):
        """Should record tools in call history."""
        client = MockOpenAIClient()
        tools = [{"type": "function", "function": {"name": "test"}}]
        
        client.chat_completion([], tools=tools)
        
        history = client.get_call_history()
        assert history[0][1] == tools

    def test_records_none_tools(self):
        """Should record None when no tools provided."""
        client = MockOpenAIClient()
        
        client.chat_completion([])
        
        history = client.get_call_history()
        assert history[0][1] is None

    def test_records_multiple_calls(self):
        """Should record all calls in order."""
        client = MockOpenAIClient()
        
        client.chat_completion([Message(role=MessageRole.USER, content="First")])
        client.chat_completion([Message(role=MessageRole.USER, content="Second")])
        
        history = client.get_call_history()
        assert len(history) == 2
        assert history[0][0][0].content == "First"
        assert history[1][0][0].content == "Second"

    def test_clear_history(self):
        """Should clear call history."""
        client = MockOpenAIClient()
        client.chat_completion([])
        
        client.clear_history()
        
        assert client.get_call_history() == []

    def test_get_history_returns_copy(self):
        """get_call_history should return a copy."""
        client = MockOpenAIClient()
        client.chat_completion([])
        
        history1 = client.get_call_history()
        history2 = client.get_call_history()
        
        assert history1 is not history2


class TestMockOpenAIClientThreadSafety:
    """Tests for MockOpenAIClient thread safety."""

    def test_concurrent_chat_completions(self):
        """Should handle concurrent chat completions safely."""
        client = MockOpenAIClient()
        
        # Pre-populate with enough responses
        for i in range(50):
            client.add_response(
                ChatCompletionResponse(
                    content=f"Response {i}",
                    tool_calls=None,
                    finish_reason="stop"
                )
            )
        
        def make_call(thread_id: int):
            for i in range(10):
                client.chat_completion([
                    Message(role=MessageRole.USER, content=f"Thread {thread_id} Call {i}")
                ])
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_call, i) for i in range(5)]
            for f in futures:
                f.result()
        
        history = client.get_call_history()
        assert len(history) == 50


class TestMockOpenAIClientIntegration:
    """Integration tests for MockOpenAIClient usage patterns."""

    def test_simulates_text_response_flow(self):
        """Should simulate a text response conversation."""
        client = MockOpenAIClient()
        client.set_responses([
            ChatCompletionResponse(
                content="I can help you create a job posting.",
                tool_calls=None,
                finish_reason="stop"
            )
        ])
        
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are Tata."),
            Message(role=MessageRole.USER, content="I need to hire a developer."),
        ]
        
        result = client.chat_completion(messages)
        
        assert "job posting" in result.content
        assert result.tool_calls is None

    def test_simulates_tool_call_flow(self):
        """Should simulate a tool call conversation."""
        client = MockOpenAIClient()
        
        # First response: tool call
        client.add_response(ChatCompletionResponse(
            content=None,
            tool_calls=[ToolCall(
                id="call_abc",
                name="create_requirement_profile",
                arguments='{"position_title": "Developer"}'
            )],
            finish_reason="tool_calls"
        ))
        
        # Second response: text after tool result
        client.add_response(ChatCompletionResponse(
            content="I've created the requirement profile.",
            tool_calls=None,
            finish_reason="stop"
        ))
        
        # First call - should get tool call
        result1 = client.chat_completion([
            Message(role=MessageRole.USER, content="Create a profile")
        ])
        assert result1.tool_calls is not None
        assert result1.tool_calls[0].name == "create_requirement_profile"
        
        # Second call - should get text response
        result2 = client.chat_completion([
            Message(role=MessageRole.TOOL, content='{"id": "123"}', tool_call_id="call_abc")
        ])
        assert result2.content == "I've created the requirement profile."
