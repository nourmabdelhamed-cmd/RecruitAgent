"""Tests for Job Ad Review module (Module H).

Tests the JobAdReviewProcessor for reviewing job ads,
detecting structure issues, and providing recommendations.

Requirements covered:
- Module H specification: Review existing job ads
- Section mapping and gap analysis
- Identify missing or duplicated content
- Provide structured feedback with scorecard
"""

import pytest
from datetime import datetime

from src.tata.session.session import SupportedLanguage
from src.tata.memory.memory import ArtifactType
from src.tata.modules.review.jobad import (
    JobAdSection,
    IssueSeverity,
    SectionAnalysis,
    ReviewIssue,
    JobAdReviewInput,
    JobAdReview,
    JobAdReviewProcessor,
    InvalidInputError,
    detect_sections,
    analyze_section,
    check_content_duplication,
    check_language_compliance,
    generate_recommendations,
    REQUIRED_SECTIONS,
    RECOMMENDED_SECTIONS,
)


class TestJobAdReviewTypes:
    """Tests for Job Ad Review data types."""
    
    def test_job_ad_section_enum_values(self):
        """Test JobAdSection enum has all expected sections."""
        assert JobAdSection.HEADLINE.value == "headline"
        assert JobAdSection.INTRO.value == "intro"
        assert JobAdSection.ROLE_DESCRIPTION.value == "role_description"
        assert JobAdSection.RESPONSIBILITIES.value == "responsibilities"
        assert JobAdSection.REQUIREMENTS.value == "requirements"
        assert JobAdSection.SOFT_SKILLS.value == "soft_skills"
        assert JobAdSection.GOOD_TO_HAVES.value == "good_to_haves"
        assert JobAdSection.TEAM_INFO.value == "team_info"
        assert JobAdSection.COMPANY_INFO.value == "company_info"
        assert JobAdSection.BENEFITS.value == "benefits"
        assert JobAdSection.PROCESS.value == "process"
        assert JobAdSection.CALL_TO_ACTION.value == "call_to_action"
    
    def test_issue_severity_enum_values(self):
        """Test IssueSeverity enum values."""
        assert IssueSeverity.LOW.value == "low"
        assert IssueSeverity.MEDIUM.value == "medium"
        assert IssueSeverity.HIGH.value == "high"
        assert IssueSeverity.CRITICAL.value == "critical"
    
    def test_section_analysis_creation(self):
        """Test SectionAnalysis dataclass creation."""
        analysis = SectionAnalysis(
            section=JobAdSection.RESPONSIBILITIES,
            found=True,
            quality_score=85,
            word_count=50,
            issues=["Minor issue"],
            suggestions=["Suggestion"],
        )
        
        assert analysis.section == JobAdSection.RESPONSIBILITIES
        assert analysis.found is True
        assert analysis.quality_score == 85
        assert analysis.word_count == 50
        assert len(analysis.issues) == 1
        assert len(analysis.suggestions) == 1
    
    def test_review_issue_creation(self):
        """Test ReviewIssue dataclass creation."""
        issue = ReviewIssue(
            category="structure",
            severity=IssueSeverity.HIGH,
            description="Missing section",
            location="Line 5",
            suggestion="Add the section",
        )
        
        assert issue.category == "structure"
        assert issue.severity == IssueSeverity.HIGH
        assert issue.description == "Missing section"
        assert issue.location == "Line 5"
        assert issue.suggestion == "Add the section"
    
    def test_job_ad_review_input_defaults(self):
        """Test JobAdReviewInput default values."""
        input_data = JobAdReviewInput(job_ad_text="Test job ad")
        
        assert input_data.job_ad_text == "Test job ad"
        assert input_data.language == SupportedLanguage.ENGLISH
        assert input_data.position_title is None
    
    def test_job_ad_review_artifact_type(self):
        """Test JobAdReview artifact_type property."""
        review = JobAdReview(
            overall_score=80,
            section_analyses=[],
            issues=[],
            recommendations=[],
            structure_score=85,
            content_score=75,
            compliance_score=90,
            original_text="Test",
        )
        
        assert review.artifact_type == ArtifactType.JOB_AD_REVIEW
    
    def test_job_ad_review_to_json(self):
        """Test JobAdReview JSON serialization."""
        review = JobAdReview(
            overall_score=80,
            section_analyses=[
                SectionAnalysis(
                    section=JobAdSection.HEADLINE,
                    found=True,
                    quality_score=90,
                    word_count=5,
                ),
            ],
            issues=[
                ReviewIssue(
                    category="structure",
                    severity=IssueSeverity.MEDIUM,
                    description="Test issue",
                ),
            ],
            recommendations=["Test recommendation"],
            structure_score=85,
            content_score=75,
            compliance_score=90,
            original_text="Test text",
        )
        
        json_str = review.to_json()
        assert "overall_score" in json_str
        assert "80" in json_str
        assert "headline" in json_str
        assert "structure" in json_str


