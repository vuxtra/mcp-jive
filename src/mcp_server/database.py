"""Weaviate database management for MCP Jive Server.

Handles embedded Weaviate database operations, schema management,
and data persistence for the MCP server infrastructure.
"""

import logging
import time
import subprocess
import signal
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
import weaviate
from weaviate.classes.config import Configure
from weaviate.classes.init import Auth

from .config import ServerConfig

logger = logging.getLogger(__name__)


class WeaviateManager:
    """Manages embedded Weaviate database instance."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.client: Optional[weaviate.WeaviateClient] = None
        self.process: Optional[subprocess.Popen] = None
        self._is_embedded = True
        
    async def start(self) -> None:
        """Start the embedded Weaviate instance."""
        logger.info("Starting embedded Weaviate database...")
        
        try:
            # Check if Weaviate is already running
            if await self._is_weaviate_running():
                logger.info("Weaviate is already running, connecting to existing instance")
                self._is_embedded = False
            else:
                await self._start_embedded_weaviate()
                
            # Connect to Weaviate
            await self._connect()
            
            # Initialize schema
            await self._initialize_schema()
            
            logger.info("Weaviate database started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Weaviate: {e}")
            raise
            
    async def stop(self) -> None:
        """Stop the embedded Weaviate instance."""
        logger.info("Stopping Weaviate database...")
        
        try:
            if self.client:
                self.client.close()
                self.client = None
                
            if self.process and self._is_embedded:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("Weaviate process did not terminate gracefully, killing...")
                    self.process.kill()
                    self.process.wait()
                    
                self.process = None
                
            logger.info("Weaviate database stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Weaviate: {e}")
            
    async def _start_embedded_weaviate(self) -> None:
        """Start embedded Weaviate process."""
        # Ensure data directory exists
        data_path = Path(self.config.weaviate_data_path)
        data_path.mkdir(parents=True, exist_ok=True)
        
        # Weaviate configuration
        env = os.environ.copy()
        env.update({
            "PERSISTENCE_DATA_PATH": str(data_path),
            "DEFAULT_VECTORIZER_MODULE": "none",
            "ENABLE_MODULES": "text2vec-openai,text2vec-cohere,text2vec-huggingface",
            "CLUSTER_HOSTNAME": "node1",
            "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
            "AUTHORIZATION_ADMINLIST_ENABLED": "false",
        })
        
        # Start Weaviate process
        cmd = [
            "weaviate",
            "--host", self.config.weaviate_host,
            "--port", str(self.config.weaviate_port),
            "--scheme", "http"
        ]
        
        try:
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Wait for Weaviate to start
            await self._wait_for_weaviate()
            
        except FileNotFoundError:
            logger.error("Weaviate binary not found. Please install Weaviate.")
            raise
        except Exception as e:
            logger.error(f"Failed to start Weaviate process: {e}")
            raise
            
    async def _wait_for_weaviate(self, timeout: int = 60) -> None:
        """Wait for Weaviate to become available."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self._is_weaviate_running():
                logger.info("Weaviate is ready")
                return
                
            await asyncio.sleep(1)
            
        raise TimeoutError(f"Weaviate did not start within {timeout} seconds")
        
    async def _is_weaviate_running(self) -> bool:
        """Check if Weaviate is running and accessible."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.weaviate_url}/v1/.well-known/ready",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
            
    async def _connect(self) -> None:
        """Connect to Weaviate instance."""
        try:
            self.client = weaviate.connect_to_local(
                host=self.config.weaviate_host,
                port=self.config.weaviate_port,
                grpc_port=self.config.weaviate_grpc_port
            )
            
            # Test connection
            if not self.client.is_ready():
                raise ConnectionError("Weaviate client is not ready")
                
            logger.info(f"Connected to Weaviate at {self.config.weaviate_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise
            
    async def _initialize_schema(self) -> None:
        """Initialize Weaviate schema for MCP data."""
        try:
            # Define collections for MCP data
            collections = [
                {
                    "name": "Task",
                    "description": "MCP task items with hierarchical relationships",
                    "properties": [
                        {"name": "title", "dataType": ["text"]},
                        {"name": "description", "dataType": ["text"]},
                        {"name": "status", "dataType": ["text"]},
                        {"name": "priority", "dataType": ["text"]},
                        {"name": "created_at", "dataType": ["date"]},
                        {"name": "updated_at", "dataType": ["date"]},
                        {"name": "metadata", "dataType": ["object"]},
                    ]
                },
                {
                    "name": "WorkItem",
                    "description": "Work items in hierarchical structure",
                    "properties": [
                        {"name": "type", "dataType": ["text"]},
                        {"name": "title", "dataType": ["text"]},
                        {"name": "content", "dataType": ["text"]},
                        {"name": "status", "dataType": ["text"]},
                        {"name": "parent_id", "dataType": ["text"]},
                        {"name": "dependencies", "dataType": ["text[]"]},
                        {"name": "created_at", "dataType": ["date"]},
                        {"name": "metadata", "dataType": ["object"]},
                    ]
                },
                {
                    "name": "SearchIndex",
                    "description": "Search index for MCP content",
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "source_type", "dataType": ["text"]},
                        {"name": "source_id", "dataType": ["text"]},
                        {"name": "tags", "dataType": ["text[]"]},
                        {"name": "indexed_at", "dataType": ["date"]},
                    ]
                }
            ]
            
            # Create collections if they don't exist
            for collection_config in collections:
                collection_name = collection_config["name"]
                
                if not self.client.collections.exists(collection_name):
                    logger.info(f"Creating collection: {collection_name}")
                    
                    # Convert to Weaviate v4 format
                    properties = []
                    for prop in collection_config["properties"]:
                        if prop["dataType"] == ["text"]:
                            properties.append(Configure.Property(name=prop["name"], data_type=Configure.DataType.TEXT))
                        elif prop["dataType"] == ["date"]:
                            properties.append(Configure.Property(name=prop["name"], data_type=Configure.DataType.DATE))
                        elif prop["dataType"] == ["object"]:
                            properties.append(Configure.Property(name=prop["name"], data_type=Configure.DataType.OBJECT))
                        elif prop["dataType"] == ["text[]"]:
                            properties.append(Configure.Property(name=prop["name"], data_type=Configure.DataType.TEXT_ARRAY))
                    
                    self.client.collections.create(
                        name=collection_name,
                        description=collection_config["description"],
                        properties=properties
                    )
                else:
                    logger.info(f"Collection {collection_name} already exists")
                    
            logger.info("Weaviate schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate schema: {e}")
            raise
            
    def get_collection(self, name: str):
        """Get a Weaviate collection by name."""
        if not self.client:
            raise RuntimeError("Weaviate client not connected")
            
        return self.client.collections.get(name)
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Weaviate."""
        try:
            if not self.client or not self.client.is_ready():
                return {
                    "status": "unhealthy",
                    "error": "Client not connected or not ready"
                }
                
            # Get cluster status
            cluster_status = self.client.cluster.get_nodes_status()
            
            return {
                "status": "healthy",
                "url": self.config.weaviate_url,
                "cluster_status": cluster_status,
                "collections": list(self.client.collections.list_all().keys())
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Import asyncio at the end to avoid circular imports
import asyncio