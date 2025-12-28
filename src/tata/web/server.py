"""FastAPI-based web server for Tata chat interface.

This module provides the ChatServer class that serves the web-based chat
interface and handles API requests for chat and session management.

Requirements covered:
- 1.1: Serve web page on configurable local port (default 8080)
- 1.2: Display chat interface when user navigates to root URL
- 1.3: Use FastAPI as lightweight Python web framework
- 1.4: Display error message with port conflict
- 4.1, 4.2, 4.3: Session management endpoints
- 5.1, 5.2, 5.3, 5.4: Chat API communication
"""

import logging
import socket
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.tata.agent.agent import TataAgent
from src.tata.agent.client import RealOpenAIClient
from src.tata.agent.registry import InMemoryToolRegistry
from src.tata.agent.executor import ToolExecutor
from src.tata.agent.conversation import InMemoryConversationManager
from src.tata.persistence.sqlite import SQLiteSessionManager, SQLiteMemoryManager
from src.tata.session.session import (
    SessionManager,
    SupportedLanguage,
    SessionNotFoundError,
    EmptyRecruiterIDError,
    EmptySessionIDError,
)
from src.tata.memory.memory import MemoryManager
from src.tata.web.models import (
    ChatRequestModel,
    ChatResponseModel,
    SessionInfoModel,
    CreateSessionModel,
    SuggestionsResponseModel,
)
from src.tata.web.suggestions import SuggestionService
from src.tata.dependency.dependency import InMemoryDependencyManager


# Configure module logger
logger = logging.getLogger(__name__)


