"""Base tool classes and interfaces for MCP Jive tools.

Defines the common interface and structure for all MCP tools in the system.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import json

try:
    from mcp.types import Tool
except ImportError:
    # Mock Tool type if MCP not available
    Tool = Dict[str, Any]

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Categories for MCP tools."""
    WORK_ITEM_MANAGEMENT = "work_item_management"
    HIERARCHY_MANAGEMENT = "hierarchy_management"
    EXECUTION_CONTROL = "execution_control"
    STORAGE_SYNC = "storage_sync"
    VALIDATION = "validation"


@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    @classmethod
    def success_result(cls, data: Any = None, message: str = None, **kwargs) -> "ToolResult":
        """Create a success result."""
        return cls(success=True, data=data, message=message, **kwargs)
    
    @classmethod
    def error_result(cls, error: str, data: Any = None, **kwargs) -> "ToolResult":
        """Create an error result."""
        return cls(success=False, error=error, data=data, **kwargs)


@dataclass
class ToolSchema:
    """Schema definition for a tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None
    properties: Optional[Dict[str, "ToolSchema"]] = None
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format."""
        schema = {
            "type": self.type,
            "description": self.description
        }
        
        if self.enum:
            schema["enum"] = self.enum
        
        if self.default is not None:
            schema["default"] = self.default
        
        if self.properties:
            schema["properties"] = {
                name: prop.to_json_schema() 
                for name, prop in self.properties.items()
            }
            schema["required"] = [
                name for name, prop in self.properties.items() 
                if prop.required
            ]
        
        return schema


class BaseTool(ABC):
    """Base class for all MCP tools.
    
    Provides common functionality and interface for tool implementation.
    """
    
    def __init__(self, database=None, config=None):
        """Initialize base tool.
        
        Args:
            database: LanceDB database manager instance.
            config: Configuration object.
        """
        self.database = database
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._execution_count = 0
        self._last_execution_time = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for AI agents."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Tool category."""
        pass
    
    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, ToolSchema]:
        """Parameters schema for the tool."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters.
            
        Returns:
            Tool execution result.
        """
        pass
    
    def get_mcp_tool_definition(self) -> Tool:
        """Get MCP tool definition.
        
        Returns:
            MCP Tool definition for registration.
        """
        # Build parameters schema
        properties = {}
        required = []
        
        for param_name, param_schema in self.parameters_schema.items():
            properties[param_name] = param_schema.to_json_schema()
            if param_schema.required:
                required.append(param_name)
        
        parameters = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
        if isinstance(Tool, type) and hasattr(Tool, '__annotations__'):
            # Real MCP Tool class
            return Tool(
                name=self.name,
                description=self.description,
                inputSchema=parameters
            )
        else:
            # Mock Tool (dict)
            return {
                "name": self.name,
                "description": self.description,
                "inputSchema": parameters
            }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> ToolResult:
        """Validate tool parameters against schema.
        
        Args:
            parameters: Parameters to validate.
            
        Returns:
            Validation result.
        """
        try:
            # Check required parameters
            for param_name, param_schema in self.parameters_schema.items():
                if param_schema.required and param_name not in parameters:
                    return ToolResult.error_result(
                        f"Missing required parameter: {param_name}"
                    )
            
            # Check parameter types and values
            for param_name, value in parameters.items():
                if param_name not in self.parameters_schema:
                    return ToolResult.error_result(
                        f"Unknown parameter: {param_name}"
                    )
                
                param_schema = self.parameters_schema[param_name]
                
                # Type validation (basic)
                if param_schema.type == "string" and not isinstance(value, str):
                    return ToolResult.error_result(
                        f"Parameter '{param_name}' must be a string"
                    )
                elif param_schema.type == "integer" and not isinstance(value, int):
                    return ToolResult.error_result(
                        f"Parameter '{param_name}' must be an integer"
                    )
                elif param_schema.type == "number" and not isinstance(value, (int, float)):
                    return ToolResult.error_result(
                        f"Parameter '{param_name}' must be a number"
                    )
                elif param_schema.type == "boolean" and not isinstance(value, bool):
                    return ToolResult.error_result(
                        f"Parameter '{param_name}' must be a boolean"
                    )
                elif param_schema.type == "array" and not isinstance(value, list):
                    return ToolResult.error_result(
                        f"Parameter '{param_name}' must be an array"
                    )
                elif param_schema.type == "object" and not isinstance(value, dict):
                    return ToolResult.error_result(
                        f"Parameter '{param_name}' must be an object"
                    )
                
                # Enum validation
                if param_schema.enum and value not in param_schema.enum:
                    return ToolResult.error_result(
                        f"Parameter '{param_name}' must be one of: {param_schema.enum}"
                    )
            
            return ToolResult.success_result(message="Parameters validated successfully")
            
        except Exception as e:
            return ToolResult.error_result(f"Parameter validation error: {str(e)}")
    
    async def safe_execute(self, **kwargs) -> ToolResult:
        """Safely execute the tool with error handling and logging.
        
        Args:
            **kwargs: Tool parameters.
            
        Returns:
            Tool execution result.
        """
        start_time = datetime.now()
        
        try:
            self.logger.debug(f"Executing tool '{self.name}' with parameters: {kwargs}")
            
            # Validate parameters
            validation_result = self.validate_parameters(kwargs)
            if not validation_result.success:
                return validation_result
            
            # Execute tool
            result = await self.execute(**kwargs)
            
            # Add execution metadata
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            if not result.metadata:
                result.metadata = {}
            result.metadata.update({
                "tool_name": self.name,
                "tool_category": self.category.value,
                "execution_time": start_time.isoformat(),
                "execution_count": self._execution_count + 1
            })
            
            # Update execution stats
            self._execution_count += 1
            self._last_execution_time = start_time
            
            if result.success:
                self.logger.debug(f"Tool '{self.name}' executed successfully in {execution_time:.2f}ms")
            else:
                self.logger.warning(f"Tool '{self.name}' execution failed: {result.error}")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Tool '{self.name}' execution error: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return ToolResult.error_result(
                error=error_msg,
                metadata={
                    "tool_name": self.name,
                    "tool_category": self.category.value,
                    "execution_time": start_time.isoformat(),
                    "execution_time_ms": execution_time
                }
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        return {
            "name": self.name,
            "category": self.category.value,
            "execution_count": self._execution_count,
            "last_execution_time": self._last_execution_time.isoformat() if self._last_execution_time else None
        }
    
    async def initialize(self) -> None:
        """Initialize the tool (override if needed)."""
        pass
    
    async def shutdown(self) -> None:
        """Shutdown the tool (override if needed)."""
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', category='{self.category.value}')"
    
    def __repr__(self) -> str:
        return self.__str__()


class ToolExecutionContext:
    """Context for tool execution with shared resources."""
    
    def __init__(self, database=None, config=None, metadata=None):
        """Initialize execution context.
        
        Args:
            database: Database manager instance.
            config: Configuration object.
            metadata: Additional context metadata.
        """
        self.database = database
        self.config = config
        self.metadata = metadata or {}
        self.start_time = datetime.now()
    
    def get_elapsed_time_ms(self) -> float:
        """Get elapsed time since context creation in milliseconds."""
        return (datetime.now() - self.start_time).total_seconds() * 1000
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the context."""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "elapsed_time_ms": self.get_elapsed_time_ms(),
            "metadata": self.metadata
        }