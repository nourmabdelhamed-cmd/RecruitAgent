"""Automated demo session with Tata using OpenAI.

Run with: uv run python demo_auto.py
"""

from dotenv import load_dotenv
load_dotenv()

from src.tata.agent.agent import TataAgent
from src.tata.agent.client import RealOpenAIClient
from src.tata.agent.registry import InMemoryToolRegistry
from src.tata.agent.executor import ToolExecutor
from src.tata.agent.conversation import InMemoryConversationManager
from src.tata.dependency.dependency import InMemoryDependencyManager
from src.tata.memory.memory import InMemoryMemoryManager


def main():
    print("🚀 Starting Tata Demo Session")
    print("=" * 60)
    
    # Initialize components
    client = RealOpenAIClient(model="gpt-4o")
    registry = InMemoryToolRegistry()
    memory = InMemoryMemoryManager()
    deps = InMemoryDependencyManager(memory)
    conversation = InMemoryConversationManager()
    
    # Create session
    session_id = "demo-session-001"
    
    # Create executor with session
    executor = ToolExecutor(
        tool_registry=registry,
        dependency_manager=deps,
        memory_manager=memory,
        session_id=session_id,
    )
    
    # Create agent
    agent = TataAgent(
        openai_client=client,
        tool_registry=registry,
        tool_executor=executor,
        conversation_manager=conversation,
    )
    
    print("\n✅ Tata initialized successfully!\n")
    
    # Demo conversation
    demo_messages = [
        "Hi! I need help creating a requirement profile for a Senior Python Developer position. "
        "Here are the notes from our startup meeting:\n\n"
        "Position: Senior Python Developer\n"
        "Team: Platform Engineering\n"
        "Location: Stockholm (hybrid)\n\n"
        "Must-have skills:\n"
        "- 5+ years Python experience\n"
        "- Experience with FastAPI or Django\n"
        "- Strong SQL and database design skills\n"
        "- Experience with AWS services\n\n"
        "Nice-to-have:\n"
        "- Kubernetes experience\n"
        "- CI/CD pipeline experience\n\n"
        "Responsibilities:\n"
        "- Design and build scalable backend services\n"
        "- Mentor junior developers\n"
        "- Participate in code reviews\n"
        "- Collaborate with product team on technical solutions",
    ]
    
    for i, message in enumerate(demo_messages, 1):
        print(f"\n{'='*60}")
        print(f"📝 Demo Message {i}:")
        print("-" * 60)
        print(message[:200] + "..." if len(message) > 200 else message)
        print("-" * 60)
        
        print("\n🤖 Tata's Response:")
        print("-" * 60)
        response = agent.chat(message)
        print(response)
        print("-" * 60)
    
    print("\n" + "=" * 60)
    print("✅ Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
