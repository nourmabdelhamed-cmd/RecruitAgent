"""Review modules for Tata recruitment assistant.

This package contains review-related modules:
- D&I Review (Module I): Diversity and Inclusion review for bias-free language
- Job Ad Review (Module H): Structured review and improvement suggestions for job ads
"""

from src.tata.modules.review.di import (
    BiasCategory,
    Severity,
    FlaggedItem,
    CategoryScore,
    DIReviewInput,
    DIReview,
    DIReviewProcessor,
)

from src.tata.modules.review.jobad import (
    JobAdSection,
    IssueSeverity,
    SectionAnalysis,
    ReviewIssue,
    JobAdReviewInput,
    JobAdReview,
    JobAdReviewProcessor,
)

__all__ = [
    # D&I Review (Module I)
    "BiasCategory",
    "Severity",
    "FlaggedItem",
    "CategoryScore",
    "DIReviewInput",
    "DIReview",
    "DIReviewProcessor",
    # Job Ad Review (Module H)
    "JobAdSection",
    "IssueSeverity",
    "SectionAnalysis",
    "ReviewIssue",
    "JobAdReviewInput",
    "JobAdReview",
    "JobAdReviewProcessor",
]
