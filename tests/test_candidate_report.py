"""Tests for the Candidate Report module (Module F).

Tests cover:
- CandidateReportInput validation
- CandidateReport creation and serialization
- Rating system validation
- Candidate anonymization
- Transcript processing
- Requirements 8.1, 8.3, 8.4, 8.5, 8.7
"""

import pytest
import json
from datetime import datetime

from src.tata.modules.report.candidate import (
    Rating,
    RATING_DESCRIPTIONS,
    Recommendation,
    SkillAssessment,
    PracticalDetails,
    TranscriptSection,
    CandidateReportInput,
    CandidateReport,
    CandidateReportProcessor,
    ValidationError,
    ValidationWarning,
    ValidationResult,
    InvalidInputError,
    InvalidRatingError,
    anonymize_name,
    validate_rating,
    create_comparison_table,
    TRANSCRIPTION_CORRECTIONS,
)
from src.tata.modules.profile.profile import (
    RequirementProfile,
    ContentSource,
)
from src.tata.modules.screening.screening import (
    ScreeningTemplate,
    SkillQuestionSet,
    SkillType,
    Question,
)
from src.tata.memory.memory import ArtifactType


@pytest.fixture
def sample_profile():
    """Create a sample requirement profile for testing."""
    return RequirementProfile(
        position_title="Senior Software Engineer",
        must_have_skills=("Python programming", "SQL databases", "REST API development", "Git version control"),
        must_have_sources=(
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.OLD_JOB_AD,
            ContentSource.HIRING_MANAGER_INPUT,
        ),
        primary_responsibilities=["Develop features", "Write tests", "Code reviews"],
        responsibility_sources=[
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
        ],
        good_to_haves=["Docker", "Kubernetes"],
        soft_skills=["Communication", "Teamwork"],
    )


@pytest.fixture
def sample_screening_template(sample_profile):
    """Create a sample screening template for testing."""
    return ScreeningTemplate(
        position_title="Senior Software Engineer",
        role_intro=None,
        motivation_questions=[Question(text="Why this role?")],
        skill_questions=[
            SkillQuestionSet(
                skill_name="Python programming",
                skill_type=SkillType.TECHNICAL,
                main_question="Tell me about your Python experience.",
                follow_up_questions=["What frameworks?", "Testing approach?"],
            ),
            SkillQuestionSet(
                skill_name="SQL databases",
                skill_type=SkillType.TECHNICAL,
                main_question="Describe your SQL experience.",
                follow_up_questions=["Query optimization?", "Database design?"],
            ),
        ],
        practical_questions=[Question(text="Notice period?")],
        closing_guidance="Thank the candidate.",
        is_hm_template=False,
    )


@pytest.fixture
def sample_transcript():
    """Create a sample Microsoft Teams transcript for testing."""
    return """0:00:15 Interviewer
Hello, thank you for joining us today. Can you tell me why you're interested in this role?

0:00:45 John Smith
I'm really excited about this opportunity. I've been working with Python programming for about 5 years now, and I'm looking for a role where I can grow my skills further. I'm particularly interested in GlobalConnect's mission.

0:01:30 Interviewer
That's great. Can you tell me about your experience with SQL databases?

0:02:00 John Smith
I have extensive experience with SQL databases. I've worked with PostgreSQL and MySQL in production environments. I've optimized queries and designed database schemas for high-traffic applications.

0:03:15 Interviewer
What about REST API development?

0:03:45 John Smith
I've built several REST APIs using Flask and FastAPI. I understand RESTful principles and have implemented authentication, rate limiting, and documentation.

0:04:30 Interviewer
Let's talk about practical matters. What's your notice period?

0:04:45 John Smith
My notice period is 3 months. I'm based in Stockholm and speak English and Swedish fluently.

0:05:15 Interviewer
What are your salary expectations?

0:05:30 John Smith
I'm expecting around 55000 SEK per month.
"""


@pytest.fixture
def sample_input(sample_profile, sample_screening_template, sample_transcript):
    """Create a sample CandidateReportInput for testing."""
    return CandidateReportInput(
        transcript=sample_transcript,
        screening_template=sample_screening_template,
        requirement_profile=sample_profile,
        candidate_name="John Smith",
        interview_date=datetime(2024, 1, 15, 10, 0),
    )


