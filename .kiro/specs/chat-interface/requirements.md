# Requirements Document

## Introduction

A minimal web-based chat interface for Tata that replaces the terminal-based interaction. The interface addresses issues with terminal input corruption when pasting text with special characters or spaces, and provides a cleaner user experience for interacting with the recruitment assistant.

## Glossary

- **Chat_Interface**: The web-based user interface for interacting with Tata
- **Message_Display**: The component that renders conversation messages
- **Input_Handler**: The component that captures and sanitizes user input
- **Session_Selector**: The component for choosing or creating recruitment sessions
- **Tata_Backend**: The existing TataAgent and supporting infrastructure

## Requirements

### Requirement 1: Web Server Setup

**User Story:** As a recruiter, I want to access Tata through a web browser, so that I can avoid terminal input issues and have a more user-friendly experience.

#### Acceptance Criteria

1. WHEN the application starts, THE Chat_Interface SHALL serve a web page on a configurable local port (default 8080)
2. WHEN a user navigates to the root URL, THE Chat_Interface SHALL display the chat interface
3. THE Chat_Interface SHALL use a lightweight Python web framework (Flask or FastAPI)
4. IF the configured port is unavailable, THEN THE Chat_Interface SHALL display an error message with the port conflict

### Requirement 2: Message Input Handling

**User Story:** As a recruiter, I want to type or paste messages without corruption, so that I can communicate effectively with Tata.

#### Acceptance Criteria

1. THE Input_Handler SHALL accept multi-line text input via a textarea element
2. WHEN a user pastes text with special characters or whitespace, THE Input_Handler SHALL preserve the original content
3. WHEN a user presses Enter (without Shift), THE Input_Handler SHALL submit the message
4. WHEN a user presses Shift+Enter, THE Input_Handler SHALL insert a newline without submitting
5. WHEN a user submits an empty or whitespace-only message, THE Input_Handler SHALL prevent submission and maintain focus
6. THE Input_Handler SHALL clear the input field after successful message submission

### Requirement 7: Context-Aware Suggestion Chips

**User Story:** As a recruiter, I want to see relevant next-step suggestions after each response, so that I can efficiently progress through the recruitment workflow.

#### Acceptance Criteria

1. WHEN Tata responds, THE Chat_Interface SHALL display suggestion chips below the response
2. THE suggestion chips SHALL be context-aware based on completed artifacts in the session:
   - WHEN no artifacts exist, suggestions SHALL include standalone modules (Requirement Profile, Funnel Report, Job Ad Review, D&I Review, Calendar Invite)
   - WHEN Requirement Profile exists, suggestions SHALL include dependent modules (Job Ad, TA Screening, HM Screening, Headhunting)
   - WHEN Requirement Profile AND TA Screening exist, suggestions SHALL also include Candidate Report
3. WHEN a user clicks a suggestion chip, THE Input_Handler SHALL populate the input field with the suggestion text
4. THE user SHALL be able to edit the populated suggestion before submitting
5. THE Chat_Interface SHALL query the backend for available next actions based on session state
6. THE suggestion chips SHALL update after each Tata response to reflect the current session state

### Requirement 3: Message Display

**User Story:** As a recruiter, I want to see the conversation history clearly, so that I can follow the dialogue with Tata.

#### Acceptance Criteria

1. THE Message_Display SHALL show user messages visually distinct from Tata responses
2. THE Message_Display SHALL render messages in chronological order (oldest at top)
3. WHEN a new message is added, THE Message_Display SHALL auto-scroll to show the latest message
4. THE Message_Display SHALL preserve whitespace and line breaks in message content
5. WHEN Tata is processing a request, THE Message_Display SHALL show a loading indicator

### Requirement 4: Session Management

**User Story:** As a recruiter, I want to select or create sessions, so that I can work on different recruitment projects.

#### Acceptance Criteria

1. WHEN the interface loads, THE Session_Selector SHALL display existing sessions for the current recruiter
2. THE Session_Selector SHALL allow creating a new session with position name and language selection
3. WHEN a session is selected, THE Chat_Interface SHALL load that session's context for the conversation
4. THE Session_Selector SHALL display session metadata (position name, language, last activity)

### Requirement 5: API Communication

**User Story:** As a recruiter, I want my messages to be processed by Tata, so that I can get recruitment assistance.

#### Acceptance Criteria

1. WHEN a user submits a message, THE Chat_Interface SHALL send it to the Tata_Backend via HTTP POST
2. THE Tata_Backend SHALL process the message using the existing TataAgent.chat() method
3. WHEN the Tata_Backend returns a response, THE Chat_Interface SHALL display it in the Message_Display
4. IF the Tata_Backend returns an error, THEN THE Chat_Interface SHALL display a user-friendly error message
5. THE Chat_Interface SHALL disable the input while waiting for a response

### Requirement 6: Minimal UI Design

**User Story:** As a recruiter, I want a clean and simple interface, so that I can focus on my recruitment tasks without distraction.

#### Acceptance Criteria

1. THE Chat_Interface SHALL use a single-page layout with no external CSS frameworks
2. THE Chat_Interface SHALL be responsive and usable on screens 800px wide or larger
3. THE Chat_Interface SHALL use a neutral color scheme suitable for professional use
4. THE Chat_Interface SHALL include a header showing the current session name
