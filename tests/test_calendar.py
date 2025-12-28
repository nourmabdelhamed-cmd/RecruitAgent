"""Tests for Calendar Invitation module (Module J).

Tests cover:
- 11.1: Must-have inputs collection
- 11.2: Office address and map link correctness
- 11.3: Jobylon booking instruction
- 11.4: Manual booking date/time
- 11.5: Candidate name in subject and greeting
- 11.6: Clean, word-ready text output
"""

import pytest
from datetime import datetime

from src.tata.modules.calendar.invite import (
    CalendarInvite,
    CalendarInviteInput,
    CalendarInviteProcessor,
    PersonInfo,
    ManualDateTime,
    OfficeLocation,
    City,
    LocationType,
    InterviewType,
    BookingMethod,
    OFFICE_LOCATIONS,
    DEFAULT_CANDIDATE_PLACEHOLDER,
    InvalidCalendarInputError,
    MissingRequiredFieldError,
    get_office_location,
    get_interview_type_display,
    format_duration,
    format_participants,
)
from src.tata.memory.memory import ArtifactType


class TestOfficeLocations:
    """Tests for office location lookup (Requirement 11.2)."""
    
    def test_stockholm_office_exists(self):
        """Stockholm office should have correct address."""
        location = get_office_location(City.STOCKHOLM)
        assert location.city == City.STOCKHOLM
        assert "Solnavägen 3H" in location.address
        assert "113 63 Stockholm" in location.address
        assert location.maps_link.startswith("https://")
    
    def test_copenhagen_office_exists(self):
        """Copenhagen office should have correct address."""
        location = get_office_location(City.COPENHAGEN)
        assert location.city == City.COPENHAGEN
        assert "Havneholmen 6" in location.address
        assert "København" in location.address
        assert location.maps_link.startswith("https://")
    
    def test_oslo_office_exists(self):
        """Oslo office should have correct address."""
        location = get_office_location(City.OSLO)
        assert location.city == City.OSLO
        assert "Snarøyveien 36" in location.address
        assert "Fornebu" in location.address
        assert location.maps_link.startswith("https://")
    
    def test_all_offices_have_map_links(self):
        """All offices should have valid Google Maps links."""
        for city in City:
            location = OFFICE_LOCATIONS[city]
            assert location.maps_link.startswith("https://maps.app.goo.gl/")


class TestPersonInfo:
    """Tests for PersonInfo dataclass."""
    
    def test_person_info_creation(self):
        """PersonInfo should store name and title."""
        person = PersonInfo(name="John Doe", title="Engineering Manager")
        assert person.name == "John Doe"
        assert person.title == "Engineering Manager"
        assert person.linkedin is None
    
    def test_person_info_with_linkedin(self):
        """PersonInfo should optionally store LinkedIn URL."""
        person = PersonInfo(
            name="Jane Smith",
            title="Tech Lead",
            linkedin="https://linkedin.com/in/janesmith"
        )
        assert person.linkedin == "https://linkedin.com/in/janesmith"


class TestManualDateTime:
    """Tests for ManualDateTime dataclass."""
    
    def test_manual_datetime_creation(self):
        """ManualDateTime should store date and time strings."""
        dt = ManualDateTime(date="Monday, 15 January", time="14:00")
        assert dt.date == "Monday, 15 January"
        assert dt.time == "14:00"


