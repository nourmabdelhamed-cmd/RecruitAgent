"""Full interactive demo with persistent sessions.

This demo integrates session persistence with the chat functionality,
allowing users to:
- Create new recruitment sessions
- Resume existing sessions
- Chat with Tata using OpenAI
- Have all data persist across restarts

Usage:
    uv run python demo_full.py
"""

from src.tata.agent.agent import TataAgent
from src.tata.agent.client import RealOpenAIClient
from src.tata.agent.registry import InMemoryToolRegistry
from src.tata.agent.executor import ToolExecutor
from src.tata.agent.conversation import InMemoryConversationManager
from src.tata.dependency.dependency import InMemoryDependencyManager
from src.tata.persistence import SQLiteSessionManager, SQLiteMemoryManager
from src.tata.session.session import SupportedLanguage, Session


LANGUAGES = {
    "1": SupportedLanguage.ENGLISH,
    "2": SupportedLanguage.SWEDISH,
    "3": SupportedLanguage.DANISH,
    "4": SupportedLanguage.NORWEGIAN,
    "5": SupportedLanguage.GERMAN,
}


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def get_recruiter_id() -> str:
    """Get or create recruiter identifier."""
    print_header("Welcome to Tata")
    print("\nEnter your recruiter ID (or press Enter for 'default-recruiter'):")
    recruiter_id = input("> ").strip()
    return recruiter_id or "default-recruiter"


def select_language() -> SupportedLanguage:
    """Let user select output language."""
    print("\nSelect output language:")
    print("  1. English (default)")
    print("  2. Swedish")
    print("  3. Danish")
    print("  4. Norwegian")
    print("  5. German")
    choice = input("> ").strip()
    return LANGUAGES.get(choice, SupportedLanguage.ENGLISH)


def display_sessions(sessions: list[Session]) -> None:
    """Display existing sessions."""
    if not sessions:
        print("\n  No existing sessions found.")
        return
    
    print(f"\n  Found {len(sessions)} existing session(s):\n")
    for i, session in enumerate(sessions, 1):
        position = session.position_name or "(no position set)"
        lang = session.language.value.upper()
        date = session.last_activity.strftime("%Y-%m-%d %H:%M")
        print(f"  {i}. [{lang}] {position}")
        print(f"      Last active: {date}")
        print(f"      ID: {session.id[:8]}...")


def select_or_create_session(
    session_mgr: SQLiteSessionManager,
    recruiter_id: str
) -> Session:
    """Let user select existing session or create new one."""
    sessions = session_mgr.list_sessions(recruiter_id)
    
    print_header("Session Selection")
    display_sessions(sessions)
    
    print("\n  Options:")
    print("  n - Create new session")
    if sessions:
        print("  1-{} - Resume existing session".format(len(sessions)))
    print("  q - Quit")
    
    while True:
        choice = input("\n> ").strip().lower()
        
        if choice == "q":
            return None
        
        if choice == "n":
            return create_new_session(session_mgr, recruiter_id)
        
        if sessions and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                session = sessions[idx]
                print(f"\n  Resuming session: {session.position_name or 'Unnamed'}")
                return session
        
        print("  Invalid choice. Try again.")


def create_new_session(
    session_mgr: SQLiteSessionManager,
    recruiter_id: str
) -> Session:
    """Create a new recruitment session."""
    print_header("New Session Setup")
    
    # Get position name
    print("\nWhat position are you recruiting for?")
    position = input("> ").strip()
    if not position:
        position = "Untitled Position"
    
    # Select language
    language = select_language()
    
    # Create session
    session = session_mgr.create_session(recruiter_id)
    session_mgr.set_position_name(session.id, position)
    session_mgr.set_language(session.id, language)
    
    print(f"\n  Created session for: {position}")
    print(f"  Language: {language.value.upper()}")
    
    return session


def run_chat(session: Session, memory_mgr: SQLiteMemoryManager) -> None:
    """Run the interactive chat loop."""
    print_header(f"Chat: {session.position_name}")
    
    # Initialize agent components
    client = RealOpenAIClient(model="gpt-4o")
    registry = InMemoryToolRegistry()
    deps = InMemoryDependencyManager(memory_mgr)
    conversation = InMemoryConversationManager()
    
    executor = ToolExecutor(
        tool_registry=registry,
        dependency_manager=deps,
        memory_manager=memory_mgr,
        session_id=session.id,
    )
    
    agent = TataAgent(
        openai_client=client,
        tool_registry=registry,
        tool_executor=executor,
        conversation_manager=conversation,
    )
    
    print("\nTata is ready! Commands:")
    print("  'quit' or 'q' - Return to session menu")
    print("  'clear' - Clear conversation history")
    print("\nTry asking Tata to help with:")
    print("  - Create a requirement profile")
    print("  - Generate a job ad")
    print("  - Review a job ad for improvements")
    print("  - Create screening questions")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ("quit", "exit", "q"):
                print("\nReturning to session menu...")
                break
            
            if user_input.lower() == "clear":
                conversation.clear()
                print("Conversation cleared.")
                continue
            
            print("\nTata: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\nReturning to session menu...")
            break
        except Exception as e:
            print(f"\nError: {e}")


def main():
    """Main entry point."""
    # Initialize persistent managers
    session_mgr = SQLiteSessionManager()
    memory_mgr = SQLiteMemoryManager()
    
    try:
        recruiter_id = get_recruiter_id()
        print(f"\n  Logged in as: {recruiter_id}")
        
        while True:
            session = select_or_create_session(session_mgr, recruiter_id)
            
            if session is None:
                print("\nGoodbye!")
                break
            
            run_chat(session, memory_mgr)
    
    except KeyboardInterrupt:
        print("\n\nGoodbye!")


if __name__ == "__main__":
    main()
