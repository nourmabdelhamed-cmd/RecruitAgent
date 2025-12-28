# Tata - Talent Acquisition Team Assistant

Tata is GlobalConnect's conversational AI assistant for recruiters, supporting the full recruitment lifecycle through natural language interactions.

## What Tata Does

Tata helps recruiters with:

- **Requirement Profiles** - Extract and structure job requirements from conversations
- **Job Ad Generation** - Create professional job advertisements
- **Job Ad Review** - Analyze and improve existing job ads
- **D&I Review** - Check content for diversity and inclusion
- **Screening Templates** - Generate TA and HM screening question templates
- **Candidate Reports** - Summarize candidate evaluations
- **Funnel Reports** - Track recruitment pipeline metrics
- **Calendar Invites** - Generate interview scheduling content
- **Headhunting Messages** - Create LinkedIn outreach messages

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key

## Setup

1. **Clone and install dependencies:**

```bash
git clone <repository-url>
cd tata
uv sync
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-key-here
```

3. **Verify installation:**

```bash
uv run pytest
```

## Usage

Tata offers three ways to interact: CLI demo, persistent sessions, and web interface.

### Quick Start (CLI Demo)

The simplest way to try Tata:

```bash
uv run python demo.py
```

This starts an interactive terminal session. Type your requests and Tata responds. Type `quit` to exit.

Example prompts:
- "Create a requirement profile for a Senior Python Developer"
- "Review this job ad for improvements: [paste job ad]"
- "Create a funnel report for our Data Engineer position"

### Persistent Sessions

For multi-session workflows with data persistence:

```bash
uv run python demo_full.py
```

Features:
- Create and resume recruitment sessions
- Data persists across restarts (stored in `tata.db`)
- Multi-language support (English, Swedish, Danish, Norwegian, German)
- Session history per recruiter

### Web Interface

Browser-based chat interface:

```bash
uv run python chat_demo.py
```

Opens at http://localhost:8080. Use `--port` to change the port:

```bash
uv run python chat_demo.py --port 3000
```

### Programmatic Usage

```python
from src.tata.agent.agent import TataAgent
from src.tata.agent.client import RealOpenAIClient
from src.tata.agent.registry import InMemoryToolRegistry
from src.tata.agent.executor import ToolExecutor
from src.tata.agent.conversation import InMemoryConversationManager
from src.tata.dependency.dependency import InMemoryDependencyManager
from src.tata.memory.memory import InMemoryMemoryManager

# Initialize components
client = RealOpenAIClient(model="gpt-4o")
registry = InMemoryToolRegistry()
memory = InMemoryMemoryManager()
deps = InMemoryDependencyManager(memory)
conversation = InMemoryConversationManager()

session_id = "my-session"
executor = ToolExecutor(
    tool_registry=registry,
    dependency_manager=deps,
    memory_manager=memory,
    session_id=session_id,
)

agent = TataAgent(
    openai_client=client,
    tool_registry=registry,
    tool_executor=executor,
    conversation_manager=conversation,
)

# Chat with Tata
response = agent.chat("Help me create a job ad for a frontend developer")
print(response)
```

For persistent storage, use SQLite managers:

```python
from src.tata.persistence import SQLiteSessionManager, SQLiteMemoryManager

session_mgr = SQLiteSessionManager()  # Uses tata.db
memory_mgr = SQLiteMemoryManager()
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/tata

# Skip integration tests (requires OpenAI API)
uv run pytest -m "not integration"
```

### Project Structure

```
src/tata/
├── agent/        # AI orchestration (OpenAI client, executor, conversation)
├── dependency/   # Module dependency management
├── interaction/  # User interaction handlers
├── language/     # Language processing (banned words, style checks)
├── memory/       # Artifact storage
├── modules/      # Feature modules (profile, jobad, screening, etc.)
├── output/       # Output generation utilities
├── persistence/  # SQLite storage implementations
├── session/      # Session management
├── validator/    # Input validation
└── web/          # Web chat server
```

### Architecture

Tata uses a Protocol → Implementation pattern for all managers:

- `SessionManager` → `InMemorySessionManager`, `SQLiteSessionManager`
- `MemoryManager` → `InMemoryMemoryManager`, `SQLiteMemoryManager`
- `DependencyManager` → `InMemoryDependencyManager`

Module processors follow a validate-then-process pattern with `Artifact` outputs stored via `MemoryManager`.

## License

Proprietary - GlobalConnect