# HTML template for the chat interface (Requirement 1.2)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tata - Recruitment Assistant</title>
    <style>
        /* Base styles (Requirement 6.1: single-page layout, no external CSS) */
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            min-width: 800px; /* Requirement 6.2: responsive, 800px+ */
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* Header with session name (Requirement 6.4) */
        header {
            background-color: #2c3e50;
            color: white;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        header h1 {
            font-size: 1.5rem;
        }
        #session-name {
            color: #bdc3c7;
        }
        
        /* Main chat container (Requirement 6.3: neutral color scheme) */
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
            padding: 1rem;
            overflow: hidden;
        }
        
        /* Message container (Requirement 3.2: chronological order) */
        #messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: white;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
        }
        
        /* Message styling (Requirement 3.1: distinct user vs Tata) */
        .message {
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            max-width: 80%;
            white-space: pre-wrap; /* Requirement 3.4: preserve whitespace */
            word-wrap: break-word;
        }
        .message.user {
            background-color: #3498db;
            color: white;
            margin-left: auto;
        }
        .message.assistant {
            background-color: #ecf0f1;
            color: #2c3e50;
        }
        .message.error {
            background-color: #e74c3c;
            color: white;
        }
        
        /* Suggestion chips container (Requirement 7.1: below messages) */
        #suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
            min-height: 2.5rem;
        }
        
        /* Suggestion chip styling (Requirement 7.1, 7.3) */
        .suggestion-chip {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.875rem;
            transition: background-color 0.2s;
        }
        .suggestion-chip:hover {
            background-color: #2980b9;
        }
        
        /* Input area (Requirement 2.1: textarea element) */
        #input-area {
            display: flex;
            gap: 0.5rem;
        }
        #message-input {
            flex: 1;
            padding: 0.75rem;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
            resize: none;
            font-family: inherit;
            font-size: 1rem;
        }
        #message-input:focus {
            outline: none;
            border-color: #3498db;
        }
        #message-input:disabled {
            background-color: #ecf0f1;
            cursor: not-allowed;
        }
        #send-btn {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
        }
        #send-btn:hover {
            background-color: #2980b9;
        }
        #send-btn:disabled {
            background-color: #bdc3c7;
            cursor: not-allowed;
        }
        
        /* Loading indicator (Requirement 3.5) */
        .loading {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #7f8c8d;
            padding: 0.75rem;
        }
        .loading-dots {
            display: flex;
            gap: 0.25rem;
        }
        .loading-dots span {
            width: 8px;
            height: 8px;
            background-color: #7f8c8d;
            border-radius: 50%;
            animation: blink 1.4s infinite both;
        }
        .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
        .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink {
            0%, 80%, 100% { opacity: 0.3; }
            40% { opacity: 1; }
        }
        
        /* Session panel (Requirement 4.1, 4.2, 4.3, 4.4) */
        aside {
            position: fixed;
            right: 0;
            top: 0;
            width: 320px;
            height: 100vh;
            background: white;
            border-left: 1px solid #bdc3c7;
            padding: 1rem;
            transform: translateX(100%);
            transition: transform 0.3s;
            overflow-y: auto;
            z-index: 100;
        }
        aside.open {
            transform: translateX(0);
        }
        
        /* Session panel toggle button */
        #session-toggle {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
        }
        #session-toggle:hover {
            background-color: #2980b9;
        }
        
        /* Session panel header */
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #ecf0f1;
        }
        .panel-header h2 {
            font-size: 1.25rem;
            color: #2c3e50;
        }
        #close-panel {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #7f8c8d;
        }
        #close-panel:hover {
            color: #2c3e50;
        }
        
        /* New session form (Requirement 4.2) */
        .new-session-form {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .new-session-form h3 {
            font-size: 1rem;
            color: #2c3e50;
            margin-bottom: 0.75rem;
        }
        .form-group {
            margin-bottom: 0.75rem;
        }
        .form-group label {
            display: block;
            font-size: 0.875rem;
            color: #7f8c8d;
            margin-bottom: 0.25rem;
        }
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 0.875rem;
        }
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #3498db;
        }
        #create-session-btn {
            width: 100%;
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
        }
        #create-session-btn:hover {
            background-color: #219a52;
        }
        #create-session-btn:disabled {
            background-color: #bdc3c7;
            cursor: not-allowed;
        }
        
        /* Sessions list (Requirement 4.1, 4.4) */
        .sessions-list h3 {
            font-size: 1rem;
            color: #2c3e50;
            margin-bottom: 0.75rem;
        }
        .session-item {
            background-color: #f8f9fa;
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            cursor: pointer;
            border: 2px solid transparent;
            transition: border-color 0.2s, background-color 0.2s;
        }
        .session-item:hover {
            background-color: #ecf0f1;
        }
        .session-item.selected {
            border-color: #3498db;
            background-color: #ebf5fb;
        }
        .session-item .position-name {
            font-weight: 500;
            color: #2c3e50;
            margin-bottom: 0.25rem;
        }
        .session-item .session-meta {
            font-size: 0.75rem;
            color: #7f8c8d;
        }
        .session-item .session-meta span {
            margin-right: 0.5rem;
        }
        .no-sessions {
            color: #7f8c8d;
            font-size: 0.875rem;
            text-align: center;
            padding: 1rem;
        }
        
        /* Loading state for sessions */
        .sessions-loading {
            text-align: center;
            padding: 1rem;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <!-- Header with session name (Requirement 6.4) -->
    <header>
        <h1>Tata</h1>
        <div style="display: flex; align-items: center; gap: 1rem;">
            <span id="session-name">No session selected</span>
            <button id="session-toggle">Sessions</button>
        </div>
    </header>
    
    <!-- Main chat container (Requirement 6.1) -->
    <main id="chat-container">
        <!-- Message container (Requirement 3.2) -->
        <div id="messages"></div>
        
        <!-- Suggestion chips container (Requirement 7.1) -->
        <div id="suggestions"></div>
        
        <!-- Input area with textarea and send button (Requirement 2.1) -->
        <div id="input-area">
            <textarea id="message-input" placeholder="Type a message..." rows="2"></textarea>
            <button id="send-btn">Send</button>
        </div>
    </main>
    
    <!-- Session panel (Requirement 4.1, 4.2, 4.3, 4.4) -->
    <aside id="session-panel">
        <div class="panel-header">
            <h2>Sessions</h2>
            <button id="close-panel">&times;</button>
        </div>
        
        <!-- New session form (Requirement 4.2) -->
        <div class="new-session-form">
            <h3>Create New Session</h3>
            <div class="form-group">
                <label for="position-name">Position Name</label>
                <input type="text" id="position-name" placeholder="e.g., Senior Developer">
            </div>
            <div class="form-group">
                <label for="language-select">Language</label>
                <select id="language-select">
                    <option value="en">English</option>
                    <option value="sv">Swedish</option>
                    <option value="da">Danish</option>
                    <option value="no">Norwegian</option>
                    <option value="de">German</option>
                </select>
            </div>
            <button id="create-session-btn">Create Session</button>
        </div>
        
        <!-- Sessions list (Requirement 4.1, 4.4) -->
        <div class="sessions-list">
            <h3>Your Sessions</h3>
            <div id="sessions-container">
                <div class="sessions-loading">Loading sessions...</div>
            </div>
        </div>
    </aside>
    
    <script>
        /**
         * InputHandler Module (Requirement 2.1, 2.3, 2.4, 2.5, 2.6)
         * 
         * Manages textarea input, keyboard events, and message submission.
         * - Enter without Shift = submit (Requirement 2.3)
         * - Shift+Enter = newline (Requirement 2.4)
         * - Empty/whitespace validation (Requirement 2.5)
         * - Clear after submission (Requirement 2.6)
         */
        const InputHandler = {
            textarea: null,
            sendButton: null,
            onSubmit: null,
            
            /**
             * Initialize the input handler.
             * @param {string} textareaId - ID of the textarea element
             * @param {string} buttonId - ID of the send button element
             * @param {Function} submitCallback - Callback when message is submitted
             */
            init(textareaId, buttonId, submitCallback) {
                this.textarea = document.getElementById(textareaId);
                this.sendButton = document.getElementById(buttonId);
                this.onSubmit = submitCallback;
                
                // Keyboard event handling (Requirement 2.3, 2.4)
                this.textarea.addEventListener('keydown', (e) => this.handleKeyDown(e));
                
                // Button click handling
                this.sendButton.addEventListener('click', () => this.submit());
            },
            
            /**
             * Handle keyboard events.
             * Enter without Shift = submit (Requirement 2.3)
             * Shift+Enter = newline (Requirement 2.4)
             * @param {KeyboardEvent} event
             */
            handleKeyDown(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    this.submit();
                }
                // Shift+Enter allows default behavior (newline)
            },
            
            /**
             * Submit the message.
             * Validates non-empty content (Requirement 2.5)
             * Clears input after submission (Requirement 2.6)
             */
            submit() {
                const message = this.textarea.value;
                
                // Validate non-empty/non-whitespace (Requirement 2.5)
                if (!message || message.trim() === '') {
                    // Prevent submission, maintain focus
                    this.textarea.focus();
                    return;
                }
                
                // Call submit callback
                if (this.onSubmit) {
                    this.onSubmit(message);
                }
                
                // Clear input after submission (Requirement 2.6)
                this.textarea.value = '';
                this.textarea.focus();
            },
            
            /**
             * Populate the input field with text.
             * Used by suggestion chips (Requirement 7.3, 7.4)
             * @param {string} text - Text to populate
             */
            populate(text) {
                this.textarea.value = text;
                this.textarea.focus();
                // Move cursor to end
                this.textarea.selectionStart = this.textarea.selectionEnd = text.length;
            },
            
            /**
             * Enable or disable input.
             * Used during processing (Requirement 5.5)
             * @param {boolean} enabled
             */
            setEnabled(enabled) {
                this.textarea.disabled = !enabled;
                this.sendButton.disabled = !enabled;
            },
            
            /**
             * Get the current input value.
             * @returns {string}
             */
            getValue() {
                return this.textarea.value;
            },
            
            /**
             * Clear the input field.
             */
            clear() {
                this.textarea.value = '';
            }
        };
        
        /**
         * MessageDisplay Module (Requirement 3.1, 3.2, 3.3, 3.4, 3.5)
         * 
         * Renders messages and manages auto-scroll.
         * - Distinct styling for user vs assistant (Requirement 3.1)
         * - Chronological order (Requirement 3.2)
         * - Auto-scroll to latest (Requirement 3.3)
         * - Preserve whitespace (Requirement 3.4)
         * - Loading indicator (Requirement 3.5)
         */
        const MessageDisplay = {
            container: null,
            loadingElement: null,
            
            /**
             * Initialize the message display.
             * @param {string} containerId - ID of the messages container
             */
            init(containerId) {
                this.container = document.getElementById(containerId);
            },
            
            /**
             * Add a message to the display.
             * Messages are added in chronological order (Requirement 3.2)
             * Whitespace is preserved via CSS (Requirement 3.4)
             * @param {string} content - Message content
             * @param {boolean} isUser - True for user messages, false for assistant
             */
            addMessage(content, isUser) {
                // Remove loading indicator if present
                this.hideLoading();
                
                // Create message element (Requirement 3.1: distinct styling)
                const messageEl = document.createElement('div');
                messageEl.className = `message ${isUser ? 'user' : 'assistant'}`;
                
                // Set text content (preserves special characters)
                // CSS white-space: pre-wrap handles whitespace (Requirement 3.4)
                messageEl.textContent = content;
                
                // Add to container (chronological order - Requirement 3.2)
                this.container.appendChild(messageEl);
                
                // Auto-scroll to latest message (Requirement 3.3)
                this.scrollToBottom();
            },
            
            /**
             * Add an error message to the display.
             * @param {string} content - Error message content
             */
            addError(content) {
                this.hideLoading();
                
                const messageEl = document.createElement('div');
                messageEl.className = 'message error';
                messageEl.textContent = content;
                
                this.container.appendChild(messageEl);
                this.scrollToBottom();
            },
            
            /**
             * Show loading indicator (Requirement 3.5)
             */
            showLoading() {
                if (this.loadingElement) return;
                
                this.loadingElement = document.createElement('div');
                this.loadingElement.className = 'loading';
                this.loadingElement.innerHTML = `
                    <span>Tata is thinking</span>
                    <div class="loading-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                `;
                
                this.container.appendChild(this.loadingElement);
                this.scrollToBottom();
            },
            
            /**
             * Hide loading indicator.
             */
            hideLoading() {
                if (this.loadingElement) {
                    this.loadingElement.remove();
                    this.loadingElement = null;
                }
            },
            
            /**
             * Scroll to the bottom of the message container.
             */
            scrollToBottom() {
                this.container.scrollTop = this.container.scrollHeight;
            },
            
            /**
             * Clear all messages.
             */
            clear() {
                this.container.innerHTML = '';
                this.loadingElement = null;
            }
        };
        
        /**
         * SuggestionChips Module (Requirement 7.1, 7.3, 7.4, 7.6)
         * 
         * Displays context-aware suggestions based on session state.
         * - Render chips from backend response (Requirement 7.1)
         * - Populate input on click (Requirement 7.3)
         * - Allow editing before submit (Requirement 7.4)
         * - Update after each response (Requirement 7.6)
         */
        const SuggestionChips = {
            container: null,
            inputHandler: null,
            
            /**
             * Initialize the suggestion chips module.
             * @param {string} containerId - ID of the suggestions container
             * @param {Object} inputHandler - Reference to InputHandler module
             */
            init(containerId, inputHandler) {
                this.container = document.getElementById(containerId);
                this.inputHandler = inputHandler;
            },
            
            /**
             * Update suggestion chips from backend response.
             * Called after each Tata response (Requirement 7.6)
             * @param {string[]} suggestions - Array of suggestion strings
             */
            update(suggestions) {
                this.render(suggestions);
            },
            
            /**
             * Render suggestion chips.
             * @param {string[]} suggestions - Array of suggestion strings
             */
            render(suggestions) {
                // Clear existing chips
                this.container.innerHTML = '';
                
                if (!suggestions || suggestions.length === 0) {
                    return;
                }
                
                // Create chip for each suggestion
                suggestions.forEach(suggestion => {
                    const chip = document.createElement('button');
                    chip.className = 'suggestion-chip';
                    chip.textContent = suggestion;
                    chip.addEventListener('click', () => this.handleClick(suggestion));
                    this.container.appendChild(chip);
                });
            },
            
            /**
             * Handle chip click.
             * Populates input with suggestion text (Requirement 7.3)
             * User can edit before submitting (Requirement 7.4)
             * @param {string} suggestion - The suggestion text
             */
            handleClick(suggestion) {
                if (this.inputHandler) {
                    this.inputHandler.populate(suggestion);
                }
            },
            
            /**
             * Clear all suggestion chips.
             */
            clear() {
                this.container.innerHTML = '';
            }
        };
        
        /**
         * ApiClient Module
         * 
         * Handles HTTP communication with backend.
         * To be fully implemented in task 6.3
         */
        const ApiClient = {
            baseUrl: '',
            
            /**
             * Send a chat message to the backend.
             * @param {string} sessionId - Session identifier
             * @param {string} message - User message
             * @returns {Promise<Object>} Response with response/error and suggestions
             */
            async sendMessage(sessionId, message) {
                const response = await fetch(`${this.baseUrl}/api/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        message: message,
                    }),
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Request failed');
                }
                
                return response.json();
            },
            
            /**
             * Get sessions for a recruiter.
             * @param {string} recruiterId - Recruiter identifier
             * @returns {Promise<Object[]>} Array of session objects
             */
            async getSessions(recruiterId) {
                const response = await fetch(
                    `${this.baseUrl}/api/sessions?recruiter_id=${encodeURIComponent(recruiterId)}`
                );
                
                if (!response.ok) {
                    throw new Error('Failed to fetch sessions');
                }
                
                return response.json();
            },
            
            /**
             * Create a new session.
             * @param {string} recruiterId - Recruiter identifier
             * @param {string} positionName - Position name
             * @param {string} language - Language code
             * @returns {Promise<Object>} Created session object
             */
            async createSession(recruiterId, positionName, language = 'en') {
                const response = await fetch(`${this.baseUrl}/api/sessions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        recruiter_id: recruiterId,
                        position_name: positionName,
                        language: language,
                    }),
                });
                
                if (!response.ok) {
                    throw new Error('Failed to create session');
                }
                
                return response.json();
            }
        };
        
        /**
         * SessionSelector Module (Requirement 4.1, 4.2, 4.3, 4.4)
         * 
         * Manages session list and creation.
         * - Load and display sessions list (Requirement 4.1)
         * - Create new session form (Requirement 4.2)
         * - Session selection handling (Requirement 4.3)
         * - Display session metadata (Requirement 4.4)
         */
        const SessionSelector = {
            panel: null,
            container: null,
            currentSession: null,
            onSessionSelect: null,
            
            /**
             * Initialize the session selector.
             * @param {string} panelId - ID of the session panel element
             * @param {string} containerId - ID of the sessions container element
             * @param {Function} selectCallback - Callback when session is selected
             */
            init(panelId, containerId, selectCallback) {
                this.panel = document.getElementById(panelId);
                this.container = document.getElementById(containerId);
                this.onSessionSelect = selectCallback;
                
                // Set up panel toggle
                const toggleBtn = document.getElementById('session-toggle');
                const closeBtn = document.getElementById('close-panel');
                
                toggleBtn.addEventListener('click', () => this.openPanel());
                closeBtn.addEventListener('click', () => this.closePanel());
                
                // Set up create session form
                const createBtn = document.getElementById('create-session-btn');
                const positionInput = document.getElementById('position-name');
                
                createBtn.addEventListener('click', () => this.handleCreateSession());
                
                // Allow Enter key to submit form
                positionInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        this.handleCreateSession();
                    }
                });
            },
            
            /**
             * Open the session panel.
             */
            openPanel() {
                this.panel.classList.add('open');
            },
            
            /**
             * Close the session panel.
             */
            closePanel() {
                this.panel.classList.remove('open');
            },
            
            /**
             * Load and display sessions for a recruiter.
             * Requirement 4.1: Display existing sessions when interface loads.
             * @param {string} recruiterId - Recruiter identifier
             */
            async loadSessions(recruiterId) {
                this.container.innerHTML = '<div class="sessions-loading">Loading sessions...</div>';
                
                try {
                    const sessions = await ApiClient.getSessions(recruiterId);
                    this.renderSessions(sessions);
                } catch (error) {
                    console.error('Failed to load sessions:', error);
                    this.container.innerHTML = '<div class="no-sessions">Failed to load sessions. Please try again.</div>';
                }
            },
            
            /**
             * Render the sessions list.
             * Requirement 4.4: Display session metadata (position name, language, last activity).
             * @param {Object[]} sessions - Array of session objects
             */
            renderSessions(sessions) {
                if (!sessions || sessions.length === 0) {
                    this.container.innerHTML = '<div class="no-sessions">No sessions yet. Create one above!</div>';
                    return;
                }
                
                this.container.innerHTML = '';
                
                // Sort sessions by last activity (most recent first)
                const sortedSessions = [...sessions].sort((a, b) => 
                    new Date(b.last_activity) - new Date(a.last_activity)
                );
                
                sortedSessions.forEach(session => {
                    const item = document.createElement('div');
                    item.className = 'session-item';
                    if (this.currentSession && this.currentSession.id === session.id) {
                        item.classList.add('selected');
                    }
                    
                    // Format last activity date
                    const lastActivity = new Date(session.last_activity);
                    const formattedDate = this.formatDate(lastActivity);
                    
                    // Get language display name
                    const languageNames = {
                        'en': 'English',
                        'sv': 'Swedish',
                        'da': 'Danish',
                        'no': 'Norwegian',
                        'de': 'German'
                    };
                    const languageDisplay = languageNames[session.language] || session.language;
                    
                    // Requirement 4.4: Display position name, language, last activity
                    item.innerHTML = `
                        <div class="position-name">${session.position_name || 'Untitled Position'}</div>
                        <div class="session-meta">
                            <span>${languageDisplay}</span>
                            <span>•</span>
                            <span>${formattedDate}</span>
                        </div>
                    `;
                    
                    item.addEventListener('click', () => this.selectSession(session));
                    this.container.appendChild(item);
                });
            },
            
            /**
             * Format a date for display.
             * @param {Date} date - Date to format
             * @returns {string} Formatted date string
             */
            formatDate(date) {
                const now = new Date();
                const diffMs = now - date;
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMs / 3600000);
                const diffDays = Math.floor(diffMs / 86400000);
                
                if (diffMins < 1) return 'Just now';
                if (diffMins < 60) return `${diffMins}m ago`;
                if (diffHours < 24) return `${diffHours}h ago`;
                if (diffDays < 7) return `${diffDays}d ago`;
                
                return date.toLocaleDateString();
            },
            
            /**
             * Handle create session button click.
             * Requirement 4.2: Create new session with position name and language.
             */
            async handleCreateSession() {
                const positionInput = document.getElementById('position-name');
                const languageSelect = document.getElementById('language-select');
                const createBtn = document.getElementById('create-session-btn');
                
                const positionName = positionInput.value.trim();
                const language = languageSelect.value;
                
                if (!positionName) {
                    positionInput.focus();
                    return;
                }
                
                // Disable button during creation
                createBtn.disabled = true;
                createBtn.textContent = 'Creating...';
                
                try {
                    const session = await ApiClient.createSession(
                        AppState.recruiterId,
                        positionName,
                        language
                    );
                    
                    // Clear form
                    positionInput.value = '';
                    languageSelect.value = 'en';
                    
                    // Reload sessions list
                    await this.loadSessions(AppState.recruiterId);
                    
                    // Select the new session
                    this.selectSession(session);
                    
                } catch (error) {
                    console.error('Failed to create session:', error);
                    alert('Failed to create session. Please try again.');
                } finally {
                    createBtn.disabled = false;
                    createBtn.textContent = 'Create Session';
                }
            },
            
            /**
             * Select a session.
             * Requirement 4.3: Load session context when selected.
             * @param {Object} session - Session object to select
             */
            selectSession(session) {
                this.currentSession = session;
                
                // Update UI to show selected session
                const items = this.container.querySelectorAll('.session-item');
                items.forEach(item => item.classList.remove('selected'));
                
                // Find and highlight the selected item
                const selectedItem = Array.from(items).find(item => {
                    const positionName = item.querySelector('.position-name').textContent;
                    return positionName === (session.position_name || 'Untitled Position');
                });
                if (selectedItem) {
                    selectedItem.classList.add('selected');
                }
                
                // Update header with session name (Requirement 6.4)
                const sessionNameEl = document.getElementById('session-name');
                sessionNameEl.textContent = session.position_name || 'Untitled Position';
                
                // Close panel after selection
                this.closePanel();
                
                // Call the selection callback
                if (this.onSessionSelect) {
                    this.onSessionSelect(session);
                }
            },
            
            /**
             * Get the currently selected session.
             * @returns {Object|null} Current session or null
             */
            getCurrentSession() {
                return this.currentSession;
            }
        };
        
        /**
         * Application State
         */
        const AppState = {
            currentSession: null,
            recruiterId: 'default',
            isProcessing: false
        };
        
        /**
         * Main application initialization
         */
        async function initApp() {
            // Initialize modules
            MessageDisplay.init('messages');
            
            InputHandler.init('message-input', 'send-btn', async (message) => {
                if (AppState.isProcessing) return;
                
                // Check if session is selected
                if (!AppState.currentSession) {
                    MessageDisplay.addError('Please select or create a session first.');
                    return;
                }
                
                // Display user message
                MessageDisplay.addMessage(message, true);
                
                // Disable input during processing
                AppState.isProcessing = true;
                InputHandler.setEnabled(false);
                MessageDisplay.showLoading();
                
                try {
                    // Send message to backend
                    const result = await ApiClient.sendMessage(
                        AppState.currentSession.id,
                        message
                    );
                    
                    if (result.error) {
                        MessageDisplay.addError(result.error);
                    } else {
                        MessageDisplay.addMessage(result.response, false);
                    }
                    
                    // Update suggestion chips (Requirement 7.6)
                    SuggestionChips.update(result.suggestions || []);
                    
                } catch (error) {
                    MessageDisplay.addError(
                        'Unable to connect to Tata. Please check your connection.'
                    );
                } finally {
                    AppState.isProcessing = false;
                    InputHandler.setEnabled(true);
                    MessageDisplay.hideLoading();
                }
            });
            
            SuggestionChips.init('suggestions', InputHandler);
            
            // Initialize SessionSelector (Requirement 4.1, 4.2, 4.3, 4.4)
            SessionSelector.init('session-panel', 'sessions-container', (session) => {
                // Update AppState when session is selected (Requirement 4.3)
                AppState.currentSession = session;
                
                // Clear messages when switching sessions
                MessageDisplay.clear();
                SuggestionChips.clear();
                
                // Show welcome message for the session
                MessageDisplay.addMessage(
                    `Session loaded: ${session.position_name || 'Untitled Position'}. How can I help you today?`,
                    false
                );
            });
            
            // Load existing sessions (Requirement 4.1)
            await SessionSelector.loadSessions(AppState.recruiterId);
            
            console.log('Tata chat interface initialized');
        }
        
        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', initApp);
    </script>
