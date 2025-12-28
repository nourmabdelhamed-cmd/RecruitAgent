"""Tests for the Funnel Report module (Module G).

Tests cover:
- Requirement 9.1: Accept data from Jobylon ATS and LinkedIn reports
- Requirement 9.2: Calculate conversion rates at each funnel stage
- Requirement 9.3: Highlight potential bottlenecks
- Requirement 9.4: Suggest possible causes linked to existing materials
- Requirement 9.5: Offer multiple output formats
- Requirement 9.6: Tie each diagnostic signal to one practical fix and one owner
"""

import pytest
from datetime import datetime

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
    InvalidInputError,
    CONVERSION_THRESHOLD_HIGH,
    CONVERSION_THRESHOLD_MEDIUM,
    TIME_THRESHOLD_HIGH,
    TIME_THRESHOLD_MEDIUM,
)
from src.tata.memory.memory import ArtifactType


class TestConversionRateCalculation:
    """Tests for conversion rate calculation per Requirement 9.2."""
    
    def test_normal_conversion(self):
        """Test normal conversion rate calculation."""
        # 50 out of 100 = 50%
        assert calculate_conversion_rate(100, 50) == 50.0
    
    def test_division_by_zero_returns_zero(self):
        """Test that division by zero returns 0.0."""
        assert calculate_conversion_rate(0, 50) == 0.0
    
    def test_full_conversion(self):
        """Test 100% conversion."""
        assert calculate_conversion_rate(100, 100) == 100.0
    
    def test_zero_conversion(self):
        """Test 0% conversion."""
        assert calculate_conversion_rate(100, 0) == 0.0
    
    def test_rounding_to_one_decimal(self):
        """Test that result is rounded to 1 decimal place."""
        # 33/100 = 33.0%
        assert calculate_conversion_rate(100, 33) == 33.0
        # 1/3 = 33.333... -> 33.3%
        assert calculate_conversion_rate(3, 1) == 33.3
    
    def test_conversion_greater_than_100(self):
        """Test conversion can exceed 100% (e.g., sourcing adds candidates)."""
        assert calculate_conversion_rate(50, 100) == 200.0


class TestBottleneckDetection:
    """Tests for bottleneck detection per Requirement 9.3."""
    
    def test_high_severity_low_conversion(self):
        """Test high severity for very low conversion."""
        severity = detect_bottleneck_severity(15.0)  # Below 20%
        assert severity == Severity.HIGH
    
    def test_medium_severity_low_conversion(self):
        """Test medium severity for moderately low conversion."""
        severity = detect_bottleneck_severity(25.0)  # Between 20-30%
        assert severity == Severity.MEDIUM
    
    def test_no_bottleneck_good_conversion(self):
        """Test no bottleneck for good conversion."""
        severity = detect_bottleneck_severity(50.0)  # Above 30%
        assert severity is None
    
    def test_high_severity_long_time_in_stage(self):
        """Test high severity for long time in stage."""
        severity = detect_bottleneck_severity(50.0, time_in_stage=20)  # > 14 days
        assert severity == Severity.HIGH
    
    def test_medium_severity_moderate_time_in_stage(self):
        """Test medium severity for moderate time in stage."""
        severity = detect_bottleneck_severity(50.0, time_in_stage=10)  # 7-14 days
        assert severity == Severity.MEDIUM
    
    def test_no_bottleneck_short_time_in_stage(self):
        """Test no bottleneck for short time in stage."""
        severity = detect_bottleneck_severity(50.0, time_in_stage=3)  # < 7 days
        assert severity is None
    
    def test_conversion_takes_precedence_over_time(self):
        """Test that low conversion triggers bottleneck even with short time."""
        severity = detect_bottleneck_severity(15.0, time_in_stage=3)
        assert severity == Severity.HIGH



