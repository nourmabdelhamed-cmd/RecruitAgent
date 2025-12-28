"""Calendar Invitation module for Tata recruitment assistant.

This module implements Module J: Calendar Invitation text generation.
Creates professional interview invitation text for candidates.

Requirements covered:
- 11.1: Conversationally collect must-have inputs (position name, hiring manager details,
        interview type, location, duration, booking method)
- 11.2: Include correct office address and map link for selected city (Stockholm, Copenhagen, Oslo)
- 11.3: Include booking link instruction for Jobylon booking
- 11.4: Ask for and include specific date and time for manual booking
- 11.5: Ensure candidate name appears in subject and greeting
- 11.6: Produce clean, word-ready text following defined templates
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
import json

from src.tata.memory.memory import ArtifactType


class City(Enum):
    """Office cities for on-site interviews (Requirement 11.2)."""
    STOCKHOLM = "stockholm"
    COPENHAGEN = "copenhagen"
    OSLO = "oslo"


class LocationType(Enum):
    """Interview location type."""
    TEAMS = "teams"
    ONSITE = "onsite"


class InterviewType(Enum):
    """Type of interview."""
    HIRING_MANAGER = "hiring_manager"
    CASE = "case"
    TEAM = "team"
    TA_SCREENING = "ta_screening"


class BookingMethod(Enum):
    """How the interview is booked (Requirements 11.3, 11.4)."""
    JOBYLON = "jobylon"
    MANUAL = "manual"


class InvalidCalendarInputError(Exception):
    """Raised when calendar input validation fails."""
    pass


class MissingRequiredFieldError(Exception):
    """Raised when a required field is missing."""
    pass


@dataclass
class OfficeLocation:
    """Office address information (Requirement 11.2).
    
    Attributes:
        city: The city enum value
        address: Full street address
        maps_link: Google Maps link to the office
    """
    city: City
    address: str
    maps_link: str


# GlobalConnect office locations (Requirement 11.2)
OFFICE_LOCATIONS: Dict[City, OfficeLocation] = {
    City.STOCKHOLM: OfficeLocation(
        city=City.STOCKHOLM,
        address="Solnavägen 3H, 113 63 Stockholm",
        maps_link="https://maps.app.goo.gl/TovPnSKBtW5MchH79",
    ),
    City.COPENHAGEN: OfficeLocation(
        city=City.COPENHAGEN,
        address="Havneholmen 6, 2450 København SV",
        maps_link="https://maps.app.goo.gl/UEk4qiah1CCsvSWZ7",
    ),
    City.OSLO: OfficeLocation(
        city=City.OSLO,
        address="Snarøyveien 36, 1364 Fornebu, Norway",
        maps_link="https://maps.app.goo.gl/Vu2iwSCthqhGvycU6",
    ),
}


@dataclass
class PersonInfo:
    """Information about a person (hiring manager, participant).
    
    Attributes:
        name: Full name of the person
        title: Job title
        linkedin: Optional LinkedIn profile URL
    """
    name: str
    title: str
    linkedin: Optional[str] = None


@dataclass
class ManualDateTime:
    """Date and time for manual booking (Requirement 11.4).
    
    Attributes:
        date: Human-readable date (e.g., "Monday, 15 January")
        time: Time in 24h format (e.g., "14:00")
    """
    date: str
    time: str


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


@dataclass
class CalendarInviteInput:
    """Input for creating calendar invitations (Requirement 11.1).
    
    Must-have inputs:
    - position_name: Name of the position
    - hiring_manager: Hiring manager details
    - recruiter_name: Name of the recruiter sending the invite
    - location_type: Teams or on-site
    - interview_type: Type of interview
    - duration: Interview duration in minutes
    - booking_method: Jobylon or manual
    
    Conditional inputs:
    - city: Required if location_type is ONSITE
    - manual_date_time: Required if booking_method is MANUAL
    
    Optional inputs:
    - job_ad_link: Link to the job ad
    - additional_participants: Other people joining the interview
    - agenda: Custom agenda for the interview
    
    Attributes:
        position_name: Name of the position being interviewed for
        hiring_manager: Hiring manager information
        recruiter_name: Name of the recruiter
        location_type: Whether interview is on Teams or on-site
        interview_type: Type of interview (HM, case, team, TA)
        duration: Duration in minutes (typically 60 or 90)
        booking_method: Jobylon or manual booking
        city: Office city (required for on-site)
        manual_date_time: Date and time (required for manual booking)
        job_ad_link: Optional link to job advertisement
        additional_participants: Other interview participants
        agenda: Optional custom agenda
    """
    position_name: str
    hiring_manager: PersonInfo
    recruiter_name: str
    location_type: LocationType
    interview_type: InterviewType
    duration: int
    booking_method: BookingMethod
    city: Optional[City] = None
    manual_date_time: Optional[ManualDateTime] = None
    job_ad_link: Optional[str] = None
    additional_participants: List[PersonInfo] = field(default_factory=list)
    agenda: Optional[str] = None


# Default candidate placeholder (Requirement 11.5)
DEFAULT_CANDIDATE_PLACEHOLDER = "[Candidate Name]"


@dataclass
class CalendarInvite:
    """Generated invitation text (Requirement 11.6).
    
    Contains the subject line and body text for the calendar invitation.
    The candidate placeholder appears in both subject and greeting per Requirement 11.5.
    
    Attributes:
        subject: Email/calendar subject line with candidate placeholder
        body: Full invitation body text
        candidate_placeholder: The placeholder used for candidate name
        created_at: When the invitation was created
    """
    subject: str
    body: str
    candidate_placeholder: str = DEFAULT_CANDIDATE_PLACEHOLDER
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Return the artifact type for memory storage."""
        return ArtifactType.CALENDAR_INVITE
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "subject": self.subject,
            "body": self.body,
            "candidate_placeholder": self.candidate_placeholder,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data, indent=2)
    
    def has_candidate_in_subject(self) -> bool:
        """Check if candidate placeholder is in subject (Requirement 11.5)."""
        return self.candidate_placeholder in self.subject
    
    def has_candidate_in_greeting(self) -> bool:
        """Check if candidate placeholder is in greeting (Requirement 11.5)."""
        # Check first few lines for greeting with candidate name
        lines = self.body.split('\n')[:5]
        return any(self.candidate_placeholder in line for line in lines)


