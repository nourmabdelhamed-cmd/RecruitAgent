"""Integration tests for OpenAI function calling with real API.

These tests verify end-to-end conversation flows using the real OpenAI API.
They require the OPENAI_API_KEY environment variable to be set.

Run these tests separately: uv run pytest -m integration

Requirements covered:
- 7.6: Integration tests that call the real OpenAI API
- 7.7: Read API key from OPENAI_API_KEY environment variable
- 7.8: Marked with pytest marker for separate execution
- 7.9: Verify end-to-end conversation flows including tool calling
"""

import os
import json
import pytest

from src.tata.agent.agent import TataAgent
from src.tata.agent.client import RealOpenAIClient
from src.tata.agent.conversation import InMemoryConversationManager
from src.tata.agent.executor import ToolExecutor
from src.tata.agent.models import MessageRole
from src.tata.agent.registry import InMemoryToolRegistry
from src.tata.dependency.dependency import InMemoryDependencyManager
from src.tata.memory.memory import InMemoryMemoryManager, ArtifactType


# Skip all tests in this module if OPENAI_API_KEY is not set
pytestmark = pytest.mark.integration


def _api_key_available() -> bool:
    """Check if OpenAI API key is available."""
    return bool(os.environ.get("OPENAI_API_KEY"))


@pytest.fixture
def real_openai_client():
    """Provide real OpenAI client for integration tests.
    
    Skips test if OPENAI_API_KEY is not set (Requirement 7.7).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set - skipping integration test")
    return RealOpenAIClient(api_key=api_key, model="gpt-4o-mini", timeout=60.0)


@pytest.fixture
def memory_manager():
    """Create a fresh memory manager for each test."""
    return InMemoryMemoryManager()


@pytest.fixture
def dependency_manager(memory_manager):
    """Create a dependency manager with the memory manager."""
    return InMemoryDependencyManager(memory_manager)


@pytest.fixture
def tool_registry():
    """Create a tool registry with all Tata tools."""
    return InMemoryToolRegistry()


@pytest.fixture
def conversation_manager():
    """Create a conversation manager."""
    return InMemoryConversationManager()


@pytest.fixture
def session_id():
    """Create a test session ID."""
    return "integration-test-session"


@pytest.fixture
def tool_executor(tool_registry, dependency_manager, memory_manager, session_id):
    """Create a ToolExecutor with all dependencies."""
    return ToolExecutor(
        tool_registry=tool_registry,
        dependency_manager=dependency_manager,
        memory_manager=memory_manager,
        session_id=session_id,
    )


@pytest.fixture
def agent(real_openai_client, tool_registry, tool_executor, conversation_manager):
    """Create a TataAgent with real OpenAI client (Requirement 7.6).
    
    This factory creates an agent configured for integration testing
    with the real OpenAI API.
    """
    return TataAgent(
        openai_client=real_openai_client,
        tool_registry=tool_registry,
        tool_executor=tool_executor,
        conversation_manager=conversation_manager,
    )



class TestIntegrationFixtures:
    """Tests to verify integration test fixtures work correctly."""
    
    def test_real_client_initializes(self, real_openai_client):
        """Real OpenAI client should initialize with API key."""
        assert real_openai_client is not None
        assert real_openai_client._api_key is not None
    
    def test_agent_factory_creates_agent(self, agent):
        """Agent factory should create a working agent."""
        assert agent is not None
        assert agent._client is not None
        assert agent._registry is not None
        assert agent._executor is not None
        assert agent._conversation is not None


class TestRequirementProfileFlow:
    """Integration tests for requirement profile creation flow (Requirement 7.9)."""
    
    def test_create_requirement_profile(self, agent, memory_manager, session_id):
        """Test creating a requirement profile through natural conversation.
        
        Verifies end-to-end flow: user message -> OpenAI -> tool call -> artifact storage.
        """
        response = agent.chat(
            "I need to hire a Senior Python Developer. "
            "They should have 5+ years of Python experience, "
            "knowledge of Django and FastAPI, "
            "experience with PostgreSQL and Redis, "
            "and good communication skills. "
            "The role is for our backend team."
        )
        
        # Response should acknowledge the profile creation
        assert response is not None
        assert len(response) > 0
        
        # Artifact should be stored
        assert memory_manager.has_artifact(session_id, ArtifactType.REQUIREMENT_PROFILE)
        
        # Retrieve and verify the artifact has content
        profile = memory_manager.retrieve(session_id, ArtifactType.REQUIREMENT_PROFILE)
        assert profile is not None


class TestJobAdFlow:
    """Integration tests for job ad generation flow with dependency (Requirement 7.9)."""
    
    def test_create_job_ad_after_profile(self, agent, memory_manager, session_id):
        """Test creating a job ad after requirement profile exists.
        
        Verifies the dependency chain: profile must exist before job ad.
        """
        # First create a requirement profile
        agent.chat(
            "Create a requirement profile for a Frontend Developer position. "
            "Must have React and TypeScript experience, 3+ years, "
            "knowledge of modern CSS and responsive design."
        )
        
        # Verify profile was created
        assert memory_manager.has_artifact(session_id, ArtifactType.REQUIREMENT_PROFILE)
        
        # Now create a job ad
        response = agent.chat(
            "Now create a job advertisement for this position."
        )
        
        # Response should acknowledge the job ad creation
        assert response is not None
        assert len(response) > 0
        
        # Job ad artifact should be stored
        assert memory_manager.has_artifact(session_id, ArtifactType.JOB_AD)


class TestDependencyErrorHandling:
    """Integration tests for error handling with missing dependencies (Requirement 7.9)."""
    
    def test_job_ad_without_profile_explains_dependency(self, agent, memory_manager, session_id):
        """Test that creating job ad without profile explains the dependency.
        
        Verifies that the agent explains what prerequisites are needed.
        """
        # Try to create job ad without profile
        response = agent.chat(
            "Create a job advertisement for a Data Scientist position."
        )
        
        # Response should mention the need for a requirement profile
        response_lower = response.lower()
        assert (
            "requirement profile" in response_lower or
            "profile" in response_lower or
            "first" in response_lower or
            "need" in response_lower
        )
        
        # Job ad should NOT be created
        assert not memory_manager.has_artifact(session_id, ArtifactType.JOB_AD)


class TestMultiTurnConversation:
    """Integration tests for multi-turn conversation flows (Requirement 7.9)."""
    
    def test_multi_turn_conversation_maintains_context(self, agent, conversation_manager):
        """Test that context is maintained across multiple turns.
        
        Verifies that the agent remembers previous messages in the conversation.
        """
        # First turn: introduce the context
        response1 = agent.chat(
            "I'm recruiting for a DevOps Engineer position at GlobalConnect."
        )
        assert response1 is not None
        
        # Second turn: ask a follow-up that requires context
        response2 = agent.chat(
            "What information do you need from me to create a requirement profile for this role?"
        )
        assert response2 is not None
        
        # Verify conversation has multiple turns
        messages = conversation_manager.get_messages()
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        assert len(user_messages) >= 2
        
        # Response should be contextually relevant
        response2_lower = response2.lower()
        assert any(word in response2_lower for word in [
            "skill", "requirement", "experience", "qualification",
            "responsibility", "information", "need", "tell"
        ])
    
    def test_full_workflow_profile_to_screening(self, agent, memory_manager, session_id):
        """Test a complete workflow from profile to screening template.
        
        Verifies multi-step workflow with dependencies.
        """
        # Step 1: Create requirement profile
        agent.chat(
            "Create a requirement profile for a QA Engineer. "
            "Requirements: 3+ years testing experience, "
            "knowledge of Selenium and Cypress, "
            "experience with CI/CD pipelines, "
            "strong attention to detail."
        )
        assert memory_manager.has_artifact(session_id, ArtifactType.REQUIREMENT_PROFILE)
        
        # Step 2: Create TA screening template
        response = agent.chat(
            "Now create a TA screening interview template for this position."
        )
        
        assert response is not None
        # TA screening should be created
        assert memory_manager.has_artifact(session_id, ArtifactType.TA_SCREENING_TEMPLATE)


class TestStandaloneModules:
    """Integration tests for standalone modules without dependencies."""
    
    def test_funnel_report_standalone(self, agent, memory_manager, session_id):
        """Test creating a funnel report (no dependencies required)."""
        response = agent.chat(
            "Create a funnel report for the Software Engineer position. "
            "We have 1 position to fill, hiring manager is John Smith. "
            "We had 500 job ad views, 100 applications, "
            "20 TA screenings, 10 HM interviews, 3 offers made, 2 accepted."
        )
        
        assert response is not None
        assert memory_manager.has_artifact(session_id, ArtifactType.FUNNEL_REPORT)
    
    def test_calendar_invite_standalone(self, agent, memory_manager, session_id):
        """Test creating a calendar invite (no dependencies required)."""
        response = agent.chat(
            "Create a calendar invite for an interview. "
            "Position: Product Manager. "
            "Hiring manager: Sarah Johnson, VP of Product. "
            "Recruiter: Mike Brown. "
            "It's a 60-minute hiring manager interview on Teams. "
            "Use Jobylon for booking."
        )
        
        assert response is not None
        assert memory_manager.has_artifact(session_id, ArtifactType.CALENDAR_INVITE)
    
    def test_job_ad_review_standalone(self, agent, memory_manager, session_id):
        """Test reviewing a job ad (no dependencies required)."""
        job_ad_text = """
        Senior Software Engineer
        
        We are looking for a rockstar developer to join our team!
        
        Requirements:
        - 5+ years experience
        - Python, Java, or similar
        - Team player
        
        Apply now!
        """
        
        response = agent.chat(
            f"Please review this job ad for improvements:\n\n{job_ad_text}"
        )
        
        assert response is not None
        assert memory_manager.has_artifact(session_id, ArtifactType.JOB_AD_REVIEW)
    
    def test_di_review_standalone(self, agent, memory_manager, session_id):
        """Test D&I review of a job ad (no dependencies required)."""
        job_ad_text = """
        Looking for a young, energetic salesman to join our team.
        Must be a native English speaker.
        We need someone who can hit the ground running.
        """
        
        response = agent.chat(
            f"Check this job ad for diversity and inclusion issues:\n\n{job_ad_text}"
        )
        
        assert response is not None
        assert memory_manager.has_artifact(session_id, ArtifactType.DI_REVIEW)