class TestFixAssignment:
    """Tests for fix and owner assignment per Requirement 9.6."""
    
    def test_fix_has_one_owner(self):
        """Test that each fix has exactly one owner."""
        fix = get_fix_for_bottleneck("Job Ad Views")
        assert fix.owner is not None
        assert isinstance(fix.owner, Owner)
    
    def test_fix_has_one_fix_action(self):
        """Test that each fix has exactly one fix action."""
        fix = get_fix_for_bottleneck("Job Ad Views")
        assert fix.fix is not None
        assert len(fix.fix) > 0
    
    def test_job_ad_views_fix(self):
        """Test fix for job ad views bottleneck."""
        fix = get_fix_for_bottleneck("job_ad_views")
        assert fix.owner == Owner.RECRUITER
        assert fix.related_artifact == ArtifactType.JOB_AD
    
    def test_qualified_applications_fix(self):
        """Test fix for qualified applications bottleneck."""
        fix = get_fix_for_bottleneck("qualified_applications")
        assert fix.owner == Owner.HIRING_MANAGER
        assert fix.related_artifact == ArtifactType.REQUIREMENT_PROFILE
    
    def test_candidates_contacted_fix(self):
        """Test fix for candidates contacted bottleneck."""
        fix = get_fix_for_bottleneck("candidates_contacted")
        assert fix.owner == Owner.RECRUITER
        assert fix.related_artifact == ArtifactType.HEADHUNTING_MESSAGES
    
    def test_unknown_stage_gets_default_fix(self):
        """Test that unknown stages get a default fix."""
        fix = get_fix_for_bottleneck("Unknown Stage")
        assert fix.owner == Owner.RECRUITER
        assert fix.related_artifact is None
        assert "Unknown Stage" in fix.fix


class TestAttractionMetrics:
    """Tests for AttractionMetrics dataclass."""
    
    def test_create_with_defaults(self):
        """Test creating metrics with default values."""
        metrics = AttractionMetrics()
        assert metrics.job_ad_views == 0
        assert metrics.apply_clicks == 0
        assert metrics.applications_received == 0
    
    def test_create_with_values(self):
        """Test creating metrics with specific values."""
        metrics = AttractionMetrics(
            job_ad_views=1000,
            apply_clicks=200,
            applications_received=50,
            qualified_applications=30,
        )
        assert metrics.job_ad_views == 1000
        assert metrics.apply_clicks == 200
        assert metrics.applications_received == 50
        assert metrics.qualified_applications == 30


class TestProcessMetrics:
    """Tests for ProcessMetrics dataclass."""
    
    def test_create_with_defaults(self):
        """Test creating metrics with default values."""
        metrics = ProcessMetrics()
        assert metrics.ta_screenings == 0
        assert metrics.offers_made == 0
    
    def test_create_with_values(self):
        """Test creating metrics with specific values."""
        metrics = ProcessMetrics(
            ta_screenings=20,
            hm_interviews=15,
            offers_made=3,
            offers_accepted=2,
        )
        assert metrics.ta_screenings == 20
        assert metrics.hm_interviews == 15
        assert metrics.offers_made == 3
        assert metrics.offers_accepted == 2


class TestTimeMetrics:
    """Tests for TimeMetrics dataclass."""
    
    def test_create_with_defaults(self):
        """Test creating metrics with default values."""
        metrics = TimeMetrics()
        assert metrics.time_in_stage == {}
        assert metrics.time_to_fill == 0
    
    def test_create_with_values(self):
        """Test creating metrics with specific values."""
        metrics = TimeMetrics(
            time_in_stage={"ta_screenings": 5, "hm_interviews": 10},
            time_to_fill=45,
        )
        assert metrics.time_in_stage["ta_screenings"] == 5
        assert metrics.time_to_fill == 45


