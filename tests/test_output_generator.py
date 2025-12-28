"""Tests for the Document Generator module.

Tests cover:
- Word-ready text generation for all artifact types
- Comparison table generation
- Output format handling
"""

import pytest
from datetime import datetime

from src.tata.output.generator import (
    OutputFormat,
    ComparisonTable,
    generate_word_ready,
    generate_comparison_table,
)
from src.tata.modules.profile.profile import (
    RequirementProfile,
    ContentSource,
)
from src.tata.modules.jobad.jobad import (
    JobAd,
    RequirementsSection,
)
from src.tata.modules.report.candidate import (
    CandidateReport,
    SkillAssessment,
    PracticalDetails,
    Rating,
    Recommendation,
)


@pytest.fixture
def sample_profile():
    """Create a sample requirement profile for testing."""
    return RequirementProfile(
        position_title="Software Engineer",
        must_have_skills=(
            "Python programming",
            "SQL databases",
            "REST APIs",
            "Git version control",
        ),
        must_have_sources=(
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
        ),
        primary_responsibilities=[
            "Develop new features",
            "Write tests",
            "Code reviews",
        ],
        responsibility_sources=[
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
            ContentSource.STARTUP_NOTES,
        ],
        good_to_haves=["Docker", "Kubernetes"],
        soft_skills=["Communication", "Teamwork"],
    )


@pytest.fixture
def sample_job_ad():
    """Create a sample job ad for testing."""
    return JobAd(
        headline="Software Engineer",
        intro="Join our team as a Software Engineer.",
        role_description="You will develop features.",
        the_why="This role matters.",
        responsibilities=["Develop features", "Write tests", "Review code"],
        requirements=RequirementsSection(
            must_haves=("Python", "SQL", "APIs", "Git"),
            soft_skills="We value teamwork.",
            good_to_haves="Docker is a plus.",
        ),
        soft_skills_paragraph="We look for collaborative people.",
        team_and_why_gc="Join GlobalConnect.",
        process="Our process is smooth.",
        ending="Apply now!",
    )


@pytest.fixture
def sample_candidate_report():
    """Create a sample candidate report for testing."""
    return CandidateReport(
        candidate_initials="JS",
        candidate_full_name="John Smith",
        position_name="Software Engineer",
        interview_date=datetime(2024, 1, 15),
        recommendation=Recommendation.RECOMMENDED,
        professional_background="5 years of experience.",
        motivation_assessment=SkillAssessment(
            skill_name="Motivation",
            summary="Strong motivation.",
            examples=["Excited about the role"],
            rating=Rating.GOOD,
            rating_explanation="Clear career goals.",
        ),
        skill_assessments=[
            SkillAssessment(
                skill_name="Python",
                summary="Strong Python skills.",
                examples=["Built APIs"],
                rating=Rating.EXCELLENT,
                rating_explanation="Demonstrated expertise.",
            ),
        ],
        practical_details=PracticalDetails(
            notice_period="1 month",
            salary_expectation="50000",
            location="Stockholm",
            languages=["English", "Swedish"],
        ),
        risks_and_considerations=["None identified"],
        conclusion="Recommended for hire.",
    )


class TestComparisonTable:
    """Tests for ComparisonTable dataclass."""
    
    def test_create_comparison_table(self):
        """Test creating a comparison table."""
        table = ComparisonTable(
            headers=["Criteria", "Candidate 1", "Candidate 2"],
            rows=[["Rating", "4/5", "3/5"]],
            title="Comparison",
        )
        assert len(table.headers) == 3
        assert len(table.rows) == 1
    
    def test_to_markdown(self):
        """Test markdown conversion."""
        table = ComparisonTable(
            headers=["Criteria", "JS", "AB"],
            rows=[["Rating", "4/5", "3/5"]],
            title="Candidate Comparison",
        )
        md = table.to_markdown()
        assert "## Candidate Comparison" in md
        assert "| Criteria | JS | AB |" in md
        assert "| Rating | 4/5 | 3/5 |" in md
    
    def test_to_markdown_empty(self):
        """Test markdown conversion with empty table."""
        table = ComparisonTable(headers=[], rows=[])
        assert table.to_markdown() == ""
    
    def test_to_plain_text(self):
        """Test plain text conversion."""
        table = ComparisonTable(
            headers=["Criteria", "JS"],
            rows=[["Rating", "4/5"]],
            title="Comparison",
        )
        text = table.to_plain_text()
        assert "Comparison" in text
        assert "Criteria" in text
        assert "Rating" in text


