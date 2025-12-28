"""Unit tests for ConversationManager.

Tests the InMemoryConversationManager implementation including
message management, system prompt initialization, and truncation.

Requirements covered:
- 2.1: Store messages in OpenAI's message format
- 2.2: Initialize with system prompt
- 2.3: Append user messages to conversation history
- 2.4: Store assistant messages and tool results
- 2.5: Provide full message history
- 2.6: Truncate older messages while preserving system prompt
"""

import pytest
import threading
from concurrent.futures import ThreadPoolExecutor

from src.tata.agent.conversation import (
    ConversationManager,
    InMemoryConversationManager,
)
from src.tata.agent.models import Message, MessageRole, ToolCall


class TestInMemoryConversationManagerInit:
    """Tests for ConversationManager initialization."""

    def test_initializes_with_system_prompt(self):
        """New conversation should start with system prompt."""
        manager = InMemoryConversationManager()
        
        messages = manager.get_messages()
        
        assert len(messages) == 1
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content is not None
        assert "Tata" in messages[0].content

    def test_system_prompt_describes_capabilities(self):
        """System prompt should describe Tata's capabilities."""
        manager = InMemoryConversationManager()
        
        messages = manager.get_messages()
        system_content = messages[0].content
        
        # Should mention key capabilities
        assert "requirement profile" in system_content.lower()
        assert "job advertisement" in system_content.lower()
        assert "screening" in system_content.lower()

    def test_custom_max_messages(self):
        """Should accept custom max_messages parameter."""
        manager = InMemoryConversationManager(max_messages=10)
        
        # Add more than 10 messages
        for i in range(15):
            manager.add_user_message(f"Message {i}")
        
        messages = manager.get_messages()
        # Should have system prompt + 10 messages
        assert len(messages) == 11


class TestAddUserMessage:
    """Tests for add_user_message method."""

    def test_adds_user_message(self):
        """add_user_message should append user message."""
        manager = InMemoryConversationManager()
        
        manager.add_user_message("Hello, I need help hiring.")
        
        messages = manager.get_messages()
        assert len(messages) == 2
        assert messages[1].role == MessageRole.USER
        assert messages[1].content == "Hello, I need help hiring."

    def test_multiple_user_messages(self):
        """Should handle multiple user messages."""
        manager = InMemoryConversationManager()
        
        manager.add_user_message("First message")
        manager.add_user_message("Second message")
        
        messages = manager.get_messages()
        assert len(messages) == 3
        assert messages[1].content == "First message"
        assert messages[2].content == "Second message"


class TestAddAssistantMessage:
    """Tests for add_assistant_message method."""

    def test_adds_assistant_message(self):
        """add_assistant_message should append assistant message."""
        manager = InMemoryConversationManager()
        
        manager.add_assistant_message("I can help you with that.")
        
        messages = manager.get_messages()
        assert len(messages) == 2
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == "I can help you with that."


class TestAddAssistantToolCalls:
    """Tests for add_assistant_tool_calls method."""

    def test_adds_tool_calls_message(self):
        """add_assistant_tool_calls should append message with tool calls."""
        manager = InMemoryConversationManager()
        tool_call = ToolCall(
            id="call_123",
            name="create_requirement_profile",
            arguments='{"position_title": "Developer"}'
        )
        
        manager.add_assistant_tool_calls([tool_call])
        
        messages = manager.get_messages()
        assert len(messages) == 2
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content is None
        assert len(messages[1].tool_calls) == 1
        assert messages[1].tool_calls[0].name == "create_requirement_profile"

    def test_multiple_tool_calls(self):
        """Should handle multiple tool calls in one message."""
        manager = InMemoryConversationManager()
        tool_calls = [
            ToolCall(id="call_1", name="tool_a", arguments='{}'),
            ToolCall(id="call_2", name="tool_b", arguments='{}'),
        ]
        
        manager.add_assistant_tool_calls(tool_calls)
        
        messages = manager.get_messages()
        assert len(messages[1].tool_calls) == 2


