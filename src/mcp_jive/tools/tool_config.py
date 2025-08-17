"""Tool Configuration for MCP Jive.

Provides unified configuration options for the MCP Jive tool system.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolConfiguration:
    """Configuration for the unified tool system."""
    
    # Performance settings
    enable_tool_caching: bool = True
    cache_ttl_seconds: int = 300
    max_concurrent_executions: int = 10
    
    # Feature flags
    enable_advanced_analytics: bool = True
    enable_workflow_orchestration: bool = True
    
    # Tool-specific settings
    tool_timeouts: Dict[str, int] = field(default_factory=lambda: {
        "jive_execute_work_item": 300,  # 5 minutes for execution
        "jive_search_content": 30,      # 30 seconds for search
        "jive_sync_data": 120,          # 2 minutes for sync
        "jive_manage_work_item": 60,    # 1 minute for management
        "jive_get_work_item": 30,       # 30 seconds for retrieval
        "jive_get_hierarchy": 60,       # 1 minute for hierarchy
        "jive_track_progress": 90,      # 1.5 minutes for progress
        "jive_reorder_work_items": 30,  # 30 seconds for reordering
        "default": 60                   # 1 minute default
    })
    
    # Environment-specific overrides
    environment_overrides: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_environment(cls) -> 'ToolConfiguration':
        """Create configuration from environment variables."""
        config = cls()
        
        # Performance settings
        config.enable_tool_caching = os.getenv('MCP_JIVE_TOOL_CACHING', 'true').lower() == 'true'
        config.cache_ttl_seconds = int(os.getenv('MCP_JIVE_CACHE_TTL', '300'))
        config.max_concurrent_executions = int(os.getenv('MCP_JIVE_MAX_CONCURRENT', '10'))
        
        # Feature flags
        config.enable_advanced_analytics = os.getenv('MCP_JIVE_ADVANCED_ANALYTICS', 'true').lower() == 'true'
        config.enable_workflow_orchestration = os.getenv('MCP_JIVE_WORKFLOW_ORCHESTRATION', 'true').lower() == 'true'
        
        return config
    
    def get_tool_timeout(self, tool_name: str) -> int:
        """Get timeout for a specific tool."""
        return self.tool_timeouts.get(tool_name, self.tool_timeouts.get("default", 60))
    
    def validate(self) -> List[str]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Check timeout values
        for tool, timeout in self.tool_timeouts.items():
            if timeout <= 0:
                issues.append(f"Invalid timeout for tool '{tool}': {timeout}")
        
        # Check cache settings
        if self.cache_ttl_seconds <= 0:
            issues.append(f"Invalid cache TTL: {self.cache_ttl_seconds}")
        
        if self.max_concurrent_executions <= 0:
            issues.append(f"Invalid max concurrent executions: {self.max_concurrent_executions}")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "enable_tool_caching": self.enable_tool_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "max_concurrent_executions": self.max_concurrent_executions,
            "enable_advanced_analytics": self.enable_advanced_analytics,
            "enable_workflow_orchestration": self.enable_workflow_orchestration,
            "tool_timeouts": self.tool_timeouts,
            "environment_overrides": self.environment_overrides
        }


# Global configuration instance
_global_config: Optional[ToolConfiguration] = None


def get_tool_config() -> ToolConfiguration:
    """Get the global tool configuration."""
    global _global_config
    if _global_config is None:
        _global_config = ToolConfiguration.from_environment()
        
        # Validate configuration
        issues = _global_config.validate()
        if issues:
            logger.warning(f"Tool configuration issues: {issues}")
    
    return _global_config


def set_tool_config(config: ToolConfiguration) -> None:
    """Set the global tool configuration."""
    global _global_config
    _global_config = config


def reset_tool_config() -> None:
    """Reset the global tool configuration."""
    global _global_config
    _global_config = None


def get_production_config() -> ToolConfiguration:
    """Get production-ready configuration."""
    return ToolConfiguration(
        enable_tool_caching=True,
        cache_ttl_seconds=300,
        max_concurrent_executions=10,
        enable_advanced_analytics=True,
        enable_workflow_orchestration=True
    )


def get_development_config() -> ToolConfiguration:
    """Get configuration for development."""
    return ToolConfiguration(
        enable_tool_caching=False,  # Disable caching for development
        cache_ttl_seconds=60,
        max_concurrent_executions=5,
        enable_advanced_analytics=True,
        enable_workflow_orchestration=True
    )