class TestRating:
    """Tests for Rating enum."""
    
    def test_all_ratings_defined(self):
        """Test all ratings are defined with correct values."""
        assert Rating.VERY_BAD.value == 1
        assert Rating.UNSATISFACTORY.value == 2
        assert Rating.OKAY.value == 3
        assert Rating.GOOD.value == 4
        assert Rating.EXCELLENT.value == 5
    
    def test_all_ratings_have_descriptions(self):
        """Test all ratings have descriptions."""
        for rating in Rating:
            assert rating in RATING_DESCRIPTIONS
            assert len(RATING_DESCRIPTIONS[rating]) > 0


class TestRecommendation:
    """Tests for Recommendation enum."""
    
    def test_all_recommendations_defined(self):
        """Test all recommendations are defined."""
        assert Recommendation.RECOMMENDED.value == "Recommended"
        assert Recommendation.NOT_RECOMMENDED.value == "Not Recommended"
        assert Recommendation.BORDERLINE.value == "Borderline"


class TestSkillAssessment:
    """Tests for SkillAssessment dataclass."""
    
    def test_create_valid_assessment(self):
        """Test creating a valid skill assessment."""
        assessment = SkillAssessment(
            skill_name="Python",
            summary="Strong Python skills demonstrated.",
            examples=["Built REST APIs", "Used pytest"],
            rating=Rating.GOOD,
            rating_explanation="Candidate showed solid experience with multiple examples.",
        )
        
        assert assessment.skill_name == "Python"
        assert assessment.rating == Rating.GOOD
        assert len(assessment.examples) == 2
    
    def test_empty_explanation_raises(self):
        """Test that empty explanation raises ValueError."""
        with pytest.raises(ValueError, match="Rating explanation cannot be empty"):
            SkillAssessment(
                skill_name="Python",
                summary="Summary",
                examples=[],
                rating=Rating.GOOD,
                rating_explanation="",
            )
    
    def test_whitespace_explanation_raises(self):
        """Test that whitespace-only explanation raises ValueError."""
        with pytest.raises(ValueError, match="Rating explanation cannot be empty"):
            SkillAssessment(
                skill_name="Python",
                summary="Summary",
                examples=[],
                rating=Rating.GOOD,
                rating_explanation="   ",
            )


class TestPracticalDetails:
    """Tests for PracticalDetails dataclass."""
    
    def test_create_practical_details(self):
        """Test creating practical details."""
        details = PracticalDetails(
            notice_period="3 months",
            salary_expectation="55000 SEK",
            location="Stockholm",
            languages=["English", "Swedish"],
        )
        
        assert details.notice_period == "3 months"
        assert details.salary_expectation == "55000 SEK"
        assert len(details.languages) == 2
    
    def test_default_languages_empty(self):
        """Test default languages is empty list."""
        details = PracticalDetails(
            notice_period="1 month",
            salary_expectation="50000",
            location="Copenhagen",
        )
        
        assert details.languages == []


class TestAnonymizeName:
    """Tests for anonymize_name function (Req 8.7)."""
    
    def test_two_part_name(self):
        """Test anonymizing a two-part name."""
        assert anonymize_name("John Smith") == "JS"
    
    def test_three_part_name(self):
        """Test anonymizing a three-part name."""
        assert anonymize_name("John Michael Smith") == "JMS"
    
    def test_single_name(self):
        """Test anonymizing a single name."""
        result = anonymize_name("John")
        assert len(result) >= 2
        assert result[0] == "J"
    
    def test_empty_name(self):
        """Test anonymizing empty name returns XX."""
        assert anonymize_name("") == "XX"
        assert anonymize_name("   ") == "XX"
    
    def test_none_name(self):
        """Test anonymizing None returns XX."""
        assert anonymize_name(None) == "XX"
    
    def test_four_part_name_truncates(self):
        """Test four-part name only uses first 3 parts."""
        result = anonymize_name("John Michael David Smith")
        assert len(result) == 3
        assert result == "JMD"
    
    def test_lowercase_converted_to_uppercase(self):
        """Test lowercase names are converted to uppercase."""
        assert anonymize_name("john smith") == "JS"


