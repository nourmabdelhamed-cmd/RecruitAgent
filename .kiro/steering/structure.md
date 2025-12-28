# Project Structure

```
tata/
├── src/
│   └── tata/                     # Application source code
│       ├── __init__.py
│       ├── session/              # Session management
│       │   └── session.py        # Session dataclass, SessionManager protocol
│       ├── memory/               # Artifact storage
│       │   └── memory.py         # MemoryManager, Artifact protocol
│       ├── dependency/           # Module dependency enforcement
│       │   └── dependency.py     # DependencyManager, MODULE_DEPENDENCIES dict
│       ├── language/             # Language processing
│       │   ├── banned_words.py   # Banned word lists per language
│       │   └── checker.py        # Style guide validation
│       ├── modules/              # Module processors
│       │   ├── profile/          # Module A: Requirement Profile
│       │   ├── jobad/            # Module B: Job Ad
│       │   ├── screening/        # Module C/D: Screening Templates
│       │   ├── headhunting/      # Module E: Headhunting Messages
│       │   ├── report/           # Module F/G: Candidate & Funnel Reports
│       │   ├── review/           # Module H/I: Job Ad & D&I Reviews
│       │   └── calendar/         # Module J: Calendar Invitations
│       ├── interaction/          # User interaction flows
│       │   └── greeting.py       # Service menu, greeting logic
│       ├── output/               # Document generation
│       │   └── generator.py      # Word-ready output, comparison tables
│       └── validator/            # Output validation
│           └── validator.py      # Profile alignment, language compliance
├── tests/                        # Test files
│   ├── conftest.py               # Pytest fixtures
│   ├── test_session.py
│   ├── test_memory.py
│   └── ...
├── pyproject.toml                # Project configuration
└── uv.lock                       # Lock file
```

## Key Files

- `src/tata/session/session.py` - Session lifecycle, language settings
- `src/tata/memory/memory.py` - Artifact storage/retrieval by session
- `src/tata/dependency/dependency.py` - Module dependency map and checks
- `src/tata/modules/*/` - Each module has its own processor implementing `ModuleProcessor[TInput, TOutput]`

## Naming Conventions

- Types: PascalCase (`RequirementProfile`, `JobAd`)
- Protocols: PascalCase with descriptive names (`SessionManager`, `MemoryManager`)
- Constants: UPPER_SNAKE_CASE for module-level (`MODULE_DEPENDENCIES`)
- Files: snake_case (`banned_words.py`)
- Functions: snake_case (`check_banned_words`)