class TestCalendarInvite:
    """Tests for CalendarInvite dataclass."""
    
    def test_calendar_invite_artifact_type(self):
        """CalendarInvite should have correct artifact type."""
        invite = CalendarInvite(
            subject="Test Subject",
            body="Test Body"
        )
        assert invite.artifact_type == ArtifactType.CALENDAR_INVITE
    
    def test_calendar_invite_to_json(self):
        """CalendarInvite should serialize to JSON."""
        invite = CalendarInvite(
            subject="Interview - [Candidate Name]",
            body="Dear [Candidate Name],\n\nTest body."
        )
        json_str = invite.to_json()
        assert "Interview - [Candidate Name]" in json_str
        assert "Dear [Candidate Name]" in json_str
    
    def test_has_candidate_in_subject(self):
        """Should detect candidate placeholder in subject."""
        invite = CalendarInvite(
            subject=f"Interview - {DEFAULT_CANDIDATE_PLACEHOLDER}",
            body="Test body"
        )
        assert invite.has_candidate_in_subject() is True
    
    def test_has_candidate_in_subject_missing(self):
        """Should detect missing candidate placeholder in subject."""
        invite = CalendarInvite(
            subject="Interview - Position",
            body="Test body"
        )
        assert invite.has_candidate_in_subject() is False
    
    def test_has_candidate_in_greeting(self):
        """Should detect candidate placeholder in greeting."""
        invite = CalendarInvite(
            subject="Test",
            body=f"Dear {DEFAULT_CANDIDATE_PLACEHOLDER},\n\nWelcome."
        )
        assert invite.has_candidate_in_greeting() is True
    
    def test_has_candidate_in_greeting_missing(self):
        """Should detect missing candidate placeholder in greeting."""
        invite = CalendarInvite(
            subject="Test",
            body="Dear Applicant,\n\nWelcome."
        )
        assert invite.has_candidate_in_greeting() is False


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_get_interview_type_display_hiring_manager(self):
        """Should return correct display name for HM interview."""
        assert get_interview_type_display(InterviewType.HIRING_MANAGER) == "Hiring Manager Interview"
    
    def test_get_interview_type_display_case(self):
        """Should return correct display name for case interview."""
        assert get_interview_type_display(InterviewType.CASE) == "Case Interview"
    
    def test_get_interview_type_display_team(self):
        """Should return correct display name for team interview."""
        assert get_interview_type_display(InterviewType.TEAM) == "Team Interview"
    
    def test_get_interview_type_display_ta_screening(self):
        """Should return correct display name for TA screening."""
        assert get_interview_type_display(InterviewType.TA_SCREENING) == "Screening Interview"
    
    def test_format_duration_60_minutes(self):
        """Should format 60 minutes as 1 hour."""
        assert format_duration(60) == "1 hour"
    
    def test_format_duration_90_minutes(self):
        """Should format 90 minutes as 1.5 hours."""
        assert format_duration(90) == "1.5 hours"
    
    def test_format_duration_30_minutes(self):
        """Should format 30 minutes correctly."""
        assert format_duration(30) == "30 minutes"
    
    def test_format_duration_120_minutes(self):
        """Should format 120 minutes as 2 hours."""
        assert format_duration(120) == "2 hours"
    
    def test_format_participants_empty(self):
        """Should return empty string for no participants."""
        assert format_participants([]) == ""
    
    def test_format_participants_single(self):
        """Should format single participant correctly."""
        participants = [PersonInfo(name="John Doe", title="Manager")]
        result = format_participants(participants)
        assert "John Doe" in result
        assert "Manager" in result
    
    def test_format_participants_multiple(self):
        """Should format multiple participants correctly."""
        participants = [
            PersonInfo(name="John Doe", title="Manager"),
            PersonInfo(name="Jane Smith", title="Tech Lead"),
        ]
        result = format_participants(participants)
        assert "John Doe" in result
        assert "Jane Smith" in result


