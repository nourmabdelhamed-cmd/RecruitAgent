"""Tool Executor for OpenAI function calling integration.

This module provides the ToolExecutor class that routes OpenAI tool calls
to appropriate Tata module processors, handles dependency checking,
and manages artifact storage.

Requirements covered:
- 3.1: Parse function name and arguments from tool calls
- 3.2: Validate that requested tool exists in Tool_Registry
- 3.3: Check module dependencies via DependencyManager before execution
- 3.4: Return error message describing missing prerequisites
- 3.5: Instantiate appropriate processor and execute with parsed arguments
- 3.6: Store resulting artifact in MemoryManager
- 3.7: Return artifact's JSON representation for inclusion in conversation
- 3.8: Return structured error message on failure
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol
import json

from src.tata.agent.models import ToolCall
from src.tata.agent.registry import ToolRegistry
from src.tata.dependency.dependency import DependencyManager, MODULE_TO_ARTIFACT
from src.tata.memory.memory import MemoryManager, ArtifactType, Artifact
from src.tata.session.session import ModuleType


@dataclass
class ToolExecutionResult:
    """Result of executing a tool.
    
    Attributes:
        success: Whether execution succeeded
        result: JSON string result on success
        error: Error message on failure
    """
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class ToolExecutor:
    """Executes tool calls using Tata processors.
    
    Routes OpenAI tool calls to appropriate module processors,
    handles dependency checking, and manages artifact storage.
    
    Attributes:
        _registry: Tool registry for looking up tool definitions
        _deps: Dependency manager for checking prerequisites
        _memory: Memory manager for storing artifacts
        _session_id: Current session identifier
    """
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        dependency_manager: DependencyManager,
        memory_manager: MemoryManager,
        session_id: str
    ) -> None:
        """Initialize the tool executor.
        
        Args:
            tool_registry: Registry for looking up tool definitions
            dependency_manager: Manager for checking module dependencies
            memory_manager: Manager for storing artifacts
            session_id: Current session identifier
        """
        self._registry = tool_registry
        self._deps = dependency_manager
        self._memory = memory_manager
        self._session_id = session_id
    
    def execute(self, tool_call: ToolCall) -> ToolExecutionResult:
        """Execute a tool call.
        
        Routes the tool call to the appropriate processor, checking
        dependencies and storing artifacts as needed.
        
        Args:
            tool_call: The tool call from OpenAI
            
        Returns:
            ToolExecutionResult with success/failure and result/error
        """
        # 1. Validate tool exists (Requirement 3.2)
        tool = self._registry.get_tool(tool_call.name)
        if not tool:
            return ToolExecutionResult(
                success=False,
                error=f"Unknown tool: {tool_call.name}"
            )
        
        # 2. Check dependencies (Requirement 3.3)
        dep_check = self._deps.can_execute(self._session_id, tool.module_type)
        if not dep_check.can_proceed:
            # Return error with missing prerequisites (Requirement 3.4)
            return ToolExecutionResult(
                success=False,
                error=dep_check.message
            )
        
        # 3. Parse arguments (Requirement 3.1)
        try:
            args = tool_call.parse_arguments()
        except json.JSONDecodeError as e:
            return ToolExecutionResult(
                success=False,
                error=f"Invalid arguments JSON: {e}"
            )
        
        # 4. Execute processor (Requirement 3.5)
        try:
            result = self._execute_processor(tool.module_type, args)
            
            # 5. Store artifact if applicable (Requirement 3.6)
            if isinstance(result, Artifact) or hasattr(result, 'artifact_type'):
                self._memory.store(self._session_id, result)
            
            # 6. Return JSON result (Requirement 3.7)
            if hasattr(result, 'to_json'):
                return ToolExecutionResult(
                    success=True,
                    result=result.to_json()
                )
            else:
                return ToolExecutionResult(
                    success=True,
                    result=json.dumps({"result": str(result)})
                )
                
        except Exception as e:
            # Return structured error (Requirement 3.8)
            return ToolExecutionResult(
                success=False,
                error=f"Tool '{tool_call.name}' execution failed: {str(e)}"
            )
    
    def _execute_processor(
        self,
        module_type: ModuleType,
        args: Dict[str, Any]
    ) -> Any:
        """Execute the appropriate processor for a module type.
        
        Args:
            module_type: The module type to execute
            args: Arguments for the processor
            
        Returns:
            The processor result (typically an artifact)
            
        Raises:
            ValueError: If module type is not supported
            Exception: If processor execution fails
        """
        # Import processors lazily to avoid circular imports
        if module_type == ModuleType.REQUIREMENT_PROFILE:
            return self._execute_requirement_profile(args)
        elif module_type == ModuleType.JOB_AD:
            return self._execute_job_ad(args)
        elif module_type == ModuleType.TA_SCREENING:
            return self._execute_ta_screening(args)
        elif module_type == ModuleType.HM_SCREENING:
            return self._execute_hm_screening(args)
        elif module_type == ModuleType.HEADHUNTING:
            return self._execute_headhunting(args)
        elif module_type == ModuleType.CANDIDATE_REPORT:
            return self._execute_candidate_report(args)
        elif module_type == ModuleType.FUNNEL_REPORT:
            return self._execute_funnel_report(args)
        elif module_type == ModuleType.JOB_AD_REVIEW:
            return self._execute_job_ad_review(args)
        elif module_type == ModuleType.DI_REVIEW:
            return self._execute_di_review(args)
        elif module_type == ModuleType.CALENDAR_INVITE:
            return self._execute_calendar_invite(args)
        else:
            raise ValueError(f"Unsupported module type: {module_type}")
    
    def _execute_requirement_profile(self, args: Dict[str, Any]) -> Any:
        """Execute requirement profile processor.
        
        Args:
            args: Arguments including startup_notes, position_title, etc.
            
        Returns:
            RequirementProfile artifact
        """
        from src.tata.modules.profile.profile import (
            RequirementProfileProcessor,
            RequirementProfileInput,
        )
        
        processor = RequirementProfileProcessor()
        input_data = RequirementProfileInput(
            startup_notes=args.get("startup_notes", ""),
            old_job_ad=args.get("old_job_ad"),
            hiring_manager_input=args.get("hiring_manager_input"),
        )
        position_title = args.get("position_title", "")
        
        return processor.process(input_data, position_title)
    
    def _execute_job_ad(self, args: Dict[str, Any]) -> Any:
        """Execute job ad processor.
        
        Args:
            args: Arguments including optional startup_notes, old_job_ad, etc.
            
        Returns:
            JobAd artifact
        """
        from src.tata.modules.jobad.jobad import (
            JobAdProcessor,
            JobAdInput,
        )
        
        # Get requirement profile from memory
        profile = self._memory.retrieve(
            self._session_id,
            ArtifactType.REQUIREMENT_PROFILE
        )
        if not profile:
            raise ValueError("Requirement profile not found in session")
        
        processor = JobAdProcessor(
            memory_manager=self._memory,
            dependency_manager=self._deps,
        )
        input_data = JobAdInput(
            requirement_profile=profile,
            startup_notes=args.get("startup_notes", ""),
            old_job_ad=args.get("old_job_ad"),
            company_context=args.get("company_context"),
        )
        
        return processor.process(input_data)
    
    def _execute_ta_screening(self, args: Dict[str, Any]) -> Any:
        """Execute TA screening template processor.
        
        Args:
            args: Arguments including optional include_good_to_haves, etc.
            
        Returns:
            ScreeningTemplate artifact
        """
        from src.tata.modules.screening.screening import (
            ScreeningTemplateProcessor,
            ScreeningTemplateInput,
        )
        
        # Get requirement profile from memory
        profile = self._memory.retrieve(
            self._session_id,
            ArtifactType.REQUIREMENT_PROFILE
        )
        if not profile:
            raise ValueError("Requirement profile not found in session")
        
        processor = ScreeningTemplateProcessor()
        input_data = ScreeningTemplateInput(
            requirement_profile=profile,
            is_hm_template=False,
            include_good_to_haves=args.get("include_good_to_haves", False),
            include_role_intro=args.get("include_role_intro", False),
            additional_areas=args.get("additional_areas", []),
        )
        
        return processor.process(input_data)
    
    def _execute_hm_screening(self, args: Dict[str, Any]) -> Any:
        """Execute HM screening template processor.
        
        Args:
            args: Arguments including optional include_good_to_haves, etc.
            
        Returns:
            ScreeningTemplate artifact
        """
        from src.tata.modules.screening.screening import (
            ScreeningTemplateProcessor,
            ScreeningTemplateInput,
        )
        
        # Get requirement profile from memory
        profile = self._memory.retrieve(
            self._session_id,
            ArtifactType.REQUIREMENT_PROFILE
        )
        if not profile:
            raise ValueError("Requirement profile not found in session")
        
        processor = ScreeningTemplateProcessor()
        input_data = ScreeningTemplateInput(
            requirement_profile=profile,
            is_hm_template=True,
            include_good_to_haves=args.get("include_good_to_haves", False),
            include_role_intro=args.get("include_role_intro", False),
            additional_areas=args.get("additional_areas", []),
        )
        
        return processor.process(input_data)
    
    def _execute_headhunting(self, args: Dict[str, Any]) -> Any:
        """Execute headhunting messages processor.
        
        Args:
            args: Arguments including optional candidate_profile, company_context
            
        Returns:
            HeadhuntingMessages artifact
        """
        from src.tata.modules.headhunting.headhunting import (
            HeadhuntingProcessor,
            HeadhuntingInput,
        )
        
        # Get requirement profile from memory
        profile = self._memory.retrieve(
            self._session_id,
            ArtifactType.REQUIREMENT_PROFILE
        )
        if not profile:
            raise ValueError("Requirement profile not found in session")
        
        # Optionally get job ad from memory
        job_ad = self._memory.retrieve(
            self._session_id,
            ArtifactType.JOB_AD
        )
        
        processor = HeadhuntingProcessor()
        input_data = HeadhuntingInput(
            requirement_profile=profile,
            job_ad=job_ad,
            candidate_profile=args.get("candidate_profile"),
            company_context=args.get("company_context"),
        )
        
        return processor.process(input_data)
    
    def _execute_candidate_report(self, args: Dict[str, Any]) -> Any:
        """Execute candidate report processor.
        
        Args:
            args: Arguments including transcript, candidate_name, interview_date
            
        Returns:
            CandidateReport artifact
        """
        from src.tata.modules.report.candidate import (
            CandidateReportProcessor,
            CandidateReportInput,
        )
        
        # Get requirement profile from memory
        profile = self._memory.retrieve(
            self._session_id,
            ArtifactType.REQUIREMENT_PROFILE
        )
        if not profile:
            raise ValueError("Requirement profile not found in session")
        
        # Get TA screening template from memory
        screening = self._memory.retrieve(
            self._session_id,
            ArtifactType.TA_SCREENING_TEMPLATE
        )
        if not screening:
            raise ValueError("TA screening template not found in session")
        
        processor = CandidateReportProcessor()
        input_data = CandidateReportInput(
            requirement_profile=profile,
            screening_template=screening,
            transcript=args.get("transcript", ""),
            candidate_name=args.get("candidate_name", ""),
            interview_date=args.get("interview_date", ""),
            candidate_cv=args.get("candidate_cv"),
        )
        
        return processor.process(input_data)
    
    def _execute_funnel_report(self, args: Dict[str, Any]) -> Any:
        """Execute funnel report processor.
        
        Args:
            args: Arguments including job_title, number_of_positions, etc.
            
        Returns:
            FunnelReport artifact
        """
        from src.tata.modules.report.funnel import (
            FunnelReportProcessor,
            FunnelReportInput,
            AttractionMetrics,
            ProcessMetrics,
            TimeMetrics,
        )
        
        # Build attraction metrics if provided
        attraction_data = None
        if any(key in args for key in [
            "job_ad_views", "apply_clicks", "applications_received",
            "qualified_applications", "candidates_sourced",
            "candidates_contacted", "candidates_replied"
        ]):
            attraction_data = AttractionMetrics(
                job_ad_views=args.get("job_ad_views", 0),
                apply_clicks=args.get("apply_clicks", 0),
                applications_received=args.get("applications_received", 0),
                qualified_applications=args.get("qualified_applications", 0),
                candidates_sourced=args.get("candidates_sourced", 0),
                candidates_contacted=args.get("candidates_contacted", 0),
                candidates_replied=args.get("candidates_replied", 0),
            )
        
        # Build process metrics if provided
        process_data = None
        if any(key in args for key in [
            "ta_screenings", "hm_interviews", "offers_made", "offers_accepted"
        ]):
            process_data = ProcessMetrics(
                ta_screenings=args.get("ta_screenings", 0),
                hm_interviews=args.get("hm_interviews", 0),
                offers_made=args.get("offers_made", 0),
                offers_accepted=args.get("offers_accepted", 0),
            )
        
        processor = FunnelReportProcessor()
        input_data = FunnelReportInput(
            job_title=args.get("job_title", ""),
            number_of_positions=args.get("number_of_positions", 1),
            hiring_manager_name=args.get("hiring_manager_name", ""),
            locations=args.get("locations", []),
            attraction_data=attraction_data,
            process_data=process_data,
        )
        
        return processor.process(input_data)
    
    def _execute_job_ad_review(self, args: Dict[str, Any]) -> Any:
        """Execute job ad review processor.
        
        Args:
            args: Arguments including job_ad_text, language, position_title
            
        Returns:
            JobAdReview artifact
        """
        from src.tata.modules.review.jobad import (
            JobAdReviewProcessor,
            JobAdReviewInput,
        )
        from src.tata.session.session import SupportedLanguage
        
        # Map language string to enum
        language_str = args.get("language", "en")
        language_map = {
            "en": SupportedLanguage.ENGLISH,
            "sv": SupportedLanguage.SWEDISH,
            "da": SupportedLanguage.DANISH,
            "no": SupportedLanguage.NORWEGIAN,
            "de": SupportedLanguage.GERMAN,
        }
        language = language_map.get(language_str, SupportedLanguage.ENGLISH)
        
        processor = JobAdReviewProcessor()
        input_data = JobAdReviewInput(
            job_ad_text=args.get("job_ad_text", ""),
            language=language,
            position_title=args.get("position_title"),
        )
        
        return processor.process(input_data)
    
    def _execute_di_review(self, args: Dict[str, Any]) -> Any:
        """Execute D&I review processor.
        
        Args:
            args: Arguments including job_ad_text, language
            
        Returns:
            DIReview artifact
        """
        from src.tata.modules.review.di import (
            DIReviewProcessor,
            DIReviewInput,
        )
        from src.tata.session.session import SupportedLanguage
        
        # Map language string to enum
        language_str = args.get("language", "en")
        language_map = {
            "en": SupportedLanguage.ENGLISH,
            "sv": SupportedLanguage.SWEDISH,
            "da": SupportedLanguage.DANISH,
            "no": SupportedLanguage.NORWEGIAN,
            "de": SupportedLanguage.GERMAN,
        }
        language = language_map.get(language_str, SupportedLanguage.ENGLISH)
        
        processor = DIReviewProcessor()
        input_data = DIReviewInput(
            job_ad_text=args.get("job_ad_text", ""),
            language=language,
        )
        
        return processor.process(input_data)
    
    def _execute_calendar_invite(self, args: Dict[str, Any]) -> Any:
        """Execute calendar invite processor.
        
        Args:
            args: Arguments including position_name, hiring_manager details, etc.
            
        Returns:
            CalendarInvite artifact
        """
        from src.tata.modules.calendar.invite import (
            CalendarInviteProcessor,
            CalendarInviteInput,
            PersonInfo,
            LocationType,
            InterviewType,
            BookingMethod,
            City,
            ManualDateTime,
        )
        
        # Map location type
        location_type_str = args.get("location_type", "teams")
        location_type = LocationType.TEAMS if location_type_str == "teams" else LocationType.ONSITE
        
        # Map interview type
        interview_type_map = {
            "hiring_manager": InterviewType.HIRING_MANAGER,
            "case": InterviewType.CASE,
            "team": InterviewType.TEAM,
            "ta_screening": InterviewType.TA_SCREENING,
        }
        interview_type = interview_type_map.get(
            args.get("interview_type", "hiring_manager"),
            InterviewType.HIRING_MANAGER
        )
        
        # Map booking method
        booking_method_str = args.get("booking_method", "jobylon")
        booking_method = BookingMethod.JOBYLON if booking_method_str == "jobylon" else BookingMethod.MANUAL
        
        # Map city if provided
        city = None
        city_str = args.get("city")
        if city_str:
            city_map = {
                "stockholm": City.STOCKHOLM,
                "copenhagen": City.COPENHAGEN,
                "oslo": City.OSLO,
            }
            city = city_map.get(city_str.lower())
        
        # Build manual date/time if provided
        manual_date_time = None
        if args.get("interview_date") and args.get("interview_time"):
            manual_date_time = ManualDateTime(
                date=args.get("interview_date"),
                time=args.get("interview_time"),
            )
        
        # Build hiring manager info
        hiring_manager = PersonInfo(
            name=args.get("hiring_manager_name", ""),
            title=args.get("hiring_manager_title", ""),
        )
        
        processor = CalendarInviteProcessor()
        input_data = CalendarInviteInput(
            position_name=args.get("position_name", ""),
            hiring_manager=hiring_manager,
            recruiter_name=args.get("recruiter_name", ""),
            location_type=location_type,
            interview_type=interview_type,
            duration=args.get("duration", 60),
            booking_method=booking_method,
            city=city,
            manual_date_time=manual_date_time,
            job_ad_link=args.get("job_ad_link"),
        )
        
        return processor.process(input_data)
