"""Funnel Report module for Tata recruitment assistant.

This module implements Module G: Funnel Report generation.
Creates diagnostic funnel reports from ATS and LinkedIn data.

Requirements covered:
- 9.1: Accept data from Jobylon ATS and LinkedIn reports
- 9.2: Calculate conversion rates at each funnel stage
- 9.3: Highlight potential bottlenecks using lowest conversions or long time-in-stage
- 9.4: Suggest possible causes linked to existing materials
- 9.5: Offer multiple output formats
- 9.6: Tie each diagnostic signal to one practical fix and one owner
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
import json


from src.tata.memory.memory import ArtifactType


class Severity(Enum):
    """Severity level for bottlenecks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Owner(Enum):
    """Owner responsible for fixing a bottleneck."""
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    TA_OPERATIONS = "ta_operations"


class OutputFormat(Enum):
    """Output format options per Requirement 9.5."""
    WORD = "word"
    VISUAL_FUNNEL = "visual_funnel"
    SLIDE_CONTENT = "slide_content"
    COMPARISON_TABLE = "comparison_table"


@dataclass
class AttractionMetrics:
    """Metrics for the attraction phase of recruitment.
    
    Attributes:
        job_ad_views: Number of job ad views
        apply_clicks: Number of apply button clicks
        applications_received: Total applications received
        qualified_applications: Applications meeting minimum criteria
        candidates_sourced: Candidates found through sourcing
        candidates_contacted: Candidates contacted via outreach
        candidates_replied: Candidates who replied to outreach
        candidates_interested: Candidates expressing interest
    """
    job_ad_views: int = 0
    apply_clicks: int = 0
    applications_received: int = 0
    qualified_applications: int = 0
    candidates_sourced: int = 0
    candidates_contacted: int = 0
    candidates_replied: int = 0
    candidates_interested: int = 0


@dataclass
class ProcessMetrics:
    """Metrics for the interview/selection process.
    
    Attributes:
        ta_screenings: Number of TA screening interviews
        hm_interviews: Number of hiring manager interviews
        case_interviews: Number of case interviews
        team_interviews: Number of team interviews
        tests: Number of assessments/tests
        references: Number of reference checks
        offers_made: Number of offers extended
        offers_accepted: Number of offers accepted
        offers_rejected: Number of offers rejected
    """
    ta_screenings: int = 0
    hm_interviews: int = 0
    case_interviews: int = 0
    team_interviews: int = 0
    tests: int = 0
    references: int = 0
    offers_made: int = 0
    offers_accepted: int = 0
    offers_rejected: int = 0


@dataclass
class TimeMetrics:
    """Time-related metrics for the recruitment process.
    
    Attributes:
        time_in_stage: Dict mapping stage name to days spent
        time_to_fill: Total days from opening to fill
    """
    time_in_stage: Dict[str, int] = field(default_factory=dict)
    time_to_fill: int = 0



@dataclass
class FunnelReportInput:
    """Input for creating funnel reports per Requirement 9.1.
    
    Attributes:
        job_title: Title of the position
        number_of_positions: Number of positions to fill
        hiring_manager_name: Name of the hiring manager
        locations: List of job locations
        attraction_data: Optional attraction phase metrics
        process_data: Optional process phase metrics
        time_metrics: Optional time-related metrics
    """
    job_title: str
    number_of_positions: int
    hiring_manager_name: str
    locations: List[str] = field(default_factory=list)
    attraction_data: Optional[AttractionMetrics] = None
    process_data: Optional[ProcessMetrics] = None
    time_metrics: Optional[TimeMetrics] = None


@dataclass
class FunnelStage:
    """Single stage in the recruitment funnel.
    
    Attributes:
        name: Name of the stage
        count: Number of candidates at this stage
        conversion_from_previous: Conversion rate from previous stage (0-100)
        cumulative_conversion: Cumulative conversion from top of funnel (0-100)
        time_in_stage: Optional days spent in this stage
        notes: Optional notes about this stage
    """
    name: str
    count: int
    conversion_from_previous: float
    cumulative_conversion: float
    time_in_stage: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class Bottleneck:
    """Identified bottleneck in the funnel per Requirement 9.3.
    
    Attributes:
        stage: Name of the bottleneck stage
        conversion_rate: Conversion rate at this stage
        time_in_stage: Optional days spent in stage
        severity: Severity level (low, medium, high)
    """
    stage: str
    conversion_rate: float
    time_in_stage: Optional[int]
    severity: Severity