def get_office_location(city: City) -> OfficeLocation:
    """Get office location for a city (Requirement 11.2).
    
    Args:
        city: The city to get location for
        
    Returns:
        OfficeLocation with address and map link
        
    Raises:
        KeyError: If city is not in OFFICE_LOCATIONS
    """
    return OFFICE_LOCATIONS[city]


def get_interview_type_display(interview_type: InterviewType) -> str:
    """Get human-readable display name for interview type.
    
    Args:
        interview_type: The interview type enum
        
    Returns:
        Human-readable string
    """
    display_names = {
        InterviewType.HIRING_MANAGER: "Hiring Manager Interview",
        InterviewType.CASE: "Case Interview",
        InterviewType.TEAM: "Team Interview",
        InterviewType.TA_SCREENING: "Screening Interview",
    }
    return display_names.get(interview_type, "Interview")


def format_duration(minutes: int) -> str:
    """Format duration in minutes to human-readable string.
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        Formatted string (e.g., "1 hour", "1.5 hours", "90 minutes")
    """
    if minutes == 60:
        return "1 hour"
    elif minutes == 90:
        return "1.5 hours"
    elif minutes == 30:
        return "30 minutes"
    elif minutes == 45:
        return "45 minutes"
    elif minutes == 120:
        return "2 hours"
    elif minutes % 60 == 0:
        hours = minutes // 60
        return f"{hours} hours" if hours > 1 else "1 hour"
    else:
        return f"{minutes} minutes"


