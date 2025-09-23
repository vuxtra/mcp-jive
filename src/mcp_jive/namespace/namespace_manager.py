"""Namespace Manager for MCP-Jive server.

Provides namespace isolation capabilities with complete data separation
between different projects while maintaining backward compatibility.
"""

import os
import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class NamespaceValidationError(Exception):
    """Exception raised for namespace validation errors."""
    pass


@dataclass
class NamespaceConfig:
    """Configuration for namespace management."""
    base_path: str = "./data/lancedb_jive"
    default_namespace: str = "default"
    max_namespaces: int = 100
    namespace_pattern: str = r"^[a-zA-Z0-9_-]+$"
    reserved_names: Set[str] = field(default_factory=lambda: {"admin", "system", "config", "temp", "backup"})
    auto_create_namespaces: bool = True
    namespace_dir: Optional[str] = None
    min_namespace_length: int = 1
    max_namespace_length: int = 50


class NamespaceManager:
    """Manages namespace isolation and directory structure.
    
    Provides complete data separation between different projects/namespaces
    while maintaining backward compatibility with existing MCP clients.
    """
    
    # Reserved namespace names that cannot be used
    RESERVED_NAMES: Set[str] = {
        "admin", "system", "config", "api", "health", "status",
        "backup", "restore", "migration", "temp", "tmp", "cache"
    }
    
    # Valid namespace name pattern (alphanumeric, hyphens, underscores)
    NAMESPACE_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$')
    
    def __init__(self, config: Optional[NamespaceConfig] = None):
        """Initialize the namespace manager.
        
        Args:
            config: Namespace configuration. Uses defaults if not provided.
        """
        self.config = config or NamespaceConfig()
        self._base_data_dir = self._determine_base_data_dir()
        self._namespaces_dir = self._base_data_dir / "namespaces"
        
        # Ensure namespaces directory exists
        self._namespaces_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"NamespaceManager initialized with base dir: {self._base_data_dir}")
    
    def _determine_base_data_dir(self) -> Path:
        """Determine the base data directory for namespaces.
        
        Returns:
            Path to the base data directory.
        """
        if self.config.namespace_dir:
            return Path(self.config.namespace_dir)
        
        # Check environment variable
        env_dir = os.getenv("MCP_JIVE_NAMESPACE_DIR")
        if env_dir:
            return Path(env_dir)
        
        # Default to data directory in project root
        return Path("data")
    
    def resolve_namespace(self, request_namespace: Optional[str] = None) -> str:
        """Resolve the namespace to use based on priority hierarchy.
        
        Priority order:
        1. Request-level namespace (from MCP request metadata)
        2. Environment variable (MCP_JIVE_NAMESPACE)
        3. Default namespace
        
        Args:
            request_namespace: Namespace specified in the request.
            
        Returns:
            The resolved namespace name.
            
        Raises:
            NamespaceValidationError: If the resolved namespace is invalid.
        """
        namespace = None
        
        # 1. Request-level namespace (highest priority)
        if request_namespace:
            namespace = request_namespace.strip()
            logger.debug(f"Using request-level namespace: {namespace}")
        
        # 2. Environment variable
        if not namespace:
            env_namespace = os.getenv("MCP_JIVE_NAMESPACE")
            if env_namespace:
                namespace = env_namespace.strip()
                logger.debug(f"Using environment namespace: {namespace}")
        
        # 3. Default namespace
        if not namespace:
            namespace = self.config.default_namespace
            logger.debug(f"Using default namespace: {namespace}")
        
        # Validate the resolved namespace
        self.validate_namespace(namespace)
        
        return namespace
    
    def validate_namespace(self, namespace: str) -> bool:
        """Validate a namespace name.
        
        Args:
            namespace: The namespace name to validate.
            
        Returns:
            True if valid.
            
        Raises:
            NamespaceValidationError: If the namespace is invalid.
        """
        if not namespace:
            raise NamespaceValidationError("Namespace cannot be empty")
        
        # Check length
        if len(namespace) < self.config.min_namespace_length:
            raise NamespaceValidationError(
                f"Namespace must be at least {self.config.min_namespace_length} characters"
            )
        
        if len(namespace) > self.config.max_namespace_length:
            raise NamespaceValidationError(
                f"Namespace must be at most {self.config.max_namespace_length} characters"
            )
        
        # Check reserved names
        if namespace.lower() in self.RESERVED_NAMES:
            raise NamespaceValidationError(
                f"Namespace '{namespace}' is reserved and cannot be used"
            )
        
        # Check pattern (alphanumeric, hyphens, underscores only)
        if not self.NAMESPACE_PATTERN.match(namespace):
            raise NamespaceValidationError(
                f"Namespace '{namespace}' contains invalid characters. "
                "Only alphanumeric characters, hyphens, and underscores are allowed."
            )
        
        return True
    
    def get_namespace_path(self, namespace: str) -> Path:
        """Get the full path for a namespace's data directory.
        
        Args:
            namespace: The namespace name.
            
        Returns:
            Path to the namespace's data directory.
        """
        self.validate_namespace(namespace)
        return self._namespaces_dir / namespace
    
    def create_namespace(self, namespace: str) -> bool:
        """Create a new namespace directory structure.
        
        Args:
            namespace: The namespace name to create.
            
        Returns:
            True if created successfully, False if already exists.
            
        Raises:
            NamespaceValidationError: If the namespace name is invalid.
        """
        self.validate_namespace(namespace)
        
        namespace_path = self.get_namespace_path(namespace)
        
        if namespace_path.exists():
            logger.info(f"Namespace '{namespace}' already exists at {namespace_path}")
            return False
        
        try:
            # Create namespace directory
            namespace_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for LanceDB tables
            (namespace_path / "work_items").mkdir(exist_ok=True)
            (namespace_path / "executions").mkdir(exist_ok=True)
            (namespace_path / "progress").mkdir(exist_ok=True)
            
            # Create namespace metadata file
            metadata_file = namespace_path / ".namespace_metadata"
            metadata_content = f"""# Namespace Metadata
namespace: {namespace}
created_at: {self._get_current_timestamp()}
version: 1.0
"""
            metadata_file.write_text(metadata_content)
            
            logger.info(f"Created namespace '{namespace}' at {namespace_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create namespace '{namespace}': {e}")
            raise
    
    def list_namespaces(self) -> List[str]:
        """List all available namespaces.
        
        Returns:
            List of namespace names, always including the default namespace.
        """
        namespaces = set()
        
        # Always include the default namespace
        namespaces.add(self.config.default_namespace)
        
        # Add existing namespace directories
        if self._namespaces_dir.exists():
            for item in self._namespaces_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    try:
                        # Validate namespace name
                        self.validate_namespace(item.name)
                        namespaces.add(item.name)
                    except NamespaceValidationError:
                        logger.warning(f"Skipping invalid namespace directory: {item.name}")
        
        return sorted(list(namespaces))
    
    def namespace_exists(self, namespace: str) -> bool:
        """Check if a namespace exists.
        
        Args:
            namespace: The namespace name to check.
            
        Returns:
            True if the namespace exists.
        """
        try:
            namespace_path = self.get_namespace_path(namespace)
            return namespace_path.exists() and namespace_path.is_dir()
        except NamespaceValidationError:
            return False
    
    def ensure_namespace_exists(self, namespace: str) -> bool:
        """Ensure a namespace exists, creating it if necessary.
        
        Args:
            namespace: The namespace name.
            
        Returns:
            True if namespace exists or was created successfully.
        """
        if self.namespace_exists(namespace):
            return True
        
        if self.config.auto_create_namespaces:
            try:
                self.create_namespace(namespace)
                return True
            except Exception as e:
                logger.error(f"Failed to auto-create namespace '{namespace}': {e}")
                return False
        
        return False
    
    def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace and all its data.
        
        Args:
            namespace: The namespace name to delete.
            
        Returns:
            True if deleted successfully, False if namespace doesn't exist.
            
        Raises:
            NamespaceValidationError: If the namespace name is invalid.
            ValueError: If trying to delete the default namespace.
        """
        self.validate_namespace(namespace)
        
        # Prevent deletion of default namespace
        if namespace == self.config.default_namespace:
            raise ValueError(f"Cannot delete default namespace '{namespace}'")
        
        namespace_path = self.get_namespace_path(namespace)
        
        if not namespace_path.exists():
            logger.info(f"Namespace '{namespace}' does not exist")
            return False
        
        try:
            # Remove the entire namespace directory
            shutil.rmtree(namespace_path)
            logger.info(f"Deleted namespace '{namespace}' at {namespace_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete namespace '{namespace}': {e}")
            raise
    
    def migrate_default_data(self) -> bool:
        """Migrate existing data to the default namespace.
        
        This method handles the migration of existing LanceDB data
        from the old structure to the new namespace structure.
        
        Returns:
            True if migration was successful or not needed.
        """
        old_data_dir = self._base_data_dir / "lancedb"
        default_namespace_dir = self.get_namespace_path(self.config.default_namespace)
        
        # Check if old data exists and default namespace doesn't
        if not old_data_dir.exists():
            logger.info("No old data to migrate")
            return True
        
        if default_namespace_dir.exists():
            logger.info("Default namespace already exists, skipping migration")
            return True
        
        try:
            logger.info(f"Migrating data from {old_data_dir} to {default_namespace_dir}")
            
            # Create default namespace
            self.create_namespace(self.config.default_namespace)
            
            # Move old data to default namespace
            import shutil
            for item in old_data_dir.iterdir():
                if item.is_dir():
                    dest = default_namespace_dir / item.name
                    if not dest.exists():
                        shutil.move(str(item), str(dest))
                        logger.info(f"Moved {item.name} to default namespace")
            
            # Create backup of old directory
            backup_dir = self._base_data_dir / f"lancedb.backup.{self._get_current_timestamp()}"
            if old_data_dir.exists():
                shutil.move(str(old_data_dir), str(backup_dir))
                logger.info(f"Created backup at {backup_dir}")
            
            logger.info("Data migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate data: {e}")
            return False
    
    def get_namespace_stats(self, namespace: str) -> dict:
        """Get statistics for a namespace.
        
        Args:
            namespace: The namespace name.
            
        Returns:
            Dictionary containing namespace statistics.
        """
        if not self.namespace_exists(namespace):
            return {"exists": False}
        
        namespace_path = self.get_namespace_path(namespace)
        
        stats = {
            "exists": True,
            "path": str(namespace_path),
            "tables": {},
            "total_size_bytes": 0
        }
        
        # Check each table directory
        for table_name in ["work_items", "executions", "progress"]:
            table_path = namespace_path / table_name
            if table_path.exists():
                size = sum(f.stat().st_size for f in table_path.rglob('*') if f.is_file())
                stats["tables"][table_name] = {
                    "exists": True,
                    "size_bytes": size
                }
                stats["total_size_bytes"] += size
            else:
                stats["tables"][table_name] = {"exists": False, "size_bytes": 0}
        
        return stats
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string.
        
        Returns:
            ISO format timestamp string.
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def __str__(self) -> str:
        """String representation of the namespace manager."""
        return f"NamespaceManager(base_dir={self._base_data_dir}, namespaces={len(self.list_namespaces())})"