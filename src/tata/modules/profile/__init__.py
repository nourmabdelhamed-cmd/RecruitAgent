"""Module A: Requirement Profile.

The requirement profile is the foundational document for all recruitment outputs.
It contains must-have skills, responsibilities, and role details.
"""

from src.tata.modules.profile.profile import (
    RequirementProfileInput,
    RequirementProfile,
    TeamInfo,
    ContentSource,
    TrackedContent,
    ValidationError,
    ValidationWarning,
    ValidationResult,
    RequirementProfileProcessor,
    InvalidInputError,
    InsufficientSkillsError,
)

__all__ = [
    "RequirementProfileInput",
    "RequirementProfile",
    "TeamInfo",
    "ContentSource",
    "TrackedContent",
    "ValidationError",
    "ValidationWarning",
    "ValidationResult",
    "RequirementProfileProcessor",
    "InvalidInputError",
    "InsufficientSkillsError",
]