def format_participants(participants: List[PersonInfo]) -> str:
    """Format list of participants for display.
    
    Args:
        participants: List of PersonInfo objects
        
    Returns:
        Formatted string with names and titles
    """
    if not participants:
        return ""
    
    formatted = []
    for p in participants:
        formatted.append(f"{p.name}, {p.title}")
    
    return "\n".join(f"  - {p}" for p in formatted)


class CalendarInviteProcessor:
    """Processor for creating calendar invitation text.
    
    Implements the ModuleProcessor pattern for Module J.
    Creates professional interview invitation text with proper
    formatting, office locations, and booking instructions.
    
    Requirements covered:
    - 11.1: Collect must-have inputs
    - 11.2: Include correct office address and map link
    - 11.3: Include Jobylon booking instruction
    - 11.4: Include date/time for manual booking
    - 11.5: Candidate name in subject and greeting
    - 11.6: Clean, word-ready text
    """
    
    def validate(self, input_data: CalendarInviteInput) -> ValidationResult:
        """Validate input data before processing.
        
        Args:
            input_data: The input to validate
            
        Returns:
            ValidationResult with any errors or warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # Check required fields (Requirement 11.1)
        if not input_data.position_name or not input_data.position_name.strip():
            errors.append(ValidationError(
                field="position_name",
                message="Position name is required"
            ))
        
        if not input_data.hiring_manager:
            errors.append(ValidationError(
                field="hiring_manager",
                message="Hiring manager information is required"
            ))
        elif not input_data.hiring_manager.name or not input_data.hiring_manager.name.strip():
            errors.append(ValidationError(
                field="hiring_manager.name",
                message="Hiring manager name is required"
            ))
        
        if not input_data.recruiter_name or not input_data.recruiter_name.strip():
            errors.append(ValidationError(
                field="recruiter_name",
                message="Recruiter name is required"
            ))
        
        # Check duration
        if input_data.duration <= 0:
            errors.append(ValidationError(
                field="duration",
                message="Duration must be positive"
            ))
        elif input_data.duration < 15:
            warnings.append(ValidationWarning(
                field="duration",
                message="Duration seems very short for an interview"
            ))
        elif input_data.duration > 180:
            warnings.append(ValidationWarning(
                field="duration",
                message="Duration seems very long for an interview"
            ))
        
        # Check conditional requirements
        # City required for on-site (Requirement 11.2)
        if input_data.location_type == LocationType.ONSITE:
            if input_data.city is None:
                errors.append(ValidationError(
                    field="city",
                    message="City is required for on-site interviews"
                ))
        
        # Date/time required for manual booking (Requirement 11.4)
        if input_data.booking_method == BookingMethod.MANUAL:
            if input_data.manual_date_time is None:
                errors.append(ValidationError(
                    field="manual_date_time",
                    message="Date and time are required for manual booking"
                ))
            elif not input_data.manual_date_time.date or not input_data.manual_date_time.time:
                errors.append(ValidationError(
                    field="manual_date_time",
                    message="Both date and time must be provided for manual booking"
                ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def process(self, input_data: CalendarInviteInput) -> CalendarInvite:
        """Process input and generate calendar invitation text.
        
        Args:
            input_data: The calendar invite input
            
        Returns:
            CalendarInvite with subject and body text
            
        Raises:
            InvalidCalendarInputError: If input validation fails
            MissingRequiredFieldError: If required field is missing
        """
        # Validate input
        validation = self.validate(input_data)
        if not validation.is_valid:
            error_msgs = "; ".join(e.message for e in validation.errors)
            if any("required" in e.message.lower() for e in validation.errors):
                raise MissingRequiredFieldError(error_msgs)
            raise InvalidCalendarInputError(f"Input validation failed: {error_msgs}")
        
        # Generate subject line (Requirement 11.5)
        subject = self._generate_subject(input_data)
        
        # Generate body text (Requirements 11.2-11.6)
        body = self._generate_body(input_data)
        
        return CalendarInvite(
            subject=subject,
            body=body,
            candidate_placeholder=DEFAULT_CANDIDATE_PLACEHOLDER,
        )
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input fields (Requirement 11.1)."""
        return [
            "position_name",
            "hiring_manager",
            "recruiter_name",
            "location_type",
            "interview_type",
            "duration",
            "booking_method",
        ]
    
    def get_optional_inputs(self) -> List[str]:
        """Get list of optional input fields."""
        return [
            "city",
            "manual_date_time",
            "job_ad_link",
            "additional_participants",
            "agenda",
        ]
    
    def _generate_subject(self, input_data: CalendarInviteInput) -> str:
        """Generate subject line with candidate placeholder (Requirement 11.5).
        
        Args:
            input_data: The calendar invite input
            
        Returns:
            Subject line string
        """
        interview_type_display = get_interview_type_display(input_data.interview_type)
        return (
            f"{interview_type_display} - {input_data.position_name} - "
            f"{DEFAULT_CANDIDATE_PLACEHOLDER}"
        )
    
    def _generate_body(self, input_data: CalendarInviteInput) -> str:
        """Generate invitation body text (Requirements 11.2-11.6).
        
        Args:
            input_data: The calendar invite input
            
        Returns:
            Body text string
        """
        lines: List[str] = []
        
        # Greeting with candidate placeholder (Requirement 11.5)
        lines.append(f"Dear {DEFAULT_CANDIDATE_PLACEHOLDER},")
        lines.append("")
        
        # Introduction
        interview_type_display = get_interview_type_display(input_data.interview_type)
        duration_display = format_duration(input_data.duration)
        
        lines.append(
            f"Thank you for your interest in the {input_data.position_name} position "
            f"at GlobalConnect. We would like to invite you to a {interview_type_display.lower()} "
            f"({duration_display})."
        )
        lines.append("")
        
        # Date/time for manual booking (Requirement 11.4)
        if input_data.booking_method == BookingMethod.MANUAL and input_data.manual_date_time:
            lines.append("Interview Details:")
            lines.append(f"  Date: {input_data.manual_date_time.date}")
            lines.append(f"  Time: {input_data.manual_date_time.time}")
            lines.append("")
        
        # Booking instruction for Jobylon (Requirement 11.3)
        if input_data.booking_method == BookingMethod.JOBYLON:
            lines.append(
                "Please book a time that suits you through our booking system in Jobylon. "
                "You will find the booking link in your application portal."
            )
            lines.append("")
        
        # Location details
        if input_data.location_type == LocationType.TEAMS:
            lines.append("Location: Microsoft Teams (link will be sent with calendar invite)")
        elif input_data.location_type == LocationType.ONSITE and input_data.city:
            # Include office address and map link (Requirement 11.2)
            office = get_office_location(input_data.city)
            lines.append("Location: On-site at our office")
            lines.append(f"  Address: {office.address}")
            lines.append(f"  Map: {office.maps_link}")
        lines.append("")
        
        # Participants
        lines.append("You will be meeting with:")
        lines.append(f"  - {input_data.hiring_manager.name}, {input_data.hiring_manager.title}")
        
        if input_data.additional_participants:
            for participant in input_data.additional_participants:
                lines.append(f"  - {participant.name}, {participant.title}")
        lines.append("")
        
        # Agenda if provided
        if input_data.agenda:
            lines.append("Agenda:")
            lines.append(input_data.agenda)
            lines.append("")
        
        # Job ad link if provided
        if input_data.job_ad_link:
            lines.append(f"Job posting: {input_data.job_ad_link}")
            lines.append("")
        
        # Closing
        lines.append(
            "If you have any questions or need to reschedule, please don't hesitate to reach out."
        )
        lines.append("")
        lines.append("Best regards,")
        lines.append(input_data.recruiter_name)
        lines.append("GlobalConnect Talent Acquisition")
        
        return "\n".join(lines)
