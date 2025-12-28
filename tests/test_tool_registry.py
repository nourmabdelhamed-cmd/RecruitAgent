"""Tests for ToolRegistry.

Tests the ToolRegistry protocol and InMemoryToolRegistry implementation
for managing OpenAI tool definitions.

Requirements covered:
- 1.1: Provide OpenAI-compatible tool definitions for all Tata modules
- 1.2: Return JSON schema matching OpenAI's function calling format
- 1.4: Include dependency information in tool descriptions
- 1.5: Provide method to retrieve all tools as a list
"""

import pytest

from src.tata.agent.registry import (
    InMemoryToolRegistry,
    REQUIREMENT_PROFILE_PARAMS,
    JOB_AD_PARAMS,
    TA_SCREENING_PARAMS,
    HM_SCREENING_PARAMS,
    HEADHUNTING_PARAMS,
    CANDIDATE_REPORT_PARAMS,
    FUNNEL_REPORT_PARAMS,
    JOB_AD_REVIEW_PARAMS,
    DI_REVIEW_PARAMS,
    CALENDAR_INVITE_PARAMS,
)
from src.tata.agent.models import ToolDefinition
from src.tata.session.session import ModuleType


class TestInMemoryToolRegistry:
    """Tests for InMemoryToolRegistry."""
    
    def test_registry_initializes_with_all_tools(self):
        """Registry should have all 10 Tata module tools registered."""
        registry = InMemoryToolRegistry()
        tools = registry.get_all_tools()
        
        assert len(tools) == 10
    
    def test_get_tool_returns_tool_definition(self):
        """get_tool should return ToolDefinition for valid name."""
        registry = InMemoryToolRegistry()
        
        tool = registry.get_tool("create_requirement_profile")
        
        assert tool is not None
        assert isinstance(tool, ToolDefinition)
        assert tool.name == "create_requirement_profile"
        assert tool.module_type == ModuleType.REQUIREMENT_PROFILE
    
    def test_get_tool_returns_none_for_unknown(self):
        """get_tool should return None for unknown tool name."""
        registry = InMemoryToolRegistry()
        
        tool = registry.get_tool("unknown_tool")
        
        assert tool is None
    
    def test_all_tools_have_required_fields(self):
        """All tools should have name, description, parameters, and module_type."""
        registry = InMemoryToolRegistry()
        
        for tool in registry.get_all_tools():
            assert tool.name, "Tool must have a name"
            assert tool.description, "Tool must have a description"
            assert tool.parameters is not None, "Tool must have parameters"
            assert tool.module_type is not None, "Tool must have module_type"
    
    def test_get_openai_tools_format(self):
        """get_openai_tools should return valid OpenAI format."""
        registry = InMemoryToolRegistry()
        
        openai_tools = registry.get_openai_tools()
        
        assert len(openai_tools) == 10
        
        for tool in openai_tools:
            # Check required OpenAI format fields
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]
            
            # Check parameters is valid JSON Schema
            params = tool["function"]["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params


class TestToolRegistryModules:
    """Tests for specific module tool registrations."""
    
    def test_requirement_profile_tool(self):
        """Requirement profile tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_requirement_profile")
        
        assert tool is not None
        assert tool.module_type == ModuleType.REQUIREMENT_PROFILE
        assert "startup_notes" in tool.parameters["properties"]
        assert "position_title" in tool.parameters["properties"]
        assert "startup_notes" in tool.parameters["required"]
        assert "position_title" in tool.parameters["required"]
    
    def test_job_ad_tool(self):
        """Job ad tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_job_ad")
        
        assert tool is not None
        assert tool.module_type == ModuleType.JOB_AD
        # Job ad has no required params (uses requirement profile from memory)
        assert tool.parameters["required"] == []
    
    def test_ta_screening_tool(self):
        """TA screening tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_ta_screening_template")
        
        assert tool is not None
        assert tool.module_type == ModuleType.TA_SCREENING
    
    def test_hm_screening_tool(self):
        """HM screening tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_hm_screening_template")
        
        assert tool is not None
        assert tool.module_type == ModuleType.HM_SCREENING
    
    def test_headhunting_tool(self):
        """Headhunting tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_headhunting_messages")
        
        assert tool is not None
        assert tool.module_type == ModuleType.HEADHUNTING
    
    def test_candidate_report_tool(self):
        """Candidate report tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_candidate_report")
        
        assert tool is not None
        assert tool.module_type == ModuleType.CANDIDATE_REPORT
        assert "transcript" in tool.parameters["required"]
        assert "candidate_name" in tool.parameters["required"]
    
    def test_funnel_report_tool(self):
        """Funnel report tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_funnel_report")
        
        assert tool is not None
        assert tool.module_type == ModuleType.FUNNEL_REPORT
        assert "job_title" in tool.parameters["required"]
        assert "number_of_positions" in tool.parameters["required"]
        assert "hiring_manager_name" in tool.parameters["required"]
    
    def test_job_ad_review_tool(self):
        """Job ad review tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("review_job_ad")
        
        assert tool is not None
        assert tool.module_type == ModuleType.JOB_AD_REVIEW
        assert "job_ad_text" in tool.parameters["required"]
    
    def test_di_review_tool(self):
        """D&I review tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("review_di_compliance")
        
        assert tool is not None
        assert tool.module_type == ModuleType.DI_REVIEW
        assert "job_ad_text" in tool.parameters["required"]
    
    def test_calendar_invite_tool(self):
        """Calendar invite tool should be correctly configured."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_calendar_invite")
        
        assert tool is not None
        assert tool.module_type == ModuleType.CALENDAR_INVITE
        assert "position_name" in tool.parameters["required"]
        assert "hiring_manager_name" in tool.parameters["required"]