</body>
</html>
"""


class PortInUseError(Exception):
    """Raised when the configured port is already in use."""
    pass


class ChatServer:
    """FastAPI-based web server for Tata chat interface.
    
    Serves the web interface and handles API requests for chat
    and session management.
    
    Attributes:
        app: FastAPI application instance
        session_manager: SessionManager for persistence
        memory_manager: MemoryManager for artifacts
        agents: Dict mapping session_id to TataAgent instances
        port: Server port (default 8080)
    """
    
    def __init__(
        self,
        port: int = 8080,
        session_manager: Optional[SessionManager] = None,
        memory_manager: Optional[MemoryManager] = None,
    ) -> None:
        """Initialize the chat server.
        
        Args:
            port: Server port (default 8080)
            session_manager: Optional SessionManager instance.
                           Defaults to SQLiteSessionManager.
            memory_manager: Optional MemoryManager instance.
                          Defaults to SQLiteMemoryManager.
        """
        self.port = port
        self.session_manager = session_manager or SQLiteSessionManager()
        self.memory_manager = memory_manager or SQLiteMemoryManager()
        self.agents: Dict[str, TataAgent] = {}
        
        # Initialize dependency manager and suggestion service
        self.dependency_manager = InMemoryDependencyManager(self.memory_manager)
        self.suggestion_service = SuggestionService(
            self.dependency_manager,
            self.memory_manager
        )
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Tata - Recruitment Assistant",
            description="Web-based chat interface for Tata",
            version="0.1.0",
        )
        
        # Configure CORS for local development
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for local dev
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Register API routes on the FastAPI app."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_chat_page() -> str:
            """Serve the chat HTML page (Requirement 1.2)."""
            return HTML_TEMPLATE
        
        @self.app.post("/api/chat", response_model=ChatResponseModel)
        async def chat(request: ChatRequestModel) -> ChatResponseModel:
            """Process a chat message and return response.
            
            Routes the message to TataAgent.chat() and returns the response.
            
            Requirements covered:
            - 5.1: Send message to Tata_Backend via HTTP POST
            - 5.2: Process message using TataAgent.chat()
            - 5.3: Display response in Message_Display
            - 5.4: Display user-friendly error message on error
            - 7.1: Include suggestions in response
            - 7.6: Update suggestions after each response
            
            Args:
                request: ChatRequestModel with session_id and message
                
            Returns:
                ChatResponseModel with response or error and suggestions
            """
            # Validate session exists
            session = self.session_manager.get_session(request.session_id)
            if session is None:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found"
                )
            
            # Get suggestions for the session (Requirement 7.1, 7.6)
            suggestions = self.suggestion_service.get_suggestions(request.session_id)
            
            # Get or create agent for session
            agent = self.get_or_create_agent(request.session_id)
            if agent is None:
                # This shouldn't happen since we validated session exists above
                return ChatResponseModel(
                    error="Failed to initialize agent for session.",
                    suggestions=suggestions
                )
            
            try:
                # Process message through agent (Requirement 5.2)
                response = agent.chat(request.message)
                
                # Get updated suggestions after processing (Requirement 7.6)
                suggestions = self.suggestion_service.get_suggestions(request.session_id)
                
                # Return successful response (Requirement 5.3)
                return ChatResponseModel(
                    response=response,
                    suggestions=suggestions
                )
            except Exception as e:
                # Log error and return user-friendly message (Requirement 5.4)
                logger.error(f"Chat error for session {request.session_id}: {e}", exc_info=True)
                return ChatResponseModel(
                    error="An error occurred while processing your message. Please try again.",
                    suggestions=suggestions
                )
        
        @self.app.get("/api/sessions", response_model=List[SessionInfoModel])
        async def list_sessions(recruiter_id: str = Query(..., description="Recruiter identifier")) -> List[SessionInfoModel]:
            """List all sessions for a recruiter.
            
            Requirement 4.1: Display existing sessions for the current recruiter.
            
            Args:
                recruiter_id: The recruiter's identifier
                
            Returns:
                List of SessionInfoModel objects
            """
            try:
                sessions = self.session_manager.list_sessions(recruiter_id)
                return [
                    SessionInfoModel(
                        id=s.id,
                        position_name=s.position_name if s.position_name else None,
                        language=s.language.value,
                        last_activity=s.last_activity.isoformat()
                    )
                    for s in sessions
                ]
            except EmptyRecruiterIDError:
                raise HTTPException(
                    status_code=400,
                    detail="Recruiter ID is required"
                )
        
        @self.app.post("/api/sessions", response_model=SessionInfoModel, status_code=201)
        async def create_session(request: CreateSessionModel) -> SessionInfoModel:
            """Create a new session.
            
            Requirement 4.2: Allow creating a new session with position name and language.
            
            Args:
                request: CreateSessionModel with recruiter_id, position_name, language
                
            Returns:
                SessionInfoModel for the created session
            """
            try:
                # Create the session
                session = self.session_manager.create_session(request.recruiter_id)
                
                # Set position name if provided
                if request.position_name:
                    self.session_manager.set_position_name(session.id, request.position_name)
                
                # Set language if not default
                if request.language != "en":
                    language_map = {
                        "sv": SupportedLanguage.SWEDISH,
                        "da": SupportedLanguage.DANISH,
                        "no": SupportedLanguage.NORWEGIAN,
                        "de": SupportedLanguage.GERMAN,
                    }
                    if request.language in language_map:
                        self.session_manager.set_language(session.id, language_map[request.language])
                
                # Fetch updated session
                updated_session = self.session_manager.get_session(session.id)
                
                return SessionInfoModel(
                    id=updated_session.id,
                    position_name=updated_session.position_name if updated_session.position_name else None,
                    language=updated_session.language.value,
                    last_activity=updated_session.last_activity.isoformat()
                )
            except EmptyRecruiterIDError:
                raise HTTPException(
                    status_code=400,
                    detail="Recruiter ID is required"
                )
        
        @self.app.get("/api/sessions/{session_id}", response_model=SessionInfoModel)
        async def get_session(session_id: str) -> SessionInfoModel:
            """Get session details.
            
            Requirement 4.3: Load session context for the conversation.
            
            Args:
                session_id: The session identifier
                
            Returns:
                SessionInfoModel for the session
            """
            try:
                session = self.session_manager.get_session(session_id)
                if session is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Session not found"
                    )
                
                return SessionInfoModel(
                    id=session.id,
                    position_name=session.position_name if session.position_name else None,
                    language=session.language.value,
                    last_activity=session.last_activity.isoformat()
                )
            except EmptySessionIDError:
                raise HTTPException(
                    status_code=400,
                    detail="Session ID is required"
                )
        
        @self.app.get("/api/suggestions/{session_id}", response_model=SuggestionsResponseModel)
        async def get_suggestions(session_id: str) -> SuggestionsResponseModel:
            """Get available suggestions based on session state.
            
            Requirement 7.5: Query backend for available next actions.
            
            Args:
                session_id: The session identifier
                
            Returns:
                SuggestionsResponseModel with available suggestions
            """
            # Validate session exists
            session = self.session_manager.get_session(session_id)
            if session is None:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found"
                )
            
            suggestions = self.suggestion_service.get_suggestions(session_id)
            return SuggestionsResponseModel(suggestions=suggestions)
    
    def get_or_create_agent(self, session_id: str) -> Optional[TataAgent]:
        """Get existing agent for session or create new one.
        
        Initializes TataAgent with session context and caches it for reuse.
        
        Args:
            session_id: The session identifier
            
        Returns:
            TataAgent instance for the session, or None if session not found
        """
        # Return cached agent if exists
        if session_id in self.agents:
            return self.agents[session_id]
        
        # Verify session exists
        session = self.session_manager.get_session(session_id)
        if session is None:
            return None
        
        # Initialize agent components for this session
        # OpenAI client (shared across agents)
        openai_client = RealOpenAIClient(model="gpt-4o")
        
        # Tool registry (shared across agents)
        tool_registry = InMemoryToolRegistry()
        
        # Conversation manager (per session)
        conversation_manager = InMemoryConversationManager()
        
        # Tool executor (per session, uses shared memory and dependency managers)
        tool_executor = ToolExecutor(
            tool_registry=tool_registry,
            dependency_manager=self.dependency_manager,
            memory_manager=self.memory_manager,
            session_id=session_id,
        )
        
        # Create the agent
        agent = TataAgent(
            openai_client=openai_client,
            tool_registry=tool_registry,
            tool_executor=tool_executor,
            conversation_manager=conversation_manager,
        )
        
        # Cache the agent for reuse
        self.agents[session_id] = agent
        
        return agent
    
    def _check_port_available(self) -> None:
        """Check if the configured port is available.
        
        Raises:
            PortInUseError: If the port is already in use
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", self.port))
        except socket.error:
            raise PortInUseError(
                f"Error: Port {self.port} is already in use. "
                f"Please choose a different port or stop the process using port {self.port}."
            )
        finally:
            sock.close()
    
    def run(self) -> None:
        """Start the server.
        
        Raises:
            PortInUseError: If the configured port is already in use
        """
        import uvicorn
        
        # Check port availability before starting (Requirement 1.4)
        self._check_port_available()
        
        logger.info(f"Starting Tata chat server on port {self.port}")
        print(f"Tata chat interface available at http://localhost:{self.port}")
        
        uvicorn.run(
            self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="info",
        )
