---
inclusion: always
---

# Tata Product Context

Tata is GlobalConnect's Talent Acquisition Team Assistant—a conversational AI supporting recruiters through the recruitment lifecycle.

## Core Domain Concepts

| Concept | Description | Key Type |
|---------|-------------|----------|
| Session | One recruitment project; stateful with persistent artifacts | `Session` in `session/session.py` |
| Artifact | Storable output; requires `artifact_type` property + `to_json()` | `Artifact` protocol in `memory/memory.py` |
| RequirementProfile | Foundation artifact; most modules depend on it | `RequirementProfile` in `modules/profile/` |

## Module Dependency Rules

Always call `DependencyManager.can_execute(session_id, module)` before processing dependent modules.

**Standalone modules** (no prerequisites): `REQUIREMENT_PROFILE`, `FUNNEL_REPORT`, `JOB_AD_REVIEW`, `DI_REVIEW`, `CALENDAR_INVITE`

**Dependent modules**:
- `JOB_AD`, `TA_SCREENING`, `HM_SCREENING`, `HEADHUNTING` → require `REQUIREMENT_PROFILE`
- `CANDIDATE_REPORT` → requires `REQUIREMENT_PROFILE` + `TA_SCREENING`

Reference: `MODULE_DEPENDENCIES` dict in `dependency/dependency.py`

## Language & Localization

- Use `SupportedLanguage` enum: `EN` (default), `SV`, `DA`, `NO`, `DE`
- For German: call `get_german_formality(context)` to determine du/Sie formality
- Default to formal (Sie) when context is ambiguous

## Content Validation Rules (MANDATORY)

All generated text MUST pass these checks before output:

| Rule | Validation | Location |
|------|------------|----------|
| No emojis | `has_emojis(text)` must return `False` | `language/checker.py` |
| No dash bullets | `has_dash_bullets(text)` must return `False` | `language/checker.py` |
| No banned words | `check_banned_words(text, lang).has_banned_words` must be `False` | `language/checker.py` |
| No invented content | All skills/responsibilities must trace to `ContentSource` | `modules/profile/profile.py` |

## Content Generation Constraints

- **Never expose internal identifiers**: Use "requirement profile" not "Module A"
- **Never invent content**: Track all extracted content via `ContentSource` enum
- **Never collect personal data**: Do not ask for recruiter's personal name
- **Exactly 4 must-have skills**: `RequirementProfile.must_have_skills` is a 4-tuple

## Processor Pattern

Every module processor must implement:

```python
class {Name}Processor:
    def validate(self, input_data: {Name}Input) -> ValidationResult:
        """Validate before processing. Return errors/warnings."""
        ...
    
    def process(self, input_data: {Name}Input, ...) -> {Name}Output:
        """Process input. Call validate() first, raise InvalidInputError on failure."""
        ...
```

## Artifact Storage

Store artifacts via `MemoryManager.store(session_id, artifact)`. Artifacts must:
1. Implement `Artifact` protocol (runtime checkable)
2. Have `artifact_type` property returning `ArtifactType` enum value
3. Implement `to_json()` for serialization
