#!/usr/bin/env python3
"""
LanceDB Manager for MCP Jive

This module provides the LanceDB database manager for the MCP Jive component,
replacing the Weaviate implementation with a true embedded vector database.

Features:
- True embedded operation (no external services)
- Built-in vectorization with sentence-transformers
- High-performance vector and keyword search
- Automatic schema management
- Async/await support
- Simplified configuration
"""

import asyncio
import os
import logging
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

# Suppress Pydantic warning for ColPaliEmbeddings model_name field
warnings.filterwarnings(
    "ignore", 
    message="Field \"model_name\" in ColPaliEmbeddings has conflict with protected namespace \"model_\".",
    category=UserWarning
)

try:
    import lancedb
    from lancedb.embeddings import SentenceTransformerEmbeddings
    from lancedb.pydantic import LanceModel, Vector
    import pandas as pd
    import pyarrow as pa
except ImportError as e:
    raise ImportError(
        f"LanceDB dependencies not installed: {e}\n"
        "Install with: pip install lancedb sentence-transformers pyarrow pandas"
    )

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SearchType(Enum):
    """Search type enumeration."""
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"

@dataclass
class DatabaseConfig:
    """Configuration for LanceDB database."""
    data_path: str = "./data/lancedb_jive"
    namespace: Optional[str] = None  # Namespace for multi-tenant support
    embedding_model: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    normalize_embeddings: bool = True
    vector_dimension: int = 384
    batch_size: int = 100
    timeout: int = 30
    enable_fts: bool = True  # Full-text search
    max_retries: int = 3
    retry_delay: float = 1.0

# Pydantic Models for LanceDB Tables (MCP Jive specific)