class TestFunnelStage:
    """Tests for FunnelStage dataclass."""
    
    def test_create_stage(self):
        """Test creating a funnel stage."""
        stage = FunnelStage(
            name="Applications",
            count=100,
            conversion_from_previous=50.0,
            cumulative_conversion=25.0,
        )
        assert stage.name == "Applications"
        assert stage.count == 100
        assert stage.conversion_from_previous == 50.0
        assert stage.cumulative_conversion == 25.0
    
    def test_optional_fields(self):
        """Test optional fields default to None."""
        stage = FunnelStage(
            name="Test",
            count=10,
            conversion_from_previous=100.0,
            cumulative_conversion=100.0,
        )
        assert stage.time_in_stage is None
        assert stage.notes is None


class TestBottleneck:
    """Tests for Bottleneck dataclass."""
    
    def test_create_bottleneck(self):
        """Test creating a bottleneck."""
        bottleneck = Bottleneck(
            stage="HM Interviews",
            conversion_rate=25.0,
            time_in_stage=10,
            severity=Severity.MEDIUM,
        )
        assert bottleneck.stage == "HM Interviews"
        assert bottleneck.conversion_rate == 25.0
        assert bottleneck.severity == Severity.MEDIUM


class TestSuggestedFix:
    """Tests for SuggestedFix dataclass."""
    
    def test_create_fix(self):
        """Test creating a suggested fix."""
        fix = SuggestedFix(
            bottleneck="Job Ad Views",
            fix="Improve job ad visibility",
            owner=Owner.RECRUITER,
            related_artifact=ArtifactType.JOB_AD,
        )
        assert fix.bottleneck == "Job Ad Views"
        assert fix.owner == Owner.RECRUITER
        assert fix.related_artifact == ArtifactType.JOB_AD



class TestFunnelReportInput:
    """Tests for FunnelReportInput dataclass."""
    
    def test_create_minimal_input(self):
        """Test creating input with minimal required fields."""
        input_data = FunnelReportInput(
            job_title="Software Engineer",
            number_of_positions=2,
            hiring_manager_name="John Smith",
        )
        assert input_data.job_title == "Software Engineer"
        assert input_data.number_of_positions == 2
        assert input_data.hiring_manager_name == "John Smith"
    
    def test_create_full_input(self):
        """Test creating input with all fields."""
        input_data = FunnelReportInput(
            job_title="Software Engineer",
            number_of_positions=2,
            hiring_manager_name="John Smith",
            locations=["Stockholm", "Copenhagen"],
            attraction_data=AttractionMetrics(job_ad_views=1000),
            process_data=ProcessMetrics(ta_screenings=20),
            time_metrics=TimeMetrics(time_to_fill=30),
        )
        assert len(input_data.locations) == 2
        assert input_data.attraction_data.job_ad_views == 1000


class TestFunnelReport:
    """Tests for FunnelReport dataclass."""
    
    def test_artifact_type(self):
        """Test that artifact type is FUNNEL_REPORT."""
        report = FunnelReport(
            summary="Test summary",
            funnel_table=[],
            bottlenecks=[],
            suggested_fixes=[],
            visual_data=FunnelVisualization(stages=[], largest_drops=[]),
        )
        assert report.artifact_type == ArtifactType.FUNNEL_REPORT
    
    def test_to_json_serialization(self):
        """Test JSON serialization."""
        stage = FunnelStage(
            name="Test",
            count=100,
            conversion_from_previous=50.0,
            cumulative_conversion=50.0,
        )
        bottleneck = Bottleneck(
            stage="Test",
            conversion_rate=25.0,
            time_in_stage=None,
            severity=Severity.MEDIUM,
        )
        fix = SuggestedFix(
            bottleneck="Test",
            fix="Fix it",
            owner=Owner.RECRUITER,
        )
        report = FunnelReport(
            summary="Test summary",
            funnel_table=[stage],
            bottlenecks=[bottleneck],
            suggested_fixes=[fix],
            visual_data=FunnelVisualization(stages=[stage], largest_drops=["Test"]),
        )
        
        json_str = report.to_json()
        assert "Test summary" in json_str
        assert "Test" in json_str
        assert "medium" in json_str


