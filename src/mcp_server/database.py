"""Weaviate database management for MCP Jive Server.

Handles embedded Weaviate database operations, schema management,
and data persistence for the MCP server infrastructure.
"""

import logging
from .error_utils import ErrorHandler, DatabaseError, with_database_retry

import time
import functools
from typing import Callable, Any

def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry database operations on connection errors."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Check if it's a connection-related error
                    if any(keyword in error_msg for keyword in [
                        'connection refused', 'connection failed', 'unavailable',
                        'timeout', 'grpc', 'network', 'unreachable'
                    ]):
                        if attempt < max_retries - 1:
                            wait_time = delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # Re-raise non-connection errors immediately
                    raise e
                    
            # If all retries failed, raise the last exception
            raise last_exception
        return wrapper
    return decorator
import time
import subprocess
import signal
import os
import asyncio
from typing import Optional, Dict, Any, List

import uuid
from typing import Optional

def validate_uuid(uuid_string: str) -> bool:
    """Validate if a string is a valid UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False

def ensure_valid_uuid(uuid_string: str) -> str:
    """Ensure a string is a valid UUID, generate one if not."""
    if validate_uuid(uuid_string):
        return uuid_string
    return str(uuid.uuid4())
from pathlib import Path
import weaviate
from weaviate.embedded import EmbeddedOptions
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.init import Auth

# SSL certificate handling
try:
    import certifi
    # Set SSL certificate file for proper certificate verification
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
except ImportError:
    logger.warning("certifi package not found. SSL certificate verification may fail.")

from .config import ServerConfig

logger = logging.getLogger(__name__)


class WeaviateManager:
    """Manages embedded Weaviate database instance."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.client: Optional[weaviate.WeaviateClient] = None
        self.process: Optional[subprocess.Popen] = None
        self._is_embedded = True
    def generate_object_id(self) -> str:
        """Generate a new UUID for database objects.
        
        Returns:
            New UUID string
        """
        from .uuid_utils import generate_uuid
        return generate_uuid()
        
    def validate_object_id(self, object_id: str, field_name: str = "id") -> str:
        """Validate an object ID.
        
        Args:
            object_id: ID to validate
            field_name: Field name for error messages
            
        Returns:
            Validated ID
            
        Raises:
            ValueError: If ID is invalid
        """
        from .uuid_utils import validate_uuid
        return validate_uuid(object_id, field_name)

        
    async def start(self) -> None:
        """Start the embedded Weaviate instance."""
        try:
            logger.info("Starting embedded Weaviate database...")
            
            # Check configuration for embedded vs external
            if self.config.weaviate_embedded:
                # Always start embedded Weaviate (it will handle existing instances)
                await self._start_embedded_weaviate()
            else:
                logger.info("Using external Weaviate instance")
                self._is_embedded = False
                
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
        try:
            logger.info("Stopping Weaviate database...")
            
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
        """Start embedded Weaviate instance using the embedded client."""
        try:
            # Ensure data directory exists
            data_path = Path(self.config.weaviate_data_path)
            data_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Starting embedded Weaviate with data path: {data_path}")
            
            # First check if Weaviate is already running on our embedded ports
            if await self._is_weaviate_running():
                logger.info("Embedded Weaviate is already running, connecting to existing instance")
                # Connect to existing embedded instance
                self.client = weaviate.connect_to_local(
                    host="127.0.0.1",
                    port=8082,
                    grpc_port=50061
                )
                self._is_embedded = True
                logger.info("Connected to existing embedded Weaviate instance")
                return
            
            # Configure embedded options with minimal modules to avoid SSL issues
            embedded_options = EmbeddedOptions(
                persistence_data_path=str(data_path),
                version="1.25.0",  # Use specific stable version instead of "latest"
                port=8082,  # Use different port to avoid conflicts
                grpc_port=50061,  # Use different GRPC port
                hostname="127.0.0.1",
                additional_env_vars={
                    "ENABLE_MODULES": self.config.weaviate_vectorizer_module if self.config.weaviate_enable_vectorizer else "",
                    "DEFAULT_VECTORIZER_MODULE": self.config.weaviate_vectorizer_module if self.config.weaviate_enable_vectorizer else "none",
                    "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
                    "AUTHORIZATION_ADMINLIST_ENABLED": "false",
                    "PERSISTENCE_DATA_PATH": str(data_path)
                }
            )
            
            # Create client with embedded options
            self.client = weaviate.WeaviateClient(
                embedded_options=embedded_options,
                additional_headers={
                    "X-Weaviate-Timeout": "60"
                }
            )
            
            # Connect to embedded instance
            self.client.connect()
            logger.info("Embedded Weaviate client connected successfully")
            
            # Wait for Weaviate to be fully ready
            await self._wait_for_weaviate(timeout=60)
            
        except Exception as e:
            logger.error(f"Failed to start embedded Weaviate: {e}")
            raise
            
    async def _wait_for_weaviate(self, timeout: int = 60) -> None:
        """Wait for Weaviate to become available."""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if await self._is_weaviate_running():
                    logger.info("Weaviate is ready")
                    return
                    
                await asyncio.sleep(1)
                
            raise TimeoutError(f"Weaviate did not start within {timeout} seconds")
        except Exception as e:
            logger.error(f"Error waiting for Weaviate: {e}")
            raise
        
    async def _is_weaviate_running(self) -> bool:
        """Check if Weaviate is running and accessible."""
        try:
            import aiohttp
            # Use port 8082 for embedded Weaviate
            weaviate_url = "http://127.0.0.1:8082" if self.config.weaviate_embedded else self.config.weaviate_url
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{weaviate_url}/v1/.well-known/ready",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
            
    async def _connect(self) -> None:
        """Connect to Weaviate instance."""
        try:
            # If client is already created (e.g., by embedded setup), skip connection
            if self.client is not None:
                logger.info("Using existing Weaviate client connection")
                return
                
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
                        {"name": "metadata", "dataType": ["text"]},
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
                        {"name": "metadata", "dataType": ["text"]},
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
                            properties.append(Property(name=prop["name"], data_type=DataType.TEXT))
                        elif prop["dataType"] == ["date"]:
                            properties.append(Property(name=prop["name"], data_type=DataType.DATE))
                        elif prop["dataType"] == ["text[]"]:
                            properties.append(Property(name=prop["name"], data_type=DataType.TEXT_ARRAY))
                    
                    # Configure vectorizer settings
                    vectorizer_config = None
                    if self.config.weaviate_enable_vectorizer:
                        if self.config.weaviate_vectorizer_module == "text2vec-transformers":
                            from weaviate.classes.config import Configure
                            vectorizer_config = Configure.Vectorizer.text2vec_transformers()
                        elif self.config.weaviate_vectorizer_module == "text2vec-openai":
                            from weaviate.classes.config import Configure
                            vectorizer_config = Configure.Vectorizer.text2vec_openai()
                    
                    # Create collection with vectorizer configuration
                    if vectorizer_config:
                        self.client.collections.create(
                            name=collection_name,
                            description=collection_config["description"],
                            properties=properties,
                            vectorizer_config=vectorizer_config
                        )
                    else:
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
        
    async def get_client(self):
        """Get the Weaviate client instance."""
        try:
            if not self.client:
                raise RuntimeError("Weaviate client not connected")
                
            return self.client
        except Exception as e:
            logger.error(f"Error getting Weaviate client: {e}")
            raise
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Weaviate."""
        try:
            if not self.client or not self.client.is_ready():
                return {
                    "status": "unhealthy",
                    "error": "Client not connected or not ready"
                }
                
            # Get basic cluster info (simplified for compatibility)
            try:
                collections = list(self.client.collections.list_all().keys())
                cluster_ready = self.client.is_ready()
            except Exception as cluster_error:
                logger.warning(f"Could not get cluster details: {cluster_error}")
                collections = []
                cluster_ready = False
            
            return {
                "status": "healthy" if cluster_ready else "degraded",
                "url": self.config.weaviate_url,
                "cluster_ready": cluster_ready,
                "collections": collections,
                "collection_count": len(collections)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
            
    async def store_work_item(self, work_item_data: Dict[str, Any]) -> str:
        """Store a work item in Weaviate."""
        try:
            from uuid import UUID
            collection = self.get_collection("WorkItem")
            
            # Convert string ID to UUID object
            work_item_id = work_item_data["id"]
            uuid_obj = UUID(work_item_id) if isinstance(work_item_id, str) else work_item_id
            
            # Remove 'id' from properties since it's a reserved field in Weaviate
            # We pass it separately as the uuid parameter
            properties = {k: v for k, v in work_item_data.items() if k != "id"}
            
            # Log the properties being sent to Weaviate
            logger.info(f"Properties being sent to Weaviate: {properties}")
            logger.info(f"Metadata type: {type(properties.get('metadata', 'N/A'))}")
            logger.info(f"Metadata value: {properties.get('metadata', 'N/A')}")
            
            # Insert the work item
            result = collection.data.insert(
                properties=properties,
                uuid=uuid_obj
            )
            
            logger.info(f"Stored work item {work_item_id}")
            return work_item_id
            
        except Exception as e:
            logger.error(f"Error storing work item: {e}")
            raise
            
    async def get_work_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a work item by ID."""
        try:
            collection = self.get_collection("WorkItem")
            
            # Get the work item by UUID
            result = collection.query.fetch_object_by_id(work_item_id)
            
            if result:
                return result.properties
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving work item {work_item_id}: {e}")
            return None
            
    async def update_work_item(self, work_item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a work item in Weaviate."""
        try:
            collection = self.get_collection("WorkItem")
            
            # Update the work item
            collection.data.update(
                uuid=work_item_id,
                properties=updates
            )
            
            # Return the updated work item
            return await self.get_work_item(work_item_id)
            
        except Exception as e:
            logger.error(f"Error updating work item {work_item_id}: {e}")
            return None
            
    async def list_work_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List work items with filtering and pagination."""
        try:
            collection = self.get_collection("WorkItem")
            
            # Build query
            query = collection.query.fetch_objects(
                limit=limit,
                offset=offset
            )
            
            # Apply filters if provided
            if filters:
                # This is a simplified implementation
                # In a real implementation, you'd build proper Weaviate filters
                pass
                
            results = []
            for obj in query.objects:
                results.append(obj.properties)
                
            return results
            
        except Exception as e:
            logger.error(f"Error listing work items: {e}")
            return []
            
    async def search_work_items(
        self,
        query: str,
        search_type: str = "semantic",
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search work items using semantic or keyword search with automatic fallback."""
        try:
            collection = self.get_collection("WorkItem")
            
            # Try semantic search first if requested
            if search_type == "semantic":
                try:
                    # Semantic search using vector similarity
                    results = collection.query.near_text(
                        query=query,
                        limit=limit
                    )
                    
                    # Check if we got results
                    if results.objects:
                        search_results = []
                        for obj in results.objects:
                            # Include UUID in work_item data
                            work_item_data = obj.properties.copy()
                            work_item_data["id"] = str(obj.uuid)
                            
                            # Convert datetime objects to ISO strings for JSON serialization
                            for key, value in work_item_data.items():
                                if hasattr(value, 'isoformat'):
                                    work_item_data[key] = value.isoformat()
                                elif value is not None and str(type(value)) == "<class 'datetime.datetime'>":
                                    work_item_data[key] = str(value)
                            
                            search_results.append({
                                "work_item": work_item_data,
                                "relevance_score": getattr(obj.metadata, 'score', 0.0),
                                "match_highlights": []
                            })
                        logger.info(f"Semantic search returned {len(search_results)} results")
                        return search_results
                    else:
                        logger.warning("Semantic search returned 0 results")
                        # Fall through to keyword search if enabled
                        
                except Exception as semantic_error:
                    logger.warning(f"Semantic search failed: {semantic_error}")
                    # Fall through to keyword search if enabled
                    
                # Automatic fallback to keyword search if enabled and semantic failed/empty
                if self.config.weaviate_search_fallback:
                    logger.info("Falling back to keyword search")
                    search_type = "keyword"
                else:
                    # No fallback enabled, return empty results
                    return []
            
            # Keyword search (either requested directly or as fallback)
            if search_type == "keyword":
                results = collection.query.bm25(
                    query=query,
                    limit=limit
                )
                
                search_results = []
                for obj in results.objects:
                    # Include UUID in work_item data
                    work_item_data = obj.properties.copy()
                    work_item_data["id"] = str(obj.uuid)
                    
                    # Convert datetime objects to ISO strings for JSON serialization
                    for key, value in work_item_data.items():
                        if hasattr(value, 'isoformat'):
                            work_item_data[key] = value.isoformat()
                        elif value is not None and str(type(value)) == "<class 'datetime.datetime'>":
                            work_item_data[key] = str(value)
                    
                    search_results.append({
                        "work_item": work_item_data,
                        "relevance_score": getattr(obj.metadata, 'score', 0.0),
                        "match_highlights": []
                    })
                    
                logger.info(f"Keyword search returned {len(search_results)} results")
                return search_results
                
            return []
            
        except Exception as e:
            logger.error(f"Error searching work items: {e}")
            return []
            
    async def get_work_item_children(self, work_item_id: str) -> List[Dict[str, Any]]:
        """Get child work items for a given parent work item."""
        try:
            collection = self.get_collection("WorkItem")
            
            # Fetch all work items and filter in Python
            # This is more reliable than complex Weaviate queries
            result = collection.query.fetch_objects(
                limit=1000  # Reasonable limit for work items
            )
            
            children = []
            for obj in result.objects:
                # Check if this item has the specified parent_id
                if obj.properties.get("parent_id") == work_item_id:
                    child_data = obj.properties.copy()
                    child_data["id"] = str(obj.uuid)  # Add the UUID as id
                    
                    # Convert datetime objects to ISO strings for JSON serialization
                    for key, value in child_data.items():
                        if hasattr(value, 'isoformat'):
                            child_data[key] = value.isoformat()
                        elif value is not None and str(type(value)) == "<class 'datetime.datetime'>":
                            child_data[key] = str(value)
                    
                    children.append(child_data)
                    
            return children
            
        except Exception as e:
            logger.error(f"Error getting work item children: {e}")
            return []
            
    async def get_work_item_dependencies(self, work_item_id: str) -> List[Dict[str, Any]]:
        """Get all dependencies for a work item."""
        try:
            # First get the work item to access its dependencies list
            work_item = await self.get_work_item(work_item_id)
            if not work_item or "dependencies" not in work_item:
                return []
                
            dependencies = []
            for dep_id in work_item["dependencies"]:
                dep_item = await self.get_work_item(dep_id)
                if dep_item:
                    dependencies.append(dep_item)
                    
            return dependencies
            
        except Exception as e:
            logger.error(f"Error getting work item dependencies: {e}")
            return []


# Import asyncio at the end to avoid circular imports
import asyncio