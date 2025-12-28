"""Data models for OpenAI integration.

This module provides dataclasses for OpenAI API message formats, tool calls,
tool definitions, and chat completion responses.

Requirements covered:
- 2.1: Store messages in OpenAI's message format
- 3.1: Parse function name and arguments from tool calls
- 1.2: Tool definitions in JSON schema format
- 5.3: Structured response containing text content or tool calls
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import json

from src.tata.session.session import ModuleType


class MessageRole(Enum):
    """OpenAI message roles.
    
    Defines the possible roles for messages in an OpenAI conversation.
    """
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """A tool call from OpenAI.
    
    Represents a function call request from the OpenAI API,
    containing the function name and JSON-encoded arguments.
    
    Attributes:
        id: Unique identifier for this call
        name: Function name to call
        arguments: JSON string of arguments
    """
    id: str
    name: str
    arguments: str  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for OpenAI API.
        
        Returns:
            Dictionary in OpenAI tool_calls format
        """
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments
            }
        }
    
    def parse_arguments(self) -> Dict[str, Any]:
        """Parse arguments JSON to dictionary.
        
        Returns:
            Dictionary of parsed arguments
            
        Raises:
            json.JSONDecodeError: If arguments is not valid JSON
        """
        return json.loads(self.arguments)


@dataclass
class Message:
    """A conversation message.
    
    Represents a message in an OpenAI conversation, supporting all
    message types: system, user, assistant, and tool responses.
    
    Attributes:
        role: The message role (system, user, assistant, tool)
        content: Text content (None for tool calls)
        tool_calls: List of tool calls (assistant only)
        tool_call_id: ID of tool call this responds to (tool only)
        name: Tool name (tool only)
    """
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI message format.
        
        Returns:
            Dictionary in OpenAI messages array format
        """
        msg: Dict[str, Any] = {"role": self.role.value}
        
        if self.content is not None:
            msg["content"] = self.content
        
        if self.tool_calls:
            msg["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        
        if self.tool_call_id is not None:
            msg["tool_call_id"] = self.tool_call_id
        
        if self.name is not None:
            msg["name"] = self.name
        
        return msg
    
    @classmethod
    def from_openai_format(cls, data: Dict[str, Any]) -> "Message":
        """Create Message from OpenAI response format.
        
        Args:
            data: Dictionary from OpenAI API response
            
        Returns:
            Message instance with parsed data
        """
        role = MessageRole(data["role"])
        content = data.get("content")
        tool_call_id = data.get("tool_call_id")
        name = data.get("name")
        
        # Parse tool_calls if present
        tool_calls = None
        if "tool_calls" in data and data["tool_calls"]:
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"]
                )
                for tc in data["tool_calls"]
            ]
        
        return cls(
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            name=name
        )



@dataclass
class ToolDefinition:
    """OpenAI function calling tool definition.
    
    Represents a tool that can be called by OpenAI, mapping to
    a Tata module processor.
    
    Attributes:
        name: Function name (snake_case, matches processor)
        description: Human-readable description for OpenAI
        parameters: JSON Schema for function parameters
        module_type: Corresponding Tata ModuleType
    """
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    module_type: ModuleType
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI tools array format.
        
        Returns:
            Dictionary in OpenAI function calling format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class ChatCompletionResponse:
    """Response from OpenAI chat completion.
    
    Represents the parsed response from an OpenAI chat completion
    API call, containing either text content or tool calls.
    
    Attributes:
        content: Text content if no tool calls
        tool_calls: List of tool calls if any
        finish_reason: Why the response ended (stop, tool_calls, etc.)
    """
    content: Optional[str]
    tool_calls: Optional[List[ToolCall]]
    finish_reason: str
