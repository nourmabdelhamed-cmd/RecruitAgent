"""Dependency management for Tata recruitment assistant.

This module enforces module dependencies and determines required prerequisites.
It ensures that modules with dependencies (like Job Ad requiring Requirement Profile)
are only executed when their prerequisites are satisfied.

Requirements covered:
- 3.1: Reuse existing requirement profile in standard flow
- 3.2: Build/confirm requirement profile when jumping to dependent modules
- 3.3: Funnel Report runs directly without requiring requirement profile
- 3.4: Job Ad Review and DI Review run directly on pasted text
"""

from dataclasses import dataclass, field
from typing import List, Protocol, Dict, Optional
from abc import abstractmethod

from src.tata.session.session import ModuleType
from src.tata.memory.memory import ArtifactType, MemoryManager


# Module dependencies map
# Maps each module to the list of modules that must be completed first
MODULE_DEPENDENCIES: Dict[ModuleType, List[ModuleType]] = {
    ModuleType.REQUIREMENT_PROFILE: [],                                    # A - no dependencies
    ModuleType.JOB_AD: [ModuleType.REQUIREMENT_PROFILE],                   # B requires A
    ModuleType.TA_SCREENING: [ModuleType.REQUIREMENT_PROFILE],             # C requires A
    ModuleType.HM_SCREENING: [ModuleType.REQUIREMENT_PROFILE],             # D requires A
    ModuleType.HEADHUNTING: [ModuleType.REQUIREMENT_PROFILE],              # E requires A
    ModuleType.CANDIDATE_REPORT: [                                         # F requires A, C
        ModuleType.REQUIREMENT_PROFILE, 
        ModuleType.TA_SCREENING
    ],
    ModuleType.FUNNEL_REPORT: [],                                          # G - standalone
    ModuleType.JOB_AD_REVIEW: [],                                          # H - standalone
    ModuleType.DI_REVIEW: [],                                              # I - standalone
    ModuleType.CALENDAR_INVITE: [],                                        # J - standalone
}


# Maps ModuleType to the ArtifactType it produces
MODULE_TO_ARTIFACT: Dict[ModuleType, ArtifactType] = {
    ModuleType.REQUIREMENT_PROFILE: ArtifactType.REQUIREMENT_PROFILE,
    ModuleType.JOB_AD: ArtifactType.JOB_AD,
    ModuleType.TA_SCREENING: ArtifactType.TA_SCREENING_TEMPLATE,
    ModuleType.HM_SCREENING: ArtifactType.HM_SCREENING_TEMPLATE,
    ModuleType.HEADHUNTING: ArtifactType.HEADHUNTING_MESSAGES,
    ModuleType.CANDIDATE_REPORT: ArtifactType.CANDIDATE_REPORTS,
    ModuleType.FUNNEL_REPORT: ArtifactType.FUNNEL_REPORT,
    ModuleType.JOB_AD_REVIEW: ArtifactType.JOB_AD_REVIEW,
    ModuleType.DI_REVIEW: ArtifactType.DI_REVIEW,
    ModuleType.CALENDAR_INVITE: ArtifactType.CALENDAR_INVITE,
}


@dataclass
class DependencyCheck:
    """Result of checking module dependencies.
    
    Attributes:
        can_proceed: True if all dependencies are satisfied
        missing_dependencies: List of modules that need to be completed first
        message: Human-readable message describing the result
    """
    can_proceed: bool
    missing_dependencies: List[ModuleType] = field(default_factory=list)
    message: str = ""


class EmptySessionIDError(Exception):
    """Raised when session ID is empty."""
    pass


class DependencyManager(Protocol):
    """Protocol for enforcing module dependencies.
    
    Implementations check whether a module can be executed based on
    the artifacts already present in the session's memory.
    """
    
    @abstractmethod
    def can_execute(self, session_id: str, module: ModuleType) -> DependencyCheck:
        """Check if a module can be executed.
        
        Args:
            session_id: The session identifier
            module: The module to check
            
        Returns:
            DependencyCheck with result and any missing dependencies
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        ...
    
    @abstractmethod
    def get_required_modules(self, module: ModuleType) -> List[ModuleType]:
        """Get required modules for a given module.
        
        Args:
            module: The module to check dependencies for
            
        Returns:
            List of modules that must be completed first (empty if standalone)
        """
        ...
    
    @abstractmethod
    def is_standalone(self, module: ModuleType) -> bool:
        """Check if a module has no dependencies.
        
        Args:
            module: The module to check
            
        Returns:
            True if the module can run without any prerequisites
        """
        ...


class InMemoryDependencyManager:
    """Implementation of DependencyManager using MemoryManager for artifact checks.
    
    This manager checks the session's memory to determine if required
    artifacts exist before allowing a module to execute.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """Initialize the dependency manager.
        
        Args:
            memory_manager: The memory manager to check for existing artifacts
        """
        self._memory_manager = memory_manager
    
    def can_execute(self, session_id: str, module: ModuleType) -> DependencyCheck:
        """Check if a module can be executed.
        
        Verifies that all required prerequisite modules have produced
        their artifacts in the session's memory.
        
        Args:
            session_id: The session identifier
            module: The module to check
            
        Returns:
            DependencyCheck with:
            - can_proceed=True if all dependencies satisfied
            - missing_dependencies listing any modules that need to run first
            - message describing the result
            
        Raises:
            EmptySessionIDError: If session_id is empty
        """
        if not session_id:
            raise EmptySessionIDError("Session ID cannot be empty")
        
        required_modules = self.get_required_modules(module)
        
        # If no dependencies, can always proceed
        if not required_modules:
            return DependencyCheck(
                can_proceed=True,
                missing_dependencies=[],
                message=f"Module {module.name} has no dependencies and can proceed."
            )
        
        # Check which required modules have their artifacts in memory
        missing: List[ModuleType] = []
        for req_module in required_modules:
            artifact_type = MODULE_TO_ARTIFACT.get(req_module)
            if artifact_type and not self._memory_manager.has_artifact(session_id, artifact_type):
                missing.append(req_module)
        
        if not missing:
            return DependencyCheck(
                can_proceed=True,
                missing_dependencies=[],
                message=f"All dependencies for {module.name} are satisfied."
            )
        
        # Build helpful message about missing dependencies
        missing_names = [m.name.replace("_", " ").title() for m in missing]
        if len(missing_names) == 1:
            message = f"Cannot execute {module.name}: requires {missing_names[0]} to be created first."
        else:
            message = f"Cannot execute {module.name}: requires {', '.join(missing_names[:-1])} and {missing_names[-1]} to be created first."
        
        return DependencyCheck(
            can_proceed=False,
            missing_dependencies=missing,
            message=message
        )
    
    def get_required_modules(self, module: ModuleType) -> List[ModuleType]:
        """Get required modules for a given module.
        
        Args:
            module: The module to check dependencies for
            
        Returns:
            List of modules that must be completed first.
            Returns empty list if module is standalone or not in dependency map.
        """
        return MODULE_DEPENDENCIES.get(module, [])
    
    def is_standalone(self, module: ModuleType) -> bool:
        """Check if a module has no dependencies.
        
        Standalone modules (G, H, I, J) can run without any prerequisites.
        
        Args:
            module: The module to check
            
        Returns:
            True if the module has no dependencies
        """
        return len(self.get_required_modules(module)) == 0