class TestCalendarInviteProcessor:
    """Tests for CalendarInviteProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return CalendarInviteProcessor()
    
    @pytest.fixture
    def valid_teams_input(self):
        """Create valid input for Teams interview."""
        return CalendarInviteInput(
            position_name="Senior Software Engineer",
            hiring_manager=PersonInfo(name="John Manager", title="Engineering Director"),
            recruiter_name="Sarah Recruiter",
            location_type=LocationType.TEAMS,
            interview_type=InterviewType.HIRING_MANAGER,
            duration=60,
            booking_method=BookingMethod.JOBYLON,
        )
    
    @pytest.fixture
    def valid_onsite_input(self):
        """Create valid input for on-site interview."""
        return CalendarInviteInput(
            position_name="Product Manager",
            hiring_manager=PersonInfo(name="Jane Director", title="VP Product"),
            recruiter_name="Tom Recruiter",
            location_type=LocationType.ONSITE,
            interview_type=InterviewType.CASE,
            duration=90,
            booking_method=BookingMethod.MANUAL,
            city=City.STOCKHOLM,
            manual_date_time=ManualDateTime(date="Monday, 20 January", time="10:00"),
        )
    
    def test_validate_valid_teams_input(self, processor, valid_teams_input):
        """Should validate correct Teams input."""
        result = processor.validate(valid_teams_input)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_valid_onsite_input(self, processor, valid_onsite_input):
        """Should validate correct on-site input."""
        result = processor.validate(valid_onsite_input)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_missing_position_name(self, processor, valid_teams_input):
        """Should reject missing position name."""
        valid_teams_input.position_name = ""
        result = processor.validate(valid_teams_input)
        assert result.is_valid is False
        assert any("position_name" in e.field for e in result.errors)
    
    def test_validate_missing_hiring_manager(self, processor, valid_teams_input):
        """Should reject missing hiring manager."""
        valid_teams_input.hiring_manager = None
        result = processor.validate(valid_teams_input)
        assert result.is_valid is False
        assert any("hiring_manager" in e.field for e in result.errors)
    
    def test_validate_missing_hiring_manager_name(self, processor, valid_teams_input):
        """Should reject empty hiring manager name."""
        valid_teams_input.hiring_manager.name = ""
        result = processor.validate(valid_teams_input)
        assert result.is_valid is False
        assert any("hiring_manager.name" in e.field for e in result.errors)
    
    def test_validate_missing_recruiter_name(self, processor, valid_teams_input):
        """Should reject missing recruiter name."""
        valid_teams_input.recruiter_name = ""
        result = processor.validate(valid_teams_input)
        assert result.is_valid is False
        assert any("recruiter_name" in e.field for e in result.errors)
    
    def test_validate_invalid_duration(self, processor, valid_teams_input):
        """Should reject zero or negative duration."""
        valid_teams_input.duration = 0
        result = processor.validate(valid_teams_input)
        assert result.is_valid is False
        assert any("duration" in e.field for e in result.errors)
    
    def test_validate_onsite_missing_city(self, processor, valid_teams_input):
        """Should reject on-site interview without city (Requirement 11.2)."""
        valid_teams_input.location_type = LocationType.ONSITE
        valid_teams_input.city = None
        result = processor.validate(valid_teams_input)
        assert result.is_valid is False
        assert any("city" in e.field for e in result.errors)
    
    def test_validate_manual_missing_datetime(self, processor, valid_teams_input):
        """Should reject manual booking without date/time (Requirement 11.4)."""
        valid_teams_input.booking_method = BookingMethod.MANUAL
        valid_teams_input.manual_date_time = None
        result = processor.validate(valid_teams_input)
        assert result.is_valid is False
        assert any("manual_date_time" in e.field for e in result.errors)
    
    def test_validate_warns_short_duration(self, processor, valid_teams_input):
        """Should warn about very short duration."""
        valid_teams_input.duration = 10
        result = processor.validate(valid_teams_input)
        assert result.is_valid is True
        assert any("duration" in w.field for w in result.warnings)
    
    def test_validate_warns_long_duration(self, processor, valid_teams_input):
        """Should warn about very long duration."""
        valid_teams_input.duration = 240
        result = processor.validate(valid_teams_input)
        assert result.is_valid is True
        assert any("duration" in w.field for w in result.warnings)


class TestCalendarInviteProcessorProcess:
    """Tests for CalendarInviteProcessor.process method."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return CalendarInviteProcessor()
    
    @pytest.fixture
    def valid_teams_jobylon_input(self):
        """Create valid input for Teams interview with Jobylon booking."""
        return CalendarInviteInput(
            position_name="Senior Software Engineer",
            hiring_manager=PersonInfo(name="John Manager", title="Engineering Director"),
            recruiter_name="Sarah Recruiter",
            location_type=LocationType.TEAMS,
            interview_type=InterviewType.HIRING_MANAGER,
            duration=60,
            booking_method=BookingMethod.JOBYLON,
        )
    
    @pytest.fixture
    def valid_onsite_manual_input(self):
        """Create valid input for on-site interview with manual booking."""
        return CalendarInviteInput(
            position_name="Product Manager",
            hiring_manager=PersonInfo(name="Jane Director", title="VP Product"),
            recruiter_name="Tom Recruiter",
            location_type=LocationType.ONSITE,
            interview_type=InterviewType.CASE,
            duration=90,
            booking_method=BookingMethod.MANUAL,
            city=City.STOCKHOLM,
            manual_date_time=ManualDateTime(date="Monday, 20 January", time="10:00"),
        )
    
    def test_process_returns_calendar_invite(self, processor, valid_teams_jobylon_input):
        """Should return CalendarInvite object."""
        result = processor.process(valid_teams_jobylon_input)
        assert isinstance(result, CalendarInvite)
    
    def test_process_candidate_in_subject(self, processor, valid_teams_jobylon_input):
        """Candidate placeholder should be in subject (Requirement 11.5)."""
        result = processor.process(valid_teams_jobylon_input)
        assert result.has_candidate_in_subject() is True
        assert DEFAULT_CANDIDATE_PLACEHOLDER in result.subject
    
    def test_process_candidate_in_greeting(self, processor, valid_teams_jobylon_input):
        """Candidate placeholder should be in greeting (Requirement 11.5)."""
        result = processor.process(valid_teams_jobylon_input)
        assert result.has_candidate_in_greeting() is True
        assert f"Dear {DEFAULT_CANDIDATE_PLACEHOLDER}" in result.body
    
    def test_process_subject_contains_interview_type(self, processor, valid_teams_jobylon_input):
        """Subject should contain interview type."""
        result = processor.process(valid_teams_jobylon_input)
        assert "Hiring Manager Interview" in result.subject
    
    def test_process_subject_contains_position(self, processor, valid_teams_jobylon_input):
        """Subject should contain position name."""
        result = processor.process(valid_teams_jobylon_input)
        assert "Senior Software Engineer" in result.subject
    
    def test_process_body_contains_position(self, processor, valid_teams_jobylon_input):
        """Body should contain position name."""
        result = processor.process(valid_teams_jobylon_input)
        assert "Senior Software Engineer" in result.body
    
    def test_process_body_contains_hiring_manager(self, processor, valid_teams_jobylon_input):
        """Body should contain hiring manager details."""
        result = processor.process(valid_teams_jobylon_input)
        assert "John Manager" in result.body
        assert "Engineering Director" in result.body
    
    def test_process_body_contains_recruiter(self, processor, valid_teams_jobylon_input):
        """Body should contain recruiter name."""
        result = processor.process(valid_teams_jobylon_input)
        assert "Sarah Recruiter" in result.body
    
    def test_process_teams_location(self, processor, valid_teams_jobylon_input):
        """Teams interview should mention Microsoft Teams."""
        result = processor.process(valid_teams_jobylon_input)
        assert "Microsoft Teams" in result.body
    
    def test_process_jobylon_booking_instruction(self, processor, valid_teams_jobylon_input):
        """Jobylon booking should include booking instruction (Requirement 11.3)."""
        result = processor.process(valid_teams_jobylon_input)
        assert "Jobylon" in result.body
        assert "booking" in result.body.lower()
    
    def test_process_onsite_includes_address(self, processor, valid_onsite_manual_input):
        """On-site interview should include office address (Requirement 11.2)."""
        result = processor.process(valid_onsite_manual_input)
        stockholm_office = OFFICE_LOCATIONS[City.STOCKHOLM]
        assert stockholm_office.address in result.body
    
    def test_process_onsite_includes_map_link(self, processor, valid_onsite_manual_input):
        """On-site interview should include map link (Requirement 11.2)."""
        result = processor.process(valid_onsite_manual_input)
        stockholm_office = OFFICE_LOCATIONS[City.STOCKHOLM]
        assert stockholm_office.maps_link in result.body
    
    def test_process_manual_booking_includes_date(self, processor, valid_onsite_manual_input):
        """Manual booking should include date (Requirement 11.4)."""
        result = processor.process(valid_onsite_manual_input)
        assert "Monday, 20 January" in result.body
    
    def test_process_manual_booking_includes_time(self, processor, valid_onsite_manual_input):
        """Manual booking should include time (Requirement 11.4)."""
        result = processor.process(valid_onsite_manual_input)
        assert "10:00" in result.body
    
    def test_process_manual_booking_no_jobylon(self, processor, valid_onsite_manual_input):
        """Manual booking should not mention Jobylon."""
        result = processor.process(valid_onsite_manual_input)
        assert "Jobylon" not in result.body
    
    def test_process_with_additional_participants(self, processor, valid_teams_jobylon_input):
        """Should include additional participants."""
        valid_teams_jobylon_input.additional_participants = [
            PersonInfo(name="Alice Tech", title="Senior Engineer"),
            PersonInfo(name="Bob Design", title="UX Lead"),
        ]
        result = processor.process(valid_teams_jobylon_input)
        assert "Alice Tech" in result.body
        assert "Bob Design" in result.body
    
    def test_process_with_agenda(self, processor, valid_teams_jobylon_input):
        """Should include custom agenda."""
        valid_teams_jobylon_input.agenda = "1. Introduction\n2. Technical discussion\n3. Q&A"
        result = processor.process(valid_teams_jobylon_input)
        assert "Agenda:" in result.body
        assert "Introduction" in result.body
    
    def test_process_with_job_ad_link(self, processor, valid_teams_jobylon_input):
        """Should include job ad link."""
        valid_teams_jobylon_input.job_ad_link = "https://jobs.globalconnect.com/123"
        result = processor.process(valid_teams_jobylon_input)
        assert "https://jobs.globalconnect.com/123" in result.body
    
    def test_process_raises_on_invalid_input(self, processor):
        """Should raise error on invalid input."""
        invalid_input = CalendarInviteInput(
            position_name="",  # Invalid: empty
            hiring_manager=PersonInfo(name="John", title="Manager"),
            recruiter_name="Sarah",
            location_type=LocationType.TEAMS,
            interview_type=InterviewType.HIRING_MANAGER,
            duration=60,
            booking_method=BookingMethod.JOBYLON,
        )
        with pytest.raises(MissingRequiredFieldError):
            processor.process(invalid_input)
    
    def test_process_raises_on_missing_city_for_onsite(self, processor):
        """Should raise error when city missing for on-site."""
        invalid_input = CalendarInviteInput(
            position_name="Engineer",
            hiring_manager=PersonInfo(name="John", title="Manager"),
            recruiter_name="Sarah",
            location_type=LocationType.ONSITE,
            interview_type=InterviewType.HIRING_MANAGER,
            duration=60,
            booking_method=BookingMethod.JOBYLON,
            city=None,  # Invalid: required for on-site
        )
        with pytest.raises(MissingRequiredFieldError):
            processor.process(invalid_input)


