"""Job Ad module for Tata recruitment assistant.

This module implements Module B: Job Ad creation.
"""

from src.tata.modules.jobad.jobad import (
    JobAd,
    JobAdInput,
    RequirementsSection,
    JobAdProcessor,
    MissingRequirementProfileError,
)

__all__ = [
    "JobAd",
    "JobAdInput",
    "RequirementsSection",
    "JobAdProcessor",
    "MissingRequirementProfileError",
]
