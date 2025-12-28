"""OpenAI client abstraction for Tata agent.

This module provides the OpenAIClient protocol and implementations for
interacting with the OpenAI API, including a real client for production
and a mock client for testing.

Requirements covered:
- 5.1: Protocol for chat completion with tools
- 5.2: Accept model name, messages, and tools as parameters
- 5.3: Return structured response containing text content or tool calls
- 5.4: Handle API errors and raise appropriate exceptions
- 5.5: Support configuration of API key, model, and timeout
"""

import os
import threading
from typing import Any, Dict, List, Optional, Protocol, Tuple

from openai import OpenAI

from src.tata.agent.models import (
    ChatCompletionResponse,
    Message,
    ToolCall,
)


class OpenAIAPIError(Exception):
    """Raised when OpenAI API call fails.
    
    Attributes:
        message: Error message describing the failure
        status_code: HTTP status code if available
    """
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize OpenAI API error.
        
        Args:
            message: Error message from API or describing the failure
            status_code: HTTP status code if available
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OpenAIClient(Protocol):
    """Protocol for OpenAI API interactions.
    
    Defines the interface for chat completion with function calling support.
    Implementations can be swapped for testing or different providers.
    """
    
    def chat_completion(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatCompletionResponse:
        """Send chat completion request.
        
        Args:
            messages: Conversation history as Message objects
            tools: Available tools in OpenAI format (optional)
            
        Returns:
            ChatCompletionResponse with content or tool calls
            
        Raises:
            OpenAIAPIError: If API call fails
        """
        ...


class RealOpenAIClient:
    """Production implementation using OpenAI SDK.
    
    Reads API key from OPENAI_API_KEY environment variable if not provided.
    Thread-safe implementation.
    
    Attributes:
        model: The OpenAI model to use (default: gpt-4o)
    """
    
    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """Initialize the OpenAI client.
        
        Args:
            model: OpenAI model name (default: gpt-4o)
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var
            timeout: Request timeout in seconds (default: 30.0)
            
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._timeout = timeout
        
        if not self._api_key:
            raise ValueError(
                "OpenAI API key must be provided or set in OPENAI_API_KEY environment variable"
            )
        
        self._client = OpenAI(api_key=self._api_key, timeout=timeout)
        self._lock = threading.Lock()
    
    def chat_completion(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatCompletionResponse:
        """Send chat completion request to OpenAI.
        
        Args:
            messages: Conversation history as Message objects
            tools: Available tools in OpenAI format (optional)
            
        Returns:
            ChatCompletionResponse with content or tool calls
            
        Raises:
            OpenAIAPIError: If API call fails
        """
        try:
            with self._lock:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[m.to_openai_format() for m in messages],
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else None,
                )
            
            choice = response.choices[0]
            message = choice.message
            
            # Parse tool calls if present
            tool_calls = None
            if message.tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=tc.function.arguments
                    )
                    for tc in message.tool_calls
                ]
            
            return ChatCompletionResponse(
                content=message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop"
            )
            
        except Exception as e:
            # Extract status code if available from OpenAI exceptions
            status_code = None
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            raise OpenAIAPIError(f"OpenAI API call failed: {e}", status_code) from e


class MockOpenAIClient:
    """Mock implementation for testing.
    
    Allows configuring predetermined responses for testing
    without making real API calls. Thread-safe implementation.
    
    Tracks all calls made for verification in tests.
    """
    
    def __init__(self):
        """Initialize mock client with empty response queue."""
        self._responses: List[ChatCompletionResponse] = []
        self._call_history: List[Tuple[List[Message], Optional[List[Dict[str, Any]]]]] = []
        self._lock = threading.Lock()
    
    def set_responses(self, responses: List[ChatCompletionResponse]) -> None:
        """Set responses to return in order.
        
        Args:
            responses: List of responses to return for subsequent calls.
                      Responses are consumed in order (FIFO).
        """
        with self._lock:
            self._responses = list(responses)
    
    def add_response(self, response: ChatCompletionResponse) -> None:
        """Add a single response to the queue.
        
        Args:
            response: Response to add to the end of the queue
        """
        with self._lock:
            self._responses.append(response)
    
    def get_call_history(self) -> List[Tuple[List[Message], Optional[List[Dict[str, Any]]]]]:
        """Get history of all calls made to this client.
        
        Returns:
            List of (messages, tools) tuples for each call
        """
        with self._lock:
            return list(self._call_history)
    
    def clear_history(self) -> None:
        """Clear the call history."""
        with self._lock:
            self._call_history = []
    
    def chat_completion(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatCompletionResponse:
        """Return next configured response.
        
        Records the call in history and returns the next queued response.
        If no responses are queued, returns a default mock response.
        
        Args:
            messages: Conversation history (recorded in history)
            tools: Available tools (recorded in history)
            
        Returns:
            Next queued ChatCompletionResponse or default mock response
        """
        with self._lock:
            # Record the call
            self._call_history.append((list(messages), tools))
            
            # Return next response or default
            if self._responses:
                return self._responses.pop(0)
            
            return ChatCompletionResponse(
                content="Mock response",
                tool_calls=None,
                finish_reason="stop"
            )
