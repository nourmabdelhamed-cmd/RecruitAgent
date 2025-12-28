# Implementation Plan: OpenAI Integration

## Overview

This plan implements the OpenAI function calling integration for Tata. Tasks are ordered to build incrementally: data models first, then core components, then the agent orchestration, and finally tests.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Add `openai` package to pyproject.toml
  - Create `src/tata/agent/` directory structure
  - Create `__init__.py` with exports
  - _Requirements: 5.5, 7.7_

- [x] 2. Implement data models
  - [x] 2.1 Create Message and ToolCall dataclasses
    - Implement `MessageRole` enum
    - Implement `Message` dataclass with `to_openai_format()` and `from_openai_format()`
    - Implement `ToolCall` dataclass with `to_dict()` and `parse_arguments()`
    - _Requirements: 2.1, 3.1_
  - [ ]* 2.2 Write property test for Message round-trip
    - **Property 3: Message Serialization Round-Trip**
    - **Validates: Requirements 2.1**
  - [x] 2.3 Create ToolDefinition and ChatCompletionResponse dataclasses
    - Implement `ToolDefinition` with `to_openai_format()`
    - Implement `ChatCompletionResponse` dataclass
    - _Requirements: 1.2, 5.3_

- [x] 3. Implement ToolRegistry
  - [x] 3.1 Create ToolRegistry protocol and InMemoryToolRegistry
    - Define protocol with `get_tool()`, `get_all_tools()`, `get_openai_tools()`
    - Implement InMemoryToolRegistry with tool storage
    - Register all 10 Tata modules as tools with parameter schemas
    - Include dependency info in descriptions for dependent modules
    - _Requirements: 1.1, 1.2, 1.4, 1.5_
  - [ ]* 3.2 Write property tests for ToolRegistry
    - **Property 1: Tool Registry Schema Validity**
    - **Property 2: Tool Registry Dependency Documentation**
    - **Validates: Requirements 1.1, 1.2, 1.4**

- [x] 4. Implement ConversationManager
  - [x] 4.1 Create ConversationManager protocol and InMemoryConversationManager
    - Define protocol with message management methods
    - Implement with system prompt initialization
    - Implement message truncation preserving system prompt
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - [ ]* 4.2 Write property tests for ConversationManager
    - **Property 4: Conversation Message Persistence**
    - **Property 5: Conversation Truncation Preserves System Prompt**
    - **Validates: Requirements 2.3, 2.4, 2.6**

- [x] 5. Implement OpenAIClient
  - [x] 5.1 Create OpenAIClient protocol and implementations
    - Define protocol with `chat_completion()` method
    - Implement `RealOpenAIClient` using OpenAI SDK
    - Implement `MockOpenAIClient` for testing
    - Implement `OpenAIAPIError` exception
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - [ ]* 5.2 Write unit tests for MockOpenAIClient
    - Test response configuration
    - Test call history tracking
    - _Requirements: 7.1, 7.2_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement ToolExecutor
  - [x] 7.1 Create ToolExecutor with processor routing
    - Implement tool validation against registry
    - Implement dependency checking via DependencyManager
    - Implement processor instantiation and execution
    - Implement artifact storage on success
    - Implement error result generation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_
  - [ ]* 7.2 Write property tests for ToolExecutor
    - **Property 6: Tool Call Argument Parsing**
    - **Property 7: Unknown Tool Rejection**
    - **Property 8: Dependency Enforcement**
    - **Property 9: Successful Execution Stores Artifact**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.5, 3.6, 3.7**

- [x] 8. Implement TataAgent
  - [x] 8.1 Create TataAgent orchestration class
    - Implement `chat()` method with conversation loop
    - Handle text-only responses
    - Handle tool call responses with execution
    - Handle multiple sequential tool calls
    - Implement error handling with user-friendly messages
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 6.1, 6.2, 6.3, 6.4_
  - [ ]* 8.2 Write property tests for TataAgent
    - **Property 10: Text Response Pass-Through**
    - **Property 11: Error Message Descriptiveness**
    - **Validates: Requirements 4.2, 6.2, 6.3**

- [x] 9. Checkpoint - Ensure all unit and property tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement integration tests
  - [x] 10.1 Create integration test fixtures
    - Add pytest marker for integration tests
    - Create fixture for real OpenAI client with API key check
    - Create agent factory with real client
    - _Requirements: 7.6, 7.7, 7.8_
  - [x] 10.2 Write integration tests for conversation flows
    - Test requirement profile creation flow
    - Test job ad generation flow (with dependency)
    - Test error handling for missing dependencies
    - Test multi-turn conversation
    - _Requirements: 7.9_

- [x] 11. Final checkpoint - Run full test suite
  - Run `uv run pytest` for unit and property tests
  - Run `uv run pytest -m integration` for integration tests
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Integration tests require `OPENAI_API_KEY` environment variable
- Run integration tests separately: `uv run pytest -m integration`
