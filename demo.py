"""Interactive demo session with Tata using OpenAI.

Run with: uv run python demo.py
"""

from src.tata.agent.agent import TataAgent
from src.tata.agent.client import RealOpenAIClient
from src.tata.agent.registry import InMemoryToolRegistry
from src.tata.agent.executor import ToolExecutor
from src.tata.agent.conversation import InMemoryConversationManager
from src.tata.dependency.dependency import InMemoryDependencyManager
from src.tata.memory.memory import InMemoryMemoryManager


def main():
    print("🚀 Starting Tata Demo Session")
    print("=" * 50)
    
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
    
    print("\n✅ Tata is ready! Type 'quit' to exit.\n")
    print("Try asking Tata to help with recruitment tasks like:")
    print("  - 'Create a requirement profile for a Senior Python Developer'")
    print("  - 'Review this job ad for improvements: [paste job ad]'")
    print("  - 'Create a funnel report for our Data Engineer position'")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("\n👋 Goodbye!")
                break
            
            print("\n🤖 Tata: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