class TestSectionDetection:
    """Tests for section detection functions."""
    
    def test_detect_headline(self):
        """Test detecting headline (first line)."""
        text = "Software Developer\n\nWe are looking for a developer."
        sections = detect_sections(text, SupportedLanguage.ENGLISH)
        
        assert JobAdSection.HEADLINE in sections
        _, _, content = sections[JobAdSection.HEADLINE]
        assert content == "Software Developer"
    
    def test_detect_responsibilities_section(self):
        """Test detecting responsibilities section."""
        text = """Software Developer

About the Role
We need a developer.

Responsibilities
• Write code
• Review PRs
• Test features
"""
        sections = detect_sections(text, SupportedLanguage.ENGLISH)
        
        assert JobAdSection.RESPONSIBILITIES in sections
        _, _, content = sections[JobAdSection.RESPONSIBILITIES]
        assert "Write code" in content
    
    def test_detect_requirements_section(self):
        """Test detecting requirements section."""
        text = """Software Developer

Requirements
• 3+ years experience
• Python knowledge
• Team player
"""
        sections = detect_sections(text, SupportedLanguage.ENGLISH)
        
        assert JobAdSection.REQUIREMENTS in sections
        _, _, content = sections[JobAdSection.REQUIREMENTS]
        assert "3+ years" in content
    
    def test_detect_swedish_sections(self):
        """Test detecting sections in Swedish."""
        text = """Utvecklare

Om rollen
Vi söker en utvecklare.

Arbetsuppgifter
• Skriva kod
• Granska PR
"""
        sections = detect_sections(text, SupportedLanguage.SWEDISH)
        
        assert JobAdSection.HEADLINE in sections
        assert JobAdSection.ROLE_DESCRIPTION in sections
    
    def test_detect_german_sections(self):
        """Test detecting sections in German."""
        text = """Entwickler

Über die Rolle
Wir suchen einen Entwickler.

Aufgaben
• Code schreiben
• PRs überprüfen
"""
        sections = detect_sections(text, SupportedLanguage.GERMAN)
        
        assert JobAdSection.HEADLINE in sections
        assert JobAdSection.ROLE_DESCRIPTION in sections


class TestSectionAnalysis:
    """Tests for section analysis functions."""
    
    def test_analyze_section_good_quality(self):
        """Test analyzing a good quality section."""
        content = """
        • Write clean, maintainable code
        • Collaborate with team members
        • Participate in code reviews
        • Contribute to technical discussions
        """
        
        analysis = analyze_section(
            JobAdSection.RESPONSIBILITIES,
            content,
            SupportedLanguage.ENGLISH,
        )
        
        assert analysis.found is True
        assert analysis.quality_score >= 70
        assert analysis.word_count > 0
    
    def test_analyze_section_too_short(self):
        """Test analyzing a section that's too short."""
        content = "Write code."
        
        analysis = analyze_section(
            JobAdSection.ROLE_DESCRIPTION,
            content,
            SupportedLanguage.ENGLISH,
        )
        
        assert analysis.quality_score < 100
        assert any("short" in issue.lower() for issue in analysis.issues)
    
    def test_analyze_section_no_bullets(self):
        """Test analyzing responsibilities without bullets."""
        # Content needs to be over 30 words to trigger bullet check
        content = """
        You will write code and review pull requests and test features
        and collaborate with team members and participate in meetings
        and contribute to technical discussions and help with documentation
        and support junior developers and attend daily standups and work
        on exciting projects with the team.
        """
        
        analysis = analyze_section(
            JobAdSection.RESPONSIBILITIES,
            content,
            SupportedLanguage.ENGLISH,
        )
        
        assert any("bullet" in issue.lower() for issue in analysis.issues)
    
    def test_analyze_section_vague_language(self):
        """Test detecting vague language in sections."""
        content = """
        You will work on various projects and handle different tasks.
        Some responsibilities include many things etc and more.
        """
        
        analysis = analyze_section(
            JobAdSection.RESPONSIBILITIES,
            content,
            SupportedLanguage.ENGLISH,
        )
        
        assert any("vague" in issue.lower() for issue in analysis.issues)


