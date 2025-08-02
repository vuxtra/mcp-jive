"""Configuration management for MCP Jive server.

Handles environment variables, .env files, and configuration validation
as specified in the MCP Server Core Infrastructure PRD.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Server configuration settings."""
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    auto_reload: bool = True


@dataclass
class DatabaseConfig:
    """Legacy Weaviate configuration (deprecated)."""
    use_embedded: bool = True
    host: str = "localhost"
    port: int = 8080
    timeout: int = 30
    persistence_path: str = ".weaviate_data"
    backup_enabled: bool = True


@dataclass
class AIConfig:
    """AI model orchestration configuration."""
    execution_mode: str = "hybrid"  # mcp_client, direct_api, hybrid
    default_provider: str = "anthropic"  # anthropic, openai, google
    fallback_execution_path: str = "direct_api"
    
    # API Keys (loaded from environment)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Model settings
    default_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4000
    temperature: float = 0.1
    
    # Rate limiting settings
    enable_rate_limiting: bool = True
    anthropic_requests_per_minute: int = 50
    openai_requests_per_minute: int = 60
    google_requests_per_minute: int = 60


@dataclass
class SecurityConfig:
    """Security and authentication settings."""
    secret_key: str = "dev-secret-key-change-in-production"
    enable_auth: bool = False
    cors_enabled: bool = True
    cors_origins: list = field(default_factory=lambda: ["*"])
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 100


@dataclass
class PerformanceConfig:
    """Performance and monitoring settings."""
    max_workers: int = 4
    request_timeout: int = 30
    connection_timeout: int = 60
    enable_metrics: bool = True
    enable_health_checks: bool = True
    enable_profiling: bool = False


@dataclass
class ToolsConfig:
    """Tool-specific configuration."""
    enable_task_management: bool = True
    enable_workflow_execution: bool = True
    enable_search_tools: bool = True
    enable_validation_tools: bool = True
    enable_sync_tools: bool = True
    
    # Task management settings
    max_task_depth: int = 5
    auto_dependency_validation: bool = True
    
    # Search settings
    search_result_limit: int = 50
    semantic_search_threshold: float = 0.7


@dataclass
class DevelopmentConfig:
    """Development and testing settings."""
    enable_hot_reload: bool = True
    enable_debug_logging: bool = False
    test_mode: bool = False
    mock_ai_responses: bool = False
    
    # Code quality
    enable_type_checking: bool = True
    enable_linting: bool = True


