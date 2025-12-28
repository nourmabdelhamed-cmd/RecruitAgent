"""Conversation management for OpenAI integration.

This module provides the ConversationManager protocol and InMemoryConversationManager
implementation for maintaining chat history and context for OpenAI API calls.

Requirements covered:
- 2.1: Store messages in OpenAI's message format
- 2.2: Initialize with system prompt describing Tata's capabilities
- 2.3: Append user messages to conversation history
- 2.4: Store assistant messages and tool results
- 2.5: Provide full message history for each OpenAI API call
- 2.6: Truncate older messages while preserving system prompt
"""

import threading
from typing import List, Protocol

from src.tata.agent.models import Message, MessageRole, ToolCall


class ConversationManager(Protocol):
    """Protocol for managing conversation history.
    
    Defines the interface for conversation management, supporting
    message storage, retrieval, and truncation while preserving
    the system prompt.
    """
    
    def get_messages(self) -> List[Message]:
        """Get all messages in conversation.
        
        Returns:
            List of all messages including system prompt
        """
        ...
    
    def add_user_message(self, content: str) -> None:
        """Add a user message.
        
        Args:
            content: The user's message text
        """
        ...
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant text response.
        
        Args:
            content: The assistant's response text
        """
        ...
    
    def add_assistant_tool_calls(self, tool_calls: List[ToolCall]) -> None:
        """Add an assistant message with tool calls.
        
        Args:
            tool_calls: List of tool calls from OpenAI
        """
        ...
    
    def add_tool_result(self, tool_call_id: str, name: str, result: str) -> None:
        """Add a tool execution result.
        
        Args:
            tool_call_id: ID of the tool call this responds to
            name: Name of the tool that was called
            result: JSON string result from tool execution
        """
        ...
    
    def clear(self) -> None:
        """Clear conversation history (keeps system prompt)."""
        ...


class InMemoryConversationManager:
    """In-memory implementation of ConversationManager.
    
    Maintains conversation history with configurable message limit.
    System prompt is always preserved during truncation.
    Thread-safe implementation using locks.
    
    Attributes:
        SYSTEM_PROMPT: Default system prompt describing Tata's capabilities
    """
    
    SYSTEM_PROMPT = """You are Tata, GlobalConnect's Talent Acquisition Team Assistant. 
You help recruiters with their recruitment workflow including:
- Creating requirement profiles for job positions
- Generating job advertisements
- Creating screening templates for interviews
- Writing headhunting messages for LinkedIn outreach
- Generating candidate and funnel reports
- Reviewing job ads for improvements
- Checking content for inclusive language

Always be helpful, professional, and focused on recruitment tasks.
When you need information to complete a task, ask the recruiter for it.
Never invent requirements or qualifications not provided by the recruiter."""

    def __init__(self, max_messages: int = 50):
        """Initialize conversation manager.
        
        Args:
            max_messages: Maximum number of messages to keep (excluding system prompt).
                         When exceeded, older messages are truncated.
        """
        self._messages: List[Message] = []
        self._max_messages = max_messages
        self._lock = threading.Lock()
        self._init_system_prompt()
    
    def _init_system_prompt(self) -> None:
        """Initialize with system prompt."""
        self._messages.append(Message(
            role=MessageRole.SYSTEM,
            content=self.SYSTEM_PROMPT
        ))
    
    def get_messages(self) -> List[Message]:
        """Get all messages in conversation.
        
        Returns:
            List of all messages including system prompt
        """
        with self._lock:
            return list(self._messages)
    
    def add_user_message(self, content: str) -> None:
        """Add a user message.
        
        Args:
            content: The user's message text
        """
        with self._lock:
            self._messages.append(Message(
                role=MessageRole.USER,
                content=content
            ))
            self._truncate_if_needed()
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant text response.
        
        Args:
            content: The assistant's response text
        """
        with self._lock:
            self._messages.append(Message(
                role=MessageRole.ASSISTANT,
                content=content
            ))
            self._truncate_if_needed()
    
    def add_assistant_tool_calls(self, tool_calls: List[ToolCall]) -> None:
        """Add an assistant message with tool calls.
        
        Args:
            tool_calls: List of tool calls from OpenAI
        """
        with self._lock:
            self._messages.append(Message(
                role=MessageRole.ASSISTANT,
                content=None,
                tool_calls=tool_calls
            ))
            self._truncate_if_needed()
    
    def add_tool_result(self, tool_call_id: str, name: str, result: str) -> None:
        """Add a tool execution result.
        
        Args:
            tool_call_id: ID of the tool call this responds to
            name: Name of the tool that was called
            result: JSON string result from tool execution
        """
        with self._lock:
            self._messages.append(Message(
                role=MessageRole.TOOL,
                content=result,
                tool_call_id=tool_call_id,
                name=name
            ))
            self._truncate_if_needed()
    
    def clear(self) -> None:
        """Clear conversation history (keeps system prompt)."""
        with self._lock:
            self._messages = []
            self._init_system_prompt()
    
    def _truncate_if_needed(self) -> None:
        """Truncate older messages if limit exceeded.
        
        Preserves the system prompt (first message) and removes
        oldest non-system messages until within limit.
        """
        # +1 accounts for the system prompt which doesn't count toward limit
        while len(self._messages) > self._max_messages + 1:
            # Remove the second message (first after system prompt)
            del self._messages[1]
