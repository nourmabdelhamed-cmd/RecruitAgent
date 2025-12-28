"""TataAgent orchestration for OpenAI function calling integration.

This module provides the TataAgent class that orchestrates conversation flow
between the user, OpenAI API, and Tata module processors.

Requirements covered:
- 4.1: Send message plus conversation history and available tools to OpenAI
- 4.2: Return text response to user when OpenAI responds with text only
- 4.3: Execute each tool via Tool_Executor when OpenAI responds with tool calls
- 4.4: Send results back to OpenAI for natural language response generation
- 4.5: Support multiple sequential tool calls in a single conversation turn
- 4.6: Maintain session context across the conversation
- 6.1: Return user-friendly error message when OpenAI API call fails
- 6.2: Explain which prerequisites are needed when tool execution fails due to missing dependencies
- 6.3: Explain what input is required when tool execution fails due to invalid input
- 6.4: Relay validation message when tool execution fails due to validation errors
"""

import logging
from typing import Optional

from src.tata.agent.client import OpenAIClient, OpenAIAPIError
from src.tata.agent.conversation import ConversationManager
from src.tata.agent.executor import ToolExecutor
from src.tata.agent.registry import ToolRegistry


# Configure module logger
logger = logging.getLogger(__name__)


class TataAgent:
    """Main agent orchestrating conversation with OpenAI.
    
    Manages the conversation loop, tool execution, and response generation
    for natural language recruitment assistance.
    
    Attributes:
        _client: OpenAI client for API calls
        _registry: Tool registry for available tools
        _executor: Tool executor for running Tata processors
        _conversation: Conversation manager for message history
    """
    
    def __init__(
        self,
        openai_client: OpenAIClient,
        tool_registry: ToolRegistry,
        tool_executor: ToolExecutor,
        conversation_manager: ConversationManager,
    ) -> None:
        """Initialize the TataAgent.
        
        Args:
            openai_client: Client for OpenAI API interactions
            tool_registry: Registry of available tools
            tool_executor: Executor for tool calls
            conversation_manager: Manager for conversation history
        """
        self._client = openai_client
        self._registry = tool_registry
        self._executor = tool_executor
        self._conversation = conversation_manager
    
    def chat(self, user_message: str) -> str:
        """Process a user message and return response.
        
        Handles the full conversation loop including:
        - Adding user message to history
        - Calling OpenAI with tools
        - Executing tool calls if any
        - Returning final text response
        
        Args:
            user_message: The user's input message
            
        Returns:
            Natural language response from the agent
        """
        # Add user message to history (Requirement 4.6)
        self._conversation.add_user_message(user_message)
        
        # Get available tools in OpenAI format
        tools = self._registry.get_openai_tools()
        
        try:
            # Call OpenAI (Requirement 4.1)
            response = self._client.chat_completion(
                messages=self._conversation.get_messages(),
                tools=tools,
            )
        except OpenAIAPIError as e:
            # Log full error details for debugging (Requirement 6.5)
            logger.error(f"OpenAI API error: {e.message}", exc_info=True)
            # Return user-friendly message (Requirement 6.1)
            return self._format_api_error()
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}", exc_info=True)
            return self._format_api_error()
        
        # Handle tool calls if any (Requirement 4.3, 4.5)
        while response.tool_calls:
            # Store assistant's tool call message
            self._conversation.add_assistant_tool_calls(response.tool_calls)
            
            # Execute each tool
            for tool_call in response.tool_calls:
                result = self._executor.execute(tool_call)
                
                # Format result content
                if result.success:
                    result_content = result.result or "{}"
                else:
                    # Format error message (Requirements 6.2, 6.3, 6.4)
                    result_content = f"Error: {result.error}"
                    logger.warning(
                        f"Tool execution failed: {tool_call.name} - {result.error}"
                    )
                
                # Add result to conversation (Requirement 4.4)
                self._conversation.add_tool_result(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    result=result_content,
                )
            
            # Get next response from OpenAI
            try:
                response = self._client.chat_completion(
                    messages=self._conversation.get_messages(),
                    tools=tools,
                )
            except OpenAIAPIError as e:
                logger.error(f"OpenAI API error during tool loop: {e.message}", exc_info=True)
                return self._format_api_error()
            except Exception as e:
                logger.error(f"Unexpected error during tool loop: {e}", exc_info=True)
                return self._format_api_error()
        
        # Handle text-only response (Requirement 4.2)
        if response.content:
            self._conversation.add_assistant_message(response.content)
            return response.content
        
        # Fallback if no content
        fallback_message = (
            "I apologize, but I couldn't generate a response. Please try again."
        )
        self._conversation.add_assistant_message(fallback_message)
        return fallback_message
    
    def clear_conversation(self) -> None:
        """Clear the conversation history.
        
        Resets the conversation to initial state with only the system prompt.
        """
        self._conversation.clear()
    
    def _format_api_error(self) -> str:
        """Format a user-friendly API error message.
        
        Returns:
            User-friendly error message without technical details
        """
        return (
            "I'm having trouble connecting to my language service right now. "
            "Please try again in a moment."
        )