class TestValidateRating:
    """Tests for validate_rating function (Req 8.4)."""
    
    def test_valid_rating_passes(self):
        """Test valid rating with explanation passes."""
        assert validate_rating(Rating.GOOD, "Good explanation") is True
    
    def test_empty_explanation_raises(self):
        """Test empty explanation raises InvalidRatingError."""
        with pytest.raises(InvalidRatingError, match="explanation cannot be empty"):
            validate_rating(Rating.GOOD, "")
    
    def test_whitespace_explanation_raises(self):
        """Test whitespace explanation raises InvalidRatingError."""
        with pytest.raises(InvalidRatingError, match="explanation cannot be empty"):
            validate_rating(Rating.GOOD, "   ")
    
    def test_invalid_rating_type_raises(self):
        """Test non-Rating type raises InvalidRatingError."""
        with pytest.raises(InvalidRatingError, match="must be a Rating enum"):
            validate_rating(3, "Explanation")


class TestCandidateReportInput:
    """Tests for CandidateReportInput dataclass."""
    
    def test_create_minimal_input(self, sample_profile, sample_screening_template, sample_transcript):
        """Test creating input with required fields."""
        input_data = CandidateReportInput(
            transcript=sample_transcript,
            screening_template=sample_screening_template,
            requirement_profile=sample_profile,
            candidate_name="John Smith",
            interview_date=datetime.now(),
        )
        
        assert input_data.transcript == sample_transcript
        assert input_data.candidate_cv is None
    
    def test_create_input_with_cv(self, sample_profile, sample_screening_template, sample_transcript):
        """Test creating input with optional CV."""
        input_data = CandidateReportInput(
            transcript=sample_transcript,
            screening_template=sample_screening_template,
            requirement_profile=sample_profile,
            candidate_name="John Smith",
            interview_date=datetime.now(),
            candidate_cv="5 years Python experience...",
        )
        
        assert input_data.candidate_cv is not None


class TestCandidateReport:
    """Tests for CandidateReport dataclass."""
    
    def test_create_report(self):
        """Test creating a candidate report."""
        report = CandidateReport(
            candidate_initials="JS",
            candidate_full_name="John Smith",
            position_name="Software Engineer",
            interview_date=datetime(2024, 1, 15),
            recommendation=Recommendation.RECOMMENDED,
            professional_background="5 years experience",
            motivation_assessment=SkillAssessment(
                skill_name="Motivation",
                summary="Strong motivation",
                examples=["Excited about role"],
                rating=Rating.GOOD,
                rating_explanation="Clear interest shown",
            ),
            skill_assessments=[
                SkillAssessment(
                    skill_name="Python",
                    summary="Strong Python",
                    examples=["Built APIs"],
                    rating=Rating.EXCELLENT,
                    rating_explanation="Excellent examples",
                ),
            ],
            practical_details=PracticalDetails(
                notice_period="3 months",
                salary_expectation="55000 SEK",
                location="Stockholm",
            ),
            risks_and_considerations=["Long notice period"],
            conclusion="Recommend proceeding.",
        )
        
        assert report.candidate_initials == "JS"
        assert report.recommendation == Recommendation.RECOMMENDED
        assert report.artifact_type == ArtifactType.CANDIDATE_REPORTS
    
    def test_to_json_serialization(self):
        """Test JSON serialization."""
        report = CandidateReport(
            candidate_initials="JS",
            candidate_full_name="John Smith",
            position_name="Software Engineer",
            interview_date=datetime(2024, 1, 15),
            recommendation=Recommendation.RECOMMENDED,
            professional_background="Background",
            motivation_assessment=SkillAssessment(
                skill_name="Motivation",
                summary="Summary",
                examples=[],
                rating=Rating.GOOD,
                rating_explanation="Explanation",
            ),
            skill_assessments=[],
            practical_details=PracticalDetails(
                notice_period="1 month",
                salary_expectation="50000",
                location="Stockholm",
            ),
            risks_and_considerations=[],
            conclusion="Conclusion",
        )
        
        json_str = report.to_json()
        data = json.loads(json_str)
        
        assert data["candidate_initials"] == "JS"
        assert data["recommendation"] == "Recommended"
        assert data["motivation_assessment"]["rating"] == 4
    
    def test_get_average_rating(self):
        """Test calculating average rating."""
        report = CandidateReport(
            candidate_initials="JS",
            candidate_full_name="John Smith",
            position_name="Engineer",
            interview_date=datetime.now(),
            recommendation=Recommendation.RECOMMENDED,
            professional_background="Background",
            motivation_assessment=SkillAssessment(
                skill_name="Motivation",
                summary="Summary",
                examples=[],
                rating=Rating.GOOD,  # 4
                rating_explanation="Explanation",
            ),
            skill_assessments=[
                SkillAssessment(
                    skill_name="Skill1",
                    summary="Summary",
                    examples=[],
                    rating=Rating.EXCELLENT,  # 5
                    rating_explanation="Explanation",
                ),
                SkillAssessment(
                    skill_name="Skill2",
                    summary="Summary",
                    examples=[],
                    rating=Rating.OKAY,  # 3
                    rating_explanation="Explanation",
                ),
            ],
            practical_details=PracticalDetails(
                notice_period="1 month",
                salary_expectation="50000",
                location="Stockholm",
            ),
            risks_and_considerations=[],
            conclusion="Conclusion",
        )
        
        # Average: (4 + 5 + 3) / 3 = 4.0
        assert report.get_average_rating() == 4.0


