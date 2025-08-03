"""AI Orchestration MCP Tools.

Provides MCP tools for AI model orchestration, execution routing,
and provider management as specified in the AI Model Orchestration PRD.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

from .base import BaseTool, ToolExecutionContext
from ..ai_orchestrator import AIRequest, AIResponse, AIProvider, ExecutionMode

logger = logging.getLogger(__name__)


class AIExecutionRequest(BaseModel):
    """AI execution request model."""
    provider: Optional[str] = Field(None, description="AI provider (anthropic, openai, google)")
    model: Optional[str] = Field(None, description="Model name")
    messages: List[Dict[str, Any]] = Field(..., description="Conversation messages")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens")
    temperature: Optional[float] = Field(None, description="Temperature setting")
    execution_mode: Optional[str] = Field(None, description="Execution mode (mcp_client_sampling, direct_api, hybrid)")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Available tools")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AIOrchestrationTool(BaseTool):
    """Execute AI requests through the orchestration system."""
    
    @property
    def name(self) -> str:
        return "ai_execute"
    
    @property
    def description(self) -> str:
        return "Execute AI model requests through the orchestration system with provider selection and execution mode routing"
    
    @property
    def category(self) -> str:
        return "ai_orchestration"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "enum": ["anthropic", "openai", "google"],
                    "description": "AI provider to use (optional, uses default if not specified)"
                },
                "model": {
                    "type": "string",
                    "description": "Specific model name (optional, uses provider default)"
                },
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                            "content": {"type": "string"}
                        },
                        "required": ["role", "content"]
                    },
                    "description": "Conversation messages"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "System prompt for the AI model"
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 8000,
                    "description": "Maximum tokens to generate"
                },
                "temperature": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "description": "Temperature for response generation"
                },
                "execution_mode": {
                    "type": "string",
                    "enum": ["mcp_client_sampling", "direct_api", "hybrid"],
                    "description": "Execution mode override"
                },
                "tools": {
                    "type": "array",
                    "description": "Available tools for the AI model"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata"
                }
            },
            "required": ["messages"]
        }
    
    def get_schema(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.parameters_schema
        )
    
    async def execute(self, context: ToolExecutionContext, **kwargs) -> List[TextContent]:
        """Execute AI request through orchestration system."""
        try:
            # Validate input
            request_data = AIExecutionRequest(**kwargs)
            
            if not context.ai_orchestrator:
                raise ValueError("AI orchestrator not available")
            
            # Create AI request
            ai_request = AIRequest(
                provider=request_data.provider,
                model=request_data.model,
                messages=request_data.messages,
                system_prompt=request_data.system_prompt,
                max_tokens=request_data.max_tokens,
                temperature=request_data.temperature,
                execution_mode=request_data.execution_mode,
                tools=request_data.tools,
                metadata=request_data.metadata
            )
            
            # Execute through orchestrator
            response = await context.ai_orchestrator.execute_ai_request(ai_request)
            
            # Format response
            result = {
                "success": True,
                "content": response.content,
                "provider": response.provider,
                "model": response.model,
                "execution_time_ms": response.execution_time_ms,
                "usage": response.usage,
                "tool_calls": response.tool_calls,
                "metadata": response.metadata,
                "error": response.error
            }
            
            self.logger.info(f"AI request executed successfully via {response.provider}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            self.logger.error(f"AI execution failed: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]


class AIProviderStatusTool(BaseTool):
    """Get status and health information for AI providers."""
    
    @property
    def name(self) -> str:
        return "ai_provider_status"
    
    @property
    def description(self) -> str:
        return "Get status, health, and usage statistics for AI providers"
    
    @property
    def category(self) -> str:
        return "ai_orchestration"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "enum": ["anthropic", "openai", "google"],
                    "description": "Specific provider to check (optional, returns all if not specified)"
                },
                "include_stats": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include usage statistics"
                }
            }
        }
    
    def get_schema(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.parameters_schema
        )
    
    async def execute(self, context: ToolExecutionContext, **kwargs) -> List[TextContent]:
        """Get AI provider status and statistics."""
        try:
            if not context.ai_orchestrator:
                raise ValueError("AI orchestrator not available")
            
            provider = kwargs.get("provider")
            include_stats = kwargs.get("include_stats", True)
            
            # Get health status
            health_status = context.ai_orchestrator.get_health_status()
            
            # Get provider stats if requested
            stats = None
            if include_stats:
                stats = context.ai_orchestrator.get_provider_stats(provider)
            
            result = {
                "success": True,
                "health_status": health_status,
                "available_providers": context.ai_orchestrator.get_available_providers(),
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            self.logger.error(f"Provider status check failed: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]


class AIConfigurationTool(BaseTool):
    """Update AI orchestrator configuration."""
    
    @property
    def name(self) -> str:
        return "ai_configure"
    
    @property
    def description(self) -> str:
        return "Update AI orchestrator configuration settings"
    
    @property
    def category(self) -> str:
        return "ai_orchestration"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "execution_mode": {
                    "type": "string",
                    "enum": ["mcp_client_sampling", "direct_api", "hybrid"],
                    "description": "Default execution mode"
                },
                "default_provider": {
                    "type": "string",
                    "enum": ["anthropic", "openai", "google"],
                    "description": "Default AI provider"
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 8000,
                    "description": "Default maximum tokens"
                },
                "temperature": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "description": "Default temperature"
                },
                "enable_rate_limiting": {
                    "type": "boolean",
                    "description": "Enable/disable rate limiting"
                }
            }
        }
    
    def get_schema(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.parameters_schema
        )
    
    async def execute(self, context: ToolExecutionContext, **kwargs) -> List[TextContent]:
        """Update AI orchestrator configuration."""
        try:
            if not context.ai_orchestrator:
                raise ValueError("AI orchestrator not available")
            
            # Update configuration
            config_updates = {k: v for k, v in kwargs.items() if v is not None}
            
            if not config_updates:
                raise ValueError("No configuration updates provided")
            
            # Apply updates to config
            for key, value in config_updates.items():
                if hasattr(context.ai_orchestrator.config, key):
                    setattr(context.ai_orchestrator.config, key, value)
                else:
                    raise ValueError(f"Unknown configuration key: {key}")
            
            # Re-initialize if needed
            await context.ai_orchestrator.initialize()
            
            result = {
                "success": True,
                "updated_config": config_updates,
                "current_config": {
                    "execution_mode": context.ai_orchestrator.config.execution_mode,
                    "default_provider": context.ai_orchestrator.config.default_provider,
                    "max_tokens": context.ai_orchestrator.config.max_tokens,
                    "temperature": context.ai_orchestrator.config.temperature,
                    "enable_rate_limiting": context.ai_orchestrator.config.enable_rate_limiting
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"AI configuration updated: {config_updates}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            self.logger.error(f"Configuration update failed: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]


# Export all AI orchestration tools
AI_ORCHESTRATION_TOOLS = [
    AIOrchestrationTool,
    AIProviderStatusTool,
    AIConfigurationTool
]