"""Greeting and service menu for Tata recruitment assistant.

This module provides the initial greeting and service menu functionality
for recruiter interactions. It implements Requirements 12.1, 12.3, 12.4, and 12.5.

Requirements covered:
- 12.1: Greet recruiter in English by default
- 12.3: Display full service menu listing all available modules
- 12.4: Offer to guide step by step starting with requirement profile
- 12.5: Never ask for recruiter's personal name
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

from src.tata.session.session import ModuleType, SupportedLanguage


# Forbidden questions that should never be asked (Requirement 12.5)
FORBIDDEN_QUESTIONS = [
    "what is your name",
    "what's your name",
    "may i have your name",
    "can i have your name",
    "could you tell me your name",
    "your name please",
    "who am i speaking with",
    "who am i talking to",
    "and you are",
    "your name",
]


@dataclass
class ServiceMenuItem:
    """A single item in the service menu.
    
    Attributes:
        module_type: The module type this menu item represents
        display_name: User-friendly name (no module letters per Req 3.5)
        description: Brief description of what the module does
        requires_profile: Whether this module requires a requirement profile
    """
    module_type: ModuleType
    display_name: str
    description: str
    requires_profile: bool = False


# Service menu items with user-friendly names (no module letters per Req 3.5)
SERVICE_MENU_ITEMS: List[ServiceMenuItem] = [
    ServiceMenuItem(
        module_type=ModuleType.REQUIREMENT_PROFILE,
        display_name="Requirement Profile",
        description="Create a structured requirement profile from your start-up notes",
        requires_profile=False,
    ),
    ServiceMenuItem(
        module_type=ModuleType.JOB_AD,
        display_name="Job Ad",
        description="Create a professional job advertisement based on the requirement profile",
        requires_profile=True,
    ),
    ServiceMenuItem(
        module_type=ModuleType.TA_SCREENING,
        display_name="TA Screening Template",
        description="Create an interview template for talent acquisition recruiters",
        requires_profile=True,
    ),
    ServiceMenuItem(
        module_type=ModuleType.HM_SCREENING,
        display_name="HM Screening Template",
        description="Create an interview template for hiring managers",
        requires_profile=True,
    ),
    ServiceMenuItem(
        module_type=ModuleType.HEADHUNTING,
        display_name="Headhunting Messages",
        description="Create LinkedIn outreach messages in multiple styles and languages",
        requires_profile=True,
    ),
    ServiceMenuItem(
        module_type=ModuleType.CANDIDATE_REPORT,
        display_name="Candidate Report",
        description="Generate structured candidate reports from interview transcripts",
        requires_profile=True,
    ),
    ServiceMenuItem(
        module_type=ModuleType.FUNNEL_REPORT,
        display_name="Funnel Report",
        description="Create diagnostic funnel reports from ATS and LinkedIn data",
        requires_profile=False,
    ),
    ServiceMenuItem(
        module_type=ModuleType.JOB_AD_REVIEW,
        display_name="Job Ad Review",
        description="Review and improve an existing job advertisement",
        requires_profile=False,
    ),
    ServiceMenuItem(
        module_type=ModuleType.DI_REVIEW,
        display_name="D&I Review",
        description="Check job ads for biased or exclusionary language",
        requires_profile=False,
    ),
    ServiceMenuItem(
        module_type=ModuleType.CALENDAR_INVITE,
        display_name="Calendar Invitation",
        description="Create professional interview invitation text for candidates",
        requires_profile=False,
    ),
]


@dataclass
class ServiceMenu:
    """The complete service menu.
    
    Attributes:
        items: List of service menu items
        intro_text: Introduction text for the menu
        guidance_offer: Text offering step-by-step guidance
    """
    items: List[ServiceMenuItem] = field(default_factory=lambda: SERVICE_MENU_ITEMS.copy())
    intro_text: str = "Here's what I can help you with:"
    guidance_offer: str = (
        "I recommend starting with the Requirement Profile as it forms the foundation "
        "for most other outputs. Would you like me to guide you step by step?"
    )


@dataclass
class Greeting:
    """The greeting message for recruiters.
    
    Attributes:
        message: The greeting message text
        language: The language of the greeting
        asks_for_position: Whether the greeting asks for position name
    """
    message: str
    language: SupportedLanguage = SupportedLanguage.ENGLISH
    asks_for_position: bool = True


# Default English greeting (Requirement 12.1)
DEFAULT_GREETING = Greeting(
    message=(
        "Hello! I'm Tata, your Talent Acquisition Team Assistant. "
        "I'm here to support you through the recruitment process. "
        "What position are you recruiting for today?"
    ),
    language=SupportedLanguage.ENGLISH,
    asks_for_position=True,
)


def generate_greeting(language: SupportedLanguage = SupportedLanguage.ENGLISH) -> Greeting:
    """Generate a greeting message for the recruiter.
    
    The greeting is in English by default per Requirement 12.1.
    It asks for the position name (not recruiter name) per Requirement 12.5.
    
    Args:
        language: The language for the greeting (default English)
        
    Returns:
        A Greeting instance with the appropriate message
    """
    # Currently only English is implemented for greeting
    # Other languages can be added as needed
    if language == SupportedLanguage.ENGLISH:
        return DEFAULT_GREETING
    
    # For other languages, return English for now
    # This can be extended with translations
    return DEFAULT_GREETING


def generate_service_menu() -> ServiceMenu:
    """Generate the service menu listing all available modules.
    
    The menu uses user-friendly names without module letters
    per Requirement 3.5.
    
    Returns:
        A ServiceMenu instance with all available services
    """
    return ServiceMenu()


def get_full_greeting_with_menu(
    language: SupportedLanguage = SupportedLanguage.ENGLISH
) -> str:
    """Get the complete greeting with service menu as formatted text.
    
    This combines the greeting and service menu into a single formatted
    string suitable for display to the recruiter.
    
    Args:
        language: The language for the greeting (default English)
        
    Returns:
        Formatted string with greeting and service menu
    """
    greeting = generate_greeting(language)
    menu = generate_service_menu()
    
    lines = [greeting.message, "", menu.intro_text, ""]
    
    for item in menu.items:
        profile_note = " (requires requirement profile)" if item.requires_profile else ""
        lines.append(f"• {item.display_name}{profile_note}")
        lines.append(f"  {item.description}")
        lines.append("")
    
    lines.append(menu.guidance_offer)
    
    return "\n".join(lines)


def contains_forbidden_question(text: str) -> bool:
    """Check if text contains a forbidden question about recruiter's name.
    
    Per Requirement 12.5, the system should never ask for the recruiter's
    personal name.
    
    Args:
        text: The text to check
        
    Returns:
        True if the text contains a forbidden question, False otherwise
    """
    text_lower = text.lower()
    return any(forbidden in text_lower for forbidden in FORBIDDEN_QUESTIONS)