class TestCandidateReportProcessor:
    """Tests for CandidateReportProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a processor instance."""
        return CandidateReportProcessor()
    
    def test_get_required_inputs(self, processor):
        """Test getting required inputs."""
        required = processor.get_required_inputs()
        assert "transcript" in required
        assert "screening_template" in required
        assert "requirement_profile" in required
        assert "candidate_name" in required
        assert "interview_date" in required
    
    def test_get_optional_inputs(self, processor):
        """Test getting optional inputs."""
        optional = processor.get_optional_inputs()
        assert "candidate_cv" in optional
    
    def test_validate_missing_transcript_fails(self, processor, sample_profile, sample_screening_template):
        """Test validation fails when transcript is empty."""
        input_data = CandidateReportInput(
            transcript="",
            screening_template=sample_screening_template,
            requirement_profile=sample_profile,
            candidate_name="John Smith",
            interview_date=datetime.now(),
        )
        result = processor.validate(input_data)
        
        assert result.is_valid is False
        assert any(e.field == "transcript" for e in result.errors)
    
    def test_validate_missing_template_fails(self, processor, sample_profile, sample_transcript):
        """Test validation fails when template is None."""
        input_data = CandidateReportInput(
            transcript=sample_transcript,
            screening_template=None,
            requirement_profile=sample_profile,
            candidate_name="John Smith",
            interview_date=datetime.now(),
        )
        result = processor.validate(input_data)
        
        assert result.is_valid is False
        assert any(e.field == "screening_template" for e in result.errors)
    
    def test_validate_missing_profile_fails(self, processor, sample_screening_template, sample_transcript):
        """Test validation fails when profile is None."""
        input_data = CandidateReportInput(
            transcript=sample_transcript,
            screening_template=sample_screening_template,
            requirement_profile=None,
            candidate_name="John Smith",
            interview_date=datetime.now(),
        )
        result = processor.validate(input_data)
        
        assert result.is_valid is False
        assert any(e.field == "requirement_profile" for e in result.errors)
    
    def test_validate_missing_name_fails(self, processor, sample_profile, sample_screening_template, sample_transcript):
        """Test validation fails when candidate name is empty."""
        input_data = CandidateReportInput(
            transcript=sample_transcript,
            screening_template=sample_screening_template,
            requirement_profile=sample_profile,
            candidate_name="",
            interview_date=datetime.now(),
        )
        result = processor.validate(input_data)
        
        assert result.is_valid is False
        assert any(e.field == "candidate_name" for e in result.errors)
    
    def test_validate_short_transcript_warns(self, processor, sample_profile, sample_screening_template):
        """Test validation warns for short transcript."""
        input_data = CandidateReportInput(
            transcript="Short transcript",
            screening_template=sample_screening_template,
            requirement_profile=sample_profile,
            candidate_name="John Smith",
            interview_date=datetime.now(),
        )
        result = processor.validate(input_data)
        
        assert result.is_valid is True  # Still valid
        assert any(w.field == "transcript" for w in result.warnings)
    
    def test_validate_valid_input_passes(self, processor, sample_input):
        """Test validation passes for valid input."""
        result = processor.validate(sample_input)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_process_creates_report(self, processor, sample_input):
        """Test processing creates a valid report."""
        report = processor.process(sample_input)
        
        assert report.candidate_initials == "JS"
        assert report.position_name == "Senior Software Engineer"
        assert report.artifact_type == ArtifactType.CANDIDATE_REPORTS
    
    def test_process_invalid_input_raises(self, processor, sample_profile, sample_screening_template):
        """Test processing raises for invalid input."""
        input_data = CandidateReportInput(
            transcript="",
            screening_template=sample_screening_template,
            requirement_profile=sample_profile,
            candidate_name="John Smith",
            interview_date=datetime.now(),
        )
        
        with pytest.raises(InvalidInputError):
            processor.process(input_data)


