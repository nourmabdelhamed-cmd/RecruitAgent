"""OpenAI integration agent for Tata.

This module provides the agent orchestration layer that integrates OpenAI's
function calling API with Tata's existing module processors.

Components:
    - TataAgent: Main orchestration class for conversation flow
    - ToolRegistry: Maps Tata modules to OpenAI tool definitions
    - ConversationManager: Maintains chat history and context
    - ToolExecutor: Routes tool calls to Tata processors
    - OpenAIClient: Abstraction over OpenAI API

Requirements covered: 5.5, 7.7
"""

from src.tata.agent.models import (
    MessageRole,
    Message,
    ToolCall,
    ToolDefinition,
    ChatCompletionResponse,
)
from src.tata.agent.registry import (
    ToolRegistry,
    InMemoryToolRegistry,
)
from src.tata.agent.conversation import (
    ConversationManager,
    InMemoryConversationManager,
)
from src.tata.agent.client import (
    OpenAIAPIError,
    OpenAIClient,
    RealOpenAIClient,
    MockOpenAIClient,
)
from src.tata.agent.executor import (
    ToolExecutor,
    ToolExecutionResult,
)
from src.tata.agent.agent import TataAgent

__all__ = [
    "MessageRole",
    "Message",
    "ToolCall",
    "ToolDefinition",
    "ChatCompletionResponse",
    "ToolRegistry",
    "InMemoryToolRegistry",
    "ConversationManager",
    "InMemoryConversationManager",
    "OpenAIAPIError",
    "OpenAIClient",
    "RealOpenAIClient",
    "MockOpenAIClient",
    "ToolExecutor",
    "ToolExecutionResult",
    "TataAgent",
]
