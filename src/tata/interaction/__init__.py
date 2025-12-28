"""Interaction module for Tata recruitment assistant.

This module provides recruiter interaction flows including greeting
and service menu functionality.
"""

from .greeting import (
    Greeting,
    ServiceMenuItem,
    ServiceMenu,
    generate_greeting,
    generate_service_menu,
    get_full_greeting_with_menu,
    FORBIDDEN_QUESTIONS,
    contains_forbidden_question,
)

__all__ = [
    "Greeting",
    "ServiceMenuItem",
    "ServiceMenu",
    "generate_greeting",
    "generate_service_menu",
    "get_full_greeting_with_menu",
    "FORBIDDEN_QUESTIONS",
    "contains_forbidden_question",
]
