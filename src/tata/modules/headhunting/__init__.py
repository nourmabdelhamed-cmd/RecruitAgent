"""Headhunting Messages module for Tata recruitment assistant.

This module implements Module E: Headhunting Messages creation.
Generates LinkedIn outreach messages in multiple styles and languages.
"""

from src.tata.modules.headhunting.headhunting import (
    HeadhuntingInput,
    HeadhuntingMessages,
    MultiLanguageMessage,
    MessageVersion,
    HeadhuntingProcessor,
    MessageTooLongError,
    MissingRequirementProfileError,
    InvalidHeadhuntingInputError,
    MessageStructure,
)

__all__ = [
    "HeadhuntingInput",
    "HeadhuntingMessages",
    "MultiLanguageMessage",
    "MessageVersion",
    "HeadhuntingProcessor",
    "MessageTooLongError",
    "MissingRequirementProfileError",
    "InvalidHeadhuntingInputError",
    "MessageStructure",
]
