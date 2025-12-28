"""Demo script to test SQLite persistence.

Run this script multiple times to see sessions persist across restarts.

Usage:
    uv run python demo_persistence.py
"""

from src.tata.persistence import SQLiteSessionManager, SQLiteMemoryManager
from src.tata.session.session import SupportedLanguage


def main():
    # Use SQLite managers (data persists in tata.db)
    session_mgr = SQLiteSessionManager()
    memory_mgr = SQLiteMemoryManager()
    
    recruiter_id = "demo-recruiter"
    
    print("=" * 50)
    print("SQLite Persistence Demo")
    print("=" * 50)
    
    # Show existing sessions
    existing = session_mgr.list_sessions(recruiter_id)
    print(f"\nExisting sessions for '{recruiter_id}': {len(existing)}")
    
    for i, session in enumerate(existing, 1):
        print(f"  {i}. {session.id[:8]}... - '{session.position_name or '(no position)'}' "
              f"({session.language.value}) - {session.last_activity}")
    
    # Create a new session
    print("\nCreating new session...")
    new_session = session_mgr.create_session(recruiter_id)
    
    # Ask for position name
    position = input("Enter position name (or press Enter for 'Test Position'): ").strip()
    position = position or "Test Position"
    
    session_mgr.set_position_name(new_session.id, position)
    session_mgr.set_language(new_session.id, SupportedLanguage.ENGLISH)
    
    print(f"\nCreated session: {new_session.id}")
    print(f"Position: {position}")
    
    # Show updated list
    updated = session_mgr.list_sessions(recruiter_id)
    print(f"\nTotal sessions now: {len(updated)}")
    
    print("\n" + "=" * 50)
    print("Run this script again to see sessions persist!")
    print("Delete 'tata.db' to start fresh.")
    print("=" * 50)


if __name__ == "__main__":
    main()