class TestGenerateWordReady:
    """Tests for generate_word_ready function."""
    
    def test_format_requirement_profile_word(self, sample_profile):
        """Test formatting requirement profile for Word."""
        output = generate_word_ready(sample_profile, OutputFormat.WORD)
        assert "REQUIREMENT PROFILE" in output
        assert "Software Engineer" in output
        assert "MUST-HAVE SKILLS" in output
        assert "Python programming" in output
    
    def test_format_requirement_profile_markdown(self, sample_profile):
        """Test formatting requirement profile for Markdown."""
        output = generate_word_ready(sample_profile, OutputFormat.MARKDOWN)
        assert "# Requirement Profile" in output
        assert "## Must-Have Skills" in output
    
    def test_format_job_ad(self, sample_job_ad):
        """Test formatting job ad."""
        output = generate_word_ready(sample_job_ad, OutputFormat.WORD)
        assert "Software Engineer" in output
        assert "Develop features" in output
    
    def test_format_candidate_report_word(self, sample_candidate_report):
        """Test formatting candidate report for Word."""
        output = generate_word_ready(sample_candidate_report, OutputFormat.WORD)
        assert "CANDIDATE REPORT: JS" in output
        assert "Software Engineer" in output
        assert "Recommended" in output
        assert "MOTIVATION ASSESSMENT" in output
    
    def test_format_candidate_report_markdown(self, sample_candidate_report):
        """Test formatting candidate report for Markdown."""
        output = generate_word_ready(sample_candidate_report, OutputFormat.MARKDOWN)
        assert "# Candidate Report: JS" in output
        assert "**Recommendation:** Recommended" in output


class TestGenerateComparisonTable:
    """Tests for generate_comparison_table function."""
    
    def test_generate_comparison_single_candidate(self, sample_candidate_report):
        """Test comparison table with single candidate."""
        table = generate_comparison_table([sample_candidate_report])
        assert len(table.headers) == 2  # Criteria + 1 candidate
        assert table.headers[1] == "JS"  # Initials
    
    def test_generate_comparison_multiple_candidates(self, sample_candidate_report):
        """Test comparison table with multiple candidates."""
        report2 = CandidateReport(
            candidate_initials="AB",
            candidate_full_name="Alice Brown",
            position_name="Software Engineer",
            interview_date=datetime(2024, 1, 16),
            recommendation=Recommendation.BORDERLINE,
            professional_background="3 years experience.",
            motivation_assessment=SkillAssessment(
                skill_name="Motivation",
                summary="Adequate motivation.",
                examples=["Interested"],
                rating=Rating.OKAY,
                rating_explanation="Some interest shown.",
            ),
            skill_assessments=[
                SkillAssessment(
                    skill_name="Python",
                    summary="Basic Python.",
                    examples=["Scripts"],
                    rating=Rating.OKAY,
                    rating_explanation="Basic level.",
                ),
            ],
            practical_details=PracticalDetails(
                notice_period="2 weeks",
                salary_expectation="45000",
                location="Copenhagen",
                languages=["English"],
            ),
            risks_and_considerations=["Limited experience"],
            conclusion="Borderline candidate.",
        )
        
        table = generate_comparison_table([sample_candidate_report, report2])
        assert len(table.headers) == 3  # Criteria + 2 candidates
        assert "JS" in table.headers
        assert "AB" in table.headers
    
    def test_generate_comparison_empty_list(self):
        """Test comparison table with empty list."""
        table = generate_comparison_table([])
        assert len(table.headers) == 0
        assert len(table.rows) == 0
    
    def test_comparison_uses_initials_only(self, sample_candidate_report):
        """Test that comparison uses initials, not full names."""
        table = generate_comparison_table([sample_candidate_report])
        # Full name should not appear
        md = table.to_markdown()
        assert "John Smith" not in md
        assert "JS" in md
    
    def test_comparison_includes_recommendation(self, sample_candidate_report):
        """Test that comparison includes recommendation."""
        table = generate_comparison_table([sample_candidate_report])
        has_recommendation = any("Recommendation" in row[0] for row in table.rows)
        assert has_recommendation
    
    def test_comparison_includes_average_rating(self, sample_candidate_report):
        """Test that comparison includes average rating."""
        table = generate_comparison_table([sample_candidate_report])
        has_avg_rating = any("Average Rating" in row[0] for row in table.rows)
        assert has_avg_rating
