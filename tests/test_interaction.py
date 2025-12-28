"""Unit tests for Interaction module (greeting and service menu)."""

import pytest

from src.tata.interaction import (
    Greeting,
    ServiceMenuItem,
    ServiceMenu,
    generate_greeting,
    generate_service_menu,
    get_full_greeting_with_menu,
    FORBIDDEN_QUESTIONS,
    contains_forbidden_question,
)
from src.tata.session import SupportedLanguage, ModuleType


class TestGreeting:
    """Tests for Greeting dataclass and generation."""

    def test_default_greeting_is_english(self):
        """Default greeting should be in English (Req 12.1)."""
        greeting = generate_greeting()
        
        assert greeting.language == SupportedLanguage.ENGLISH

    def test_greeting_asks_for_position_not_name(self):
        """Greeting should ask for position, not recruiter name (Req 12.5)."""
        greeting = generate_greeting()
        
        assert greeting.asks_for_position is True
        assert "position" in greeting.message.lower()
        # Should not ask for recruiter's name
        assert not contains_forbidden_question(greeting.message)

    def test_greeting_introduces_tata(self):
        """Greeting should introduce Tata."""
        greeting = generate_greeting()
        
        assert "Tata" in greeting.message

    def test_greeting_with_explicit_english(self):
        """Greeting with explicit English language should work."""
        greeting = generate_greeting(SupportedLanguage.ENGLISH)
        
        assert greeting.language == SupportedLanguage.ENGLISH
        assert len(greeting.message) > 0


class TestServiceMenu:
    """Tests for ServiceMenu and ServiceMenuItem."""

    def test_service_menu_has_all_modules(self):
        """Service menu should list all 10 modules (Req 12.3)."""
        menu = generate_service_menu()
        
        assert len(menu.items) == 10

    def test_service_menu_items_have_display_names(self):
        """All menu items should have user-friendly display names."""
        menu = generate_service_menu()
        
        for item in menu.items:
            assert len(item.display_name) > 0
            assert item.display_name != item.module_type.value

    def test_service_menu_items_have_descriptions(self):
        """All menu items should have descriptions."""
        menu = generate_service_menu()
        
        for item in menu.items:
            assert len(item.description) > 0

    def test_service_menu_no_module_letters(self):
        """Menu items should not expose module letters (Req 3.5)."""
        menu = generate_service_menu()
        
        for item in menu.items:
            # Display name should not contain "Module A", "Module B", etc.
            assert "Module A" not in item.display_name
            assert "Module B" not in item.display_name
            assert "Module C" not in item.display_name
            # Description should not contain module letters
            assert "Module A" not in item.description
            assert "Module B" not in item.description

    def test_service_menu_marks_profile_dependencies(self):
        """Menu should indicate which modules require requirement profile."""
        menu = generate_service_menu()
        
        # Modules that require profile: B, C, D, E, F
        profile_required_modules = {
            ModuleType.JOB_AD,
            ModuleType.TA_SCREENING,
            ModuleType.HM_SCREENING,
            ModuleType.HEADHUNTING,
            ModuleType.CANDIDATE_REPORT,
        }
        
        for item in menu.items:
            if item.module_type in profile_required_modules:
                assert item.requires_profile is True
            else:
                assert item.requires_profile is False

    def test_service_menu_offers_guidance(self):
        """Menu should offer step-by-step guidance (Req 12.4)."""
        menu = generate_service_menu()
        
        assert "step by step" in menu.guidance_offer.lower() or "guide" in menu.guidance_offer.lower()

    def test_service_menu_recommends_starting_with_profile(self):
        """Menu should recommend starting with requirement profile (Req 12.4)."""
        menu = generate_service_menu()
        
        assert "requirement profile" in menu.guidance_offer.lower()


class TestFullGreetingWithMenu:
    """Tests for the combined greeting and menu output."""

    def test_full_greeting_contains_greeting(self):
        """Full output should contain the greeting message."""
        output = get_full_greeting_with_menu()
        
        assert "Tata" in output
        assert "position" in output.lower()

    def test_full_greeting_contains_all_services(self):
        """Full output should list all services."""
        output = get_full_greeting_with_menu()
        
        assert "Requirement Profile" in output
        assert "Job Ad" in output
        assert "Screening Template" in output
        assert "Headhunting" in output
        assert "Candidate Report" in output
        assert "Funnel Report" in output
        assert "D&I Review" in output
        assert "Calendar Invitation" in output

    def test_full_greeting_no_forbidden_questions(self):
        """Full output should not ask for recruiter's name (Req 12.5)."""
        output = get_full_greeting_with_menu()
        
        assert not contains_forbidden_question(output)


class TestForbiddenQuestions:
    """Tests for forbidden question detection (Req 12.5)."""

    def test_detects_direct_name_question(self):
        """Should detect 'what is your name'."""
        assert contains_forbidden_question("What is your name?") is True

    def test_detects_contracted_name_question(self):
        """Should detect 'what's your name'."""
        assert contains_forbidden_question("What's your name?") is True

    def test_detects_polite_name_request(self):
        """Should detect polite name requests."""
        assert contains_forbidden_question("May I have your name?") is True
        assert contains_forbidden_question("Can I have your name?") is True

    def test_detects_indirect_name_question(self):
        """Should detect indirect name questions."""
        assert contains_forbidden_question("Who am I speaking with?") is True
        assert contains_forbidden_question("Who am I talking to?") is True

    def test_allows_position_question(self):
        """Should allow questions about position."""
        assert contains_forbidden_question("What position are you recruiting for?") is False

    def test_allows_general_greeting(self):
        """Should allow general greetings without name questions."""
        assert contains_forbidden_question("Hello! How can I help you today?") is False

    def test_case_insensitive(self):
        """Detection should be case insensitive."""
        assert contains_forbidden_question("WHAT IS YOUR NAME?") is True
        assert contains_forbidden_question("What Is Your Name?") is True

    def test_all_forbidden_patterns_defined(self):
        """All forbidden patterns should be defined."""
        assert len(FORBIDDEN_QUESTIONS) > 0
        for pattern in FORBIDDEN_QUESTIONS:
            assert len(pattern) > 0
            assert pattern == pattern.lower()  # Should be lowercase


class TestServiceMenuItem:
    """Tests for ServiceMenuItem dataclass."""

    def test_service_menu_item_creation(self):
        """ServiceMenuItem should be creatable with all fields."""
        item = ServiceMenuItem(
            module_type=ModuleType.JOB_AD,
            display_name="Job Advertisement",
            description="Create a job ad",
            requires_profile=True,
        )
        
        assert item.module_type == ModuleType.JOB_AD
        assert item.display_name == "Job Advertisement"
        assert item.description == "Create a job ad"
        assert item.requires_profile is True

    def test_service_menu_item_default_requires_profile(self):
        """ServiceMenuItem should default requires_profile to False."""
        item = ServiceMenuItem(
            module_type=ModuleType.FUNNEL_REPORT,
            display_name="Funnel Report",
            description="Create a funnel report",
        )
        
        assert item.requires_profile is False
