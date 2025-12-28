---
inclusion: always
---

# Tech Stack & Development Guidelines

## Runtime

- Python 3.11+
- Package manager: `uv`
- Module: `tata` (located at `src/tata/`)

## Commands

| Action | Command |
|--------|---------|
| Run tests | `uv run pytest` |
| Run with coverage | `uv run pytest --cov=src/tata` |
| Target coverage | >80% line coverage |

## Architecture Patterns

### Protocol → Implementation Pattern

All managers use Protocol classes with in-memory implementations:

```python
# Protocol defines interface
class SessionManager(Protocol):
    def create_session(self, recruiter_id: str) -> Session: ...

# Implementation is thread-safe
class InMemorySessionManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict[str, Session] = {}
```

Current implementations:
- `SessionManager` → `InMemorySessionManager`, `SQLiteSessionManager`
- `MemoryManager` → `InMemoryMemoryManager`, `SQLiteMemoryManager`
- `DependencyManager` → `InMemoryDependencyManager`

### Data Modeling

- `@dataclass` for all data models
- `Enum` for type-safe constants (`SupportedLanguage`, `ModuleType`, `ArtifactType`)
- `Artifact` protocol for storable outputs: requires `artifact_type` property and `to_json()` method

### Thread Safety

All manager implementations MUST use `threading.Lock` for thread safety.

### Error Handling

- Define custom exceptions per module (e.g., `SessionNotFoundError`, `EmptySessionIDError`)
- Validate inputs at method entry
- Raise specific exceptions, never generic `Exception`

## Code Style

| Element | Convention | Example |
|---------|------------|---------|
| Classes/Protocols | PascalCase | `RequirementProfile` |
| Constants | UPPER_SNAKE_CASE | `MODULE_DEPENDENCIES` |
| Functions/variables | snake_case | `get_session` |
| Files | snake_case.py | `banned_words.py` |

### Documentation Requirements

- Module docstring: purpose + requirements covered
- Class docstring: attributes list
- Method docstring: Args, Returns, Raises sections

## Testing Requirements

### Framework

- `pytest` with `hypothesis` for property-based testing
- Minimum 100 iterations for property tests (configured in `tests/conftest.py`)

### Test Structure

Follow the pattern in existing tests (see `tests/test_funnel_report.py`):

```python
"""Tests for {Module Name}.

Tests cover:
- Requirement X.Y: Description
"""

class TestFeatureName:
    """Tests for specific feature."""
    
    def test_specific_behavior(self):
        """Test description matching requirement."""
        # Arrange
        # Act
        # Assert
```

### Test Organization

- Group related tests in classes
- Use descriptive test names: `test_{what}_{condition}_{expected}`
- Use `@pytest.fixture` for shared setup
- Reference requirements in docstrings

## AI Assistant Rules

1. **Never run Python via shell** - No `uv run python -c "..."` commands
2. **Write unit tests** - Always create tests instead of ad-hoc scripts
3. **Reuse test patterns** - Follow existing test file structure
4. **Follow Protocol pattern** - New managers need Protocol + Implementation
5. **Validate before processing** - All processors need `validate()` before `process()`