class TestFunnelReportProcessor:
    """Tests for FunnelReportProcessor."""
    
    def test_get_required_inputs(self):
        """Test required inputs list."""
        processor = FunnelReportProcessor()
        required = processor.get_required_inputs()
        assert "job_title" in required
        assert "number_of_positions" in required
        assert "hiring_manager_name" in required
    
    def test_get_optional_inputs(self):
        """Test optional inputs list."""
        processor = FunnelReportProcessor()
        optional = processor.get_optional_inputs()
        assert "attraction_data" in optional
        assert "process_data" in optional
        assert "time_metrics" in optional
    
    def test_validate_missing_job_title_fails(self):
        """Test validation fails without job title."""
        processor = FunnelReportProcessor()
        input_data = FunnelReportInput(
            job_title="",
            number_of_positions=1,
            hiring_manager_name="John",
            attraction_data=AttractionMetrics(job_ad_views=100),
        )
        result = processor.validate(input_data)
        assert not result.is_valid
        assert any(e.field == "job_title" for e in result.errors)
    
    def test_validate_missing_data_fails(self):
        """Test validation fails without any metrics data."""
        processor = FunnelReportProcessor()
        input_data = FunnelReportInput(
            job_title="Engineer",
            number_of_positions=1,
            hiring_manager_name="John",
        )
        result = processor.validate(input_data)
        assert not result.is_valid
        assert any(e.field == "data" for e in result.errors)
    
    def test_validate_valid_input_passes(self):
        """Test validation passes with valid input."""
        processor = FunnelReportProcessor()
        input_data = FunnelReportInput(
            job_title="Software Engineer",
            number_of_positions=2,
            hiring_manager_name="John Smith",
            attraction_data=AttractionMetrics(job_ad_views=1000, apply_clicks=200),
        )
        result = processor.validate(input_data)
        assert result.is_valid
    
    def test_process_creates_report(self):
        """Test processing creates a complete report."""
        processor = FunnelReportProcessor()
        input_data = FunnelReportInput(
            job_title="Software Engineer",
            number_of_positions=2,
            hiring_manager_name="John Smith",
            locations=["Stockholm"],
            attraction_data=AttractionMetrics(
                job_ad_views=1000,
                apply_clicks=200,
                applications_received=50,
                qualified_applications=30,
            ),
            process_data=ProcessMetrics(
                ta_screenings=20,
                hm_interviews=10,
                offers_made=3,
                offers_accepted=2,
            ),
        )
        
        report = processor.process(input_data)
        
        assert report.summary is not None
        assert len(report.funnel_table) > 0
        assert report.visual_data is not None
    
    def test_process_invalid_input_raises(self):
        """Test processing invalid input raises error."""
        processor = FunnelReportProcessor()
        input_data = FunnelReportInput(
            job_title="",
            number_of_positions=1,
            hiring_manager_name="John",
        )
        
        with pytest.raises(InvalidInputError):
            processor.process(input_data)
    
    def test_process_identifies_bottlenecks(self):
        """Test that bottlenecks are identified correctly."""
        processor = FunnelReportProcessor()
        input_data = FunnelReportInput(
            job_title="Software Engineer",
            number_of_positions=1,
            hiring_manager_name="John Smith",
            attraction_data=AttractionMetrics(
                job_ad_views=1000,
                apply_clicks=100,  # 10% conversion - bottleneck!
                applications_received=50,
                qualified_applications=40,
            ),
        )
        
        report = processor.process(input_data)
        
        # Should identify the low conversion as a bottleneck
        assert len(report.bottlenecks) > 0
    
    def test_process_generates_fixes_for_bottlenecks(self):
        """Test that fixes are generated for each bottleneck."""
        processor = FunnelReportProcessor()
        input_data = FunnelReportInput(
            job_title="Software Engineer",
            number_of_positions=1,
            hiring_manager_name="John Smith",
            attraction_data=AttractionMetrics(
                job_ad_views=1000,
                apply_clicks=100,  # 10% - bottleneck
            ),
        )
        
        report = processor.process(input_data)
        
        # Each bottleneck should have a fix
        assert len(report.suggested_fixes) == len(report.bottlenecks)