class WorkItemModel(LanceModel):
    """Work item data model for MCP Jive."""
    id: str = Field(description="Unique work item identifier")
    item_id: str = Field(description="Work item ID (may differ from primary id)")
    title: str = Field(description="Work item title")
    description: str = Field(description="Detailed description")
    vector: Vector(384) = Field(description="Embedding vector")
    item_type: str = Field(description="Type: Initiative/Epic/Feature/Story/Task")
    status: str = Field(description="Current status")
    priority: str = Field(description="Priority level")
    assignee: Optional[str] = Field(description="Assigned person or AI agent", default=None)
    tags: List[str] = Field(description="Associated tags", default_factory=list)
    estimated_hours: Optional[float] = Field(description="Estimated effort", default=None)
    actual_hours: Optional[float] = Field(description="Actual time spent", default=None)
    progress: float = Field(description="Completion percentage (0-100)", default=0.0)
    parent_id: Optional[str] = Field(description="Parent work item ID", default=None)
    dependencies: List[str] = Field(description="Dependent work item IDs", default_factory=list)
    
    # Ordering and sequencing
    sequence_number: Optional[str] = Field(description="Hierarchical sequence number (e.g., '1.1', '1.2', '2.1')", default=None)
    order_index: int = Field(description="Numeric order within parent for sorting", default=0)
    
    # AI Optimization Parameters
    context_tags: List[str] = Field(description="Technical context tags for AI categorization", default_factory=list)
    complexity: Optional[str] = Field(description="Implementation complexity: simple, moderate, complex", default=None)
    notes: Optional[str] = Field(description="Implementation notes, constraints, or context for AI agent", default=None)
    acceptance_criteria: List[str] = Field(description="Clear, testable criteria for AI agents to validate completion", default_factory=list)
    executable: bool = Field(description="Can be executed by the system", default=False)
    execution_instructions: Optional[str] = Field(description="Instructions for execution", default=None)
    created_at: datetime = Field(description="Creation timestamp", default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(description="Last update timestamp", default_factory=lambda: datetime.now(timezone.utc))
    metadata: str = Field(description="Additional metadata (JSON string)", default="{}")

class ExecutionLogModel(LanceModel):
    """Execution log data model for MCP Jive."""
    id: str = Field(description="Unique log identifier")
    log_id: str = Field(description="Log entry ID")
    work_item_id: Optional[str] = Field(description="Associated work item ID", default=None)
    action: str = Field(description="Action performed")
    status: str = Field(description="Execution status")
    agent_id: Optional[str] = Field(description="AI agent identifier", default=None)
    details: str = Field(description="Execution details", default="")
    error_message: Optional[str] = Field(description="Error message if failed", default=None)
    duration_seconds: float = Field(description="Execution duration", default=0.0)
    timestamp: datetime = Field(description="Execution timestamp", default_factory=lambda: datetime.now(timezone.utc))
    metadata: str = Field(description="Additional metadata (JSON string)", default="{}")

class ArchitectureMemoryModel(LanceModel):
    """Architecture Memory data model for MCP Jive."""
    id: str = Field(description="Unique identifier")
    unique_slug: str = Field(description="Unique short slug for identification")
    title: str = Field(description="Human-friendly short name")
    ai_when_to_use: List[str] = Field(description="AI-friendly instructions for when to apply", default_factory=list)
    ai_requirements: str = Field(description="AI-friendly detailed specifications (Markdown)")
    vector: Vector(384) = Field(description="Embedding vector for semantic search")
    keywords: List[str] = Field(description="Keywords that describe this architecture item", default_factory=list)
    children_slugs: List[str] = Field(description="Child architecture item slugs", default_factory=list)
    related_slugs: List[str] = Field(description="Related architecture item slugs", default_factory=list)
    linked_epic_ids: List[str] = Field(description="Epic work item IDs that reference this", default_factory=list)
    tags: List[str] = Field(description="Tags for categorization", default_factory=list)
    created_on: datetime = Field(description="Creation timestamp", default_factory=lambda: datetime.now(timezone.utc))
    last_updated_on: datetime = Field(description="Last update timestamp", default_factory=lambda: datetime.now(timezone.utc))
    metadata: str = Field(description="Additional metadata (JSON string)", default="{}")

class TroubleshootMemoryModel(LanceModel):
    """Troubleshoot Memory data model for MCP Jive."""
    id: str = Field(description="Unique identifier")
    unique_slug: str = Field(description="Unique short slug for identification")
    title: str = Field(description="Human-friendly short name")
    ai_use_case: List[str] = Field(description="AI-friendly problem descriptions", default_factory=list)
    ai_solutions: str = Field(description="AI-friendly solution with tips and steps (Markdown)")
    vector: Vector(384) = Field(description="Embedding vector for semantic search")
    keywords: List[str] = Field(description="Keywords that describe this troubleshooting item", default_factory=list)
    tags: List[str] = Field(description="Tags for categorization", default_factory=list)
    usage_count: int = Field(description="Number of times retrieved", default=0)
    success_count: int = Field(description="Number of times marked as successful", default=0)
    created_on: datetime = Field(description="Creation timestamp", default_factory=lambda: datetime.now(timezone.utc))
    last_updated_on: datetime = Field(description="Last update timestamp", default_factory=lambda: datetime.now(timezone.utc))
    metadata: str = Field(description="Additional metadata (JSON string)", default="{}")

class LanceDBManager:
    """LanceDB database manager for MCP Jive."""
    
    def __init__(self, config: DatabaseConfig, namespace: Optional[str] = None):
        self.config = config
        # Override namespace if provided directly
        if namespace is not None:
            self.config.namespace = namespace

        # Calculate namespace-aware database path
        self.namespace = self.config.namespace or "default"
        self.db_path = self._get_namespace_path()
        
        self.db = None
        self.embedding_func = None
        self._initialized = False
        self._tables_initialized = False
        self._tables = {}
        
        # Table model mapping for MCP Jive
        self.table_models = {
            'WorkItem': WorkItemModel,
            'ExecutionLog': ExecutionLogModel,
            'ArchitectureMemory': ArchitectureMemoryModel,
            'TroubleshootMemory': TroubleshootMemoryModel
        }
    
    def _get_namespace_path(self) -> str:
        """Get the namespace-specific database path."""
        base_path = Path(self.config.data_path)
        if self.namespace == "default":
            return str(base_path)
        else:
            return str(base_path / "namespaces" / self.namespace)
    
    def get_namespace(self) -> str:
        """Get the current namespace."""
        return self.namespace
    
    def get_database_path(self) -> str:
        """Get the current database path."""
        return self.db_path
    
    async def initialize(self) -> None:
        """Initialize LanceDB connection and embedding function."""
        if self._initialized:
            return
        
        try:
            # Create namespace-specific data directory
            os.makedirs(self.db_path, exist_ok=True)
            
            # Connect to LanceDB with namespace-specific path
            self.db = lancedb.connect(self.db_path)
            
            # Initialize embedding function lazily (defer model loading)
            self.embedding_func = None
            self._embedding_config = {
                'model_name': self.config.embedding_model,
                'device': self.config.device,
                'normalize': self.config.normalize_embeddings
            }
            
            # Defer table initialization until first use (lazy loading)
            # This prevents blocking during MCP handshake
            self._tables_initialized = False
            
            self._initialized = True
            logger.info(f"✅ MCP Jive LanceDB initialized at {self.db_path} (namespace: {self.namespace}, tables and embedding model will load on first use)")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP Jive LanceDB: {e}")
            raise
    
    async def _initialize_tables(self) -> None:
        """Initialize all required tables with proper schemas."""
        # Ensure basic initialization happened first
        if not self._initialized or self.db is None:
            await self.initialize()

        if self._tables_initialized:
            return
            
        logger.info("🔧 Initializing LanceDB tables...")
        
        for table_name, model_class in self.table_models.items():
            try:
                # Check if table exists
                existing_tables = self.db.table_names()
                if table_name not in existing_tables:
                    logger.info(f"📋 Creating table: {table_name}")
                    
                    # Create table with schema
                    try:
                        self.db.create_table(table_name, schema=model_class)
                    except Exception as e:
                        logger.warning(f"⚠️ Primary table creation failed for {table_name}: {e}")
                        # Fallback: create with sample data that matches schema
                        try:
                            if table_name == "WorkItem":
                                sample_data = {
                                    'id': 'temp_id',
                                    'item_id': 'temp_id', 
                                    'title': 'temp',
                                    'description': 'temp',
                                    'vector': [0.0] * 384,
                                    'item_type': 'Task',
                                    'status': 'Draft',
                                    'priority': 'Medium',
                                    'assignee': None,
                                    'tags': [],
                                    'estimated_hours': None,
                                    'actual_hours': None,
                                    'progress': 0.0,
                                    'parent_id': None,
                                    'dependencies': [],
                                    'sequence_number': None,
                                    'order_index': 0,
                                    'context_tags': [],
                                    'complexity': None,
                                    'notes': None,
                                    'acceptance_criteria': [],
                                    'executable': False,
                                    'execution_instructions': None,
                                    'created_at': datetime.now(timezone.utc),
                                    'updated_at': datetime.now(timezone.utc),
                                    'metadata': '{}'
                                }
                            else:  # ExecutionLog
                                sample_data = {
                                    'id': 'temp_id',
                                    'log_id': 'temp_id',
                                    'work_item_id': None,
                                    'action': 'temp',
                                    'status': 'temp',
                                    'agent_id': None,
                                    'details': '',
                                    'error_message': None,
                                    'duration_seconds': 0.0,
                                    'timestamp': datetime.now(timezone.utc),
                                    'metadata': '{}'
                                }
                            
                            sample_df = pd.DataFrame([sample_data])
                            table = self.db.create_table(table_name, data=sample_df)
                            # Remove the temporary record
                            table.delete("id = 'temp_id'")
                            logger.info(f"✅ Table {table_name} created with fallback method")
                        except Exception as fallback_error:
                            logger.error(f"❌ Fallback table creation also failed for {table_name}: {fallback_error}")
                            raise
                    
                    logger.info(f"✅ Table {table_name} created successfully")
                else:
                    logger.info(f"📋 Table {table_name} already exists")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize table {table_name}: {e}")
                raise
        
        self._tables_initialized = True
    
    async def _create_fts_indexes(self) -> None:
        """Create full-text search indexes for text fields."""
        try:
            logger.info("🔍 Preparing full-text search index configurations...")
            
            # Define FTS index configurations for each table
            self.fts_configs = {
                'WorkItem': ['title', 'description', 'acceptance_criteria', 'status', 'priority', 'item_type'],
                'ExecutionLog': ['action', 'details', 'error_message', 'status']
            }
            
            # Store FTS configuration for later use
            logger.info("✅ FTS configurations prepared (indexes will be created when data is available)")
            
        except Exception as e:
            logger.error(f"❌ Failed to prepare FTS configurations: {e}")
            # Don't raise - FTS is optional functionality
    
    async def _ensure_fts_index(self, table_name: str) -> None:
        """Ensure FTS index exists for a table with data."""
        if not self.config.enable_fts or not hasattr(self, 'fts_configs'):
            return
            
        try:
            table = self.db.open_table(table_name)
            row_count = table.count_rows()
            
            # Only create FTS index if table has data
            if row_count > 0 and table_name in self.fts_configs:
                text_fields = self.fts_configs[table_name]
                
                try:
                    # Check if FTS index already exists by trying a simple search
                    table.search("test", query_type="fts").limit(1).to_pandas()
                    # If no exception, index exists
                    logger.debug(f"✅ FTS index already exists for {table_name}")
                except Exception:
                    # Index doesn't exist or is broken, create it
                    logger.info(f"🔍 Creating FTS index for {table_name} with {row_count} rows...")
                    
                    table.create_fts_index(
                        text_fields,
                        replace=True,  # Replace if exists
                        use_tantivy=True,  # Use modern Tantivy implementation
                        with_position=True,  # Enable phrase queries
                        base_tokenizer="simple",  # Split by whitespace and punctuation
                        language="English",
                        lower_case=True,  # Case-insensitive search
                        stem=True,  # Enable stemming
                        remove_stop_words=True,  # Remove common words
                        ascii_folding=True  # Handle accented characters
                    )
                    logger.info(f"✅ Created FTS index for {table_name} fields: {text_fields}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to ensure FTS index for {table_name}: {e}")
    
    async def _ensure_embedding_func(self) -> None:
        """Ensure embedding function is initialized (lazy loading)."""
        if self.embedding_func is None:
            logger.info(f"🤖 Loading embedding model: {self._embedding_config['model_name']}...")
            try:
                self.embedding_func = SentenceTransformerEmbeddings(
                    model_name=self._embedding_config['model_name'],
                    device=self._embedding_config['device'],
                    normalize=self._embedding_config['normalize']
                )
                logger.info(f"✅ Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                raise
    
    async def _ensure_tables_initialized(self) -> None:
        """Ensure tables are initialized (lazy loading)."""
        if not self._tables_initialized:
            await self._initialize_tables()
            if self.config.enable_fts:
                await self._create_fts_indexes()
    
    async def warm_up_embedding_model(self) -> None:
        """Pre-warm the embedding model for better performance."""
        try:
            logger.info("🔥 Pre-warming embedding model...")
            await self._ensure_embedding_func()
            # Generate a test embedding to fully initialize the model
            test_text = "test embedding initialization"
            _ = self._generate_embedding(test_text)
            logger.info("✅ Embedding model pre-warmed successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to pre-warm embedding model: {e}")
    
    def _generate_embedding(self, text_content: str) -> List[float]:
        """Generate embedding for text content."""
        try:
            # Ensure embedding function is loaded
            if self.embedding_func is None:
                # Run async initialization in sync context
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If we're in an async context, we need to handle this differently
                        logger.warning("Embedding function not initialized - using zero vector")
                        return [0.0] * self.config.vector_dimension
                    else:
                        loop.run_until_complete(self._ensure_embedding_func())
                except RuntimeError:
                    # No event loop running
                    asyncio.run(self._ensure_embedding_func())
            
            if not text_content or not text_content.strip():
                # Return zero vector for empty content
                return [0.0] * self.config.vector_dimension
            
            embeddings = self.embedding_func.compute_query_embeddings([text_content])
            embedding = embeddings[0]
            
            # Convert to list if needed
            if isinstance(embedding, list):
                return embedding
            elif hasattr(embedding, 'tolist'):
                return embedding.tolist()
            else:
                return list(embedding)
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.config.vector_dimension
    
    async def generate_embedding(self, text_content: str) -> List[float]:
        """Public method to generate embedding for text content."""
        # Ensure embedding function is loaded
        await self._ensure_embedding_func()
        return self._generate_embedding(text_content)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Public method to generate embeddings for multiple texts."""
        # Ensure embedding function is loaded
        await self._ensure_embedding_func()
        return [self._generate_embedding(text) for text in texts]
    
    def _convert_numpy_to_python(self, work_item_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert numpy arrays and scalars to Python native types."""
        import numpy as np
        
        # List fields that should be converted from numpy arrays to Python lists
        list_fields = ['dependencies', 'tags', 'context_tags', 'acceptance_criteria']
        
        # Fields that should be excluded from serialization (like vector embeddings)
        exclude_fields = ['vector']
        
        # Remove vector field to avoid serialization issues
        for field in exclude_fields:
            if field in work_item_dict:
                del work_item_dict[field]
        
        # Convert all numpy types to Python types
        converted_dict = {}
        for key, value in work_item_dict.items():
            try:
                # Handle numpy arrays first (before checking pd.isna to avoid array ambiguity)
                if isinstance(value, np.ndarray):
                    if key in list_fields:
                        converted_dict[key] = value.tolist()
                    elif value.size == 1:
                        converted_dict[key] = value.item()
                    else:
                        converted_dict[key] = value.tolist()
                # Handle numpy scalars
                elif hasattr(value, 'item') and hasattr(value, 'dtype'):
                    converted_dict[key] = value.item()
                # Handle pandas NA/NaN values (only for scalar values, not arrays)
                elif not isinstance(value, (list, np.ndarray)) and hasattr(pd, 'isna'):
                    try:
                        if pd.isna(value):
                            if key in list_fields:
                                converted_dict[key] = []
                            else:
                                converted_dict[key] = None
                        else:
                            converted_dict[key] = value
                    except (ValueError, TypeError):
                        # If pd.isna fails, just use the original value
                        converted_dict[key] = value
                # Handle regular Python types
                else:
                    converted_dict[key] = value
            except (ValueError, TypeError, AttributeError) as e:
                # If conversion fails, try to handle gracefully
                logger.warning(f"Failed to convert field {key} with value {value}: {e}")
                if key in list_fields:
                    converted_dict[key] = []
                else:
                    converted_dict[key] = None
        
        return converted_dict
    
    async def _retry_operation(self, operation, *args, **kwargs):
        """Retry database operations with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Call the operation and check if result is a coroutine
                result = operation(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    return await result
                else:
                    return result
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"⚠️ Operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Operation failed after {self.config.max_retries} attempts: {e}")
        
        raise last_exception
    
    async def get_collection(self, collection_name: str):
        """Get a LanceDB table (compatibility method)."""
        if not self._initialized:
            await self.initialize()

        await self._ensure_tables_initialized()

        try:
            return self.db.open_table(collection_name)
        except Exception as e:
            logger.error(f"❌ Failed to get collection {collection_name}: {e}")
            raise
    
    async def get_table(self, table_name: str):
        """Get a LanceDB table."""
        await self._ensure_tables_initialized()
        return await self.get_collection(table_name)
    
    async def create_work_item(self, work_item_data: Dict[str, Any]) -> str:
        """Create a new work item with automatic vectorization."""
        try:
            # Generate text content for embedding
            text_content = f"{work_item_data.get('title', '')} {work_item_data.get('description', '')}"
            
            # Convert data for WorkItemModel compatibility
            model_data = work_item_data.copy()
            
            # Ensure item_id is set
            if 'item_id' not in model_data:
                model_data['item_id'] = model_data.get('id', '')
            
            # Convert 'type' to 'item_type' if present
            if 'type' in model_data:
                model_data['item_type'] = model_data.pop('type')
            
            # Ensure acceptance_criteria is a list (WorkItemModel expects List[str])
            if 'acceptance_criteria' in model_data and model_data['acceptance_criteria'] is None:
                model_data['acceptance_criteria'] = []
            
            # Create work item with embedding
            work_item = WorkItemModel(
                **model_data,
                vector=self._generate_embedding(text_content)
            )
            
            # Insert into table
            table = await self.get_table("WorkItem")
            # Use model_dump() instead of deprecated dict() method
            work_item_dict = work_item.model_dump() if hasattr(work_item, 'model_dump') else work_item.dict()
            logger.info(f"Work item dict keys before insertion: {list(work_item_dict.keys())}")
            logger.info(f"Work item dict has item_id: {'item_id' in work_item_dict}")
            await self._retry_operation(table.add, [work_item_dict])
            
            logger.info(f"✅ Created MCP Jive work item: {work_item.id}")
            return work_item.id
            
        except Exception as e:
            logger.error(f"❌ Failed to create MCP Jive work item: {e}")
            raise
    
    async def store_work_item(self, work_item_data: Dict[str, Any]) -> str:
        """Store a work item (compatibility method for create_work_item)."""
        try:
            result = await self.create_work_item(work_item_data)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to store MCP Jive work item: {e}")
            raise
    
    async def update_work_item(self, work_item_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing work item."""
        try:
            table = await self.get_table("WorkItem")
            
            # Get existing item
            existing = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            
            if len(existing) == 0:
                # Try searching by item_id as fallback
                existing = table.search().where(f"item_id = '{work_item_id}'").limit(1).to_pandas()
                
                if len(existing) == 0:
                    logger.warning(f"⚠️ MCP Jive work item {work_item_id} not found")
                    return False
            
            # Update fields
            updated_data = existing.iloc[0].to_dict()
            updated_data.update(updates)
            updated_data['updated_at'] = datetime.now(timezone.utc)
            
            # Regenerate embedding if title or description changed
            if 'title' in updates or 'description' in updates:
                text_content = f"{updated_data.get('title', '')} {updated_data.get('description', '')}"
                updated_data['vector'] = self._generate_embedding(text_content)
            
            # Delete old record and insert updated one
            actual_id = updated_data['id']
            table.delete(f"id = '{actual_id}'")
            await self._retry_operation(table.add, [updated_data])
            
            # Add a small delay to ensure the database operation is committed
            await asyncio.sleep(0.1)
            
            # Verify the update was successful by checking if the record exists
            verification = table.search().where(f"id = '{actual_id}'").limit(1).to_pandas()
            if len(verification) == 0:
                logger.error(f"❌ Failed to verify update for work item {work_item_id}")
                return False
            
            logger.info(f"✅ Updated MCP Jive work item: {work_item_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update MCP Jive work item {work_item_id}: {e}")
            raise
    
    async def get_work_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get a work item by ID or item_id."""
        try:
            table = await self.get_table("WorkItem")
            
            # Try by primary id first
            result = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            
            if len(result) == 0:
                # Try by item_id as fallback
                result = table.search().where(f"item_id = '{work_item_id}'").limit(1).to_pandas()
            
            if len(result) == 0:
                return None
            
            # Convert to dict and handle numpy arrays
            work_item_dict = result.iloc[0].to_dict()
            return self._convert_numpy_to_python(work_item_dict)
            
        except Exception as e:
            logger.error(f"❌ Failed to get MCP Jive work item {work_item_id}: {e}")
            raise
    
    async def delete_work_item(self, work_item_id: str) -> bool:
        """Delete a work item."""
        try:
            table = await self.get_table("WorkItem")
            
            # Check if item exists by id
            existing = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            
            if len(existing) == 0:
                # Try by item_id
                existing = table.search().where(f"item_id = '{work_item_id}'").limit(1).to_pandas()
                
                if len(existing) == 0:
                    logger.warning(f"⚠️ MCP Jive work item {work_item_id} not found")
                    return False
                
                # Use the actual id for deletion
                actual_id = existing.iloc[0]['id']
                table.delete(f"id = '{actual_id}'")
            else:
                # Delete by id
                table.delete(f"id = '{work_item_id}'")
            
            logger.info(f"✅ Deleted MCP Jive work item: {work_item_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete MCP Jive work item {work_item_id}: {e}")
            raise
    
    async def search_work_items(
        self, 
        query: str, 
        search_type: Union[SearchType, str] = SearchType.VECTOR,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search work items with various search types."""
        try:
            # Convert string search types to enum
            if isinstance(search_type, str):
                search_type_mapping = {
                    "semantic": SearchType.VECTOR,
                    "vector": SearchType.VECTOR,
                    "keyword": SearchType.KEYWORD,
                    "hybrid": SearchType.HYBRID
                }
                if search_type not in search_type_mapping:
                    raise ValueError(f"Unknown search type: {search_type}. Valid types: semantic, vector, keyword, hybrid")
                search_type = search_type_mapping[search_type]
            
            # Ensure FTS index exists if needed
            if search_type in [SearchType.KEYWORD, SearchType.HYBRID]:
                await self._ensure_fts_index("WorkItem")
            
            table = await self.get_table("WorkItem")
            
            if search_type == SearchType.VECTOR:
                # Vector similarity search - generate embedding from query text
                query_embedding = self._generate_embedding(query)
                search_query = table.search(query_embedding).limit(limit)
                
            elif search_type == SearchType.KEYWORD:
                # Full-text search (if available)
                if self.config.enable_fts:
                    search_query = table.search(query, query_type="fts").limit(limit)
                else:
                    # Fallback to simple text matching across multiple fields
                    search_query = table.search().where(
                        f"title LIKE '%{query}%' OR description LIKE '%{query}%' OR status LIKE '%{query}%' OR priority LIKE '%{query}%'"
                    ).limit(limit)
                    
            elif search_type == SearchType.HYBRID:
                # Combine vector and keyword search
                query_embedding = self._generate_embedding(query)
                vector_results = table.search(query_embedding).limit(limit // 2).to_pandas()
                
                # Apply similarity threshold to vector results
                similarity_threshold = 0.8
                if not vector_results.empty and '_distance' in vector_results.columns:
                    vector_results = vector_results[vector_results['_distance'] <= similarity_threshold]
                
                if self.config.enable_fts:
                    keyword_results = table.search(query, query_type="fts").limit(limit // 2).to_pandas()
                else:
                    keyword_results = table.search().where(
                        f"title LIKE '%{query}%' OR description LIKE '%{query}%' OR status LIKE '%{query}%' OR priority LIKE '%{query}%'"
                    ).limit(limit // 2).to_pandas()
                
                # Combine and deduplicate
                if not vector_results.empty and not keyword_results.empty:
                    combined = pd.concat([vector_results, keyword_results]).drop_duplicates(subset=['id'])
                elif not vector_results.empty:
                    combined = vector_results
                elif not keyword_results.empty:
                    combined = keyword_results
                else:
                    return []  # No results from either search
                
                result_items = combined.head(limit).to_dict('records')
                return [self._convert_numpy_to_python(item) for item in result_items]
            
            else:
                raise ValueError(f"Unknown search type: {search_type}")
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if isinstance(value, str):
                        search_query = search_query.where(f"{key} = '{value}'")
                    else:
                        search_query = search_query.where(f"{key} = {value}")
            
            results = search_query.to_pandas()
            
            # Filter out results with poor similarity for vector and hybrid searches
            # LanceDB uses cosine distance, where lower values mean higher similarity
            # Threshold of 0.8 means we only keep results with reasonable similarity
            similarity_threshold = 0.8
            if search_type in [SearchType.VECTOR, SearchType.HYBRID] and not results.empty:
                if '_distance' in results.columns:
                    results = results[results['_distance'] <= similarity_threshold]
                    # If no results meet the threshold, return empty list
                    if results.empty:
                        return []
            
            # Sort by order_index to maintain sequence order
            if hasattr(results, 'columns') and 'order_index' in results.columns.tolist():
                results = results.sort_values(by='order_index', ascending=True)
            
            work_items = results.to_dict('records')
            return [self._convert_numpy_to_python(item) for item in work_items]
            
        except Exception as e:
            logger.error(f"❌ Failed to search MCP Jive work items: {e}")
            raise
    
    async def list_work_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "order_index",
        sort_order: str = "asc"
    ) -> List[Dict[str, Any]]:
        """List work items with filtering, pagination, and sorting."""
        try:
            table = await self.get_table("WorkItem")
            
            # Handle filtering
            if filters:
                # Build filter conditions
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Handle array filters (e.g., status in ['active', 'pending'])
                        # Use len() check to avoid numpy boolean evaluation error
                        if len(value) > 0:  # Only add if list is not empty
                            condition_parts = [f"{key} = '{v}'" for v in value]
                            filter_conditions.append(f"({' OR '.join(condition_parts)})")
                    elif isinstance(value, str):
                        filter_conditions.append(f"{key} = '{value}'")
                    elif isinstance(value, (int, float)):
                        filter_conditions.append(f"{key} = {value}")
                    elif isinstance(value, bool):
                        filter_conditions.append(f"{key} = {str(value).lower()}")
                
                if filter_conditions is not None and len(filter_conditions) > 0:
                    filter_expr = " AND ".join(filter_conditions)
                    df = table.search().where(filter_expr).to_pandas()
                else:
                    df = table.to_pandas()
            else:
                df = table.to_pandas()
            
            # Handle sorting
            if hasattr(df, 'columns') and sort_by in df.columns.tolist():
                ascending = sort_order.lower() == "asc"
                df = df.sort_values(by=sort_by, ascending=ascending)
            
            # Handle pagination
            total_count = len(df)
            df = df.iloc[offset:offset + limit]
            
            # Convert to list of dictionaries and handle numpy types
            work_items = df.to_dict('records')
            
            # Convert numpy types to native Python types for JSON serialization
            work_items = [self._convert_numpy_to_python(item) for item in work_items]
            
            logger.info(f"✅ Listed {len(work_items)} work items (total: {total_count})")
            return work_items
            
        except Exception as e:
            logger.error(f"Error listing work items: {e}")
            raise
    
    async def get_work_item_children(self, work_item_id: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """Get child work items for a given parent work item."""
        try:
            table = await self.get_table("WorkItem")
            
            # Get all work items and filter by parent_id
            df = table.to_pandas()
            
            # Filter for direct children - use safe comparison to avoid numpy boolean evaluation
            # Convert parent_id column to string to avoid numpy array comparison issues
            df_safe = df.copy()
            df_safe['parent_id'] = df_safe['parent_id'].astype(str)
            children_df = df_safe[df_safe['parent_id'] == str(work_item_id)]
            
            # Convert to list of dictionaries
            children = children_df.to_dict('records')
            
            # Convert numpy types to native Python types for JSON serialization
            children = [self._convert_numpy_to_python(child) for child in children]
            
            # If recursive, get children of children
            if recursive:
                all_children = children.copy()
                for child in children:
                    grandchildren = await self.get_work_item_children(child['id'], recursive=True)
                    all_children.extend(grandchildren)
                children = all_children
            
            logger.info(f"✅ Found {len(children)} children for work item {work_item_id}")
            return children
            
        except Exception as e:
            logger.error(f"Error getting work item children: {e}")
            raise
    
    async def log_execution(self, log_data: Dict[str, Any]) -> str:
        """Log an execution event."""
        try:
            # Ensure log_id is set
            if 'log_id' not in log_data:
                log_data['log_id'] = log_data.get('id', '')
            
            # Create execution log
            execution_log = ExecutionLogModel(**log_data)
            
            # Insert into table
            table = await self.get_table("ExecutionLog")
            await self._retry_operation(table.add, [execution_log.dict()])
            
            logger.info(f"✅ Logged MCP Jive execution: {execution_log.id}")
            return execution_log.id
            
        except Exception as e:
            logger.error(f"❌ Failed to log MCP Jive execution: {e}")
            raise
    
    async def get_execution_logs(
        self, 
        work_item_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution logs, optionally filtered by work item."""
        try:
            table = await self.get_table("ExecutionLog")
            
            if work_item_id:
                results = table.search().where(
                    f"work_item_id = '{work_item_id}'"
                ).limit(limit).to_pandas()
            else:
                results = table.search().limit(limit).to_pandas()
            
            # Sort by timestamp descending
            results = results.sort_values('timestamp', ascending=False)
            
            logs = results.to_dict('records')
            # Convert numpy types for execution logs (simpler conversion since no list fields)
            for log in logs:
                for key, value in log.items():
                    if hasattr(value, 'item'):  # numpy scalar
                        try:
                            log[key] = value.item()
                        except (ValueError, AttributeError):
                            pass
                    elif pd.isna(value):
                        log[key] = None
            return logs
            
        except Exception as e:
            logger.error(f"❌ Failed to get MCP Jive execution logs: {e}")
            raise
    
    async def _verify_connection(self) -> bool:
        """Verify database connection and schema."""
        try:
            if not self._initialized:
                return False
            
            # Check if we can list tables
            tables = self.db.table_names()
            
            # Check if required tables exist
            required_tables = set(self.table_models.keys())
            existing_tables = set(tables)
            
            missing_tables = required_tables - existing_tables
            if missing_tables:
                logger.warning(f"⚠️ Missing MCP Jive tables: {missing_tables}")
                # Try to create missing tables
                await self._initialize_tables()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ MCP Jive connection verification failed: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get database health status."""
        try:
            if not self._initialized:
                return {
                    'status': 'not_initialized',
                    'message': 'MCP Jive database not initialized'
                }
            
            # Check table status
            tables = self.db.table_names()
            table_status = {}
            
            for table_name in self.table_models.keys():
                if table_name in tables:
                    try:
                        table = self.db.open_table(table_name)
                        count = table.count_rows()
                        table_status[table_name] = {
                            'exists': True,
                            'count': count,
                            'status': 'healthy'
                        }
                    except Exception as e:
                        table_status[table_name] = {
                            'exists': True,
                            'count': 0,
                            'status': 'error',
                            'error': str(e)
                        }
                else:
                    table_status[table_name] = {
                        'exists': False,
                        'count': 0,
                        'status': 'missing'
                    }
            
            # Overall status
            all_healthy = all(
                status['status'] == 'healthy' 
                for status in table_status.values()
            )
            
            return {
                'status': 'healthy' if all_healthy else 'degraded',
                'database_path': self.config.data_path,
                'embedding_model': self.config.embedding_model,
                'tables': table_status,
                'total_tables': len(tables),
                'initialized': self._initialized,
                'component': 'mcp_jive'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'initialized': self._initialized,
                'component': 'mcp_jive'
            }
    
    async def ensure_tables_exist(self) -> None:
        """Ensure all required tables exist (compatibility method)."""
        await self._ensure_tables_initialized()

    async def shutdown(self) -> None:
        """Shutdown database connections (compatibility method)."""
        await self.cleanup()
    
    async def cleanup(self) -> None:
        """Clean up database connections."""
        try:
            # LanceDB doesn't require explicit cleanup, but we can reset state
            self._initialized = False
            self._tables.clear()
            self.db = None
            self.embedding_func = None
            
            logger.info("✅ MCP Jive LanceDB cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during MCP Jive cleanup: {e}")
    
    def get_database_size(self) -> int:
        """Get total database size in bytes."""
        try:
            total_size = 0
            data_path = Path(self.config.data_path)
            
            if data_path.exists():
                for file_path in data_path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            return total_size
            
        except Exception as e:
            logger.error(f"❌ Failed to get MCP Jive database size: {e}")
            return 0

    async def add_data(self, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]],
                       text_field: Optional[str] = None) -> str:
        """Add one or more rows to a table.

        Args:
            table_name: Name of the table
            data: Dictionary with row data or list of dictionaries
            text_field: Optional field name to use for vector embedding generation

        Returns:
            ID of the created row (or first row if multiple)
        """
        await self._ensure_tables_initialized()
        table = await self.get_table(table_name)

        # Normalize data to list
        if isinstance(data, dict):
            data_list = [data]
        else:
            data_list = data

        # Ensure IDs exist and generate embeddings if text_field specified
        for item in data_list:
            if 'id' not in item:
                item['id'] = str(uuid4())

            # Generate vector embedding if text_field specified
            if text_field and text_field in item and item[text_field]:
                text_content = item[text_field]
                if isinstance(text_content, str) and text_content.strip():
                    item['vector'] = await self.generate_embedding(text_content)

        # Add to table (table.add is synchronous, not async)
        table.add(data_list)

        return data_list[0]['id']

    async def search_data(self, table_name: str, query: Optional[str] = None,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Search for rows in a table with optional semantic query and filters.

        Args:
            table_name: Name of the table
            query: Optional semantic search query string
            filters: Optional filters to apply (key-value pairs)
            limit: Maximum number of results

        Returns:
            List of matching rows as dictionaries
        """
        await self._ensure_tables_initialized()
        table = await self.get_table(table_name)

        # Build filter string for LanceDB
        filter_str = None
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    filter_conditions.append(f"{key} = '{value}'")
                elif isinstance(value, (int, float)):
                    filter_conditions.append(f"{key} = {value}")
                elif isinstance(value, bool):
                    filter_conditions.append(f"{key} = {str(value).lower()}")
            if filter_conditions:
                filter_str = " AND ".join(filter_conditions)

        # Execute search
        if query:
            # Semantic/vector search
            query_embedding = await self.generate_embedding(query)
            search_query = table.search(query_embedding)
        else:
            # Regular search/list
            search_query = table.search()

        # Apply filters if provided
        if filter_str:
            search_query = search_query.where(filter_str)

        results = search_query.limit(limit).to_list()
        return [self._convert_numpy_to_python(r) for r in results]

    async def delete_data(self, table_name: str, filters: Dict[str, Any]) -> int:
        """Delete rows from a table matching the filters.

        Args:
            table_name: Name of the table
            filters: Filters to identify rows to delete (key-value pairs)

        Returns:
            Number of rows deleted
        """
        await self._ensure_tables_initialized()
        table = await self.get_table(table_name)

        # Build filter string
        filter_conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                filter_conditions.append(f"{key} = '{value}'")
            elif isinstance(value, (int, float)):
                filter_conditions.append(f"{key} = {value}")
            elif isinstance(value, bool):
                filter_conditions.append(f"{key} = {str(value).lower()}")

        if filter_conditions:
            filter_str = " AND ".join(filter_conditions)
            table.delete(filter_str)
            return 1  # LanceDB doesn't return count, so we return 1 on success

        return 0

    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        try:
            if not self._initialized:
                return []
            return self.db.table_names()
        except Exception as e:
            logger.error(f"❌ Failed to list MCP Jive tables: {e}")
            return []
    
    async def optimize_tables(self) -> Dict[str, Any]:
        """Optimize database tables for better performance."""
        try:
            optimization_results = {}
            
            for table_name in self.list_tables():
                try:
                    table = await self.get_table(table_name)
                    
                    # Compact the table (LanceDB specific optimization)
                    table.compact_files()
                    
                    optimization_results[table_name] = {
                        'status': 'optimized',
                        'row_count': table.count_rows()
                    }
                    
                except Exception as e:
                    optimization_results[table_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            logger.info("✅ MCP Jive database optimization completed")
            return optimization_results
            
        except Exception as e:
            logger.error(f"❌ Failed to optimize MCP Jive tables: {e}")
            raise

# Compatibility aliases for migration
class WeaviateManager(LanceDBManager):
    """Compatibility alias for gradual migration from Weaviate."""
    
    def __init__(self, config):
        # Convert config if needed
        if hasattr(config, 'lancedb_data_path'):
            db_config = DatabaseConfig(
                data_path=getattr(config, 'lancedb_data_path', './data/lancedb_jive'),
                embedding_model=getattr(config, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
                device=getattr(config, 'lancedb_device', 'cpu')
            )
        else:
            db_config = DatabaseConfig()
        
        super().__init__(db_config)
        logger.warning("⚠️ Using WeaviateManager compatibility alias for MCP Jive. Please update to LanceDBManager.")
    
    async def start(self):
        """Compatibility method for Weaviate start()."""
        await self.initialize()
    
    async def stop(self):
        """Compatibility method for Weaviate stop()."""
        await self.cleanup()

# Export main classes
__all__ = [
    'LanceDBManager',
    'WeaviateManager',  # Compatibility alias
    'DatabaseConfig',
    'SearchType',
    'WorkItemModel',
    'ExecutionLogModel'
]