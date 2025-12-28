"""Tool Registry for OpenAI function calling integration.

This module provides the ToolRegistry protocol and InMemoryToolRegistry implementation
for managing tool definitions that map Tata modules to OpenAI-callable functions.

Requirements covered:
- 1.1: Provide OpenAI-compatible tool definitions for all Tata modules
- 1.2: Return JSON schema matching OpenAI's function calling format
- 1.4: Include dependency information in tool descriptions
- 1.5: Provide method to retrieve all tools as a list
"""

from typing import Any, Dict, List, Optional, Protocol

from src.tata.agent.models import ToolDefinition
from src.tata.session.session import ModuleType
from src.tata.dependency.dependency import MODULE_DEPENDENCIES


class ToolRegistry(Protocol):
    """Protocol for managing tool definitions.
    
    Implementations maintain the mapping between OpenAI tools and Tata processors,
    providing tool definitions in OpenAI-compatible format.
    """
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name.
        
        Args:
            name: The tool name (snake_case)
            
        Returns:
            ToolDefinition if found, None otherwise
        """
        ...
    
    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools.
        
        Returns:
            List of all ToolDefinition objects
        """
        ...
    
    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI format.
        
        Returns:
            List of tool definitions in OpenAI function calling format
        """
        ...


# Parameter schemas for each Tata module
# Derived from module input dataclasses per Requirement 1.3

REQUIREMENT_PROFILE_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "startup_notes": {
            "type": "string",
            "description": "Notes from the recruitment start-up meeting containing role requirements, skills needed, and context"
        },
        "position_title": {
            "type": "string",
            "description": "The job position title (e.g., 'Senior Python Developer')"
        },
        "old_job_ad": {
            "type": "string",
            "description": "Previous job advertisement for the role (optional, for reference)"
        },
        "hiring_manager_input": {
            "type": "string",
            "description": "Direct input or notes from the hiring manager (optional)"
        }
    },
    "required": ["startup_notes", "position_title"]
}

JOB_AD_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "startup_notes": {
            "type": "string",
            "description": "Additional notes from recruitment start-up meeting (optional)"
        },
        "old_job_ad": {
            "type": "string",
            "description": "Previous job advertisement for reference (optional)"
        },
        "company_context": {
            "type": "string",
            "description": "Additional company or team context (optional)"
        }
    },
    "required": []
}

TA_SCREENING_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "include_good_to_haves": {
            "type": "boolean",
            "description": "Whether to include good-to-have skill questions (default: false)"
        },
        "include_role_intro": {
            "type": "boolean",
            "description": "Whether to include a role introduction section (default: false)"
        },
        "additional_areas": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Additional areas to cover beyond the profile (optional)"
        }
    },
    "required": []
}

HM_SCREENING_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "include_good_to_haves": {
            "type": "boolean",
            "description": "Whether to include good-to-have skill questions (default: false)"
        },
        "include_role_intro": {
            "type": "boolean",
            "description": "Whether to include a role introduction section (default: false)"
        },
        "additional_areas": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Additional areas to cover beyond the profile (optional)"
        }
    },
    "required": []
}

HEADHUNTING_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "candidate_profile": {
            "type": "string",
            "description": "LinkedIn profile text for personalization (optional)"
        },
        "company_context": {
            "type": "string",
            "description": "Additional company or team context (optional)"
        }
    },
    "required": []
}

CANDIDATE_REPORT_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript": {
            "type": "string",
            "description": "Microsoft Teams interview transcript text"
        },
        "candidate_name": {
            "type": "string",
            "description": "Full name of the candidate"
        },
        "interview_date": {
            "type": "string",
            "description": "Date of the interview (ISO format: YYYY-MM-DD)"
        },
        "candidate_cv": {
            "type": "string",
            "description": "Candidate's CV text for enrichment (optional)"
        }
    },
    "required": ["transcript", "candidate_name", "interview_date"]
}

FUNNEL_REPORT_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "job_title": {
            "type": "string",
            "description": "Title of the position"
        },
        "number_of_positions": {
            "type": "integer",
            "description": "Number of positions to fill"
        },
        "hiring_manager_name": {
            "type": "string",
            "description": "Name of the hiring manager"
        },
        "locations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of job locations (optional)"
        },
        "job_ad_views": {
            "type": "integer",
            "description": "Number of job ad views (optional)"
        },
        "apply_clicks": {
            "type": "integer",
            "description": "Number of apply button clicks (optional)"
        },
        "applications_received": {
            "type": "integer",
            "description": "Total applications received (optional)"
        },
        "qualified_applications": {
            "type": "integer",
            "description": "Applications meeting minimum criteria (optional)"
        },
        "candidates_sourced": {
            "type": "integer",
            "description": "Candidates found through sourcing (optional)"
        },
        "candidates_contacted": {
            "type": "integer",
            "description": "Candidates contacted via outreach (optional)"
        },
        "candidates_replied": {
            "type": "integer",
            "description": "Candidates who replied to outreach (optional)"
        },
        "ta_screenings": {
            "type": "integer",
            "description": "Number of TA screening interviews (optional)"
        },
        "hm_interviews": {
            "type": "integer",
            "description": "Number of hiring manager interviews (optional)"
        },
        "offers_made": {
            "type": "integer",
            "description": "Number of offers extended (optional)"
        },
        "offers_accepted": {
            "type": "integer",
            "description": "Number of offers accepted (optional)"
        }
    },
    "required": ["job_title", "number_of_positions", "hiring_manager_name"]
}

JOB_AD_REVIEW_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "job_ad_text": {
            "type": "string",
            "description": "The job ad text to review"
        },
        "language": {
            "type": "string",
            "enum": ["en", "sv", "da", "no", "de"],
            "description": "Language of the job ad (default: en)"
        },
        "position_title": {
            "type": "string",
            "description": "Position title for context (optional)"
        }
    },
    "required": ["job_ad_text"]
}

DI_REVIEW_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "job_ad_text": {
            "type": "string",
            "description": "The job ad text to review for D&I compliance"
        },
        "language": {
            "type": "string",
            "enum": ["en", "sv", "da", "no", "de"],
            "description": "Language of the job ad (default: en)"
        }
    },
    "required": ["job_ad_text"]
}

CALENDAR_INVITE_PARAMS: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "position_name": {
            "type": "string",
            "description": "Name of the position being interviewed for"
        },
        "hiring_manager_name": {
            "type": "string",
            "description": "Name of the hiring manager"
        },
        "hiring_manager_title": {
            "type": "string",
            "description": "Job title of the hiring manager"
        },
        "recruiter_name": {
            "type": "string",
            "description": "Name of the recruiter sending the invite"
        },
        "location_type": {
            "type": "string",
            "enum": ["teams", "onsite"],
            "description": "Whether interview is on Teams or on-site"
        },
        "interview_type": {
            "type": "string",
            "enum": ["hiring_manager", "case", "team", "ta_screening"],
            "description": "Type of interview"
        },
        "duration": {
            "type": "integer",
            "description": "Duration in minutes (typically 60 or 90)"
        },
        "booking_method": {
            "type": "string",
            "enum": ["jobylon", "manual"],
            "description": "Jobylon booking link or manual date/time"
        },
        "city": {
            "type": "string",
            "enum": ["stockholm", "copenhagen", "oslo"],
            "description": "Office city (required for on-site interviews)"
        },
        "interview_date": {
            "type": "string",
            "description": "Human-readable date for manual booking (e.g., 'Monday, 15 January')"
        },
        "interview_time": {
            "type": "string",
            "description": "Time in 24h format for manual booking (e.g., '14:00')"
        },
        "job_ad_link": {
            "type": "string",
            "description": "Link to the job advertisement (optional)"
        }
    },
    "required": [
        "position_name",
        "hiring_manager_name",
        "hiring_manager_title",
        "recruiter_name",
        "location_type",
        "interview_type",
        "duration",
        "booking_method"
    ]
}


def _get_dependency_description(module_type: ModuleType) -> str:
    """Get dependency description for a module.
    
    Args:
        module_type: The module to get dependencies for
        
    Returns:
        Description string mentioning dependencies, or empty string if none
    """
    deps = MODULE_DEPENDENCIES.get(module_type, [])
    if not deps:
        return ""
    
    dep_names = []
    for dep in deps:
        if dep == ModuleType.REQUIREMENT_PROFILE:
            dep_names.append("requirement profile")
        elif dep == ModuleType.TA_SCREENING:
            dep_names.append("TA screening template")
        else:
            dep_names.append(dep.name.lower().replace("_", " "))
    
    if len(dep_names) == 1:
        return f" Requires {dep_names[0]} to be created first."
    else:
        return f" Requires {', '.join(dep_names[:-1])} and {dep_names[-1]} to be created first."




class InMemoryToolRegistry:
    """In-memory implementation of ToolRegistry.
    
    Registers all Tata modules as OpenAI-callable tools with
    appropriate parameter schemas derived from input dataclasses.
    
    Attributes:
        _tools: Dictionary mapping tool names to ToolDefinition objects
    """
    
    def __init__(self) -> None:
        """Initialize the registry with all Tata module tools."""
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register all Tata module tools.
        
        Creates ToolDefinition for each of the 10 Tata modules:
        - RequirementProfile (A)
        - JobAd (B)
        - TAScreening (C)
        - HMScreening (D)
        - Headhunting (E)
        - CandidateReport (F)
        - FunnelReport (G)
        - JobAdReview (H)
        - DIReview (I)
        - CalendarInvite (J)
        """
        # Module A: Requirement Profile (no dependencies)
        self._register_tool(ToolDefinition(
            name="create_requirement_profile",
            description=(
                "Create a requirement profile for a job position. "
                "The requirement profile is the foundational document containing must-have skills, "
                "responsibilities, and role details. It serves as the backbone for all other outputs."
            ),
            parameters=REQUIREMENT_PROFILE_PARAMS,
            module_type=ModuleType.REQUIREMENT_PROFILE,
        ))
        
        # Module B: Job Ad (requires A)
        self._register_tool(ToolDefinition(
            name="create_job_ad",
            description=(
                "Create a job advertisement based on the requirement profile. "
                "Generates a structured job ad with all required sections including "
                "headline, intro, responsibilities, requirements, and more."
                + _get_dependency_description(ModuleType.JOB_AD)
            ),
            parameters=JOB_AD_PARAMS,
            module_type=ModuleType.JOB_AD,
        ))
        
        # Module C: TA Screening (requires A)
        self._register_tool(ToolDefinition(
            name="create_ta_screening_template",
            description=(
                "Create a Talent Acquisition screening interview template. "
                "Generates structured interview questions based on the requirement profile, "
                "including motivation, skills assessment, and practical questions."
                + _get_dependency_description(ModuleType.TA_SCREENING)
            ),
            parameters=TA_SCREENING_PARAMS,
            module_type=ModuleType.TA_SCREENING,
        ))
        
        # Module D: HM Screening (requires A)
        self._register_tool(ToolDefinition(
            name="create_hm_screening_template",
            description=(
                "Create a Hiring Manager screening interview template. "
                "Similar to TA screening but includes space for notes after every question. "
                "Generates structured interview questions based on the requirement profile."
                + _get_dependency_description(ModuleType.HM_SCREENING)
            ),
            parameters=HM_SCREENING_PARAMS,
            module_type=ModuleType.HM_SCREENING,
        ))
        
        # Module E: Headhunting (requires A)
        self._register_tool(ToolDefinition(
            name="create_headhunting_messages",
            description=(
                "Create LinkedIn outreach messages for headhunting passive candidates. "
                "Generates three message versions (short & direct, value-proposition, call-to-action) "
                "in all supported languages (EN, SV, DA, NO, DE)."
                + _get_dependency_description(ModuleType.HEADHUNTING)
            ),
            parameters=HEADHUNTING_PARAMS,
            module_type=ModuleType.HEADHUNTING,
        ))
        
        # Module F: Candidate Report (requires A, C)
        self._register_tool(ToolDefinition(
            name="create_candidate_report",
            description=(
                "Create a candidate assessment report from an interview transcript. "
                "Parses Microsoft Teams transcripts and generates structured reports with "
                "skill ratings (1-5), background summary, and recommendations."
                + _get_dependency_description(ModuleType.CANDIDATE_REPORT)
            ),
            parameters=CANDIDATE_REPORT_PARAMS,
            module_type=ModuleType.CANDIDATE_REPORT,
        ))
        
        # Module G: Funnel Report (no dependencies)
        self._register_tool(ToolDefinition(
            name="create_funnel_report",
            description=(
                "Create a recruitment funnel analysis report. "
                "Analyzes ATS and LinkedIn data to calculate conversion rates, "
                "identify bottlenecks, and suggest fixes with assigned owners. "
                "This is a standalone module with no dependencies."
            ),
            parameters=FUNNEL_REPORT_PARAMS,
            module_type=ModuleType.FUNNEL_REPORT,
        ))
        
        # Module H: Job Ad Review (no dependencies)
        self._register_tool(ToolDefinition(
            name="review_job_ad",
            description=(
                "Review an existing job ad for structure, completeness, and quality. "
                "Provides a scorecard with section analysis, identifies issues, "
                "and generates improvement recommendations. "
                "This is a standalone module with no dependencies."
            ),
            parameters=JOB_AD_REVIEW_PARAMS,
            module_type=ModuleType.JOB_AD_REVIEW,
        ))
        
        # Module I: D&I Review (no dependencies)
        self._register_tool(ToolDefinition(
            name="review_di_compliance",
            description=(
                "Review a job ad for Diversity & Inclusion compliance. "
                "Checks for biased or exclusionary language across categories "
                "(gender, age, disability, nationality, etc.) and suggests alternatives. "
                "This is a standalone module with no dependencies."
            ),
            parameters=DI_REVIEW_PARAMS,
            module_type=ModuleType.DI_REVIEW,
        ))
        
        # Module J: Calendar Invite (no dependencies)
        self._register_tool(ToolDefinition(
            name="create_calendar_invite",
            description=(
                "Create interview invitation text for candidates. "
                "Generates professional calendar invitation with correct office addresses, "
                "booking instructions, and participant details. "
                "This is a standalone module with no dependencies."
            ),
            parameters=CALENDAR_INVITE_PARAMS,
            module_type=ModuleType.CALENDAR_INVITE,
        ))
    
    def _register_tool(self, tool: ToolDefinition) -> None:
        """Register a tool definition.
        
        Args:
            tool: The ToolDefinition to register
        """
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name.
        
        Args:
            name: The tool name (snake_case)
            
        Returns:
            ToolDefinition if found, None otherwise
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools.
        
        Returns:
            List of all ToolDefinition objects
        """
        return list(self._tools.values())
    
    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI format.
        
        Returns:
            List of tool definitions in OpenAI function calling format,
            each with type="function" and function object containing
            name, description, and parameters.
        """
        return [tool.to_openai_format() for tool in self._tools.values()]
