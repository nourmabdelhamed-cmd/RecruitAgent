# Tata - Talent Acquisition Team Assistant

Tata is GlobalConnect's conversational AI assistant for recruiters, supporting the full recruitment lifecycle through natural language interactions powered by OpenAI function calling.

## Architecture Overview

Tata follows a layered architecture with clear separation between AI orchestration, business logic, and persistence:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Interface Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  CLI Demo   │  │  Web Chat   │  │  Programmatic API       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Layer (OpenAI)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ TataAgent   │──│ OpenAI      │──│ ConversationManager     │  │
│  │             │  │ Client      │  │                         │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘  │
│         │                                                       │
│  ┌──────┴──────┐  ┌─────────────┐                               │
│  │ToolExecutor │──│ToolRegistry │                               │
│  └──────┬──────┘  └─────────────┘                               │
└─────────┼───────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────────┐
│         │              Core Layer                               │
│  ┌──────┴──────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Module      │  │ Dependency  │  │ Language                │  │
│  │ Processors  │  │ Manager     │  │ Processor               │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘  │
└─────────┼───────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────────┐
│         │           Persistence Layer                           │
│  ┌──────┴──────┐  ┌─────────────┐                               │
│  │ Memory      │  │ Session     │                               │
│  │ Manager     │  │ Manager     │                               │
│  └─────────────┘  └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Patterns

**Protocol → Implementation**: All managers use Protocol classes with swappable implementations for testability and flexibility:

| Protocol | Implementations |
|----------|-----------------|
| `SessionManager` | `InMemorySessionManager`, `SQLiteSessionManager` |
| `MemoryManager` | `InMemoryMemoryManager`, `SQLiteMemoryManager` |
| `DependencyManager` | `InMemoryDependencyManager` |
| `OpenAIClient` | `RealOpenAIClient`, `MockOpenAIClient` |
| `ConversationManager` | `InMemoryConversationManager` |

**Artifact Protocol**: All module outputs implement the `Artifact` protocol with `artifact_type` property and `to_json()` method for consistent storage and serialization.

**Validate-then-Process**: Module processors follow a two-step pattern where `validate()` checks inputs before `process()` generates outputs.

### Request Flow

```
User Message → TataAgent → OpenAI API (with tools)
                              ↓
                    Tool Call Response
                              ↓
              ToolExecutor → DependencyManager (check prerequisites)
                              ↓
                    Module Processor → Artifact
                              ↓
                    MemoryManager (store)
                              ↓
              OpenAI API (with tool result) → Natural Language Response
```

### Module Dependencies

Modules have explicit dependencies enforced by `DependencyManager`:

- **Standalone**: Requirement Profile, Funnel Report, Job Ad Review, D&I Review, Calendar Invite
- **Require Profile**: Job Ad, TA Screening, HM Screening, Headhunting
- **Require Profile + TA Screening**: Candidate Report

## Capabilities

- **Requirement Profiles** - Extract and structure job requirements
- **Job Ad Generation** - Create professional job advertisements
- **Job Ad Review** - Analyze and improve existing job ads
- **D&I Review** - Check content for diversity and inclusion
- **Screening Templates** - Generate TA and HM interview templates
- **Candidate Reports** - Summarize candidate evaluations
- **Funnel Reports** - Track recruitment pipeline metrics
- **Calendar Invites** - Generate interview scheduling content
- **Headhunting Messages** - Create LinkedIn outreach in 5 languages

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key

## Setup

```bash
git clone <repository-url>
cd tata
uv sync
cp .env.example .env  # Add OPENAI_API_KEY
uv run pytest         # Verify installation
```

## Usage

### CLI Demo

```bash
uv run python demo.py
```

### Persistent Sessions

```bash
uv run python demo_full.py
```

### Web Interface

```bash
uv run python chat_demo.py  # Opens at http://localhost:8080
```

### Programmatic

```python
from src.tata.agent.agent import TataAgent
from src.tata.agent.client import RealOpenAIClient
from src.tata.agent.registry import InMemoryToolRegistry
from src.tata.agent.executor import ToolExecutor
from src.tata.agent.conversation import InMemoryConversationManager
from src.tata.dependency.dependency import InMemoryDependencyManager
from src.tata.memory.memory import InMemoryMemoryManager

client = RealOpenAIClient(model="gpt-4o")
registry = InMemoryToolRegistry()
memory = InMemoryMemoryManager()
deps = InMemoryDependencyManager(memory)
conversation = InMemoryConversationManager()

executor = ToolExecutor(
    tool_registry=registry,
    dependency_manager=deps,
    memory_manager=memory,
    session_id="my-session",
)

agent = TataAgent(
    openai_client=client,
    tool_registry=registry,
    tool_executor=executor,
    conversation_manager=conversation,
)

response = agent.chat("Create a requirement profile for a Python developer")
```

## Project Structure

```
src/tata/
├── agent/        # AI orchestration (TataAgent, OpenAI client, executor, registry)
├── dependency/   # Module dependency management
├── interaction/  # User interaction handlers
├── language/     # Language processing (banned words, style checks)
├── memory/       # Artifact storage (MemoryManager protocol)
├── modules/      # Feature modules (profile, jobad, screening, report, etc.)
├── output/       # Output generation utilities
├── persistence/  # SQLite storage implementations
├── session/      # Session management (SessionManager protocol)
├── validator/    # Input validation
└── web/          # FastAPI chat server
```

## Development

```bash
uv run pytest                    # Run all tests
uv run pytest --cov=src/tata     # With coverage
uv run pytest -m "not integration"  # Skip OpenAI integration tests
```

## License

Proprietary - GlobalConnect
