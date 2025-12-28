"""Pydantic models for Tata web API request/response validation.

This module defines the data models used for API communication between
the frontend and backend.

Requirements covered:
- 5.1: Send message to Tata_Backend via HTTP POST
"""

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequestModel(BaseModel):
    """Request body for chat endpoint.
    
    Attributes:
        session_id: Active session identifier
        message: User's message text
    """
    session_id: str = Field(..., description="Active session identifier")
    message: str = Field(..., description="User's message text")


class ChatResponseModel(BaseModel):
    """Response body from chat endpoint.
    
    Attributes:
        response: Tata's response text (None on error)
        error: Error message if request failed (None on success)
        suggestions: List of context-aware next action suggestions
    """
    response: Optional[str] = Field(None, description="Tata's response text")
    error: Optional[str] = Field(None, description="Error message if request failed")
    suggestions: list[str] = Field(
        default_factory=list,
        description="Context-aware suggestions based on session state"
    )


class SessionInfoModel(BaseModel):
    """Session information for API responses.
    
    Attributes:
        id: Session identifier
        position_name: Job position name (may be empty)
        language: Output language code
        last_activity: ISO timestamp of last activity
    """
    id: str = Field(..., description="Session identifier")
    position_name: Optional[str] = Field(None, description="Job position name")
    language: str = Field(..., description="Output language code")
    last_activity: str = Field(..., description="ISO timestamp of last activity")


class CreateSessionModel(BaseModel):
    """Request body for creating a session.
    
    Attributes:
        recruiter_id: Recruiter identifier
        position_name: Job position name
        language: Language code (en, sv, da, no, de)
    """
    recruiter_id: str = Field(..., description="Recruiter identifier")
    position_name: str = Field(..., description="Job position name")
    language: str = Field(default="en", description="Language code (en, sv, da, no, de)")


class SuggestionsResponseModel(BaseModel):
    """Response body for suggestions endpoint.
    
    Attributes:
        suggestions: List of available next action suggestions
    """
    suggestions: list[str] = Field(
        default_factory=list,
        description="Available next action suggestions"
    )
