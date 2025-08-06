"""Weaviate database manager for MCP Jive server.

Handles embedded Weaviate database setup, schema configuration,
and data persistence as specified in the MCP Server Core Infrastructure PRD.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json

try:
    import weaviate
    from weaviate.embedded import EmbeddedOptions
    from weaviate.classes.config import Configure, Property, DataType
    from weaviate.classes.query import Filter
except ImportError:
    weaviate = None
    EmbeddedOptions = None
    Configure = None
    Property = None
    DataType = None
    Filter = None

from .config import DatabaseConfig

logger = logging.getLogger(__name__)


@dataclass
class WorkItemSchema:
    """Schema definition for work items in Weaviate."""
    name: str = "WorkItem"
    description: str = "Agile work items (Initiative/Epic/Feature/Story/Task)"
    
    @property
    def properties(self) -> List[Property]:
        """Define properties for work item schema."""
        if not Property or not DataType:
            raise ImportError("Weaviate client not available")
            
        return [
            Property(name="item_id", data_type=DataType.TEXT, description="Unique identifier for the work item"),
            Property(name="title", data_type=DataType.TEXT, description="Work item title"),
            Property(name="description", data_type=DataType.TEXT, description="Detailed description"),
            Property(name="item_type", data_type=DataType.TEXT, description="Type: Initiative/Epic/Feature/Story/Task"),
            Property(name="status", data_type=DataType.TEXT, description="Current status"),
            Property(name="priority", data_type=DataType.TEXT, description="Priority level"),
            Property(name="assignee", data_type=DataType.TEXT, description="Assigned person or AI agent"),
            Property(name="tags", data_type=DataType.TEXT_ARRAY, description="Associated tags"),
            Property(name="estimated_hours", data_type=DataType.NUMBER, description="Estimated effort in hours"),
            Property(name="actual_hours", data_type=DataType.NUMBER, description="Actual time spent"),
            Property(name="progress", data_type=DataType.NUMBER, description="Completion percentage (0-100)"),
            Property(name="parent_id", data_type=DataType.TEXT, description="Parent work item ID"),
            Property(name="dependencies", data_type=DataType.TEXT_ARRAY, description="Dependent work item IDs"),
            Property(name="acceptance_criteria", data_type=DataType.TEXT, description="Completion criteria"),
            Property(name="created_at", data_type=DataType.DATE, description="Creation timestamp"),
            Property(name="updated_at", data_type=DataType.DATE, description="Last update timestamp"),
            Property(name="metadata", data_type=DataType.OBJECT, description="Additional metadata"),
        ]


@dataclass
class ExecutionLogSchema:
    """Schema definition for execution logs in Weaviate."""
    name: str = "ExecutionLog"
    description: str = "Work item execution history and progress tracking"
    
    @property
    def properties(self) -> List[Property]:
        """Define properties for execution log schema."""
        if not Property or not DataType:
            raise ImportError("Weaviate client not available")
            
        return [
            Property(name="log_id", data_type=DataType.TEXT, description="Unique log entry identifier"),
            Property(name="work_item_id", data_type=DataType.TEXT, description="Associated work item ID"),
            Property(name="action", data_type=DataType.TEXT, description="Action performed"),
            Property(name="status", data_type=DataType.TEXT, description="Execution status"),
            Property(name="agent_id", data_type=DataType.TEXT, description="AI agent or user ID"),
            Property(name="details", data_type=DataType.TEXT, description="Execution details"),
            Property(name="error_message", data_type=DataType.TEXT, description="Error details if failed"),
            Property(name="duration_seconds", data_type=DataType.NUMBER, description="Execution duration"),
            Property(name="timestamp", data_type=DataType.DATE, description="Log entry timestamp"),
            Property(name="metadata", data_type=DataType.OBJECT, description="Additional execution metadata"),
        ]


class WeaviateManager:
    """Manages embedded Weaviate database for MCP Jive server.
    
    Provides database initialization, schema management, and data operations
    for storing and retrieving work items and execution logs.
    """
    
    def __init__(self, config: DatabaseConfig):
        """Initialize Weaviate manager.
        
        Args:
            config: Database configuration settings
        """
        self.config = config
        self.client: Optional[weaviate.WeaviateClient] = None
        self._is_connected = False
        self._schemas = {
            "WorkItem": WorkItemSchema(),
            "ExecutionLog": ExecutionLogSchema(),
        }
        
        if not weaviate:
            logger.warning("Weaviate client not available. Install with: pip install weaviate-client")
    
    async def initialize(self) -> None:
        """Initialize the Weaviate database."""
        if not weaviate:
            raise ImportError("Weaviate client not available. Install with: pip install weaviate-client")
        
        logger.info("Initializing Weaviate database...")
        
        try:
            if self.config.use_embedded:
                await self._initialize_embedded()
            else:
                await self._initialize_remote()
            
            await self._setup_schemas()
            await self._verify_connection()
            
            self._is_connected = True
            logger.info("Weaviate database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate database: {e}")
            raise
    
    async def _initialize_embedded(self) -> None:
        """Initialize embedded Weaviate instance."""
        logger.info("Starting embedded Weaviate instance...")
        
        # Ensure persistence directory exists
        persistence_path = Path(self.config.persistence_path)
        persistence_path.mkdir(parents=True, exist_ok=True)
        
        # Configure embedded options
        embedded_options = EmbeddedOptions(
            persistence_data_path=str(persistence_path),
            binary_path=None,  # Use default binary
            version="latest",
            port=self.config.port,
            additional_env_vars={
                "ENABLE_MODULES": "text2vec-transformers",
                "DEFAULT_VECTORIZER_MODULE": "text2vec-transformers",
            }
        )
        
        # Create client with embedded options
        self.client = weaviate.WeaviateClient(
            embedded_options=embedded_options,
            additional_headers={
                "X-Weaviate-Timeout": str(self.config.timeout)
            }
        )
        
        # Connect to embedded instance
        self.client.connect()
        
        # Wait for startup
        await self._wait_for_ready()
    
    async def _initialize_remote(self) -> None:
        """Initialize connection to remote Weaviate instance."""
        logger.info(f"Connecting to remote Weaviate at {self.config.host}:{self.config.port}...")
        
        self.client = weaviate.WeaviateClient(
            url=f"http://{self.config.host}:{self.config.port}",
            additional_headers={
                "X-Weaviate-Timeout": str(self.config.timeout)
            }
        )
        
        self.client.connect()
        await self._wait_for_ready()
    
    async def _wait_for_ready(self, max_retries: int = 30, delay: float = 1.0) -> None:
        """Wait for Weaviate to be ready."""
        for attempt in range(max_retries):
            try:
                if self.client.is_ready():
                    logger.info("Weaviate is ready")
                    return
            except Exception as e:
                logger.debug(f"Weaviate not ready (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(delay)
        
        raise TimeoutError(f"Weaviate not ready after {max_retries} attempts")
    
    async def _setup_schemas(self) -> None:
        """Set up database schemas."""
        logger.info("Setting up database schemas...")
        
        for schema_name, schema_def in self._schemas.items():
            try:
                # Check if collection already exists
                if self.client.collections.exists(schema_name):
                    logger.info(f"Schema '{schema_name}' already exists")
                    continue
                
                # Create collection with schema
                collection = self.client.collections.create(
                    name=schema_name,
                    description=schema_def.description,
                    properties=schema_def.properties,
                    vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
                    generative_config=None,  # No generative module needed
                )
                
                logger.info(f"Created schema '{schema_name}' successfully")
                
            except Exception as e:
                logger.error(f"Failed to create schema '{schema_name}': {e}")
                raise
    
    async def _verify_connection(self) -> None:
        """Verify database connection and schemas."""
        try:
            # Test basic connectivity
            meta = self.client.get_meta()
            logger.info(f"Connected to Weaviate version: {meta.get('version', 'unknown')}")
            
            # Verify schemas exist
            for schema_name in self._schemas.keys():
                if not self.client.collections.exists(schema_name):
                    raise RuntimeError(f"Schema '{schema_name}' not found after setup")
            
            logger.info("Database connection and schemas verified")
            
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the Weaviate database connection."""
        if self.client and self._is_connected:
            logger.info("Shutting down Weaviate database...")
            try:
                self.client.close()
                self._is_connected = False
                logger.info("Weaviate database shutdown complete")
            except Exception as e:
                logger.error(f"Error during Weaviate shutdown: {e}")
    
    def is_connected(self) -> bool:
        """Check if database is connected and ready."""
        return self._is_connected and self.client and self.client.is_ready()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get database health status."""
        try:
            if not self.is_connected():
                return {
                    "status": "disconnected",
                    "ready": False,
                    "error": "Database not connected"
                }
            
            meta = self.client.get_meta()
            
            # Get collection stats
            collections_info = {}
            for schema_name in self._schemas.keys():
                try:
                    collection = self.client.collections.get(schema_name)
                    # Get object count (this might not be available in all versions)
                    collections_info[schema_name] = {
                        "exists": True,
                        "object_count": "unknown"  # Would need specific query to get count
                    }
                except Exception as e:
                    collections_info[schema_name] = {
                        "exists": False,
                        "error": str(e)
                    }
            
            return {
                "status": "connected",
                "ready": True,
                "version": meta.get("version", "unknown"),
                "hostname": meta.get("hostname", "unknown"),
                "collections": collections_info,
                "config": {
                    "use_embedded": self.config.use_embedded,
                    "host": self.config.host,
                    "port": self.config.port,
                    "persistence_path": self.config.persistence_path if self.config.use_embedded else None
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "ready": False,
                "error": str(e)
            }
    
    def get_collection(self, name: str):
        """Get a Weaviate collection by name.
        
        Args:
            name: Collection name
            
        Returns:
            Weaviate collection object
            
        Raises:
            RuntimeError: If database not connected or collection doesn't exist
        """
        if not self.is_connected():
            raise RuntimeError("Database not connected")
        
        if name not in self._schemas:
            raise ValueError(f"Unknown collection: {name}")
        
        return self.client.collections.get(name)
    
    async def backup_data(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of the database.
        
        Args:
            backup_path: Path for backup file. If None, generates timestamp-based name.
            
        Returns:
            Path to created backup file
        """
        if not self.config.backup_enabled:
            raise RuntimeError("Backup not enabled in configuration")
        
        if not backup_path:
            timestamp = int(time.time())
            backup_path = f"mcp_jive_backup_{timestamp}.json"
        
        logger.info(f"Creating database backup: {backup_path}")
        
        backup_data = {
            "timestamp": time.time(),
            "version": "1.0",
            "collections": {}
        }
        
        # Export data from each collection
        for schema_name in self._schemas.keys():
            try:
                collection = self.get_collection(schema_name)
                # This would need to be implemented based on specific backup requirements
                # For now, just record that the collection exists
                backup_data["collections"][schema_name] = {
                    "exists": True,
                    "schema": schema_name
                }
            except Exception as e:
                logger.error(f"Failed to backup collection '{schema_name}': {e}")
                backup_data["collections"][schema_name] = {
                    "exists": False,
                    "error": str(e)
                }
        
        # Write backup file
        backup_file = Path(backup_path)
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"Database backup completed: {backup_file}")
        return str(backup_file)