class TestTranscriptProcessing:
    """Tests for transcript processing (Req 8.1, 8.2)."""
    
    @pytest.fixture
    def processor(self):
        return CandidateReportProcessor()
    
    def test_corrects_transcription_errors(self, processor):
        """Test transcription errors are corrected (Req 8.2)."""
        transcript = "I'm gonna work on this. I wanna learn more."
        corrected = processor._correct_transcription_errors(transcript)
        
        assert "going to" in corrected
        assert "want to" in corrected
        assert "gonna" not in corrected
        assert "wanna" not in corrected
    
    def test_parses_teams_format(self, processor, sample_transcript):
        """Test parsing Microsoft Teams transcript format (Req 8.1)."""
        sections = processor._parse_transcript(sample_transcript)
        
        assert len(sections) > 0
        assert any(s.speaker == "Interviewer" for s in sections)
        assert any(s.speaker == "John Smith" for s in sections)
    
    def test_handles_unstructured_transcript(self, processor):
        """Test handling unstructured transcript."""
        transcript = "This is just plain text without timestamps or speakers."
        sections = processor._parse_transcript(transcript)
        
        assert len(sections) == 1
        assert sections[0].speaker == "Unknown"
        assert sections[0].content == transcript


class TestContentExtraction:
    """Tests for content extraction (Req 8.3)."""
    
    @pytest.fixture
    def processor(self):
        return CandidateReportProcessor()
    
    def test_extracts_motivation_content(self, processor, sample_transcript):
        """Test extracting motivation-related content."""
        sections = processor._parse_transcript(sample_transcript)
        motivation = processor._extract_motivation_content(sections)
        
        assert len(motivation) > 0
        # Should find content about being "excited" or "interested"
        assert any("excited" in m.lower() or "interested" in m.lower() for m in motivation)
    
    def test_extracts_practical_content(self, processor, sample_transcript):
        """Test extracting practical information."""
        sections = processor._parse_transcript(sample_transcript)
        practical = processor._extract_practical_content(sections)
        
        assert len(practical) > 0
        # Should find content about notice period, salary, location
        combined = " ".join(practical).lower()
        assert "notice" in combined or "salary" in combined or "stockholm" in combined


class TestReportStructure:
    """Tests for report structure (Req 8.5)."""
    
    @pytest.fixture
    def processor(self):
        return CandidateReportProcessor()
    
    def test_report_has_all_sections(self, processor, sample_input):
        """Test report has all required sections."""
        report = processor.process(sample_input)
        
        # Candidate Summary (via initials and recommendation)
        assert report.candidate_initials
        assert report.recommendation
        
        # Professional Background
        assert report.professional_background
        
        # Motivation Assessment
        assert report.motivation_assessment
        assert report.motivation_assessment.skill_name == "Motivation"
        
        # Skill Assessments
        assert len(report.skill_assessments) > 0
        
        # Practical Details
        assert report.practical_details
        
        # Risks/Considerations
        assert isinstance(report.risks_and_considerations, list)
        
        # Conclusion
        assert report.conclusion
    
    def test_report_anonymizes_candidate(self, processor, sample_input):
        """Test candidate is anonymized (Req 8.7)."""
        report = processor.process(sample_input)
        
        # Initials should be 2-3 characters
        assert 2 <= len(report.candidate_initials) <= 3
        # Full name should still be stored internally
        assert report.candidate_full_name == "John Smith"


