"""Configuration management for MCP Jive Server.

Handles environment variables, server settings, and configuration validation.
Supports development, testing, and production environments.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ServerConfig:
    """Main server configuration class."""
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("MCP_ENV", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("MCP_DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("MCP_LOG_LEVEL", "INFO"))
    
    # Server Configuration
    host: str = field(default_factory=lambda: os.getenv("MCP_SERVER_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("MCP_SERVER_PORT", "8000")))
    workers: int = field(default_factory=lambda: int(os.getenv("MCP_SERVER_WORKERS", "1")))
    max_connections: int = field(default_factory=lambda: int(os.getenv("MCP_MAX_CONNECTIONS", "100")))
    
    # Legacy Weaviate Configuration (deprecated)
    weaviate_host: str = field(default_factory=lambda: os.getenv("WEAVIATE_HOST", "localhost"))
    weaviate_port: int = field(default_factory=lambda: int(os.getenv("WEAVIATE_PORT", "8080")))
    weaviate_grpc_port: int = field(default_factory=lambda: int(os.getenv("WEAVIATE_GRPC_PORT", "50051")))
    weaviate_data_path: str = field(default_factory=lambda: os.getenv("WEAVIATE_DATA_PATH", os.path.join(os.getcwd(), "data", "weaviate")))
    weaviate_embedded: bool = field(default_factory=lambda: os.getenv("WEAVIATE_EMBEDDED", "true").lower() == "true")
    
    # Weaviate Vectorizer Configuration
    weaviate_enable_vectorizer: bool = field(default_factory=lambda: os.getenv("WEAVIATE_ENABLE_VECTORIZER", "true").lower() == "true")
    weaviate_vectorizer_module: str = field(default_factory=lambda: os.getenv("WEAVIATE_VECTORIZER_MODULE", "text2vec-transformers"))
    weaviate_search_fallback: bool = field(default_factory=lambda: os.getenv("WEAVIATE_SEARCH_FALLBACK", "true").lower() == "true")
    
    # AI Model Configuration
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    google_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    
    # Security
    auth_enabled: bool = field(default_factory=lambda: os.getenv("MCP_AUTH_ENABLED", "true").lower() == "true")
    auth_secret: Optional[str] = field(default_factory=lambda: os.getenv("MCP_AUTH_SECRET"))
    
    # Performance
    query_timeout: int = field(default_factory=lambda: int(os.getenv("MCP_QUERY_TIMEOUT", "30")))
    startup_timeout: int = field(default_factory=lambda: int(os.getenv("MCP_STARTUP_TIMEOUT", "60")))
    memory_limit_mb: int = field(default_factory=lambda: int(os.getenv("MCP_MEMORY_LIMIT_MB", "512")))
    
    # Tool Configuration
    tool_mode: str = field(default_factory=lambda: os.getenv("MCP_TOOL_MODE", "minimal"))  # "minimal" (16 tools) or "full" (35 tools)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
        self._setup_logging()
        
    def _validate_config(self) -> None:
        """Validate configuration values."""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")
            
        if self.workers < 1:
            raise ValueError(f"Workers must be >= 1, got: {self.workers}")
            
        if self.max_connections < 1:
            raise ValueError(f"Max connections must be >= 1, got: {self.max_connections}")
            
        if self.environment not in ["development", "testing", "production"]:
            raise ValueError(f"Invalid environment: {self.environment}")
            
        if self.tool_mode not in ["minimal", "full"]:
            raise ValueError(f"Invalid tool_mode: {self.tool_mode}. Must be 'minimal' or 'full'")
            
        # Ensure data directory exists
        Path(self.weaviate_data_path).mkdir(parents=True, exist_ok=True)
        
        # Validate AI API keys in production
        if self.environment == "production":
            if not any([self.anthropic_api_key, self.openai_api_key, self.google_api_key]):
                raise ValueError("At least one AI provider API key must be configured in production")
                
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        if self.debug:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
            
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f"logs/mcp-server-{self.environment}.log")
            ] if self.environment != "testing" else [logging.StreamHandler()]
        )
        
    @property
    def legacy_weaviate_url(self) -> str:
        """Get Weaviate HTTP URL."""
        return f"http://{self.weaviate_host}:{self.weaviate_port}"
        
    @property
    def legacy_weaviate_grpc_url(self) -> str:
        """Get Weaviate gRPC URL."""
        return f"{self.weaviate_host}:{self.weaviate_grpc_port}"
        
    @property
    def server_url(self) -> str:
        """Get server URL."""
        return f"http://{self.host}:{self.port}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)."""
        config_dict = {
            "environment": self.environment,
            "debug": self.debug,
            "log_level": self.log_level,
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "max_connections": self.max_connections,
            "weaviate_host": self.weaviate_host,
            "weaviate_port": self.weaviate_port,
            "weaviate_grpc_port": self.weaviate_grpc_port,
            "auth_enabled": self.auth_enabled,
            "query_timeout": self.query_timeout,
            "startup_timeout": self.startup_timeout,
            "memory_limit_mb": self.memory_limit_mb,
            "tool_mode": self.tool_mode,
        }
        
        # Add AI provider availability (without keys)
        config_dict["ai_providers"] = {
            "anthropic": bool(self.anthropic_api_key),
            "openai": bool(self.openai_api_key),
            "google": bool(self.google_api_key),
        }
        
        return config_dict


def load_config() -> ServerConfig:
    """Load server configuration from environment."""
    return ServerConfig()