class Config:
    """Main configuration manager for MCP Jive server.
    
    Loads configuration from environment variables and .env files,
    validates settings, and provides access to all configuration sections.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            env_file: Path to .env file. If None, looks for .env.dev, .env.local, .env
        """
        self.env_file = env_file
        self._load_environment()
        self._initialize_configs()
        self._validate_configuration()
    
    def _load_environment(self) -> None:
        """Load environment variables from .env files."""
        if self.env_file:
            env_path = Path(self.env_file)
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment from {env_path}")
            else:
                logger.warning(f"Environment file not found: {env_path}")
        else:
            # Try to load from common .env files in order of preference
            env_files = [".env.dev", ".env.local", ".env"]
            for env_file in env_files:
                env_path = Path(env_file)
                if env_path.exists():
                    load_dotenv(env_path)
                    logger.info(f"Loaded environment from {env_path}")
                    break
            else:
                logger.info("No .env file found, using environment variables only")
    
    def _initialize_configs(self) -> None:
        """Initialize all configuration sections."""
        self.server = ServerConfig(
            host=os.getenv("MCP_JIVE_HOST", "localhost"),
            port=int(os.getenv("MCP_JIVE_PORT", "8000")),
            debug=os.getenv("MCP_JIVE_DEBUG", "false").lower() == "true",
            log_level=os.getenv("MCP_JIVE_LOG_LEVEL", "INFO"),
            auto_reload=os.getenv("MCP_JIVE_AUTO_RELOAD", "true").lower() == "true"
        )
        
        self.database = DatabaseConfig(
            use_embedded=os.getenv("WEAVIATE_USE_EMBEDDED", "true").lower() == "true",
            host=os.getenv("WEAVIATE_HOST", "localhost"),
            port=int(os.getenv("WEAVIATE_PORT", "8080")),
            timeout=int(os.getenv("WEAVIATE_TIMEOUT", "30")),
            persistence_path=os.getenv("WEAVIATE_PERSISTENCE_PATH", ".weaviate_data"),
            backup_enabled=os.getenv("WEAVIATE_BACKUP_ENABLED", "true").lower() == "true"
        )
        
        self.ai = AIConfig(
            execution_mode=os.getenv("AI_EXECUTION_MODE", "hybrid"),
            default_provider=os.getenv("DEFAULT_AI_PROVIDER", "anthropic"),
            fallback_execution_path=os.getenv("FALLBACK_EXECUTION_PATH", "direct_api"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            default_model=os.getenv("AI_DEFAULT_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "4000")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.1")),
            enable_rate_limiting=os.getenv("AI_ENABLE_RATE_LIMITING", "true").lower() == "true",
            anthropic_requests_per_minute=int(os.getenv("AI_ANTHROPIC_RPM", "50")),
            openai_requests_per_minute=int(os.getenv("AI_OPENAI_RPM", "60")),
            google_requests_per_minute=int(os.getenv("AI_GOOGLE_RPM", "60"))
        )
        
        self.security = SecurityConfig(
            secret_key=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
            enable_auth=os.getenv("ENABLE_AUTH", "false").lower() == "true",
            cors_enabled=os.getenv("CORS_ENABLED", "true").lower() == "true",
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            max_requests_per_minute=int(os.getenv("MAX_REQUESTS_PER_MINUTE", "100"))
        )
        
        self.performance = PerformanceConfig(
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            connection_timeout=int(os.getenv("CONNECTION_TIMEOUT", "60")),
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            enable_health_checks=os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true",
            enable_profiling=os.getenv("ENABLE_PROFILING", "false").lower() == "true"
        )
        
        self.tools = ToolsConfig(
            enable_task_management=os.getenv("ENABLE_TASK_MANAGEMENT", "true").lower() == "true",
            enable_workflow_execution=os.getenv("ENABLE_WORKFLOW_EXECUTION", "true").lower() == "true",
            enable_search_tools=os.getenv("ENABLE_SEARCH_TOOLS", "true").lower() == "true",
            enable_validation_tools=os.getenv("ENABLE_VALIDATION_TOOLS", "true").lower() == "true",
            enable_sync_tools=os.getenv("ENABLE_SYNC_TOOLS", "true").lower() == "true",
            max_task_depth=int(os.getenv("MAX_TASK_DEPTH", "5")),
            auto_dependency_validation=os.getenv("AUTO_DEPENDENCY_VALIDATION", "true").lower() == "true",
            search_result_limit=int(os.getenv("SEARCH_RESULT_LIMIT", "50")),
            semantic_search_threshold=float(os.getenv("SEMANTIC_SEARCH_THRESHOLD", "0.7"))
        )
        
        self.development = DevelopmentConfig(
            enable_hot_reload=os.getenv("ENABLE_HOT_RELOAD", "true").lower() == "true",
            enable_debug_logging=os.getenv("ENABLE_DEBUG_LOGGING", "false").lower() == "true",
            test_mode=os.getenv("TEST_MODE", "false").lower() == "true",
            mock_ai_responses=os.getenv("MOCK_AI_RESPONSES", "false").lower() == "true",
            enable_type_checking=os.getenv("ENABLE_TYPE_CHECKING", "true").lower() == "true",
            enable_linting=os.getenv("ENABLE_LINTING", "true").lower() == "true"
        )
    
    def _validate_configuration(self) -> None:
        """Validate configuration settings."""
        errors = []
        
        # Validate server settings
        if not (1 <= self.server.port <= 65535):
            errors.append(f"Invalid server port: {self.server.port}")
        
        if self.server.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"Invalid log level: {self.server.log_level}")
        
        # Validate database settings
        if not (1 <= self.database.port <= 65535):
            errors.append(f"Invalid database port: {self.database.port}")
        
        if self.database.timeout <= 0:
            errors.append(f"Invalid database timeout: {self.database.timeout}")
        
        # Validate AI settings
        if self.ai.execution_mode not in ["mcp_client", "direct_api", "hybrid"]:
            errors.append(f"Invalid AI execution mode: {self.ai.execution_mode}")
        
        if self.ai.default_provider not in ["anthropic", "openai", "google"]:
            errors.append(f"Invalid AI provider: {self.ai.default_provider}")
        
        # Check for required API keys based on provider
        if self.ai.execution_mode in ["direct_api", "hybrid"]:
            if self.ai.default_provider == "anthropic" and not self.ai.anthropic_api_key:
                errors.append("Anthropic API key required for direct API execution")
            elif self.ai.default_provider == "openai" and not self.ai.openai_api_key:
                errors.append("OpenAI API key required for direct API execution")
            elif self.ai.default_provider == "google" and not self.ai.google_api_key:
                errors.append("Google API key required for direct API execution")
        
        # Validate performance settings
        if self.performance.max_workers <= 0:
            errors.append(f"Invalid max workers: {self.performance.max_workers}")
        
        if self.performance.request_timeout <= 0:
            errors.append(f"Invalid request timeout: {self.performance.request_timeout}")
        
        # Validate tools settings
        if self.tools.max_task_depth <= 0:
            errors.append(f"Invalid max task depth: {self.tools.max_task_depth}")
        
        if not (0.0 <= self.tools.semantic_search_threshold <= 1.0):
            errors.append(f"Invalid semantic search threshold: {self.tools.semantic_search_threshold}")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def reload(self) -> None:
        """Reload configuration from environment."""
        logger.info("Reloading configuration...")
        self._load_environment()
        self._initialize_configs()
        self._validate_configuration()
        logger.info("Configuration reloaded successfully")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "server": self.server.__dict__,
            "database": self.database.__dict__,
            "ai": {
                **self.ai.__dict__,
                # Mask sensitive API keys
                "anthropic_api_key": "***" if self.ai.anthropic_api_key else None,
                "openai_api_key": "***" if self.ai.openai_api_key else None,
                "google_api_key": "***" if self.ai.google_api_key else None,
            },
            "security": {
                **self.security.__dict__,
                "secret_key": "***",  # Always mask secret key
            },
            "performance": self.performance.__dict__,
            "tools": self.tools.__dict__,
            "development": self.development.__dict__,
        }
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"Config(server={self.server.host}:{self.server.port}, provider={self.ai.default_provider})"