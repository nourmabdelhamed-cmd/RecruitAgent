"""Document generator for Tata recruitment assistant.

This module provides document generation and formatting capabilities
for all Tata artifacts, producing Word-ready text and comparison tables.

Requirements covered:
- Output formatting for all module artifacts
- Comparison table generation for candidate reports
- Word-ready text generation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Protocol, Union, Any
from abc import abstractmethod

from src.tata.memory.memory import Artifact, ArtifactType
from src.tata.modules.profile.profile import RequirementProfile
from src.tata.modules.jobad.jobad import JobAd
from src.tata.modules.screening.screening import ScreeningTemplate
from src.tata.modules.headhunting.headhunting import HeadhuntingMessages
from src.tata.modules.report.candidate import CandidateReport, anonymize_name
from src.tata.modules.report.funnel import FunnelReport


class OutputFormat(Enum):
    """Output format type for document generation."""
    WORD = "word"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"


@dataclass
class ComparisonTable:
    """Table comparing multiple candidates.
    
    Used for side-by-side candidate comparison with anonymized identifiers.
    
    Attributes:
        headers: Column headers (e.g., ["Skill", "Candidate 1", "Candidate 2"])
        rows: Table rows with data
        title: Optional table title
    """
    headers: List[str]
    rows: List[List[str]]
    title: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Convert table to markdown format.
        
        Returns:
            Markdown-formatted table string
        """
        if not self.headers or not self.rows:
            return ""
        
        lines = []
        
        if self.title:
            lines.append(f"## {self.title}")
            lines.append("")
        
        # Header row
        lines.append("| " + " | ".join(self.headers) + " |")
        
        # Separator row
        lines.append("| " + " | ".join(["---"] * len(self.headers)) + " |")
        
        # Data rows
        for row in self.rows:
            # Pad row if needed
            padded_row = row + [""] * (len(self.headers) - len(row))
            lines.append("| " + " | ".join(padded_row[:len(self.headers)]) + " |")
        
        return "\n".join(lines)
    
    def to_plain_text(self) -> str:
        """Convert table to plain text format.
        
        Returns:
            Plain text formatted table string
        """
        if not self.headers or not self.rows:
            return ""
        
        lines = []
        
        if self.title:
            lines.append(self.title)
            lines.append("=" * len(self.title))
            lines.append("")
        
        # Calculate column widths
        all_rows = [self.headers] + self.rows
        col_widths = []
        for i in range(len(self.headers)):
            max_width = max(
                len(str(row[i])) if i < len(row) else 0
                for row in all_rows
            )
            col_widths.append(max(max_width, 10))
        
        # Header row
        header_line = "  ".join(
            str(h).ljust(col_widths[i])
            for i, h in enumerate(self.headers)
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        # Data rows
        for row in self.rows:
            padded_row = row + [""] * (len(self.headers) - len(row))
            row_line = "  ".join(
                str(padded_row[i]).ljust(col_widths[i])
                for i in range(len(self.headers))
            )
            lines.append(row_line)
        
        return "\n".join(lines)



class DocumentGenerator(Protocol):
    """Protocol for document generation.
    
    Implementations produce formatted outputs from Tata artifacts.
    """
    
    @abstractmethod
    def generate_word_ready(
        self,
        artifact: Artifact,
        output_format: OutputFormat = OutputFormat.WORD
    ) -> str:
        """Generate Word-ready output from an artifact.
        
        Args:
            artifact: The artifact to format
            output_format: The desired output format
            
        Returns:
            Formatted text string
        """
        ...
    
    @abstractmethod
    def generate_comparison(
        self,
        reports: List[CandidateReport]
    ) -> ComparisonTable:
        """Generate candidate comparison table.
        
        Args:
            reports: List of candidate reports to compare
            
        Returns:
            ComparisonTable with anonymized candidates
        """
        ...


def generate_word_ready(
    artifact: Artifact,
    output_format: OutputFormat = OutputFormat.WORD
) -> str:
    """Generate Word-ready output from an artifact.
    
    Dispatches to the appropriate formatter based on artifact type.
    
    Args:
        artifact: The artifact to format
        output_format: The desired output format
        
    Returns:
        Formatted text string ready for Word or other document editors
    """
    artifact_type = artifact.artifact_type
    
    if artifact_type == ArtifactType.REQUIREMENT_PROFILE:
        return _format_requirement_profile(artifact, output_format)  # type: ignore
    elif artifact_type == ArtifactType.JOB_AD:
        return _format_job_ad(artifact, output_format)  # type: ignore
    elif artifact_type in (ArtifactType.TA_SCREENING_TEMPLATE, ArtifactType.HM_SCREENING_TEMPLATE):
        return _format_screening_template(artifact, output_format)  # type: ignore
    elif artifact_type == ArtifactType.HEADHUNTING_MESSAGES:
        return _format_headhunting_messages(artifact, output_format)  # type: ignore
    elif artifact_type == ArtifactType.CANDIDATE_REPORTS:
        return _format_candidate_report(artifact, output_format)  # type: ignore
    elif artifact_type == ArtifactType.FUNNEL_REPORT:
        return _format_funnel_report(artifact, output_format)  # type: ignore
    else:
        # Fallback to JSON for unknown types
        return artifact.to_json()


def _format_requirement_profile(
    profile: RequirementProfile,
    output_format: OutputFormat
) -> str:
    """Format a requirement profile for output.
    
    Args:
        profile: The requirement profile
        output_format: The desired format
        
    Returns:
        Formatted string
    """
    lines = []
    
    if output_format == OutputFormat.MARKDOWN:
        lines.append(f"# Requirement Profile: {profile.position_title}")
        lines.append("")
        lines.append("## Must-Have Skills")
        for i, skill in enumerate(profile.must_have_skills, 1):
            lines.append(f"{i}. {skill}")
        lines.append("")
        lines.append("## Primary Responsibilities")
        for resp in profile.primary_responsibilities:
            lines.append(f"• {resp}")
        if profile.good_to_haves:
            lines.append("")
            lines.append("## Good to Have")
            for gth in profile.good_to_haves:
                lines.append(f"• {gth}")
        if profile.soft_skills:
            lines.append("")
            lines.append("## Soft Skills")
            lines.append(", ".join(profile.soft_skills))
    else:
        # WORD or PLAIN_TEXT format
        lines.append(f"REQUIREMENT PROFILE: {profile.position_title}")
        lines.append("")
        lines.append("MUST-HAVE SKILLS")
        for i, skill in enumerate(profile.must_have_skills, 1):
            lines.append(f"  {i}. {skill}")
        lines.append("")
        lines.append("PRIMARY RESPONSIBILITIES")
        for resp in profile.primary_responsibilities:
            lines.append(f"  • {resp}")
        if profile.good_to_haves:
            lines.append("")
            lines.append("GOOD TO HAVE")
            for gth in profile.good_to_haves:
                lines.append(f"  • {gth}")
        if profile.soft_skills:
            lines.append("")
            lines.append("SOFT SKILLS")
            lines.append(f"  {', '.join(profile.soft_skills)}")
    
    return "\n".join(lines)


def _format_job_ad(job_ad: JobAd, output_format: OutputFormat) -> str:
    """Format a job ad for output.
    
    Args:
        job_ad: The job ad
        output_format: The desired format
        
    Returns:
        Formatted string
    """
    # JobAd already has a to_text method
    if output_format == OutputFormat.MARKDOWN:
        return job_ad.to_text()
    else:
        # For WORD format, use the same text output
        return job_ad.to_text()


def _format_screening_template(
    template: ScreeningTemplate,
    output_format: OutputFormat
) -> str:
    """Format a screening template for output.
    
    Args:
        template: The screening template
        output_format: The desired format
        
    Returns:
        Formatted string
    """
    lines = []
    template_type = "Hiring Manager" if template.is_hm_template else "TA"
    
    if output_format == OutputFormat.MARKDOWN:
        lines.append(f"# {template_type} Screening Template")
        lines.append("")
        
        if template.role_intro:
            lines.append("## Role Introduction")
            lines.append(template.role_intro)
            lines.append("")
        
        lines.append("## Motivation Questions")
        for q in template.motivation_questions:
            lines.append(f"• {q.text}")
        lines.append("")
        
        lines.append("## Skill Questions")
        for skill_set in template.skill_questions:
            lines.append(f"### {skill_set.skill_name} ({skill_set.skill_type.value})")
            lines.append(f"**Main Question:** {skill_set.main_question}")
            lines.append("**Follow-ups:**")
            for fu in skill_set.follow_up_questions:
                lines.append(f"  • {fu}")
            if skill_set.notes_space:
                lines.append("**Notes:** _________________________________")
            lines.append("")
        
        lines.append("## Practical Questions")
        for q in template.practical_questions:
            lines.append(f"• {q.text}")
        lines.append("")
        
        lines.append("## Closing")
        lines.append(template.closing_guidance)
    else:
        # WORD or PLAIN_TEXT format
        lines.append(f"{template_type.upper()} SCREENING TEMPLATE")
        lines.append("")
        
        if template.role_intro:
            lines.append("ROLE INTRODUCTION")
            lines.append(template.role_intro)
            lines.append("")
        
        lines.append("MOTIVATION QUESTIONS")
        for q in template.motivation_questions:
            lines.append(f"  • {q.text}")
        lines.append("")
        
        lines.append("SKILL QUESTIONS")
        for skill_set in template.skill_questions:
            lines.append(f"  {skill_set.skill_name} ({skill_set.skill_type.value})")
            lines.append(f"    Main: {skill_set.main_question}")
            lines.append("    Follow-ups:")
            for fu in skill_set.follow_up_questions:
                lines.append(f"      • {fu}")
            if skill_set.notes_space:
                lines.append("    Notes: _________________________________")
            lines.append("")
        
        lines.append("PRACTICAL QUESTIONS")
        for q in template.practical_questions:
            lines.append(f"  • {q.text}")
        lines.append("")
        
        lines.append("CLOSING")
        lines.append(f"  {template.closing_guidance}")
    
    return "\n".join(lines)



def _format_headhunting_messages(
    messages: HeadhuntingMessages,
    output_format: OutputFormat
) -> str:
    """Format headhunting messages for output.
    
    Args:
        messages: The headhunting messages
        output_format: The desired format
        
    Returns:
        Formatted string with all message versions and languages
    """
    lines = []
    
    if output_format == OutputFormat.MARKDOWN:
        lines.append("# Headhunting Messages")
        lines.append("")
        
        # Short & Direct
        lines.append("## Short & Direct")
        lines.append(f"**English:** {messages.short_direct.en}")
        lines.append(f"**Swedish:** {messages.short_direct.sv}")
        lines.append(f"**Danish:** {messages.short_direct.da}")
        lines.append(f"**Norwegian:** {messages.short_direct.no}")
        lines.append(f"**German (du):** {messages.short_direct.de_du}")
        lines.append(f"**German (Sie):** {messages.short_direct.de_sie}")
        lines.append("")
        
        # Value Proposition
        lines.append("## Value Proposition")
        lines.append(f"**English:** {messages.value_proposition.en}")
        lines.append(f"**Swedish:** {messages.value_proposition.sv}")
        lines.append(f"**Danish:** {messages.value_proposition.da}")
        lines.append(f"**Norwegian:** {messages.value_proposition.no}")
        lines.append(f"**German (du):** {messages.value_proposition.de_du}")
        lines.append(f"**German (Sie):** {messages.value_proposition.de_sie}")
        lines.append("")
        
        # Call to Action
        lines.append("## Call to Action")
        lines.append(f"**English:** {messages.call_to_action.en}")
        lines.append(f"**Swedish:** {messages.call_to_action.sv}")
        lines.append(f"**Danish:** {messages.call_to_action.da}")
        lines.append(f"**Norwegian:** {messages.call_to_action.no}")
        lines.append(f"**German (du):** {messages.call_to_action.de_du}")
        lines.append(f"**German (Sie):** {messages.call_to_action.de_sie}")
    else:
        # WORD or PLAIN_TEXT format
        lines.append("HEADHUNTING MESSAGES")
        lines.append("")
        
        lines.append("SHORT & DIRECT")
        lines.append(f"  English: {messages.short_direct.en}")
        lines.append(f"  Swedish: {messages.short_direct.sv}")
        lines.append(f"  Danish: {messages.short_direct.da}")
        lines.append(f"  Norwegian: {messages.short_direct.no}")
        lines.append(f"  German (du): {messages.short_direct.de_du}")
        lines.append(f"  German (Sie): {messages.short_direct.de_sie}")
        lines.append("")
        
        lines.append("VALUE PROPOSITION")
        lines.append(f"  English: {messages.value_proposition.en}")
        lines.append(f"  Swedish: {messages.value_proposition.sv}")
        lines.append(f"  Danish: {messages.value_proposition.da}")
        lines.append(f"  Norwegian: {messages.value_proposition.no}")
        lines.append(f"  German (du): {messages.value_proposition.de_du}")
        lines.append(f"  German (Sie): {messages.value_proposition.de_sie}")
        lines.append("")
        
        lines.append("CALL TO ACTION")
        lines.append(f"  English: {messages.call_to_action.en}")
        lines.append(f"  Swedish: {messages.call_to_action.sv}")
        lines.append(f"  Danish: {messages.call_to_action.da}")
        lines.append(f"  Norwegian: {messages.call_to_action.no}")
        lines.append(f"  German (du): {messages.call_to_action.de_du}")
        lines.append(f"  German (Sie): {messages.call_to_action.de_sie}")
    
    return "\n".join(lines)


def _format_candidate_report(
    report: CandidateReport,
    output_format: OutputFormat
) -> str:
    """Format a candidate report for output.
    
    Args:
        report: The candidate report
        output_format: The desired format
        
    Returns:
        Formatted string
    """
    lines = []
    
    if output_format == OutputFormat.MARKDOWN:
        lines.append(f"# Candidate Report: {report.candidate_initials}")
        lines.append(f"**Position:** {report.position_name}")
        lines.append(f"**Interview Date:** {report.interview_date.strftime('%Y-%m-%d')}")
        lines.append(f"**Recommendation:** {report.recommendation.value}")
        lines.append("")
        
        lines.append("## Professional Background")
        lines.append(report.professional_background)
        lines.append("")
        
        lines.append("## Motivation Assessment")
        lines.append(f"**Rating:** {report.motivation_assessment.rating.value}/5")
        lines.append(f"**Summary:** {report.motivation_assessment.summary}")
        lines.append(f"**Explanation:** {report.motivation_assessment.rating_explanation}")
        lines.append("")
        
        lines.append("## Skill Assessments")
        for sa in report.skill_assessments:
            lines.append(f"### {sa.skill_name}")
            lines.append(f"**Rating:** {sa.rating.value}/5")
            lines.append(f"**Summary:** {sa.summary}")
            lines.append(f"**Explanation:** {sa.rating_explanation}")
            if sa.examples:
                lines.append("**Examples:**")
                for ex in sa.examples:
                    lines.append(f"  • {ex[:100]}...")
            lines.append("")
        
        lines.append("## Practical Details")
        lines.append(f"• Notice Period: {report.practical_details.notice_period}")
        lines.append(f"• Salary Expectation: {report.practical_details.salary_expectation}")
        lines.append(f"• Location: {report.practical_details.location}")
        lines.append(f"• Languages: {', '.join(report.practical_details.languages)}")
        lines.append("")
        
        if report.risks_and_considerations:
            lines.append("## Risks & Considerations")
            for risk in report.risks_and_considerations:
                lines.append(f"• {risk}")
            lines.append("")
        
        lines.append("## Conclusion")
        lines.append(report.conclusion)
    else:
        # WORD or PLAIN_TEXT format
        lines.append(f"CANDIDATE REPORT: {report.candidate_initials}")
        lines.append(f"Position: {report.position_name}")
        lines.append(f"Interview Date: {report.interview_date.strftime('%Y-%m-%d')}")
        lines.append(f"Recommendation: {report.recommendation.value}")
        lines.append("")
        
        lines.append("PROFESSIONAL BACKGROUND")
        lines.append(f"  {report.professional_background}")
        lines.append("")
        
        lines.append("MOTIVATION ASSESSMENT")
        lines.append(f"  Rating: {report.motivation_assessment.rating.value}/5")
        lines.append(f"  Summary: {report.motivation_assessment.summary}")
        lines.append(f"  Explanation: {report.motivation_assessment.rating_explanation}")
        lines.append("")
        
        lines.append("SKILL ASSESSMENTS")
        for sa in report.skill_assessments:
            lines.append(f"  {sa.skill_name}")
            lines.append(f"    Rating: {sa.rating.value}/5")
            lines.append(f"    Summary: {sa.summary}")
            lines.append(f"    Explanation: {sa.rating_explanation}")
            lines.append("")
        
        lines.append("PRACTICAL DETAILS")
        lines.append(f"  Notice Period: {report.practical_details.notice_period}")
        lines.append(f"  Salary Expectation: {report.practical_details.salary_expectation}")
        lines.append(f"  Location: {report.practical_details.location}")
        lines.append(f"  Languages: {', '.join(report.practical_details.languages)}")
        lines.append("")
        
        if report.risks_and_considerations:
            lines.append("RISKS & CONSIDERATIONS")
            for risk in report.risks_and_considerations:
                lines.append(f"  • {risk}")
            lines.append("")
        
        lines.append("CONCLUSION")
        lines.append(f"  {report.conclusion}")
    
    return "\n".join(lines)


def _format_funnel_report(
    report: FunnelReport,
    output_format: OutputFormat
) -> str:
    """Format a funnel report for output.
    
    Args:
        report: The funnel report
        output_format: The desired format
        
    Returns:
        Formatted string
    """
    lines = []
    
    if output_format == OutputFormat.MARKDOWN:
        lines.append("# Funnel Report")
        lines.append("")
        lines.append("## Summary")
        lines.append(report.summary)
        lines.append("")
        
        lines.append("## Funnel Stages")
        lines.append("| Stage | Count | Conversion | Cumulative |")
        lines.append("|-------|-------|------------|------------|")
        for stage in report.funnel_table:
            lines.append(
                f"| {stage.name} | {stage.count} | "
                f"{stage.conversion_from_previous:.1f}% | "
                f"{stage.cumulative_conversion:.1f}% |"
            )
        lines.append("")
        
        if report.bottlenecks:
            lines.append("## Bottlenecks")
            for bn in report.bottlenecks:
                lines.append(f"• **{bn.stage}** ({bn.severity}): {bn.conversion_rate:.1f}% conversion")
            lines.append("")
        
        if report.suggested_fixes:
            lines.append("## Suggested Fixes")
            for fix in report.suggested_fixes:
                lines.append(f"• **{fix.bottleneck}**: {fix.fix} (Owner: {fix.owner})")
            lines.append("")
    else:
        # WORD or PLAIN_TEXT format
        lines.append("FUNNEL REPORT")
        lines.append("")
        lines.append("SUMMARY")
        lines.append(f"  {report.summary}")
        lines.append("")
        
        lines.append("FUNNEL STAGES")
        lines.append(f"  {'Stage':<20} {'Count':<10} {'Conversion':<12} {'Cumulative':<12}")
        lines.append("  " + "-" * 54)
        for stage in report.funnel_table:
            lines.append(
                f"  {stage.name:<20} {stage.count:<10} "
                f"{stage.conversion_from_previous:.1f}%{'':<7} "
                f"{stage.cumulative_conversion:.1f}%"
            )
        lines.append("")
        
        if report.bottlenecks:
            lines.append("BOTTLENECKS")
            for bn in report.bottlenecks:
                lines.append(f"  • {bn.stage} ({bn.severity}): {bn.conversion_rate:.1f}% conversion")
            lines.append("")
        
        if report.suggested_fixes:
            lines.append("SUGGESTED FIXES")
            for fix in report.suggested_fixes:
                lines.append(f"  • {fix.bottleneck}: {fix.fix} (Owner: {fix.owner})")
            lines.append("")
    
    return "\n".join(lines)


def generate_comparison_table(
    reports: List[CandidateReport],
    include_skills: bool = True,
    include_practical: bool = True
) -> ComparisonTable:
    """Generate a comparison table from multiple candidate reports.
    
    Creates a side-by-side comparison with anonymized candidate identifiers.
    Per Requirement 8.7, candidates are identified by initials only.
    
    Args:
        reports: List of candidate reports to compare
        include_skills: Whether to include skill ratings
        include_practical: Whether to include practical details
        
    Returns:
        ComparisonTable with anonymized candidates
    """
    if not reports:
        return ComparisonTable(headers=[], rows=[], title="Candidate Comparison")
    
    # Build headers with anonymized candidate identifiers
    headers = ["Criteria"]
    for report in reports:
        # Use initials only per Requirement 8.7
        headers.append(report.candidate_initials)
    
    rows: List[List[str]] = []
    
    # Recommendation row
    rec_row = ["Recommendation"]
    for report in reports:
        rec_row.append(report.recommendation.value)
    rows.append(rec_row)
    
    # Average rating row
    avg_row = ["Average Rating"]
    for report in reports:
        avg_row.append(f"{report.get_average_rating():.1f}/5")
    rows.append(avg_row)
    
    # Motivation rating row
    mot_row = ["Motivation"]
    for report in reports:
        mot_row.append(f"{report.motivation_assessment.rating.value}/5")
    rows.append(mot_row)
    
    # Skill ratings
    if include_skills and reports:
        # Get all unique skill names
        skill_names = set()
        for report in reports:
            for sa in report.skill_assessments:
                skill_names.add(sa.skill_name)
        
        for skill_name in sorted(skill_names):
            skill_row = [skill_name]
            for report in reports:
                # Find this skill in the report
                rating = "-"
                for sa in report.skill_assessments:
                    if sa.skill_name == skill_name:
                        rating = f"{sa.rating.value}/5"
                        break
                skill_row.append(rating)
            rows.append(skill_row)
    
    # Practical details
    if include_practical:
        notice_row = ["Notice Period"]
        salary_row = ["Salary Expectation"]
        location_row = ["Location"]
        
        for report in reports:
            notice_row.append(report.practical_details.notice_period)
            salary_row.append(report.practical_details.salary_expectation)
            location_row.append(report.practical_details.location)
        
        rows.extend([notice_row, salary_row, location_row])
    
    return ComparisonTable(
        headers=headers,
        rows=rows,
        title="Candidate Comparison"
    )