class TestAddToolResult:
    """Tests for add_tool_result method."""

    def test_adds_tool_result(self):
        """add_tool_result should append tool result message."""
        manager = InMemoryConversationManager()
        
        manager.add_tool_result(
            tool_call_id="call_123",
            name="create_requirement_profile",
            result='{"status": "success"}'
        )
        
        messages = manager.get_messages()
        assert len(messages) == 2
        assert messages[1].role == MessageRole.TOOL
        assert messages[1].content == '{"status": "success"}'
        assert messages[1].tool_call_id == "call_123"
        assert messages[1].name == "create_requirement_profile"


class TestGetMessages:
    """Tests for get_messages method."""

    def test_returns_copy(self):
        """get_messages should return a copy, not the internal list."""
        manager = InMemoryConversationManager()
        
        messages1 = manager.get_messages()
        messages2 = manager.get_messages()
        
        assert messages1 is not messages2

    def test_preserves_message_order(self):
        """Messages should be returned in order added."""
        manager = InMemoryConversationManager()
        
        manager.add_user_message("User 1")
        manager.add_assistant_message("Assistant 1")
        manager.add_user_message("User 2")
        
        messages = manager.get_messages()
        
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[1].content == "User 1"
        assert messages[2].content == "Assistant 1"
        assert messages[3].content == "User 2"


class TestClear:
    """Tests for clear method."""

    def test_clears_conversation(self):
        """clear should remove all messages except system prompt."""
        manager = InMemoryConversationManager()
        manager.add_user_message("Hello")
        manager.add_assistant_message("Hi there")
        
        manager.clear()
        
        messages = manager.get_messages()
        assert len(messages) == 1
        assert messages[0].role == MessageRole.SYSTEM

    def test_preserves_system_prompt_after_clear(self):
        """System prompt should be preserved after clear."""
        manager = InMemoryConversationManager()
        original_prompt = manager.get_messages()[0].content
        
        manager.add_user_message("Test")
        manager.clear()
        
        messages = manager.get_messages()
        assert messages[0].content == original_prompt


class TestTruncation:
    """Tests for message truncation."""

    def test_truncates_when_exceeds_limit(self):
        """Should truncate oldest messages when limit exceeded."""
        manager = InMemoryConversationManager(max_messages=3)
        
        manager.add_user_message("Message 1")
        manager.add_user_message("Message 2")
        manager.add_user_message("Message 3")
        manager.add_user_message("Message 4")
        
        messages = manager.get_messages()
        # System prompt + 3 messages
        assert len(messages) == 4
        # Oldest non-system message should be removed
        assert messages[1].content == "Message 2"
        assert messages[3].content == "Message 4"

    def test_preserves_system_prompt_during_truncation(self):
        """System prompt should never be truncated."""
        manager = InMemoryConversationManager(max_messages=2)
        
        for i in range(10):
            manager.add_user_message(f"Message {i}")
        
        messages = manager.get_messages()
        assert messages[0].role == MessageRole.SYSTEM
        assert "Tata" in messages[0].content


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_message_addition(self):
        """Should handle concurrent message additions safely."""
        manager = InMemoryConversationManager(max_messages=100)
        
        def add_messages(thread_id: int):
            for i in range(10):
                manager.add_user_message(f"Thread {thread_id} Message {i}")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(add_messages, i) for i in range(5)]
            for f in futures:
                f.result()
        
        messages = manager.get_messages()
        # System prompt + 50 messages
        assert len(messages) == 51


class TestConversationFlow:
    """Tests for realistic conversation flows."""

    def test_typical_conversation_flow(self):
        """Should handle typical user-assistant-tool flow."""
        manager = InMemoryConversationManager()
        
        # User asks for help
        manager.add_user_message("I need to hire a Python developer")
        
        # Assistant calls a tool
        tool_call = ToolCall(
            id="call_abc",
            name="create_requirement_profile",
            arguments='{"position_title": "Python Developer"}'
        )
        manager.add_assistant_tool_calls([tool_call])
        
        # Tool returns result
        manager.add_tool_result(
            tool_call_id="call_abc",
            name="create_requirement_profile",
            result='{"profile_id": "123"}'
        )
        
        # Assistant responds with summary
        manager.add_assistant_message("I've created a requirement profile for you.")
        
        messages = manager.get_messages()
        assert len(messages) == 5
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[1].role == MessageRole.USER
        assert messages[2].role == MessageRole.ASSISTANT
        assert messages[3].role == MessageRole.TOOL
        assert messages[4].role == MessageRole.ASSISTANT
