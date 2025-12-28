# Implementation Plan: Chat Interface

## Overview

This plan implements a minimal web-based chat interface for Tata using FastAPI and vanilla JavaScript. Tasks are ordered to build incrementally, with core functionality first and enhancements later.

## Tasks

- [x] 1. Set up FastAPI server foundation
  - [x] 1.1 Create `src/tata/web/__init__.py` and `src/tata/web/server.py`
    - Define ChatServer class with FastAPI app
    - Configure CORS for local development
    - Add configurable port (default 8080)
    - _Requirements: 1.1, 1.3_
  - [x] 1.2 Add port conflict handling
    - Catch socket binding errors
    - Display clear error message with port number
    - _Requirements: 1.4_
  - [x] 1.3 Create Pydantic request/response models in `src/tata/web/models.py`
    - ChatRequestModel, ChatResponseModel
    - SessionInfoModel, CreateSessionModel, SuggestionsResponseModel
    - _Requirements: 5.1_

- [x] 2. Implement API endpoints
  - [x] 2.1 Implement GET `/` to serve HTML page
    - Return embedded HTML template
    - _Requirements: 1.2_
  - [x] 2.2 Implement POST `/api/chat` endpoint
    - Accept ChatRequestModel
    - Route to TataAgent.chat()
    - Return ChatResponseModel
    - Handle errors gracefully
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [x] 2.3 Implement session endpoints
    - GET `/api/sessions` - list sessions for recruiter
    - POST `/api/sessions` - create new session
    - GET `/api/sessions/{id}` - get session details
    - _Requirements: 4.1, 4.2, 4.3_
  - [ ]* 2.4 Write unit tests for API endpoints
    - Test successful chat flow
    - Test session CRUD operations
    - Test error responses
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 3. Create HTML/CSS/JS frontend
  - [x] 3.1 Create base HTML structure
    - Header with session name
    - Message container
    - Suggestion chips container (below messages)
    - Input area with textarea and send button
    - Session panel placeholder
    - _Requirements: 6.1, 6.4_
  - [x] 3.2 Implement InputHandler JavaScript module
    - Textarea event handling
    - Enter to submit, Shift+Enter for newline
    - Empty/whitespace validation
    - Clear after submission
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6_
  - [ ]* 3.3 Write property test for whitespace rejection
    - **Property 2: Whitespace-only input rejection**
    - **Validates: Requirements 2.5**
  - [x] 3.4 Implement MessageDisplay JavaScript module
    - Add message with user/assistant styling
    - Preserve whitespace (CSS white-space: pre-wrap)
    - Auto-scroll to latest message
    - Loading indicator
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - [ ]* 3.5 Write property test for message ordering
    - **Property 5: Message chronological ordering**
    - **Validates: Requirements 3.2**
  - [x] 3.6 Implement SuggestionChips JavaScript module
    - Render suggestion chips from backend response
    - Update chips after each Tata response
    - Populate input on click
    - _Requirements: 7.1, 7.3, 7.4, 7.6_
  - [ ]* 3.7 Write property test for suggestion population
    - **Property 4: Suggestion chip population**
    - **Validates: Requirements 7.3**
  - [x] 3.8 Implement ApiClient JavaScript module
    - sendMessage() for chat (returns suggestions)
    - getSessions(), createSession() for sessions
    - Error handling
    - _Requirements: 5.1, 5.4_
  - [x] 3.9 Add CSS for responsive layout and styling
    - Flexbox layout for chat container
    - Min-width 800px support
    - Neutral color scheme
    - Distinct message bubble colors for user vs Tata
    - Suggestion chip styling with hover states
    - _Requirements: 6.2, 6.3, 3.1, 7.1_

- [x] 4. Implement SuggestionService backend
  - [x] 4.1 Create `src/tata/web/suggestions.py` with SuggestionService class
    - Use DependencyManager to check available modules
    - Map ModuleType to user-friendly suggestion text
    - Return list of available suggestions for session
    - _Requirements: 7.2, 7.5_
  - [x] 4.2 Add GET `/api/suggestions/{session_id}` endpoint
    - Return available suggestions based on session state
    - _Requirements: 7.5_
  - [x] 4.3 Update POST `/api/chat` to include suggestions in response
    - Call SuggestionService after processing message
    - Include suggestions array in ChatResponseModel
    - _Requirements: 7.1, 7.6_
  - [ ]* 4.4 Write property test for context-aware suggestions
    - **Property 8: Context-aware suggestions based on dependencies**
    - **Validates: Requirements 7.2**

- [ ] 5. Checkpoint - Ensure core functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement session management UI
  - [x] 6.1 Implement SessionSelector JavaScript module in HTML template
    - Load and display sessions list
    - Create new session form with position name and language
    - Session selection handling to switch active session
    - Update header with selected session name
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [ ]* 6.2 Write property test for session metadata display
    - **Property 7: Session metadata completeness**
    - **Validates: Requirements 4.4**

- [x] 7. Wire everything together
  - [x] 7.1 Complete TataAgent integration in ChatServer.get_or_create_agent()
    - Initialize TataAgent with session context
    - Cache agents per session
    - _Requirements: 5.2_
  - [x] 7.2 Create `chat_demo.py` launcher script
    - Similar to existing demo.py
    - Start server with default config
    - _Requirements: 1.1_

- [ ] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Frontend JavaScript is embedded in the HTML template (no build step)
- Property tests focus on backend logic; frontend behavior tested via integration tests
- The existing TataAgent and persistence infrastructure is reused without modification
- ApiClient and CSS styling are already implemented in the HTML template (tasks 3.8, 3.9 marked complete)
