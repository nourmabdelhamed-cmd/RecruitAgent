---
inclusion: always
---

# Project Structure

## Directory Layout

```
src/tata/
├── agent/              # AI agent orchestration (client, executor, conversation, registry)
├── dependency/         # Module dependency management
├── interaction/        # User interaction handlers (greeting)
├── language/           # Language processing (banned words, style checker)
├── memory/             # Artifact storage (MemoryManager protocol)
├── modules/            # Feature modules (one folder per module)
│   ├── calendar/       # Calendar invite generation
│   ├── headhunting/    # LinkedIn outreach messages
│   ├── jobad/          # Job ad generation
│   ├── profile/        # Requirement profile (foundation artifact)
│   ├── report/         # Candidate & funnel reports
│   ├── review/         # Job ad & D&I review
│   └── screening/      # TA/HM screening templates
├── output/             # Output generation utilities
├── persistence/        # SQLite-based persistent storage implementations
├── session/            # Session management (SessionManager protocol)
└── validator/          # Input validation

tests/
├── conftest.py         # Shared fixtures (hypothesis settings, common mocks)
└── test_*.py           # One test file per module/component
```

## File Placement Rules

| Component | Path Pattern | Example |
|-----------|--------------|---------|
| Module processor | `src/tata/modules/{name}/{name}.py` | `modules/profile/profile.py` |
| Module init | `src/tata/modules/{name}/__init__.py` | `modules/profile/__init__.py` |
| Core domain | `src/tata/{domain}/{domain}.py` | `session/session.py` |
| Tests | `tests/test_{name}.py` | `tests/test_profile.py` |

## Key Protocols & Implementations

| Protocol | Implementation | Location |
|----------|----------------|----------|
| `SessionManager` | `InMemorySessionManager` | `session/session.py` |
| `SessionManager` | `SQLiteSessionManager` | `persistence/sqlite.py` |
| `MemoryManager` | `InMemoryMemoryManager` | `memory/memory.py` |
| `MemoryManager` | `SQLiteMemoryManager` | `persistence/sqlite.py` |
| `DependencyManager` | `InMemoryDependencyManager` | `dependency/dependency.py` |
| `Artifact` | Per-module outputs | `modules/*/` |

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes/Protocols | PascalCase | `RequirementProfile`, `SessionManager` |
| Constants | UPPER_SNAKE_CASE | `MODULE_DEPENDENCIES` |
| Files/Functions | snake_case | `banned_words.py`, `check_banned_words` |

## Adding New Modules

1. Create `src/tata/modules/{name}/{name}.py` with:
   - Input dataclass (e.g., `{Name}Input`)
   - Output dataclass implementing `Artifact` protocol (`artifact_type` property, `to_json()` method)
   - Processor class with `validate()` and `process()` methods
2. Create `src/tata/modules/{name}/__init__.py` exporting public classes
3. Register in `MODULE_DEPENDENCIES` (in `dependency/dependency.py`) if module has prerequisites
4. Add `tests/test_{name}.py` following existing test patterns
