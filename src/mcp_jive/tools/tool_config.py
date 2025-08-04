"""Tool Configuration for MCP Jive.

Provides configuration options for switching between consolidated and legacy tools,
and utilities for managing the transition period.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ToolMode(Enum):
    """Tool registry modes."""
    CONSOLIDATED = "consolidated"  # 7 consolidated tools only
    MINIMAL = "minimal"           # 7 consolidated + essential legacy
    FULL = "full"                 # 7 consolidated + all legacy
    LEGACY_ONLY = "legacy_only"   # Original 35+ legacy tools only


@dataclass
class ToolConfiguration:
    """Configuration for tool registry behavior."""
    
    # Primary mode selection
    mode: ToolMode = ToolMode.CONSOLIDATED
    
    # Legacy support settings
    enable_legacy_support: bool = True
    legacy_deprecation_warnings: bool = True
    legacy_usage_tracking: bool = True
    
    # Performance settings
    enable_tool_caching: bool = True
    cache_ttl_seconds: int = 300
    max_concurrent_executions: int = 10
    
    # Migration settings
    migration_mode: bool = False  # Special mode for migration testing
    migration_log_file: Optional[str] = None
    migration_dry_run: bool = False
    
    # Feature flags
    enable_ai_orchestration: bool = False  # Disabled in consolidated mode
    enable_quality_gates: bool = False     # Disabled in consolidated mode
    enable_advanced_analytics: bool = True
    enable_workflow_orchestration: bool = True
    
    # Tool-specific settings
    tool_timeouts: Dict[str, int] = field(default_factory=lambda: {
        "jive_execute_work_item": 300,  # 5 minutes for execution
        "jive_search_content": 30,      # 30 seconds for search
        "jive_sync_data": 120,          # 2 minutes for sync
        "default": 60                   # 1 minute default
    })
    
    # Environment-specific overrides
    environment_overrides: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_environment(cls) -> 'ToolConfiguration':
        """Create configuration from environment variables."""
        config = cls()
        
        # Mode selection
        mode_str = os.getenv('MCP_JIVE_TOOL_MODE', 'consolidated').lower()
        try:
            config.mode = ToolMode(mode_str)
        except ValueError:
            logger.warning(f"Invalid tool mode '{mode_str}', using consolidated")
            config.mode = ToolMode.CONSOLIDATED
        
        # Legacy support
        config.enable_legacy_support = os.getenv('MCP_JIVE_LEGACY_SUPPORT', 'true').lower() == 'true'
        config.legacy_deprecation_warnings = os.getenv('MCP_JIVE_LEGACY_WARNINGS', 'true').lower() == 'true'
        config.legacy_usage_tracking = os.getenv('MCP_JIVE_LEGACY_TRACKING', 'true').lower() == 'true'
        
        # Performance settings
        config.enable_tool_caching = os.getenv('MCP_JIVE_TOOL_CACHING', 'true').lower() == 'true'
        config.cache_ttl_seconds = int(os.getenv('MCP_JIVE_CACHE_TTL', '300'))
        config.max_concurrent_executions = int(os.getenv('MCP_JIVE_MAX_CONCURRENT', '10'))
        
        # Migration settings
        config.migration_mode = os.getenv('MCP_JIVE_MIGRATION_MODE', 'false').lower() == 'true'
        config.migration_log_file = os.getenv('MCP_JIVE_MIGRATION_LOG')
        config.migration_dry_run = os.getenv('MCP_JIVE_MIGRATION_DRY_RUN', 'false').lower() == 'true'
        
        # Feature flags
        config.enable_ai_orchestration = os.getenv('MCP_JIVE_AI_ORCHESTRATION', 'false').lower() == 'true'
        config.enable_quality_gates = os.getenv('MCP_JIVE_QUALITY_GATES', 'false').lower() == 'true'
        config.enable_advanced_analytics = os.getenv('MCP_JIVE_ADVANCED_ANALYTICS', 'true').lower() == 'true'
        config.enable_workflow_orchestration = os.getenv('MCP_JIVE_WORKFLOW_ORCHESTRATION', 'true').lower() == 'true'
        
        return config
    
    def get_effective_mode(self) -> str:
        """Get the effective tool mode for registry initialization."""
        if self.mode == ToolMode.LEGACY_ONLY:
            return "legacy"
        else:
            return self.mode.value
    
    def should_use_consolidated_registry(self) -> bool:
        """Determine if consolidated registry should be used."""
        return self.mode != ToolMode.LEGACY_ONLY
    
    def get_tool_timeout(self, tool_name: str) -> int:
        """Get timeout for a specific tool."""
        return self.tool_timeouts.get(tool_name, self.tool_timeouts.get("default", 60))
    
    def validate(self) -> List[str]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Check for conflicting settings
        if self.mode == ToolMode.CONSOLIDATED and self.enable_ai_orchestration:
            issues.append("AI Orchestration is not available in consolidated mode")
        
        if self.mode == ToolMode.CONSOLIDATED and self.enable_quality_gates:
            issues.append("Quality Gates are not available in consolidated mode")
        
        if self.migration_mode and not self.enable_legacy_support:
            issues.append("Migration mode requires legacy support to be enabled")
        
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
            "mode": self.mode.value,
            "enable_legacy_support": self.enable_legacy_support,
            "legacy_deprecation_warnings": self.legacy_deprecation_warnings,
            "legacy_usage_tracking": self.legacy_usage_tracking,
            "enable_tool_caching": self.enable_tool_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "max_concurrent_executions": self.max_concurrent_executions,
            "migration_mode": self.migration_mode,
            "migration_log_file": self.migration_log_file,
            "migration_dry_run": self.migration_dry_run,
            "enable_ai_orchestration": self.enable_ai_orchestration,
            "enable_quality_gates": self.enable_quality_gates,
            "enable_advanced_analytics": self.enable_advanced_analytics,
            "enable_workflow_orchestration": self.enable_workflow_orchestration,
            "tool_timeouts": self.tool_timeouts,
            "environment_overrides": self.environment_overrides
        }


class ToolMigrationManager:
    """Manages the migration from legacy to consolidated tools."""
    
    def __init__(self, config: ToolConfiguration):
        self.config = config
        self.migration_stats = {
            "legacy_calls": 0,
            "consolidated_calls": 0,
            "migration_warnings": 0,
            "failed_migrations": 0,
            "tool_usage": {}
        }
    
    def log_tool_usage(self, tool_name: str, is_legacy: bool, success: bool) -> None:
        """Log tool usage for migration tracking."""
        if not self.config.legacy_usage_tracking:
            return
        
        # Update stats
        if is_legacy:
            self.migration_stats["legacy_calls"] += 1
        else:
            self.migration_stats["consolidated_calls"] += 1
        
        if not success:
            self.migration_stats["failed_migrations"] += 1
        
        # Track individual tool usage
        if tool_name not in self.migration_stats["tool_usage"]:
            self.migration_stats["tool_usage"][tool_name] = {
                "legacy_calls": 0,
                "consolidated_calls": 0,
                "failures": 0
            }
        
        tool_stats = self.migration_stats["tool_usage"][tool_name]
        if is_legacy:
            tool_stats["legacy_calls"] += 1
        else:
            tool_stats["consolidated_calls"] += 1
        
        if not success:
            tool_stats["failures"] += 1
        
        # Log to file if configured
        if self.config.migration_log_file:
            self._log_to_file(tool_name, is_legacy, success)
    
    def _log_to_file(self, tool_name: str, is_legacy: bool, success: bool) -> None:
        """Log migration event to file."""
        try:
            import json
            from datetime import datetime
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "tool_name": tool_name,
                "is_legacy": is_legacy,
                "success": success,
                "mode": self.config.mode.value
            }
            
            with open(self.config.migration_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to log migration event: {e}")
    
    def get_migration_report(self) -> Dict[str, Any]:
        """Generate migration progress report."""
        total_calls = self.migration_stats["legacy_calls"] + self.migration_stats["consolidated_calls"]
        
        if total_calls == 0:
            migration_progress = 0
        else:
            migration_progress = (self.migration_stats["consolidated_calls"] / total_calls) * 100
        
        return {
            "migration_progress_percentage": round(migration_progress, 2),
            "total_calls": total_calls,
            "legacy_calls": self.migration_stats["legacy_calls"],
            "consolidated_calls": self.migration_stats["consolidated_calls"],
            "failed_migrations": self.migration_stats["failed_migrations"],
            "success_rate": round((total_calls - self.migration_stats["failed_migrations"]) / max(total_calls, 1) * 100, 2),
            "tool_usage": self.migration_stats["tool_usage"],
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate migration recommendations based on usage patterns."""
        recommendations = []
        
        total_calls = self.migration_stats["legacy_calls"] + self.migration_stats["consolidated_calls"]
        
        if total_calls == 0:
            return ["No tool usage detected yet"]
        
        legacy_percentage = (self.migration_stats["legacy_calls"] / total_calls) * 100
        
        if legacy_percentage > 80:
            recommendations.append("High legacy tool usage detected. Consider migration training.")
        elif legacy_percentage > 50:
            recommendations.append("Moderate legacy tool usage. Migration is progressing.")
        elif legacy_percentage > 20:
            recommendations.append("Good migration progress. Consider disabling legacy warnings.")
        else:
            recommendations.append("Excellent migration progress. Consider disabling legacy support.")
        
        # Check for problematic tools
        for tool_name, stats in self.migration_stats["tool_usage"].items():
            tool_total = stats["legacy_calls"] + stats["consolidated_calls"]
            if tool_total > 0:
                failure_rate = (stats["failures"] / tool_total) * 100
                if failure_rate > 20:
                    recommendations.append(f"High failure rate for {tool_name} ({failure_rate:.1f}%). Check implementation.")
        
        return recommendations


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


# Convenience functions for common configurations
def get_production_config() -> ToolConfiguration:
    """Get production-ready configuration."""
    return ToolConfiguration(
        mode=ToolMode.CONSOLIDATED,
        enable_legacy_support=False,
        legacy_deprecation_warnings=False,
        legacy_usage_tracking=False,
        enable_tool_caching=True,
        migration_mode=False
    )


def get_migration_config() -> ToolConfiguration:
    """Get configuration for migration period."""
    return ToolConfiguration(
        mode=ToolMode.MINIMAL,
        enable_legacy_support=True,
        legacy_deprecation_warnings=True,
        legacy_usage_tracking=True,
        migration_mode=True,
        migration_log_file="./logs/tool_migration.log"
    )


def get_development_config() -> ToolConfiguration:
    """Get configuration for development."""
    return ToolConfiguration(
        mode=ToolMode.FULL,
        enable_legacy_support=True,
        legacy_deprecation_warnings=True,
        legacy_usage_tracking=True,
        enable_tool_caching=False,  # Disable caching for development
        migration_mode=False
    )