class TestOutputFormats:
    """Tests for output format generation per Requirement 9.5."""
    
    @pytest.fixture
    def sample_report(self):
        """Create a sample report for testing."""
        stage = FunnelStage(
            name="Applications",
            count=100,
            conversion_from_previous=50.0,
            cumulative_conversion=50.0,
            time_in_stage=5,
        )
        bottleneck = Bottleneck(
            stage="Applications",
            conversion_rate=25.0,
            time_in_stage=5,
            severity=Severity.MEDIUM,
        )
        fix = SuggestedFix(
            bottleneck="Applications",
            fix="Improve application process",
            owner=Owner.RECRUITER,
        )
        return FunnelReport(
            summary="Test funnel report",
            funnel_table=[stage],
            bottlenecks=[bottleneck],
            suggested_fixes=[fix],
            visual_data=FunnelVisualization(stages=[stage], largest_drops=["Applications"]),
        )
    
    def test_word_format(self, sample_report):
        """Test Word document format output."""
        output = format_funnel_for_output(sample_report, OutputFormat.WORD)
        assert "FUNNEL REPORT" in output
        assert "Applications" in output
        assert "BOTTLENECKS" in output
    
    def test_visual_funnel_format(self, sample_report):
        """Test visual funnel format output."""
        output = format_funnel_for_output(sample_report, OutputFormat.VISUAL_FUNNEL)
        assert "Applications" in output
        assert "█" in output  # ASCII bar
    
    def test_slide_format(self, sample_report):
        """Test slide content format output."""
        output = format_funnel_for_output(sample_report, OutputFormat.SLIDE_CONTENT)
        assert "SLIDE 1" in output
        assert "SLIDE 2" in output
    
    def test_comparison_table_format(self, sample_report):
        """Test comparison table format output."""
        output = format_funnel_for_output(sample_report, OutputFormat.COMPARISON_TABLE)
        assert "Stage" in output
        assert "Count" in output
        assert "Conversion" in output


class TestFunnelVisualization:
    """Tests for FunnelVisualization dataclass."""
    
    def test_create_visualization(self):
        """Test creating visualization data."""
        stage = FunnelStage(
            name="Test",
            count=100,
            conversion_from_previous=100.0,
            cumulative_conversion=100.0,
        )
        viz = FunnelVisualization(
            stages=[stage],
            largest_drops=["Test Stage"],
        )
        assert len(viz.stages) == 1
        assert len(viz.largest_drops) == 1
    
    def test_largest_drops_limited_to_two(self):
        """Test that largest drops are limited to top 2."""
        processor = FunnelReportProcessor()
        input_data = FunnelReportInput(
            job_title="Engineer",
            number_of_positions=1,
            hiring_manager_name="John",
            attraction_data=AttractionMetrics(
                job_ad_views=1000,
                apply_clicks=500,
                applications_received=200,
                qualified_applications=50,
            ),
        )
        
        report = processor.process(input_data)
        
        # Should have at most 2 largest drops
        assert len(report.visual_data.largest_drops) <= 2


class TestEnums:
    """Tests for enum types."""
    
    def test_severity_values(self):
        """Test Severity enum values."""
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
    
    def test_owner_values(self):
        """Test Owner enum values."""
        assert Owner.RECRUITER.value == "recruiter"
        assert Owner.HIRING_MANAGER.value == "hiring_manager"
        assert Owner.TA_OPERATIONS.value == "ta_operations"
    
    def test_output_format_values(self):
        """Test OutputFormat enum values."""
        assert OutputFormat.WORD.value == "word"
        assert OutputFormat.VISUAL_FUNNEL.value == "visual_funnel"
        assert OutputFormat.SLIDE_CONTENT.value == "slide_content"
        assert OutputFormat.COMPARISON_TABLE.value == "comparison_table"
