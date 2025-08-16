"""Configuration settings for MCP Jive tools."""

from typing import Dict, Any
import os


class ToolConfig:
    """Configuration class for MCP Jive tools with adjustable limits and settings."""
    
    # Default validation limits
    DEFAULT_VALIDATION_LIMITS = {
        "context_tags_max_items": 10,
        "acceptance_criteria_max_items": 15,
        "notes_max_length": 2000,
        "description_max_length": 5000,
        "title_max_length": 200,
        "search_results_max_limit": 100,
        "hierarchy_max_depth": 10
    }
    
    # Response formatting settings
    DEFAULT_RESPONSE_SETTINGS = {
        "max_response_size": 50000,
        "truncation_threshold": 45000,
        "enable_auto_truncation": True,
        "preserve_essential_fields": True,
        "max_array_items_in_response": 50,
        "max_description_length_in_response": 1000
    }
    
    # Execution settings
    DEFAULT_EXECUTION_SETTINGS = {
        "max_parallel_executions": 5,
        "execution_timeout_minutes": 60,
        "enable_detailed_error_messages": True,
        "enable_execution_suggestions": True,
        "auto_cleanup_completed_executions": True,
        "max_execution_history": 100
    }
    
    def __init__(self, config_overrides: Dict[str, Any] = None):
        """Initialize configuration with optional overrides."""
        self.validation_limits = self.DEFAULT_VALIDATION_LIMITS.copy()
        self.response_settings = self.DEFAULT_RESPONSE_SETTINGS.copy()
        self.execution_settings = self.DEFAULT_EXECUTION_SETTINGS.copy()
        
        # Apply environment variable overrides
        self._load_from_environment()
        
        # Apply provided overrides
        if config_overrides:
            self._apply_overrides(config_overrides)
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # Validation limits from environment
        env_mappings = {
            "MCP_JIVE_CONTEXT_TAGS_MAX": ("validation_limits", "context_tags_max_items"),
            "MCP_JIVE_ACCEPTANCE_CRITERIA_MAX": ("validation_limits", "acceptance_criteria_max_items"),
            "MCP_JIVE_NOTES_MAX_LENGTH": ("validation_limits", "notes_max_length"),
            "MCP_JIVE_DESCRIPTION_MAX_LENGTH": ("validation_limits", "description_max_length"),
            "MCP_JIVE_MAX_RESPONSE_SIZE": ("response_settings", "max_response_size"),
            "MCP_JIVE_TRUNCATION_THRESHOLD": ("response_settings", "truncation_threshold"),
            "MCP_JIVE_ENABLE_AUTO_TRUNCATION": ("response_settings", "enable_auto_truncation"),
            "MCP_JIVE_MAX_PARALLEL_EXECUTIONS": ("execution_settings", "max_parallel_executions"),
            "MCP_JIVE_EXECUTION_TIMEOUT": ("execution_settings", "execution_timeout_minutes")
        }
        
        for env_var, (config_section, config_key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    # Convert to appropriate type
                    if config_key.endswith("_max_items") or config_key.endswith("_length") or config_key.endswith("_size") or config_key.endswith("_minutes") or config_key.endswith("_executions"):
                        value = int(value)
                    elif config_key.startswith("enable_"):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    
                    # Apply to appropriate config section
                    if config_section == "validation_limits":
                        self.validation_limits[config_key] = value
                    elif config_section == "response_settings":
                        self.response_settings[config_key] = value
                    elif config_section == "execution_settings":
                        self.execution_settings[config_key] = value
                        
                except (ValueError, TypeError):
                    # Ignore invalid environment values
                    pass
    
    def _apply_overrides(self, overrides: Dict[str, Any]):
        """Apply configuration overrides."""
        for key, value in overrides.items():
            if key in self.validation_limits:
                self.validation_limits[key] = value
            elif key in self.response_settings:
                self.response_settings[key] = value
            elif key in self.execution_settings:
                self.execution_settings[key] = value
    
    def get_validation_limit(self, limit_name: str) -> Any:
        """Get a validation limit by name."""
        return self.validation_limits.get(limit_name)
    
    def get_response_setting(self, setting_name: str) -> Any:
        """Get a response setting by name."""
        return self.response_settings.get(setting_name)
    
    def get_execution_setting(self, setting_name: str) -> Any:
        """Get an execution setting by name."""
        return self.execution_settings.get(setting_name)
    
    def update_validation_limit(self, limit_name: str, value: Any):
        """Update a validation limit."""
        if limit_name in self.validation_limits:
            self.validation_limits[limit_name] = value
    
    def update_response_setting(self, setting_name: str, value: Any):
        """Update a response setting."""
        if setting_name in self.response_settings:
            self.response_settings[setting_name] = value
    
    def update_execution_setting(self, setting_name: str, value: Any):
        """Update an execution setting."""
        if setting_name in self.execution_settings:
            self.execution_settings[setting_name] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "validation_limits": self.validation_limits,
            "response_settings": self.response_settings,
            "execution_settings": self.execution_settings
        }
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"ToolConfig(validation_limits={self.validation_limits}, response_settings={self.response_settings}, execution_settings={self.execution_settings})"


# Global configuration instance
_global_config = None


def get_config() -> ToolConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = ToolConfig()
    return _global_config


def set_config(config: ToolConfig):
    """Set the global configuration instance."""
    global _global_config
    _global_config = config


def reset_config():
    """Reset configuration to defaults."""
    global _global_config
    _global_config = ToolConfig()