# Tech Stack

## Language & Runtime

- Python 3.11+
- Package manager: `uv`
- Module: `tata`

## Testing

- `hypothesis` - property-based testing framework
- `pytest` for unit tests
- Minimum 100 iterations for property tests
- Target: >80% line coverage

## Project Structure

```
src/tata/        # Application source code
tests/           # Test files
pyproject.toml   # Project configuration
```

## Common Commands

```bash
# Initialize project
uv init

# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/tata

# Run specific package tests
uv run pytest tests/session/

# Add a dependency
uv add hypothesis pytest
```

## Key Dependencies

- `hypothesis` - property-based testing
- `pytest` - test framework
- `pytest-cov` - coverage reporting

## Code Patterns

- Protocols for all managers (SessionManager, MemoryManager, DependencyManager)
- Generic ModuleProcessor protocol for all modules
- Artifact protocol for storable outputs
- Property tests validate 31 correctness properties
- Dataclasses for data models
- Enums for type-safe constants
- Don't run shell script with python code, do test