class TestCalendarInviteProcessorInputLists:
    """Tests for required/optional input lists."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return CalendarInviteProcessor()
    
    def test_get_required_inputs(self, processor):
        """Should return all required inputs (Requirement 11.1)."""
        required = processor.get_required_inputs()
        assert "position_name" in required
        assert "hiring_manager" in required
        assert "recruiter_name" in required
        assert "location_type" in required
        assert "interview_type" in required
        assert "duration" in required
        assert "booking_method" in required
    
    def test_get_optional_inputs(self, processor):
        """Should return all optional inputs."""
        optional = processor.get_optional_inputs()
        assert "city" in optional
        assert "manual_date_time" in optional
        assert "job_ad_link" in optional
        assert "additional_participants" in optional
        assert "agenda" in optional


class TestAllCityOfficeAddresses:
    """Tests for office address correctness across all cities (Property 28)."""
    
    def test_stockholm_address_in_invite(self):
        """Stockholm address should appear correctly in invite."""
        processor = CalendarInviteProcessor()
        input_data = CalendarInviteInput(
            position_name="Engineer",
            hiring_manager=PersonInfo(name="John", title="Manager"),
            recruiter_name="Sarah",
            location_type=LocationType.ONSITE,
            interview_type=InterviewType.HIRING_MANAGER,
            duration=60,
            booking_method=BookingMethod.MANUAL,
            city=City.STOCKHOLM,
            manual_date_time=ManualDateTime(date="Monday", time="10:00"),
        )
        result = processor.process(input_data)
        office = OFFICE_LOCATIONS[City.STOCKHOLM]
        assert office.address in result.body
        assert office.maps_link in result.body
    
    def test_copenhagen_address_in_invite(self):
        """Copenhagen address should appear correctly in invite."""
        processor = CalendarInviteProcessor()
        input_data = CalendarInviteInput(
            position_name="Engineer",
            hiring_manager=PersonInfo(name="John", title="Manager"),
            recruiter_name="Sarah",
            location_type=LocationType.ONSITE,
            interview_type=InterviewType.HIRING_MANAGER,
            duration=60,
            booking_method=BookingMethod.MANUAL,
            city=City.COPENHAGEN,
            manual_date_time=ManualDateTime(date="Monday", time="10:00"),
        )
        result = processor.process(input_data)
        office = OFFICE_LOCATIONS[City.COPENHAGEN]
        assert office.address in result.body
        assert office.maps_link in result.body
    
    def test_oslo_address_in_invite(self):
        """Oslo address should appear correctly in invite."""
        processor = CalendarInviteProcessor()
        input_data = CalendarInviteInput(
            position_name="Engineer",
            hiring_manager=PersonInfo(name="John", title="Manager"),
            recruiter_name="Sarah",
            location_type=LocationType.ONSITE,
            interview_type=InterviewType.HIRING_MANAGER,
            duration=60,
            booking_method=BookingMethod.MANUAL,
            city=City.OSLO,
            manual_date_time=ManualDateTime(date="Monday", time="10:00"),
        )
        result = processor.process(input_data)
        office = OFFICE_LOCATIONS[City.OSLO]
        assert office.address in result.body
        assert office.maps_link in result.body