class TestDuplicationDetection:
    """Tests for content duplication detection."""
    
    def test_detect_duplicate_sentences(self):
        """Test detecting duplicate sentences."""
        text = """
        We are looking for a developer. The role is exciting.
        We are looking for a developer. Join our team.
        """
        
        issues = check_content_duplication(text)
        
        assert len(issues) >= 1
        assert any(i.category == "duplication" for i in issues)
    
    def test_no_duplication_in_unique_text(self):
        """Test no duplication detected in unique text."""
        text = """
        We are looking for a developer to join our team.
        The ideal candidate will have experience in Python.
        You will work on exciting projects with great people.
        """
        
        issues = check_content_duplication(text)
        
        # Should have no or minimal duplication issues
        sentence_duplicates = [
            i for i in issues
            if "duplicate sentence" in i.description.lower()
        ]
        assert len(sentence_duplicates) == 0


class TestLanguageCompliance:
    """Tests for language compliance checking."""
    
    def test_detect_emojis(self):
        """Test detecting emojis in job ad."""
        text = "Join our amazing team! 🚀 We're hiring!"
        
        score, issues = check_language_compliance(text, SupportedLanguage.ENGLISH)
        
        assert score < 100
        assert any("emoji" in i.description.lower() for i in issues)
    
    def test_detect_dash_bullets(self):
        """Test detecting dash-style bullets."""
        text = """
        Responsibilities:
        - Write code
        - Review PRs
        """
        
        score, issues = check_language_compliance(text, SupportedLanguage.ENGLISH)
        
        assert score < 100
        assert any("dash" in i.description.lower() for i in issues)
    
    def test_clean_text_compliance(self):
        """Test compliance score for clean text."""
        text = """
        We are looking for a developer.
        
        Responsibilities:
        • Write clean code
        • Review pull requests
        """
        
        score, issues = check_language_compliance(text, SupportedLanguage.ENGLISH)
        
        # Should have high compliance score
        assert score >= 80


class TestRecommendations:
    """Tests for recommendation generation."""
    
    def test_recommendations_for_missing_required_sections(self):
        """Test recommendations when required sections are missing."""
        section_analyses = [
            SectionAnalysis(
                section=JobAdSection.HEADLINE,
                found=True,
                quality_score=90,
            ),
            SectionAnalysis(
                section=JobAdSection.RESPONSIBILITIES,
                found=False,
                quality_score=0,
            ),
        ]
        
        recommendations = generate_recommendations(section_analyses, [], 50)
        
        assert any("responsibilities" in r.lower() for r in recommendations)
    
    def test_recommendations_for_low_quality_sections(self):
        """Test recommendations for low quality sections."""
        section_analyses = [
            SectionAnalysis(
                section=JobAdSection.ROLE_DESCRIPTION,
                found=True,
                quality_score=40,
                suggestions=["Add more detail"],
            ),
        ]
        
        recommendations = generate_recommendations(section_analyses, [], 60)
        
        assert len(recommendations) > 0
    
    def test_recommendations_limited_to_ten(self):
        """Test that recommendations are limited to 10."""
        section_analyses = [
            SectionAnalysis(
                section=section,
                found=False,
                quality_score=0,
            )
            for section in JobAdSection
        ]
        
        recommendations = generate_recommendations(section_analyses, [], 20)
        
        assert len(recommendations) <= 10


