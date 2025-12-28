"""Suggestion service for Tata chat interface.

This module provides context-aware suggestions based on session state.
It uses DependencyManager to determine which modules can be executed
and maps them to user-friendly suggestion text.

Requirements covered:
- 7.2: Context-aware suggestions based on completed artifacts
- 7.5: Query backend for available next actions based on session state
"""

from typing import Dict, List

from src.tata.dependency.dependency import DependencyManager
from src.tata.memory.memory import MemoryManager
from src.tata.session.session import ModuleType


# Maps ModuleType to user-friendly suggestion text
# Based on design document SuggestionChips.SUGGESTION_TEMPLATES
MODULE_SUGGESTION_TEXT: Dict[ModuleType, str] = {
    # Standalone modules (always available)
    ModuleType.REQUIREMENT_PROFILE: "Create a requirement profile",
    ModuleType.FUNNEL_REPORT: "Create a funnel report",
    ModuleType.JOB_AD_REVIEW: "Review a job ad",
    ModuleType.DI_REVIEW: "Check text for inclusive language",
    ModuleType.CALENDAR_INVITE: "Create a calendar invite",
    # Dependent modules (require prerequisite artifacts)
    ModuleType.JOB_AD: "Generate a job ad",
    ModuleType.TA_SCREENING: "Create TA screening questions",
    ModuleType.HM_SCREENING: "Create HM screening questions",
    ModuleType.HEADHUNTING: "Write a headhunting message",
    ModuleType.CANDIDATE_REPORT: "Generate candidate report",
}


class SuggestionService:
    """Determines available next actions based on session state.
    
    Uses DependencyManager to check which modules can be executed
    based on existing artifacts in the session.
    
    Attributes:
        _deps: DependencyManager for checking module prerequisites
        _memory: MemoryManager for artifact storage (unused directly but
                 passed to DependencyManager)
    """
    
    def __init__(
        self,
        dependency_manager: DependencyManager,
        memory_manager: MemoryManager,
    ) -> None:
        """Initialize the suggestion service.
        
        Args:
            dependency_manager: DependencyManager for checking prerequisites
            memory_manager: MemoryManager for artifact storage
        """
        self._deps = dependency_manager
        self._memory = memory_manager
    
    def get_suggestions(self, session_id: str) -> List[str]:
        """Get available next action suggestions for a session.
        
        Returns suggestions based on:
        - Standalone modules are always available
        - Dependent modules only if prerequisites exist
        
        Args:
            session_id: The session to check
            
        Returns:
            List of suggestion strings for available actions
        """
        if not session_id:
            return []
        
        suggestions: List[str] = []
        
        for module in ModuleType:
            check = self._deps.can_execute(session_id, module)
            if check.can_proceed:
                suggestion_text = self._get_suggestion_for_module(module)
                if suggestion_text:
                    suggestions.append(suggestion_text)
        
        return suggestions
    
    def _get_suggestion_for_module(self, module: ModuleType) -> str:
        """Map module type to user-friendly suggestion text.
        
        Args:
            module: The module type to get suggestion for
            
        Returns:
            User-friendly suggestion text for the module
        """
        return MODULE_SUGGESTION_TEXT.get(module, "")