class TestToolDependencyDescriptions:
    """Tests for dependency information in tool descriptions (Requirement 1.4)."""
    
    def test_job_ad_mentions_dependency(self):
        """Job ad tool description should mention requirement profile dependency."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_job_ad")
        
        description_lower = tool.description.lower()
        assert "requires" in description_lower or "depends" in description_lower
        assert "requirement profile" in description_lower
    
    def test_ta_screening_mentions_dependency(self):
        """TA screening tool description should mention requirement profile dependency."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_ta_screening_template")
        
        description_lower = tool.description.lower()
        assert "requires" in description_lower or "depends" in description_lower
        assert "requirement profile" in description_lower
    
    def test_hm_screening_mentions_dependency(self):
        """HM screening tool description should mention requirement profile dependency."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_hm_screening_template")
        
        description_lower = tool.description.lower()
        assert "requires" in description_lower or "depends" in description_lower
        assert "requirement profile" in description_lower
    
    def test_headhunting_mentions_dependency(self):
        """Headhunting tool description should mention requirement profile dependency."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_headhunting_messages")
        
        description_lower = tool.description.lower()
        assert "requires" in description_lower or "depends" in description_lower
        assert "requirement profile" in description_lower
    
    def test_candidate_report_mentions_dependencies(self):
        """Candidate report tool description should mention both dependencies."""
        registry = InMemoryToolRegistry()
        tool = registry.get_tool("create_candidate_report")
        
        description_lower = tool.description.lower()
        assert "requires" in description_lower or "depends" in description_lower
        assert "requirement profile" in description_lower
        assert "ta screening" in description_lower or "screening template" in description_lower
    
    def test_standalone_modules_no_dependency_mention(self):
        """Standalone modules should not mention dependencies as requirements."""
        registry = InMemoryToolRegistry()
        
        standalone_tools = [
            "create_funnel_report",
            "review_job_ad",
            "review_di_compliance",
            "create_calendar_invite",
        ]
        
        for tool_name in standalone_tools:
            tool = registry.get_tool(tool_name)
            description_lower = tool.description.lower()
            # Should mention "standalone" or "no dependencies"
            assert "standalone" in description_lower or "no dependencies" in description_lower


class TestParameterSchemas:
    """Tests for parameter schema validity."""
    
    def test_all_schemas_have_type_object(self):
        """All parameter schemas should have type: object."""
        registry = InMemoryToolRegistry()
        
        for tool in registry.get_all_tools():
            assert tool.parameters["type"] == "object"
    
    def test_all_schemas_have_properties(self):
        """All parameter schemas should have properties dict."""
        registry = InMemoryToolRegistry()
        
        for tool in registry.get_all_tools():
            assert "properties" in tool.parameters
            assert isinstance(tool.parameters["properties"], dict)
    
    def test_all_schemas_have_required_list(self):
        """All parameter schemas should have required list."""
        registry = InMemoryToolRegistry()
        
        for tool in registry.get_all_tools():
            assert "required" in tool.parameters
            assert isinstance(tool.parameters["required"], list)
    
    def test_required_fields_exist_in_properties(self):
        """All required fields should exist in properties."""
        registry = InMemoryToolRegistry()
        
        for tool in registry.get_all_tools():
            properties = tool.parameters["properties"]
            required = tool.parameters["required"]
            
            for field in required:
                assert field in properties, f"Required field '{field}' not in properties for {tool.name}"
    
    def test_property_types_are_valid(self):
        """All property types should be valid JSON Schema types."""
        valid_types = {"string", "integer", "number", "boolean", "array", "object"}
        registry = InMemoryToolRegistry()
        
        for tool in registry.get_all_tools():
            for prop_name, prop_def in tool.parameters["properties"].items():
                assert "type" in prop_def, f"Property '{prop_name}' missing type in {tool.name}"
                assert prop_def["type"] in valid_types, f"Invalid type for '{prop_name}' in {tool.name}"
    
    def test_properties_have_descriptions(self):
        """All properties should have descriptions."""
        registry = InMemoryToolRegistry()
        
        for tool in registry.get_all_tools():
            for prop_name, prop_def in tool.parameters["properties"].items():
                assert "description" in prop_def, f"Property '{prop_name}' missing description in {tool.name}"
                assert prop_def["description"], f"Empty description for '{prop_name}' in {tool.name}"
