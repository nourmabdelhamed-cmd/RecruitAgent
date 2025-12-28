"""Report modules for Tata recruitment assistant.

This package contains:
- Module F: Candidate Report - structured assessment from interview transcripts
- Module G: Funnel Report - recruitment metrics and diagnostics
"""

from src.tata.modules.report.candidate import (
    Rating,
    RATING_DESCRIPTIONS,
    Recommendation,
    SkillAssessment,
    PracticalDetails,
    CandidateReportInput,
    CandidateReport,
    CandidateReportProcessor,
)

from src.tata.modules.report.funnel import (
    Severity,
    Owner,
    OutputFormat,
    AttractionMetrics,
    ProcessMetrics,
    TimeMetrics,
    FunnelReportInput,
    FunnelStage,
    Bottleneck,
    SuggestedFix,
    FunnelVisualization,
    FunnelReport,
    FunnelReportProcessor,
    calculate_conversion_rate,
    detect_bottleneck_severity,
    get_fix_for_bottleneck,
    format_funnel_for_output,
)

__all__ = [
    # Candidate Report (Module F)
    "Rating",
    "RATING_DESCRIPTIONS",
    "Recommendation",
    "SkillAssessment",
    "PracticalDetails",
    "CandidateReportInput",
    "CandidateReport",
    "CandidateReportProcessor",
    # Funnel Report (Module G)
    "Severity",
    "Owner",
    "OutputFormat",
    "AttractionMetrics",
    "ProcessMetrics",
    "TimeMetrics",
    "FunnelReportInput",
    "FunnelStage",
    "Bottleneck",
    "SuggestedFix",
    "FunnelVisualization",
    "FunnelReport",
    "FunnelReportProcessor",
    "calculate_conversion_rate",
    "detect_bottleneck_severity",
    "get_fix_for_bottleneck",
    "format_funnel_for_output",
]