class TestJobAdReviewProcessor:
    """Tests for JobAdReviewProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a JobAdReviewProcessor instance."""
        return JobAdReviewProcessor()
    
    def test_validate_valid_input(self, processor):
        """Test validation with valid input."""
        input_data = JobAdReviewInput(
            job_ad_text="We are looking for a software developer to join our team. " * 10,
            language=SupportedLanguage.ENGLISH,
        )
        
        result = processor.validate(input_data)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_empty_text(self, processor):
        """Test validation with empty text."""
        input_data = JobAdReviewInput(job_ad_text="")
        
        result = processor.validate(input_data)
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].field == "job_ad_text"
    
    def test_validate_short_text_warning(self, processor):
        """Test validation warning for short text."""
        input_data = JobAdReviewInput(job_ad_text="Short text")
        
        result = processor.validate(input_data)
        
        assert result.is_valid  # Still valid, just a warning
        assert len(result.warnings) == 1
        assert result.warnings[0].field == "job_ad_text"
    
    def test_process_complete_job_ad(self, processor):
        """Test processing a complete job ad."""
        input_data = JobAdReviewInput(
            job_ad_text="""Software Developer

About the Role
We are looking for a talented software developer to join our growing team.
You will work on exciting projects and collaborate with great people.

Responsibilities
• Write clean, maintainable code
• Collaborate with team members on projects
• Participate in code reviews and technical discussions
• Contribute to architecture decisions

Requirements
• 3+ years of software development experience
• Strong knowledge of Python or JavaScript
• Experience with modern frameworks
• Excellent communication skills

About the Team
You will join a team of 10 passionate developers working on cutting-edge technology.

Benefits
• Competitive salary
• Flexible working hours
• Professional development budget

Apply Now
Ready to join us? Send your application today!
""",
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        assert review.overall_score >= 60
        assert review.structure_score >= 60
        assert len(review.section_analyses) > 0
        assert review.original_text == input_data.job_ad_text
    
    def test_process_incomplete_job_ad(self, processor):
        """Test processing an incomplete job ad."""
        input_data = JobAdReviewInput(
            job_ad_text="""Software Developer

We need someone to write code.
""",
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        # Score should be lower due to missing sections
        assert review.overall_score < 80
        assert len(review.recommendations) > 0
        
        # Should identify missing required sections
        missing_sections = [
            sa for sa in review.section_analyses
            if sa.section in REQUIRED_SECTIONS and not sa.found
        ]
        assert len(missing_sections) > 0
    
    def test_process_preserves_original_text(self, processor):
        """Test that original text is preserved unchanged."""
        original = "Software Developer\n\nWe are looking for a developer."
        input_data = JobAdReviewInput(
            job_ad_text=original,
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        assert review.original_text == original
    
    def test_process_invalid_input_raises(self, processor):
        """Test that invalid input raises InvalidInputError."""
        input_data = JobAdReviewInput(job_ad_text="")
        
        with pytest.raises(InvalidInputError):
            processor.process(input_data)
    
    def test_get_required_inputs(self, processor):
        """Test get_required_inputs method."""
        required = processor.get_required_inputs()
        
        assert "job_ad_text" in required
    
    def test_get_optional_inputs(self, processor):
        """Test get_optional_inputs method."""
        optional = processor.get_optional_inputs()
        
        assert "language" in optional
        assert "position_title" in optional
    
    def test_process_generates_recommendations(self, processor):
        """Test that processing generates recommendations."""
        input_data = JobAdReviewInput(
            job_ad_text="""Software Developer

Short description.
""",
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        assert len(review.recommendations) > 0
    
    def test_process_detects_compliance_issues(self, processor):
        """Test that processing detects compliance issues."""
        input_data = JobAdReviewInput(
            job_ad_text="""Software Developer 🚀

Join our amazing team!

Responsibilities:
- Write code
- Review PRs
""",
            language=SupportedLanguage.ENGLISH,
        )
        
        review = processor.process(input_data)
        
        # Should detect emoji and dash bullets
        assert review.compliance_score < 100
        compliance_issues = [
            i for i in review.issues
            if i.category in ["compliance", "banned_words"]
        ]
        assert len(compliance_issues) > 0


class TestMultiLanguageSupport:
    """Tests for multi-language job ad review."""
    
    @pytest.fixture
    def processor(self):
        return JobAdReviewProcessor()
    
    def test_swedish_job_ad_review(self, processor):
        """Test reviewing a Swedish job ad."""
        input_data = JobAdReviewInput(
            job_ad_text="""Utvecklare

Om rollen
Vi söker en utvecklare till vårt team.

Arbetsuppgifter
• Skriva kod
• Granska pull requests
• Samarbeta med teamet

Krav
• 3+ års erfarenhet
• Kunskaper i Python
""",
            language=SupportedLanguage.SWEDISH,
        )
        
        review = processor.process(input_data)
        
        assert review.overall_score > 0
        assert len(review.section_analyses) > 0
    
    def test_german_job_ad_review(self, processor):
        """Test reviewing a German job ad."""
        input_data = JobAdReviewInput(
            job_ad_text="""Entwickler

Über die Rolle
Wir suchen einen Entwickler für unser Team.

Aufgaben
• Code schreiben
• Pull Requests überprüfen
• Mit dem Team zusammenarbeiten

Anforderungen
• 3+ Jahre Erfahrung
• Python-Kenntnisse
""",
            language=SupportedLanguage.GERMAN,
        )
        
        review = processor.process(input_data)
        
        assert review.overall_score > 0
        assert len(review.section_analyses) > 0


class TestRequiredAndRecommendedSections:
    """Tests for required and recommended section constants."""
    
    def test_required_sections_defined(self):
        """Test that required sections are defined."""
        assert JobAdSection.HEADLINE in REQUIRED_SECTIONS
        assert JobAdSection.ROLE_DESCRIPTION in REQUIRED_SECTIONS
        assert JobAdSection.RESPONSIBILITIES in REQUIRED_SECTIONS
        assert JobAdSection.REQUIREMENTS in REQUIRED_SECTIONS
    
    def test_recommended_sections_defined(self):
        """Test that recommended sections are defined."""
        assert JobAdSection.INTRO in RECOMMENDED_SECTIONS
        assert JobAdSection.TEAM_INFO in RECOMMENDED_SECTIONS
        assert JobAdSection.BENEFITS in RECOMMENDED_SECTIONS
        assert JobAdSection.CALL_TO_ACTION in RECOMMENDED_SECTIONS