class TestComparisonTable:
    """Tests for comparison table creation (Req 8.7)."""
    
    def test_creates_comparison_table(self):
        """Test creating a comparison table."""
        reports = [
            CandidateReport(
                candidate_initials="JS",
                candidate_full_name="John Smith",
                position_name="Engineer",
                interview_date=datetime.now(),
                recommendation=Recommendation.RECOMMENDED,
                professional_background="Background",
                motivation_assessment=SkillAssessment(
                    skill_name="Motivation",
                    summary="Summary",
                    examples=[],
                    rating=Rating.GOOD,
                    rating_explanation="Explanation",
                ),
                skill_assessments=[
                    SkillAssessment(
                        skill_name="Python",
                        summary="Summary",
                        examples=[],
                        rating=Rating.EXCELLENT,
                        rating_explanation="Explanation",
                    ),
                ],
                practical_details=PracticalDetails(
                    notice_period="1 month",
                    salary_expectation="50000",
                    location="Stockholm",
                ),
                risks_and_considerations=[],
                conclusion="Conclusion",
            ),
            CandidateReport(
                candidate_initials="JD",
                candidate_full_name="Jane Doe",
                position_name="Engineer",
                interview_date=datetime.now(),
                recommendation=Recommendation.BORDERLINE,
                professional_background="Background",
                motivation_assessment=SkillAssessment(
                    skill_name="Motivation",
                    summary="Summary",
                    examples=[],
                    rating=Rating.OKAY,
                    rating_explanation="Explanation",
                ),
                skill_assessments=[
                    SkillAssessment(
                        skill_name="Python",
                        summary="Summary",
                        examples=[],
                        rating=Rating.GOOD,
                        rating_explanation="Explanation",
                    ),
                ],
                practical_details=PracticalDetails(
                    notice_period="2 months",
                    salary_expectation="55000",
                    location="Copenhagen",
                ),
                risks_and_considerations=[],
                conclusion="Conclusion",
            ),
        ]
        
        table = create_comparison_table(reports)
        
        assert "headers" in table
        assert "rows" in table
        assert len(table["rows"]) == 2
        
        # Check headers include expected columns
        assert "Candidate" in table["headers"]
        assert "Motivation" in table["headers"]
        assert "Recommendation" in table["headers"]
        
        # Check candidates are anonymized (initials only)
        assert table["rows"][0][0] == "JS"
        assert table["rows"][1][0] == "JD"
    
    def test_empty_reports_returns_empty_table(self):
        """Test empty reports list returns empty table."""
        table = create_comparison_table([])
        
        assert table["headers"] == []
        assert table["rows"] == []
    
    def test_uses_initials_not_full_names(self):
        """Test comparison table uses initials, not full names (Req 8.7)."""
        report = CandidateReport(
            candidate_initials="ABC",
            candidate_full_name="Alice Bob Charlie",
            position_name="Engineer",
            interview_date=datetime.now(),
            recommendation=Recommendation.RECOMMENDED,
            professional_background="Background",
            motivation_assessment=SkillAssessment(
                skill_name="Motivation",
                summary="Summary",
                examples=[],
                rating=Rating.GOOD,
                rating_explanation="Explanation",
            ),
            skill_assessments=[],
            practical_details=PracticalDetails(
                notice_period="1 month",
                salary_expectation="50000",
                location="Stockholm",
            ),
            risks_and_considerations=[],
            conclusion="Conclusion",
        )
        
        table = create_comparison_table([report])
        
        # First column should be initials
        assert table["rows"][0][0] == "ABC"
        # Full name should NOT appear anywhere in the table
        for row in table["rows"]:
            for cell in row:
                assert "Alice" not in str(cell)
                assert "Charlie" not in str(cell)