@dataclass
class SuggestedFix:
    """Recommended fix for a bottleneck per Requirement 9.6.
    
    Each bottleneck gets exactly one fix and one owner.
    
    Attributes:
        bottleneck: Name of the bottleneck stage
        fix: The recommended fix action
        owner: Who is responsible for implementing the fix
        related_artifact: Optional related artifact type
    """
    bottleneck: str
    fix: str
    owner: Owner
    related_artifact: Optional[ArtifactType] = None


@dataclass
class FunnelVisualization:
    """Data for visual funnel representation per Requirement 9.5.
    
    Attributes:
        stages: List of funnel stages
        largest_drops: Top 2 stages with largest conversion drops
    """
    stages: List[FunnelStage]
    largest_drops: List[str]


@dataclass
class ValidationError:
    """A validation error for input data."""
    field: str
    message: str


@dataclass
class ValidationWarning:
    """A validation warning for input data."""
    field: str
    message: str


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)


class InvalidInputError(Exception):
    """Raised when input validation fails."""
    pass


@dataclass
class FunnelReport:
    """Complete funnel analysis per Requirements 9.1-9.6.
    
    Attributes:
        summary: Executive summary of the funnel analysis
        funnel_table: List of funnel stages with metrics
        bottlenecks: Identified bottlenecks
        suggested_fixes: Recommended fixes with owners
        visual_data: Data for visualization
        created_at: When the report was created
    """
    summary: str
    funnel_table: List[FunnelStage]
    bottlenecks: List[Bottleneck]
    suggested_fixes: List[SuggestedFix]
    visual_data: FunnelVisualization
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type for memory storage."""
        return ArtifactType.FUNNEL_REPORT
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "summary": self.summary,
            "funnel_table": [
                {
                    "name": stage.name,
                    "count": stage.count,
                    "conversion_from_previous": stage.conversion_from_previous,
                    "cumulative_conversion": stage.cumulative_conversion,
                    "time_in_stage": stage.time_in_stage,
                    "notes": stage.notes,
                }
                for stage in self.funnel_table
            ],
            "bottlenecks": [
                {
                    "stage": b.stage,
                    "conversion_rate": b.conversion_rate,
                    "time_in_stage": b.time_in_stage,
                    "severity": b.severity.value,
                }
                for b in self.bottlenecks
            ],
            "suggested_fixes": [
                {
                    "bottleneck": sf.bottleneck,
                    "fix": sf.fix,
                    "owner": sf.owner.value,
                    "related_artifact": sf.related_artifact.value if sf.related_artifact else None,
                }
                for sf in self.suggested_fixes
            ],
            "visual_data": {
                "stages": [
                    {
                        "name": s.name,
                        "count": s.count,
                        "conversion_from_previous": s.conversion_from_previous,
                        "cumulative_conversion": s.cumulative_conversion,
                    }
                    for s in self.visual_data.stages
                ],
                "largest_drops": self.visual_data.largest_drops,
            },
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data, indent=2)



# Thresholds for bottleneck detection per Requirement 9.3
CONVERSION_THRESHOLD_HIGH = 20.0  # Below this = high severity
CONVERSION_THRESHOLD_MEDIUM = 30.0  # Below this = medium severity
TIME_THRESHOLD_HIGH = 14  # Days - above this = high severity
TIME_THRESHOLD_MEDIUM = 7  # Days - above this = medium severity


def calculate_conversion_rate(count_a: int, count_b: int) -> float:
    """Calculate conversion rate per Requirement 9.2.
    
    Formula: (count_B / count_A) × 100
    
    Args:
        count_a: Count at stage A (previous stage)
        count_b: Count at stage B (current stage)
        
    Returns:
        Conversion rate as percentage (0-100), rounded to 1 decimal
        Returns 0.0 if count_a is 0 (division by zero handling)
    """
    if count_a == 0:
        return 0.0
    
    rate = (count_b / count_a) * 100
    return round(rate, 1)


def detect_bottleneck_severity(
    conversion_rate: float,
    time_in_stage: Optional[int] = None
) -> Optional[Severity]:
    """Detect if a stage is a bottleneck and determine severity.
    
    Per Requirement 9.3: Flag stages with low conversion or high time-in-stage.
    
    Args:
        conversion_rate: Conversion rate at this stage
        time_in_stage: Optional days spent in stage
        
    Returns:
        Severity level if bottleneck, None otherwise
    """
    # Check conversion rate
    if conversion_rate < CONVERSION_THRESHOLD_HIGH:
        return Severity.HIGH
    elif conversion_rate < CONVERSION_THRESHOLD_MEDIUM:
        return Severity.MEDIUM
    
    # Check time in stage
    if time_in_stage is not None:
        if time_in_stage > TIME_THRESHOLD_HIGH:
            return Severity.HIGH
        elif time_in_stage > TIME_THRESHOLD_MEDIUM:
            return Severity.MEDIUM
    
    return None


# Fix suggestions mapped to stages per Requirement 9.4, 9.6
STAGE_FIX_MAPPING: Dict[str, Dict[str, any]] = {
    "job_ad_views": {
        "fix": "Review job ad title and posting channels for better visibility",
        "owner": Owner.RECRUITER,
        "artifact": ArtifactType.JOB_AD,
    },
    "apply_clicks": {
        "fix": "Improve job ad content to increase apply intent",
        "owner": Owner.RECRUITER,
        "artifact": ArtifactType.JOB_AD,
    },
    "applications_received": {
        "fix": "Simplify application process and reduce friction",
        "owner": Owner.TA_OPERATIONS,
        "artifact": None,
    },
    "qualified_applications": {
        "fix": "Review requirement profile for realistic qualifications",
        "owner": Owner.HIRING_MANAGER,
        "artifact": ArtifactType.REQUIREMENT_PROFILE,
    },
    "candidates_contacted": {
        "fix": "Improve headhunting message quality and targeting",
        "owner": Owner.RECRUITER,
        "artifact": ArtifactType.HEADHUNTING_MESSAGES,
    },
    "candidates_replied": {
        "fix": "Personalize outreach messages with candidate-specific details",
        "owner": Owner.RECRUITER,
        "artifact": ArtifactType.HEADHUNTING_MESSAGES,
    },
    "candidates_interested": {
        "fix": "Strengthen value proposition in outreach",
        "owner": Owner.RECRUITER,
        "artifact": ArtifactType.HEADHUNTING_MESSAGES,
    },
    "ta_screenings": {
        "fix": "Review screening criteria and candidate communication",
        "owner": Owner.RECRUITER,
        "artifact": ArtifactType.TA_SCREENING_TEMPLATE,
    },
    "hm_interviews": {
        "fix": "Align hiring manager availability and interview scheduling",
        "owner": Owner.HIRING_MANAGER,
        "artifact": ArtifactType.HM_SCREENING_TEMPLATE,
    },
    "case_interviews": {
        "fix": "Review case interview difficulty and relevance",
        "owner": Owner.HIRING_MANAGER,
        "artifact": None,
    },
    "team_interviews": {
        "fix": "Streamline team interview process and feedback collection",
        "owner": Owner.HIRING_MANAGER,
        "artifact": None,
    },
    "offers_made": {
        "fix": "Review offer competitiveness and timing",
        "owner": Owner.HIRING_MANAGER,
        "artifact": None,
    },
    "offers_accepted": {
        "fix": "Improve offer package and candidate experience",
        "owner": Owner.HIRING_MANAGER,
        "artifact": None,
    },
}


def get_fix_for_bottleneck(stage_name: str) -> SuggestedFix:
    """Get the suggested fix for a bottleneck stage per Requirement 9.6.
    
    Each bottleneck gets exactly one fix and one owner.
    
    Args:
        stage_name: Name of the bottleneck stage
        
    Returns:
        SuggestedFix with fix, owner, and optional related artifact
    """
    # Normalize stage name for lookup
    normalized = stage_name.lower().replace(" ", "_")
    
    if normalized in STAGE_FIX_MAPPING:
        mapping = STAGE_FIX_MAPPING[normalized]
        return SuggestedFix(
            bottleneck=stage_name,
            fix=mapping["fix"],
            owner=mapping["owner"],
            related_artifact=mapping["artifact"],
        )
    
    # Default fix for unknown stages
    return SuggestedFix(
        bottleneck=stage_name,
        fix=f"Review and optimize the {stage_name} stage",
        owner=Owner.RECRUITER,
        related_artifact=None,
    )



class FunnelReportProcessor:
    """Processor for creating funnel reports from ATS/LinkedIn data.
    
    Implements the ModuleProcessor pattern for Module G.
    Parses recruitment metrics, calculates conversions, identifies bottlenecks,
    and generates diagnostic reports with actionable fixes.
    
    Requirements covered:
    - 9.1: Accept data from Jobylon ATS and LinkedIn reports
    - 9.2: Calculate conversion rates at each funnel stage
    - 9.3: Highlight potential bottlenecks
    - 9.4: Suggest possible causes linked to existing materials
    - 9.5: Offer multiple output formats
    - 9.6: Tie each diagnostic signal to one practical fix and one owner
    """
    
    # Stage names in funnel order
    ATTRACTION_STAGES = [
        ("job_ad_views", "Job Ad Views"),
        ("apply_clicks", "Apply Clicks"),
        ("applications_received", "Applications Received"),
        ("qualified_applications", "Qualified Applications"),
    ]
    
    SOURCING_STAGES = [
        ("candidates_sourced", "Candidates Sourced"),
        ("candidates_contacted", "Candidates Contacted"),
        ("candidates_replied", "Candidates Replied"),
        ("candidates_interested", "Candidates Interested"),
    ]
    
    PROCESS_STAGES = [
        ("ta_screenings", "TA Screenings"),
        ("hm_interviews", "HM Interviews"),
        ("case_interviews", "Case Interviews"),
        ("team_interviews", "Team Interviews"),
        ("tests", "Tests"),
        ("references", "References"),
        ("offers_made", "Offers Made"),
        ("offers_accepted", "Offers Accepted"),
    ]
    
    def validate(self, input_data: FunnelReportInput) -> ValidationResult:
        """Validate input data before processing.
        
        Args:
            input_data: The input to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # Check job title
        if not input_data.job_title or not input_data.job_title.strip():
            errors.append(ValidationError(
                field="job_title",
                message="Job title is required"
            ))
        
        # Check number of positions
        if input_data.number_of_positions < 1:
            errors.append(ValidationError(
                field="number_of_positions",
                message="Number of positions must be at least 1"
            ))
        
        # Check hiring manager name
        if not input_data.hiring_manager_name or not input_data.hiring_manager_name.strip():
            errors.append(ValidationError(
                field="hiring_manager_name",
                message="Hiring manager name is required"
            ))
        
        # Check that at least some data is provided
        has_attraction = input_data.attraction_data is not None
        has_process = input_data.process_data is not None
        
        if not has_attraction and not has_process:
            errors.append(ValidationError(
                field="data",
                message="At least attraction_data or process_data must be provided"
            ))
        
        # Warnings for missing optional data
        if not has_attraction:
            warnings.append(ValidationWarning(
                field="attraction_data",
                message="No attraction data provided; attraction funnel will be empty"
            ))
        
        if not has_process:
            warnings.append(ValidationWarning(
                field="process_data",
                message="No process data provided; process funnel will be empty"
            ))
        
        if input_data.time_metrics is None:
            warnings.append(ValidationWarning(
                field="time_metrics",
                message="No time metrics provided; time-based bottleneck detection disabled"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def process(self, input_data: FunnelReportInput) -> FunnelReport:
        """Process input and generate a funnel report.
        
        Args:
            input_data: The funnel report input
            
        Returns:
            A complete FunnelReport
            
        Raises:
            InvalidInputError: If input validation fails
        """
        # Validate first
        validation = self.validate(input_data)
        if not validation.is_valid:
            error_msgs = "; ".join(e.message for e in validation.errors)
            raise InvalidInputError(f"Input validation failed: {error_msgs}")
        
        # Build funnel stages
        funnel_stages = self._build_funnel_stages(input_data)
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(funnel_stages)
        
        # Generate fixes for bottlenecks
        suggested_fixes = [get_fix_for_bottleneck(b.stage) for b in bottlenecks]
        
        # Create visualization data
        visual_data = self._create_visualization(funnel_stages)
        
        # Generate summary
        summary = self._generate_summary(
            input_data,
            funnel_stages,
            bottlenecks
        )
        
        return FunnelReport(
            summary=summary,
            funnel_table=funnel_stages,
            bottlenecks=bottlenecks,
            suggested_fixes=suggested_fixes,
            visual_data=visual_data,
        )
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input fields."""
        return ["job_title", "number_of_positions", "hiring_manager_name"]
    
    def get_optional_inputs(self) -> List[str]:
        """Get list of optional input fields."""
        return ["locations", "attraction_data", "process_data", "time_metrics"]
    
    def _build_funnel_stages(
        self,
        input_data: FunnelReportInput
    ) -> List[FunnelStage]:
        """Build the complete funnel from input data.
        
        Args:
            input_data: The funnel report input
            
        Returns:
            List of FunnelStage objects
        """
        stages: List[FunnelStage] = []
        previous_count: Optional[int] = None
        top_of_funnel: Optional[int] = None
        
        # Process attraction data
        if input_data.attraction_data:
            attraction = input_data.attraction_data
            attraction_values = [
                (self.ATTRACTION_STAGES[0], attraction.job_ad_views),
                (self.ATTRACTION_STAGES[1], attraction.apply_clicks),
                (self.ATTRACTION_STAGES[2], attraction.applications_received),
                (self.ATTRACTION_STAGES[3], attraction.qualified_applications),
            ]
            
            for (key, name), count in attraction_values:
                if count > 0:
                    if top_of_funnel is None:
                        top_of_funnel = count
                    
                    conversion = calculate_conversion_rate(previous_count, count) if previous_count else 100.0
                    cumulative = calculate_conversion_rate(top_of_funnel, count)
                    time_in = input_data.time_metrics.time_in_stage.get(key) if input_data.time_metrics else None
                    
                    stages.append(FunnelStage(
                        name=name,
                        count=count,
                        conversion_from_previous=conversion,
                        cumulative_conversion=cumulative,
                        time_in_stage=time_in,
                    ))
                    previous_count = count
        
        # Process sourcing data (parallel to attraction)
        if input_data.attraction_data:
            attraction = input_data.attraction_data
            sourcing_values = [
                (self.SOURCING_STAGES[0], attraction.candidates_sourced),
                (self.SOURCING_STAGES[1], attraction.candidates_contacted),
                (self.SOURCING_STAGES[2], attraction.candidates_replied),
                (self.SOURCING_STAGES[3], attraction.candidates_interested),
            ]
            
            sourcing_previous: Optional[int] = None
            sourcing_top: Optional[int] = None
            
            for (key, name), count in sourcing_values:
                if count > 0:
                    if sourcing_top is None:
                        sourcing_top = count
                    
                    conversion = calculate_conversion_rate(sourcing_previous, count) if sourcing_previous else 100.0
                    cumulative = calculate_conversion_rate(sourcing_top, count)
                    time_in = input_data.time_metrics.time_in_stage.get(key) if input_data.time_metrics else None
                    
                    stages.append(FunnelStage(
                        name=name,
                        count=count,
                        conversion_from_previous=conversion,
                        cumulative_conversion=cumulative,
                        time_in_stage=time_in,
                    ))
                    sourcing_previous = count
        
        # Process interview/selection data
        if input_data.process_data:
            process = input_data.process_data
            process_values = [
                (self.PROCESS_STAGES[0], process.ta_screenings),
                (self.PROCESS_STAGES[1], process.hm_interviews),
                (self.PROCESS_STAGES[2], process.case_interviews),
                (self.PROCESS_STAGES[3], process.team_interviews),
                (self.PROCESS_STAGES[4], process.tests),
                (self.PROCESS_STAGES[5], process.references),
                (self.PROCESS_STAGES[6], process.offers_made),
                (self.PROCESS_STAGES[7], process.offers_accepted),
            ]
            
            # Continue from previous count or start fresh
            if previous_count is None:
                # Find first non-zero value as top
                for (key, name), count in process_values:
                    if count > 0:
                        top_of_funnel = count
                        break
            
            for (key, name), count in process_values:
                if count > 0:
                    if top_of_funnel is None:
                        top_of_funnel = count
                    
                    conversion = calculate_conversion_rate(previous_count, count) if previous_count else 100.0
                    cumulative = calculate_conversion_rate(top_of_funnel, count)
                    time_in = input_data.time_metrics.time_in_stage.get(key) if input_data.time_metrics else None
                    
                    stages.append(FunnelStage(
                        name=name,
                        count=count,
                        conversion_from_previous=conversion,
                        cumulative_conversion=cumulative,
                        time_in_stage=time_in,
                    ))
                    previous_count = count
        
        return stages
    
    def _identify_bottlenecks(
        self,
        stages: List[FunnelStage]
    ) -> List[Bottleneck]:
        """Identify bottlenecks in the funnel per Requirement 9.3.
        
        Args:
            stages: List of funnel stages
            
        Returns:
            List of identified bottlenecks
        """
        bottlenecks: List[Bottleneck] = []
        
        for stage in stages:
            # Skip first stage (no conversion to measure)
            if stage.conversion_from_previous >= 100.0:
                continue
            
            severity = detect_bottleneck_severity(
                stage.conversion_from_previous,
                stage.time_in_stage
            )
            
            if severity is not None:
                bottlenecks.append(Bottleneck(
                    stage=stage.name,
                    conversion_rate=stage.conversion_from_previous,
                    time_in_stage=stage.time_in_stage,
                    severity=severity,
                ))
        
        # Sort by severity (high first)
        severity_order = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
        bottlenecks.sort(key=lambda b: severity_order[b.severity])
        
        return bottlenecks
    
    def _create_visualization(
        self,
        stages: List[FunnelStage]
    ) -> FunnelVisualization:
        """Create visualization data per Requirement 9.5.
        
        Args:
            stages: List of funnel stages
            
        Returns:
            FunnelVisualization with stages and largest drops
        """
        # Find top 2 largest drops
        drops: List[tuple] = []
        
        for stage in stages:
            if stage.conversion_from_previous < 100.0:
                drop = 100.0 - stage.conversion_from_previous
                drops.append((stage.name, drop))
        
        # Sort by drop size (largest first)
        drops.sort(key=lambda x: x[1], reverse=True)
        largest_drops = [name for name, _ in drops[:2]]
        
        return FunnelVisualization(
            stages=stages,
            largest_drops=largest_drops,
        )
    
    def _generate_summary(
        self,
        input_data: FunnelReportInput,
        stages: List[FunnelStage],
        bottlenecks: List[Bottleneck]
    ) -> str:
        """Generate executive summary for the report.
        
        Args:
            input_data: The funnel report input
            stages: List of funnel stages
            bottlenecks: Identified bottlenecks
            
        Returns:
            Summary text
        """
        parts: List[str] = []
        
        # Header
        parts.append(f"Funnel Report for {input_data.job_title}")
        parts.append(f"Hiring Manager: {input_data.hiring_manager_name}")
        parts.append(f"Positions: {input_data.number_of_positions}")
        
        if input_data.locations:
            parts.append(f"Locations: {', '.join(input_data.locations)}")
        
        # Funnel overview
        if stages:
            first_stage = stages[0]
            last_stage = stages[-1]
            overall_conversion = calculate_conversion_rate(first_stage.count, last_stage.count)
            parts.append(f"\nOverall funnel conversion: {overall_conversion}%")
            parts.append(f"From {first_stage.count} {first_stage.name} to {last_stage.count} {last_stage.name}")
        
        # Bottleneck summary
        if bottlenecks:
            high_severity = [b for b in bottlenecks if b.severity == Severity.HIGH]
            medium_severity = [b for b in bottlenecks if b.severity == Severity.MEDIUM]
            
            parts.append(f"\nBottlenecks identified: {len(bottlenecks)}")
            if high_severity:
                parts.append(f"  High severity: {len(high_severity)} ({', '.join(b.stage for b in high_severity)})")
            if medium_severity:
                parts.append(f"  Medium severity: {len(medium_severity)} ({', '.join(b.stage for b in medium_severity)})")
        else:
            parts.append("\nNo significant bottlenecks identified.")
        
        # Time to fill
        if input_data.time_metrics and input_data.time_metrics.time_to_fill > 0:
            parts.append(f"\nTime to fill: {input_data.time_metrics.time_to_fill} days")
        
        return "\n".join(parts)


def format_funnel_for_output(
    report: FunnelReport,
    output_format: OutputFormat
) -> str:
    """Format funnel report for different output types per Requirement 9.5.
    
    Args:
        report: The funnel report
        output_format: Desired output format
        
    Returns:
        Formatted string output
    """
    if output_format == OutputFormat.WORD:
        return _format_for_word(report)
    elif output_format == OutputFormat.VISUAL_FUNNEL:
        return _format_visual_funnel(report)
    elif output_format == OutputFormat.SLIDE_CONTENT:
        return _format_for_slides(report)
    elif output_format == OutputFormat.COMPARISON_TABLE:
        return _format_comparison_table(report)
    else:
        return report.summary


def _format_for_word(report: FunnelReport) -> str:
    """Format report for Word document."""
    lines: List[str] = []
    
    lines.append("FUNNEL REPORT")
    lines.append("=" * 50)
    lines.append("")
    lines.append(report.summary)
    lines.append("")
    lines.append("FUNNEL STAGES")
    lines.append("-" * 50)
    
    for stage in report.funnel_table:
        lines.append(f"{stage.name}: {stage.count}")
        lines.append(f"  Conversion: {stage.conversion_from_previous}%")
        if stage.time_in_stage:
            lines.append(f"  Time in stage: {stage.time_in_stage} days")
    
    if report.bottlenecks:
        lines.append("")
        lines.append("BOTTLENECKS")
        lines.append("-" * 50)
        for bottleneck in report.bottlenecks:
            lines.append(f"{bottleneck.stage} ({bottleneck.severity.value})")
            lines.append(f"  Conversion: {bottleneck.conversion_rate}%")
    
    if report.suggested_fixes:
        lines.append("")
        lines.append("RECOMMENDED ACTIONS")
        lines.append("-" * 50)
        for fix in report.suggested_fixes:
            lines.append(f"• {fix.bottleneck}: {fix.fix}")
            lines.append(f"  Owner: {fix.owner.value}")
    
    return "\n".join(lines)


def _format_visual_funnel(report: FunnelReport) -> str:
    """Format report as ASCII visual funnel."""
    lines: List[str] = []
    
    if not report.funnel_table:
        return "No funnel data available"
    
    max_count = max(s.count for s in report.funnel_table)
    max_width = 60
    
    for stage in report.funnel_table:
        width = int((stage.count / max_count) * max_width) if max_count > 0 else 0
        bar = "█" * width
        lines.append(f"{stage.name:25} {bar} {stage.count} ({stage.conversion_from_previous}%)")
    
    return "\n".join(lines)


def _format_for_slides(report: FunnelReport) -> str:
    """Format report for presentation slides."""
    lines: List[str] = []
    
    lines.append("SLIDE 1: Overview")
    lines.append(report.summary.split("\n")[0])  # Title only
    
    lines.append("\nSLIDE 2: Funnel Metrics")
    for stage in report.funnel_table[:5]:  # Top 5 stages
        lines.append(f"• {stage.name}: {stage.count} ({stage.conversion_from_previous}%)")
    
    lines.append("\nSLIDE 3: Key Bottlenecks")
    for bottleneck in report.bottlenecks[:3]:  # Top 3 bottlenecks
        lines.append(f"• {bottleneck.stage}: {bottleneck.conversion_rate}% conversion")
    
    lines.append("\nSLIDE 4: Action Items")
    for fix in report.suggested_fixes[:3]:  # Top 3 fixes
        lines.append(f"• {fix.fix} (Owner: {fix.owner.value})")
    
    return "\n".join(lines)


def _format_comparison_table(report: FunnelReport) -> str:
    """Format report as comparison table."""
    lines: List[str] = []
    
    # Header
    lines.append("Stage | Count | Conversion | Cumulative | Time")
    lines.append("-" * 60)
    
    for stage in report.funnel_table:
        time_str = f"{stage.time_in_stage}d" if stage.time_in_stage else "-"
        lines.append(
            f"{stage.name:20} | {stage.count:5} | {stage.conversion_from_previous:6.1f}% | "
            f"{stage.cumulative_conversion:6.1f}% | {time_str}"
        )
    
    return "\n".join(lines)
