# Requirements Document

## Introduction

This specification defines the integration of OpenAI's function calling API with Tata, GlobalConnect's Talent Acquisition Team Assistant. The integration enables natural language conversation where OpenAI determines user intent and routes requests to appropriate Tata module processors, while Tata handles all business logic, artifact storage, and content validation.

## Glossary

- **Agent**: The orchestration layer that manages conversation flow between user, OpenAI API, and Tata processors
- **Tool**: An OpenAI function definition that maps to a Tata module processor
- **Tool_Registry**: Component that maintains the mapping between OpenAI tools and Tata processors
- **Conversation_Manager**: Component that maintains chat history and context for OpenAI API calls
- **Tool_Executor**: Component that routes OpenAI tool calls to appropriate Tata processors
- **OpenAI_Client**: Wrapper around OpenAI API for chat completions with function calling
- **Session**: A recruitment project context with persistent artifacts (existing Tata concept)
- **Artifact**: A generated output from a module processor (existing Tata concept)

## Requirements

### Requirement 1: Tool Registry

**User Story:** As a developer, I want a registry that maps Tata modules to OpenAI tool definitions, so that the agent knows which tools are available and how to call them.

#### Acceptance Criteria

1. THE Tool_Registry SHALL provide OpenAI-compatible tool definitions for all Tata modules (RequirementProfile, JobAd, TAScreening, HMScreening, Headhunting, CandidateReport, FunnelReport, JobAdReview, DIReview, CalendarInvite)
2. WHEN a tool definition is requested, THE Tool_Registry SHALL return a JSON schema matching OpenAI's function calling format with name, description, and parameters
3. THE Tool_Registry SHALL derive parameter schemas from existing module input dataclasses
4. WHEN a module has dependencies, THE Tool_Registry SHALL include dependency information in the tool description
5. THE Tool_Registry SHALL provide a method to retrieve all tools as a list for OpenAI API calls

### Requirement 2: Conversation Manager

**User Story:** As a developer, I want to maintain conversation history, so that OpenAI has context for multi-turn conversations.

#### Acceptance Criteria

1. THE Conversation_Manager SHALL store messages in OpenAI's message format (role: system/user/assistant/tool, content)
2. WHEN a new conversation starts, THE Conversation_Manager SHALL initialize with a system prompt describing Tata's capabilities
3. WHEN a user message is received, THE Conversation_Manager SHALL append it to the conversation history
4. WHEN OpenAI responds with a tool call, THE Conversation_Manager SHALL store both the assistant message and the tool result
5. THE Conversation_Manager SHALL provide the full message history for each OpenAI API call
6. WHEN conversation history exceeds a configurable token limit, THE Conversation_Manager SHALL truncate older messages while preserving the system prompt

### Requirement 3: Tool Executor

**User Story:** As a developer, I want to execute OpenAI tool calls using existing Tata processors, so that business logic remains centralized.

#### Acceptance Criteria

1. WHEN OpenAI returns a tool call, THE Tool_Executor SHALL parse the function name and arguments
2. THE Tool_Executor SHALL validate that the requested tool exists in the Tool_Registry
3. THE Tool_Executor SHALL check module dependencies via DependencyManager before execution
4. IF dependencies are not satisfied, THEN THE Tool_Executor SHALL return an error message describing missing prerequisites
5. WHEN dependencies are satisfied, THE Tool_Executor SHALL instantiate the appropriate processor and execute with parsed arguments
6. WHEN execution succeeds, THE Tool_Executor SHALL store the resulting artifact in MemoryManager
7. THE Tool_Executor SHALL return the artifact's JSON representation for inclusion in conversation
8. IF execution fails, THEN THE Tool_Executor SHALL return a structured error message

### Requirement 4: Agent Orchestration

**User Story:** As a recruiter, I want to have natural conversations with Tata, so that I can accomplish recruitment tasks without knowing specific commands.

#### Acceptance Criteria

1. WHEN a user sends a message, THE Agent SHALL send the message plus conversation history and available tools to OpenAI
2. WHEN OpenAI responds with text only, THE Agent SHALL return the text to the user
3. WHEN OpenAI responds with tool calls, THE Agent SHALL execute each tool via Tool_Executor
4. WHEN tool execution completes, THE Agent SHALL send results back to OpenAI for natural language response generation
5. THE Agent SHALL support multiple sequential tool calls in a single conversation turn
6. THE Agent SHALL maintain session context across the conversation

### Requirement 5: OpenAI Client Abstraction

**User Story:** As a developer, I want an abstraction over the OpenAI API, so that I can easily mock it for testing and swap implementations.

#### Acceptance Criteria

1. THE OpenAI_Client SHALL implement a Protocol for chat completion with tools
2. THE OpenAI_Client SHALL accept model name, messages, and tools as parameters
3. THE OpenAI_Client SHALL return a structured response containing either text content or tool calls
4. THE OpenAI_Client SHALL handle API errors and raise appropriate exceptions
5. THE OpenAI_Client SHALL support configuration of API key, model, and timeout

### Requirement 6: Error Handling

**User Story:** As a recruiter, I want clear error messages when something goes wrong, so that I understand what happened and how to proceed.

#### Acceptance Criteria

1. WHEN OpenAI API call fails, THE Agent SHALL return a user-friendly error message without exposing technical details
2. WHEN a tool execution fails due to missing dependencies, THE Agent SHALL explain which prerequisites are needed
3. WHEN a tool execution fails due to invalid input, THE Agent SHALL explain what input is required
4. WHEN a tool execution fails due to validation errors, THE Agent SHALL relay the validation message
5. THE Agent SHALL log all errors with full technical details for debugging

### Requirement 7: Testing Support

**User Story:** As a developer, I want comprehensive testing including both unit tests and real API integration tests, so that I can verify the system works end-to-end.

#### Acceptance Criteria

1. THE OpenAI_Client Protocol SHALL allow mock implementations for fast unit testing
2. THE Agent SHALL accept an OpenAI_Client instance via dependency injection
3. WHEN testing tool execution, THE Tool_Executor SHALL work with in-memory managers
4. THE test suite SHALL include property-based tests for tool registry schema generation
5. THE test suite SHALL include property-based tests for conversation message serialization round-trips
6. THE test suite SHALL include integration tests that call the real OpenAI API
7. WHEN running integration tests, THE test suite SHALL read the API key from OPENAI_API_KEY environment variable
8. THE integration tests SHALL be marked with a pytest marker so they can be run separately (e.g., `pytest -m integration`)
9. THE integration tests SHALL verify end-to-end conversation flows including tool calling and response generation
