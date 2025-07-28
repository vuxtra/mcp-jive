"""AI model orchestration for MCP Jive.

Handles AI model execution, provider management, and execution path routing
as specified in the MCP Server Core Infrastructure PRD.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import time

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .config import AIConfig

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """AI execution modes."""
    MCP_CLIENT_SAMPLING = "mcp_client_sampling"
    DIRECT_API = "direct_api"
    HYBRID = "hybrid"


class AIProvider(Enum):
    """Supported AI providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


@dataclass
class AIRequest:
    """AI execution request."""
    provider: str
    model: str
    messages: List[Dict[str, Any]]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    tools: Optional[List[Dict[str, Any]]] = None
    system_prompt: Optional[str] = None
    execution_mode: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIResponse:
    """AI execution response."""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    execution_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ProviderStats:
    """Provider usage statistics."""
    requests_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_response_time_ms: float = 0.0
    last_request_time: Optional[datetime] = None


class AIOrchestrator:
    """AI model orchestration and provider management.
    
    Handles execution path routing, provider selection, and AI model calls
    with support for multiple providers and execution modes.
    """
    
    def __init__(self, config: AIConfig):
        """Initialize AI orchestrator.
        
        Args:
            config: AI configuration settings.
        """
        self.config = config
        self.providers: Dict[str, Any] = {}
        self.stats: Dict[str, ProviderStats] = {}
        self._initialized = False
        
        # Initialize provider stats
        for provider in AIProvider:
            self.stats[provider.value] = ProviderStats()
    
    async def initialize(self) -> None:
        """Initialize AI providers and clients."""
        logger.info("Initializing AI orchestrator...")
        
        try:
            # Initialize Anthropic
            if self.config.anthropic_api_key and anthropic:
                self.providers[AIProvider.ANTHROPIC.value] = anthropic.AsyncAnthropic(
                    api_key=self.config.anthropic_api_key
                )
                logger.info("Anthropic client initialized")
            elif self.config.anthropic_api_key:
                logger.warning("Anthropic API key provided but anthropic package not installed")
            
            # Initialize OpenAI
            if self.config.openai_api_key and openai:
                self.providers[AIProvider.OPENAI.value] = openai.AsyncOpenAI(
                    api_key=self.config.openai_api_key
                )
                logger.info("OpenAI client initialized")
            elif self.config.openai_api_key:
                logger.warning("OpenAI API key provided but openai package not installed")
            
            # Initialize Google Gemini
            if self.config.google_api_key and genai:
                genai.configure(api_key=self.config.google_api_key)
                self.providers[AIProvider.GOOGLE.value] = genai
                logger.info("Google Gemini client initialized")
            elif self.config.google_api_key:
                logger.warning("Google API key provided but google-generativeai package not installed")
            
            if not self.providers:
                logger.warning("No AI providers initialized. Check API keys and package installations.")
            
            self._initialized = True
            logger.info(f"AI orchestrator initialized with {len(self.providers)} providers")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI orchestrator: {e}")
            raise
    
    async def execute_ai_request(self, request: AIRequest) -> AIResponse:
        """Execute AI request with specified provider and model.
        
        Args:
            request: AI execution request.
            
        Returns:
            AI response with content and metadata.
        """
        if not self._initialized:
            raise RuntimeError("AI orchestrator not initialized")
        
        start_time = time.time()
        provider = request.provider or self.config.default_provider
        execution_mode = request.execution_mode or self.config.execution_mode
        
        logger.debug(f"Executing AI request: provider={provider}, model={request.model}, mode={execution_mode}")
        
        try:
            # Route based on execution mode
            if execution_mode == ExecutionMode.MCP_CLIENT_SAMPLING.value:
                response = await self._execute_mcp_client_sampling(request)
            elif execution_mode == ExecutionMode.DIRECT_API.value:
                response = await self._execute_direct_api(request)
            elif execution_mode == ExecutionMode.HYBRID.value:
                response = await self._execute_hybrid(request)
            else:
                raise ValueError(f"Unknown execution mode: {execution_mode}")
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            response.execution_time_ms = execution_time
            
            # Update stats
            self._update_stats(provider, True, execution_time, response.usage)
            
            return response
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"AI request failed: {e}")
            
            # Update error stats
            self._update_stats(provider, False, execution_time)
            
            return AIResponse(
                content="",
                provider=provider,
                model=request.model,
                execution_time_ms=execution_time,
                error=str(e)
            )
    
    async def _execute_mcp_client_sampling(self, request: AIRequest) -> AIResponse:
        """Execute request using MCP client sampling mode.
        
        In this mode, the MCP client handles the AI model execution.
        This is a placeholder for the actual MCP client integration.
        """
        logger.debug("Executing in MCP client sampling mode")
        
        # For now, return a placeholder response
        # In actual implementation, this would delegate to MCP client
        return AIResponse(
            content="MCP client sampling mode not yet implemented",
            provider=request.provider,
            model=request.model,
            metadata={"execution_mode": "mcp_client_sampling"}
        )
    
    async def _execute_direct_api(self, request: AIRequest) -> AIResponse:
        """Execute request using direct API calls."""
        provider = request.provider or self.config.default_provider
        
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not available")
        
        logger.debug(f"Executing direct API call to {provider}")
        
        if provider == AIProvider.ANTHROPIC.value:
            return await self._call_anthropic(request)
        elif provider == AIProvider.OPENAI.value:
            return await self._call_openai(request)
        elif provider == AIProvider.GOOGLE.value:
            return await self._call_google(request)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _execute_hybrid(self, request: AIRequest) -> AIResponse:
        """Execute request using hybrid mode.
        
        Attempts MCP client sampling first, falls back to direct API.
        """
        logger.debug("Executing in hybrid mode")
        
        try:
            # Try MCP client sampling first
            return await self._execute_mcp_client_sampling(request)
        except Exception as e:
            logger.warning(f"MCP client sampling failed, falling back to direct API: {e}")
            return await self._execute_direct_api(request)
    
    async def _call_anthropic(self, request: AIRequest) -> AIResponse:
        """Call Anthropic Claude API."""
        client = self.providers[AIProvider.ANTHROPIC.value]
        
        # Prepare messages
        messages = request.messages.copy()
        system_prompt = request.system_prompt
        
        # Prepare request parameters
        params = {
            "model": request.model or self.config.default_models.get("anthropic", "claude-3-sonnet-20240229"),
            "messages": messages,
            "max_tokens": request.max_tokens or self.config.max_tokens,
        }
        
        if request.temperature is not None:
            params["temperature"] = request.temperature
        
        if system_prompt:
            params["system"] = system_prompt
        
        if request.tools:
            params["tools"] = request.tools
        
        # Make API call
        response = await client.messages.create(**params)
        
        # Extract content
        content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input
                })
        
        return AIResponse(
            content=content,
            provider=AIProvider.ANTHROPIC.value,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            tool_calls=tool_calls if tool_calls else None
        )
    
    async def _call_openai(self, request: AIRequest) -> AIResponse:
        """Call OpenAI GPT API."""
        client = self.providers[AIProvider.OPENAI.value]
        
        # Prepare messages
        messages = request.messages.copy()
        
        if request.system_prompt:
            messages.insert(0, {"role": "system", "content": request.system_prompt})
        
        # Prepare request parameters
        params = {
            "model": request.model or self.config.default_models.get("openai", "gpt-4"),
            "messages": messages,
            "max_tokens": request.max_tokens or self.config.max_tokens,
        }
        
        if request.temperature is not None:
            params["temperature"] = request.temperature
        
        if request.tools:
            params["tools"] = request.tools
            params["tool_choice"] = "auto"
        
        # Make API call
        response = await client.chat.completions.create(**params)
        
        # Extract content and tool calls
        message = response.choices[0].message
        content = message.content or ""
        tool_calls = []
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments)
                })
        
        return AIResponse(
            content=content,
            provider=AIProvider.OPENAI.value,
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            tool_calls=tool_calls if tool_calls else None
        )
    
    async def _call_google(self, request: AIRequest) -> AIResponse:
        """Call Google Gemini API."""
        genai_client = self.providers[AIProvider.GOOGLE.value]
        
        # Prepare model
        model_name = request.model or self.config.default_models.get("google", "gemini-pro")
        model = genai_client.GenerativeModel(model_name)
        
        # Prepare content
        content_parts = []
        for message in request.messages:
            if message["role"] == "user":
                content_parts.append(message["content"])
        
        # Prepare generation config
        generation_config = {
            "max_output_tokens": request.max_tokens or self.config.max_tokens,
        }
        
        if request.temperature is not None:
            generation_config["temperature"] = request.temperature
        
        # Make API call
        response = await model.generate_content_async(
            content_parts,
            generation_config=generation_config
        )
        
        return AIResponse(
            content=response.text,
            provider=AIProvider.GOOGLE.value,
            model=model_name,
            usage={
                "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }
        )
    
    def _update_stats(self, provider: str, success: bool, execution_time_ms: float, usage: Optional[Dict[str, Any]] = None) -> None:
        """Update provider statistics."""
        if provider not in self.stats:
            self.stats[provider] = ProviderStats()
        
        stats = self.stats[provider]
        stats.requests_count += 1
        stats.last_request_time = datetime.now()
        
        if success:
            stats.success_count += 1
            
            # Update response time average
            if stats.avg_response_time_ms == 0:
                stats.avg_response_time_ms = execution_time_ms
            else:
                stats.avg_response_time_ms = (
                    (stats.avg_response_time_ms * (stats.success_count - 1) + execution_time_ms) / stats.success_count
                )
            
            # Update token usage
            if usage and "total_tokens" in usage:
                stats.total_tokens += usage["total_tokens"]
        else:
            stats.error_count += 1
    
    async def update_config(self, config: AIConfig) -> None:
        """Update AI configuration."""
        logger.info("Updating AI orchestrator configuration")
        self.config = config
        
        # Re-initialize providers if needed
        await self.initialize()
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        return list(self.providers.keys())
    
    def get_provider_stats(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get provider usage statistics."""
        if provider:
            if provider in self.stats:
                return asdict(self.stats[provider])
            else:
                return {}
        else:
            return {p: asdict(stats) for p, stats in self.stats.items()}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get AI orchestrator health status."""
        try:
            available_providers = self.get_available_providers()
            
            status = "ready" if self._initialized and available_providers else "not_ready"
            if not self._initialized:
                status = "not_initialized"
            elif not available_providers:
                status = "no_providers"
            
            return {
                "status": status,
                "initialized": self._initialized,
                "available_providers": available_providers,
                "default_provider": self.config.default_provider,
                "execution_mode": self.config.execution_mode,
                "stats": self.get_provider_stats()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def shutdown(self) -> None:
        """Shutdown AI orchestrator."""
        logger.info("Shutting down AI orchestrator")
        
        # Close any persistent connections if needed
        self.providers.clear()
        self._initialized = False
        
        logger.info("AI orchestrator shutdown complete")