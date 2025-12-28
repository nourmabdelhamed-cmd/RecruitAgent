"""Web interface for Tata recruitment assistant.

This module provides a FastAPI-based web server for the chat interface,
replacing the terminal-based interaction with a browser-based UI.
"""

from src.tata.web.server import ChatServer, PortInUseError
from src.tata.web.models import (
    ChatRequestModel,
    ChatResponseModel,
    SessionInfoModel,
    CreateSessionModel,
    SuggestionsResponseModel,
)

__all__ = [
    "ChatServer",
    "PortInUseError",
    "ChatRequestModel",
    "ChatResponseModel",
    "SessionInfoModel",
    "CreateSessionModel",
    "SuggestionsResponseModel",
]
