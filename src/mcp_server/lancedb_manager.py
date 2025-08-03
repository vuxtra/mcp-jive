#!/usr/bin/env python3
"""
LanceDB Manager for MCP Server

This module provides the LanceDB database manager for the MCP server,
replacing the Weaviate implementation with a true embedded vector database.

Features:
- True embedded operation (no external services)
- Built-in vectorization with sentence-transformers
- High-performance vector and keyword search
- Automatic schema management
- Async/await support
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
    """LanceDB configuration."""
    data_path: str = "./data/lancedb"
    embedding_model: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    normalize_embeddings: bool = True
    vector_dimension: int = 384
    batch_size: int = 100
    timeout: int = 30
    enable_fts: bool = True  # Full-text search
    max_retries: int = 3
    retry_delay: float = 1.0

# Pydantic Models for LanceDB Tables

class WorkItemModel(LanceModel):
    """Work item data model for LanceDB."""
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
    acceptance_criteria: Optional[str] = Field(description="Completion criteria", default=None)
    created_at: datetime = Field(description="Creation timestamp", default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(description="Last update timestamp", default_factory=lambda: datetime.now(timezone.utc))
    metadata: str = Field(description="Additional metadata (JSON string)", default="{}")

class TaskModel(LanceModel):
    """Task data model for LanceDB."""
    id: str = Field(description="Unique task identifier")
    title: str = Field(description="Task title")
    description: str = Field(description="Task description")
    vector: Vector(384) = Field(description="Embedding vector")
    status: str = Field(description="Task status", default="todo")
    priority: str = Field(description="Task priority", default="medium")
    tags: List[str] = Field(description="Associated tags", default_factory=list)
    created_at: datetime = Field(description="Creation timestamp", default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(description="Last update timestamp", default_factory=lambda: datetime.now(timezone.utc))
    metadata: str = Field(description="Additional metadata (JSON string)", default="{}")

class SearchIndexModel(LanceModel):
    """Search index data model for LanceDB."""
    id: str = Field(description="Unique index identifier")
    content: str = Field(description="Indexed content")
    vector: Vector(384) = Field(description="Embedding vector")
    source_type: str = Field(description="Source type (file, database, etc.)")
    source_id: Optional[str] = Field(description="Source identifier", default=None)
    tags: List[str] = Field(description="Associated tags", default_factory=list)
    indexed_at: datetime = Field(description="Indexing timestamp", default_factory=lambda: datetime.now(timezone.utc))
    metadata: str = Field(description="Additional metadata (JSON string)", default="{}")

class ExecutionLogModel(LanceModel):
    """Execution log data model for LanceDB."""
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

class LanceDBManager:
    """LanceDB database manager for MCP server."""
    
    def __init__(self, config):
        # Handle both DatabaseConfig and ServerConfig
        if hasattr(config, 'lancedb_data_path'):
            # ServerConfig
            self.data_path = config.lancedb_data_path
            self.embedding_model = getattr(config, 'lancedb_embedding_model', 'all-MiniLM-L6-v2')
            self.device = getattr(config, 'lancedb_device', 'cpu')
            self.normalize_embeddings = True
            self.enable_fts = True  # Default to enabled for ServerConfig
        else:
            # DatabaseConfig
            self.data_path = config.data_path
            self.embedding_model = config.embedding_model
            self.device = config.device
            self.normalize_embeddings = getattr(config, 'normalize_embeddings', True)
            self.enable_fts = getattr(config, 'enable_fts', True)
            
        self.config = config
        self.db = None
        self.embedding_func = None
        self._initialized = False
        self._tables = {}
        
        # Table model mapping
        self.table_models = {
            'WorkItem': WorkItemModel,
            'Task': TaskModel,
            'SearchIndex': SearchIndexModel,
            'ExecutionLog': ExecutionLogModel
        }
    
    async def initialize(self) -> None:
        """Initialize LanceDB connection and embedding function."""
        if self._initialized:
            return
        
        try:
            # Create data directory
            os.makedirs(self.data_path, exist_ok=True)
            
            # Connect to LanceDB
            self.db = lancedb.connect(self.data_path)
            
            # Initialize embedding function
            self.embedding_func = SentenceTransformerEmbeddings(
                model_name=self.embedding_model,
                device=self.device,
                normalize=self.normalize_embeddings
            )
            
            # Initialize tables
            await self._initialize_tables()
            
            # Create full-text search indexes after everything is initialized
            if self.enable_fts:
                await self._create_fts_indexes()
            
            self._initialized = True
            logger.info(f"✅ LanceDB initialized at {self.data_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LanceDB: {e}")
            raise
    
    async def _initialize_tables(self) -> None:
        """Initialize all required tables."""
        existing_tables = self.db.table_names()
        
        for table_name, model_class in self.table_models.items():
            if table_name not in existing_tables:
                try:
                    # Create table with schema using LanceModel
                    table = self.db.create_table(table_name, schema=model_class)
                    logger.info(f"📋 Created table: {table_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to create table {table_name}: {e}")
                    # Try alternative approach with empty data
                    try:
                        import pandas as pd
                        # Create empty DataFrame with correct schema
                        empty_df = pd.DataFrame()
                        table = self.db.create_table(table_name, data=empty_df, schema=model_class)
                        logger.info(f"📋 Created table (fallback): {table_name}")
                    except Exception as e2:
                        logger.error(f"❌ Failed to create table {table_name} with fallback: {e2}")
                        raise
            else:
                logger.info(f"✅ Table {table_name} already exists")
        

    
    async def _create_fts_indexes(self) -> None:
        """Create full-text search indexes for text fields."""
        try:
            logger.info("🔍 Preparing full-text search index configurations...")
            
            # Define FTS index configurations for each table
            self.fts_configs = {
                'WorkItem': ['title', 'description', 'acceptance_criteria', 'status', 'priority', 'item_type'],
                'Task': ['title', 'description', 'status', 'priority'],
                'SearchIndex': ['content', 'source_type'],
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
    
    async def ensure_tables_exist(self) -> None:
        """Ensure all required tables exist."""
        await self._initialize_tables()
    
    def _generate_embedding(self, text_content: str) -> List[float]:
        """Generate embedding for text content."""
        try:
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
        return self._generate_embedding(text_content)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Public method to generate embeddings for multiple texts."""
        return [self._generate_embedding(text) for text in texts]
    
    async def _retry_operation(self, operation, *args, **kwargs):
        """Retry database operations with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                return await operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation) else operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"⚠️ Operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Operation failed after {self.config.max_retries} attempts: {e}")
        
        raise last_exception
    
    def get_table(self, table_name: str):
        """Get a LanceDB table."""
        if not self._initialized:
            raise RuntimeError("LanceDB not initialized. Call initialize() first.")
        
        try:
            return self.db.open_table(table_name)
        except Exception as e:
            logger.error(f"❌ Failed to get table {table_name}: {e}")
            raise
    
    async def create_work_item(self, work_item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new work item with automatic vectorization."""
        try:
            # Generate text content for embedding
            text_content = f"{work_item_data.get('title', '')} {work_item_data.get('description', '')}"
            
            # Convert data for WorkItemModel compatibility
            model_data = work_item_data.copy()
            
            # Convert 'type' to 'item_type' if present
            if 'type' in model_data:
                model_data['item_type'] = model_data.pop('type')
            
            # Convert acceptance_criteria list to string if present
            if 'acceptance_criteria' in model_data and isinstance(model_data['acceptance_criteria'], list):
                model_data['acceptance_criteria'] = '\n'.join(model_data['acceptance_criteria']) if model_data['acceptance_criteria'] else None
            
            # Create work item with embedding
            work_item = WorkItemModel(
                **model_data,
                vector=self._generate_embedding(text_content)
            )
            
            # Insert into table
            table = self.get_table("WorkItem")
            await self._retry_operation(table.add, [work_item.dict()])
            
            logger.info(f"✅ Created work item: {work_item.id}")
            return work_item.dict()
            
        except Exception as e:
            logger.error(f"Error creating work item: {e}")
            raise

    async def store_work_item(self, work_item_data: Dict[str, Any]) -> str:
        """Store a work item (compatibility method for create_work_item)."""
        try:
            result = await self.create_work_item(work_item_data)
            return result["id"]
        except Exception as e:
            logger.error(f"Error storing work item: {e}")
            raise

    async def update_work_item(self, work_item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing work item."""
        try:
            table = self.get_table("WorkItem")
            
            # Get existing item
            existing = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            
            if existing.empty:
                logger.warning(f"⚠️ Work item {work_item_id} not found")
                return None
            
            # Update fields
            updated_data = existing.iloc[0].to_dict()
            updated_data.update(updates)
            updated_data['updated_at'] = datetime.now(timezone.utc)
            
            # Regenerate embedding if title or description changed
            if 'title' in updates or 'description' in updates:
                text_content = f"{updated_data.get('title', '')} {updated_data.get('description', '')}"
                updated_data['vector'] = self._generate_embedding(text_content)
            
            # Delete old record and insert updated one
            table.delete(f"id = '{work_item_id}'")
            await self._retry_operation(table.add, [updated_data])
            
            logger.info(f"✅ Updated work item: {work_item_id}")
            return updated_data
            
        except Exception as e:
            logger.error(f"❌ Failed to update work item {work_item_id}: {e}")
            raise
    
    async def get_work_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get a work item by ID."""
        try:
            table = self.get_table("WorkItem")
            result = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            
            if result.empty:
                return None
            
            return result.iloc[0].to_dict()
            
        except Exception as e:
            logger.error(f"❌ Failed to get work item {work_item_id}: {e}")
            raise
    
    async def delete_work_item(self, work_item_id: str) -> bool:
        """Delete a work item."""
        try:
            table = self.get_table("WorkItem")
            
            # Check if item exists
            existing = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            if existing.empty:
                logger.warning(f"⚠️ Work item {work_item_id} not found")
                return False
            
            # Delete the item
            table.delete(f"id = '{work_item_id}'")
            
            logger.info(f"✅ Deleted work item: {work_item_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete work item {work_item_id}: {e}")
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
            
            table = self.get_table("WorkItem")
            
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
                # Combine vector and keyword search using safe Arrow conversion
                query_embedding = self._generate_embedding(query)
                
                # Get vector results safely
                try:
                    vector_result = table.search(query_embedding).limit(limit // 2).to_arrow()
                    vector_records = []
                    for i in range(len(vector_result)):
                        record = {}
                        for field in vector_result.schema:
                            try:
                                value = vector_result[field.name][i].as_py()
                                if field.name == 'vector' and hasattr(value, '__len__') and not isinstance(value, str):
                                    record[field.name] = "[vector data]"
                                else:
                                    record[field.name] = value
                            except Exception:
                                record[field.name] = None
                        vector_records.append(record)
                except Exception as e:
                    logger.warning(f"Vector search failed: {e}")
                    vector_records = []
                
                # Get keyword results safely
                try:
                    if self.config.enable_fts:
                        keyword_result = table.search(query, query_type="fts").limit(limit // 2).to_arrow()
                    else:
                        keyword_result = table.search().where(
                            f"title LIKE '%{query}%' OR description LIKE '%{query}%' OR status LIKE '%{query}%' OR priority LIKE '%{query}%'"
                        ).limit(limit // 2).to_arrow()
                    
                    keyword_records = []
                    for i in range(len(keyword_result)):
                        record = {}
                        for field in keyword_result.schema:
                            try:
                                value = keyword_result[field.name][i].as_py()
                                if field.name == 'vector' and hasattr(value, '__len__') and not isinstance(value, str):
                                    record[field.name] = "[vector data]"
                                else:
                                    record[field.name] = value
                            except Exception:
                                record[field.name] = None
                        keyword_records.append(record)
                except Exception as e:
                    logger.warning(f"Keyword search failed: {e}")
                    keyword_records = []
                
                # Combine and deduplicate manually
                seen_ids = set()
                combined_records = []
                for record in vector_records + keyword_records:
                    if record.get('id') not in seen_ids:
                        seen_ids.add(record.get('id'))
                        combined_records.append(record)
                        if len(combined_records) >= limit:
                            break
                
                return combined_records
            
            else:
                raise ValueError(f"Unknown search type: {search_type}")
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if isinstance(value, str):
                        search_query = search_query.where(f"{key} = '{value}'")
                    else:
                        search_query = search_query.where(f"{key} = {value}")
            
            # Use safe Arrow conversion to avoid array boolean evaluation issues
            try:
                result = search_query.to_arrow()
                
                # Convert to list of dictionaries safely
                records = []
                for i in range(len(result)):
                    record = {}
                    for field in result.schema:
                        try:
                            value = result[field.name][i].as_py()
                            # Handle vector field specially
                            if field.name == 'vector' and hasattr(value, '__len__') and not isinstance(value, str):
                                record[field.name] = "[vector data]"
                            else:
                                record[field.name] = value
                        except Exception:
                            record[field.name] = None
                    records.append(record)
                    
                return records
                
            except Exception as e:
                logger.warning(f"Arrow conversion failed, returning empty results: {e}")
                return []
            
        except Exception as e:
            logger.error(f"❌ Failed to search work items: {e}")
            raise
    
    async def list_work_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List work items with filtering, pagination, and sorting."""
        try:
            table = self.get_table("WorkItem")
            
            # Build filter conditions
            where_clause = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Handle array filters (e.g., status in ["todo", "in_progress"])
                        value_list = "', '".join(str(v) for v in value)
                        filter_conditions.append(f"{key} IN ('{value_list}')")
                    elif isinstance(value, str):
                        filter_conditions.append(f"{key} = '{value}'")
                    else:
                        filter_conditions.append(f"{key} = {value}")
                
                if filter_conditions:
                    where_clause = " AND ".join(filter_conditions)
            
            # Use scan() for listing all items with filtering and sorting
            if where_clause:
                query = table.search().where(where_clause)
            else:
                # For listing all items without search, use safe Arrow conversion
                try:
                    result = table.to_arrow()
                    
                    # Convert to list of dictionaries safely
                    records = []
                    for i in range(len(result)):
                        record = {}
                        for field in result.schema:
                            try:
                                value = result[field.name][i].as_py()
                                if field.name == 'vector' and hasattr(value, '__len__') and not isinstance(value, str):
                                    record[field.name] = "[vector data]"
                                else:
                                    record[field.name] = value
                            except Exception:
                                record[field.name] = None
                        records.append(record)
                    
                    # Apply sorting manually
                    if sort_by and records:
                        reverse = sort_order.lower() == "desc"
                        try:
                            records.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
                        except Exception:
                            pass  # Skip sorting if it fails
                    
                    # Apply pagination
                    return records[offset:offset + limit]
                    
                except Exception as e:
                    logger.warning(f"Arrow conversion failed, returning empty results: {e}")
                    return []
            
            # For filtered queries, apply limit and get results using safe Arrow conversion
            query = query.limit(limit + offset)  # Get more to handle offset
            try:
                result = query.to_arrow()
                
                # Convert to list of dictionaries safely
                records = []
                for i in range(len(result)):
                    record = {}
                    for field in result.schema:
                        try:
                            value = result[field.name][i].as_py()
                            if field.name == 'vector' and hasattr(value, '__len__') and not isinstance(value, str):
                                record[field.name] = "[vector data]"
                            else:
                                record[field.name] = value
                        except Exception:
                            record[field.name] = None
                    records.append(record)
                
                # Apply sorting manually
                if sort_by and records:
                    reverse = sort_order.lower() == "desc"
                    try:
                        records.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
                    except Exception:
                        pass  # Skip sorting if it fails
                
                # Apply pagination
                return records[offset:offset + limit]
                
            except Exception as e:
                logger.warning(f"Arrow conversion failed, returning empty results: {e}")
                return []
            
        except Exception as e:
            logger.error(f"❌ Failed to list work items: {e}")
            raise
    
    async def get_work_item_children(self, work_item_id: str, recursive: bool = False, _visited: Optional[set] = None, _depth: int = 0) -> List[Dict[str, Any]]:
        """Get child work items for a given parent work item.
        
        Args:
            work_item_id: The parent work item ID
            recursive: Whether to get all descendants recursively
            _visited: Internal set to track visited items (prevents cycles)
            _depth: Internal depth counter (prevents infinite recursion)
        """
        try:
            # Initialize visited set for cycle detection
            if _visited is None:
                _visited = set()
            
            # Prevent infinite recursion with depth limit
            if _depth > 10:  # Maximum depth of 10 levels
                logger.warning(f"⚠️ Maximum recursion depth reached for work item {work_item_id}")
                return []
            
            # Prevent cycles
            if work_item_id in _visited:
                logger.warning(f"⚠️ Cycle detected: work item {work_item_id} already visited")
                return []
            
            # Add current item to visited set
            _visited.add(work_item_id)
            
            logger.info(f"🔍 Getting children for work item: {work_item_id} (depth: {_depth})")
            
            # Use list_work_items instead of search to get all items reliably
            # This avoids search-specific issues and gets all work items
            try:
                # Get all work items using list_work_items
                all_work_items = await self.list_work_items(
                    limit=1000  # Large limit to get all items
                )
                
                logger.info(f"📊 Retrieved {len(all_work_items)} total work items")
                logger.info(f"🔍 Looking for children with parent_id: {work_item_id}")
                
                # Filter for children manually
                children = []
                for item in all_work_items:
                    try:
                        item_parent_id = item.get('parent_id')
                        item_id = item.get('id', 'unknown')
                        item_title = item.get('title', 'unknown')
                        # Safe comparison to avoid NumPy array boolean evaluation issues
                        def safe_equals(val1, val2):
                            """Safely compare values that might be NumPy arrays."""
                            if hasattr(val1, 'item') and not isinstance(val1, (str, list, dict)):
                                val1 = val1.item()
                            if hasattr(val2, 'item') and not isinstance(val2, (str, list, dict)):
                                val2 = val2.item()
                            if hasattr(val1, 'tolist') and not isinstance(val1, (str, list)):
                                val1 = val1.tolist()
                            if hasattr(val2, 'tolist') and not isinstance(val2, (str, list)):
                                val2 = val2.tolist()
                            return val1 == val2
                        
                        if safe_equals(item_parent_id, work_item_id):
                            # Clean up the item to ensure JSON serialization
                            clean_item = {}
                            for key, value in item.items():
                                if key == 'vector':
                                    clean_item[key] = "[vector excluded]"
                                elif value is None:
                                    clean_item[key] = None
                                elif isinstance(value, (str, int, float, bool)):
                                    clean_item[key] = value
                                elif hasattr(value, 'isoformat'):
                                    clean_item[key] = value.isoformat()
                                else:
                                    clean_item[key] = str(value)
                            
                            children.append(clean_item)
                            logger.info(f"📊 Found child: {clean_item.get('id', 'unknown')}")
                    except Exception as item_error:
                        logger.warning(f"⚠️ Error processing item: {item_error}")
                        continue
                
                logger.info(f"📊 Found {len(children)} direct children")
                
            except Exception as search_error:
                logger.error(f"❌ Error during search: {search_error}")
                return []
            
            # If recursive, get children of children
            if recursive:
                logger.info(f"🔄 Processing recursive children (depth: {_depth})")
                all_children = children.copy()
                for child in children:
                    try:
                        child_id = child['id']
                        # Skip if we've already visited this child (cycle prevention)
                        if child_id not in _visited:
                            grandchildren = await self.get_work_item_children(
                                child_id, 
                                recursive=True, 
                                _visited=_visited.copy(),  # Pass a copy to avoid shared state issues
                                _depth=_depth + 1
                            )
                            all_children.extend(grandchildren)
                        else:
                            logger.info(f"🔄 Skipping already visited child: {child_id}")
                    except Exception as recursive_error:
                        logger.warning(f"⚠️ Error getting grandchildren for {child.get('id', 'unknown')}: {recursive_error}")
                children = all_children
            
            logger.info(f"✅ Found {len(children)} children for work item {work_item_id}")
            return children
            
        except Exception as e:
            logger.error(f"❌ Error getting work item children: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []
        finally:
            # Remove from visited set when exiting this call (for proper backtracking)
            if _visited and work_item_id in _visited:
                _visited.discard(work_item_id)
    
    async def get_work_item_dependencies(self, work_item_id: str, include_transitive: bool = True, only_blocking: bool = True) -> List[Dict[str, Any]]:
        """Get dependencies for a work item."""
        try:
            logger.info(f"🔍 Getting dependencies for work item: {work_item_id}")
            
            # Get the work item first
            work_item = await self.get_work_item(work_item_id)
            if not work_item:
                logger.warning(f"⚠️ Work item not found: {work_item_id}")
                return []
            
            dependencies = []
            dependency_ids = work_item.get('dependencies', [])
            
            if not dependency_ids:
                logger.info(f"✅ No dependencies found for work item {work_item_id}")
                return []
            
            # Get direct dependencies
            for dep_id in dependency_ids:
                try:
                    dep_item = await self.get_work_item(dep_id)
                    if dep_item:
                        # Check if blocking (if only_blocking is True)
                        if only_blocking:
                            # Consider blocking if status is not completed
                            status = dep_item.get('status', '').lower()
                            if status not in ['completed', 'done', 'finished']:
                                dependencies.append(dep_item)
                        else:
                            dependencies.append(dep_item)
                except Exception as dep_error:
                    logger.warning(f"⚠️ Error getting dependency {dep_id}: {dep_error}")
            
            # Get transitive dependencies if requested
            if include_transitive:
                visited = {work_item_id}  # Prevent cycles
                transitive_deps = []
                
                for dep in dependencies.copy():
                    dep_id = dep['id']
                    if dep_id not in visited:
                        visited.add(dep_id)
                        try:
                            sub_deps = await self.get_work_item_dependencies(
                                dep_id, 
                                include_transitive=True, 
                                only_blocking=only_blocking
                            )
                            for sub_dep in sub_deps:
                                if sub_dep['id'] not in visited and sub_dep not in transitive_deps:
                                    transitive_deps.append(sub_dep)
                                    visited.add(sub_dep['id'])
                        except Exception as trans_error:
                            logger.warning(f"⚠️ Error getting transitive dependencies for {dep_id}: {trans_error}")
                
                dependencies.extend(transitive_deps)
            
            logger.info(f"✅ Found {len(dependencies)} dependencies for work item {work_item_id}")
            return dependencies
            
        except Exception as e:
            logger.error(f"❌ Error getting work item dependencies: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []
    
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new task with automatic vectorization."""
        try:
            # Generate text content for embedding
            text_content = f"{task_data.get('title', '')} {task_data.get('description', '')}"
            
            # Convert any numpy arrays in task_data to Python types
            import numpy as np
            clean_task_data = {}
            for key, value in task_data.items():
                if isinstance(value, np.ndarray):  # numpy array
                    clean_task_data[key] = value.tolist()
                elif isinstance(value, (np.integer, np.floating, np.bool_)):  # numpy scalar
                    clean_task_data[key] = value.item()
                elif hasattr(value, 'tolist') and not isinstance(value, (str, list)):  # other array-like
                    clean_task_data[key] = value.tolist()
                elif hasattr(value, 'item') and not isinstance(value, (str, list, dict)):  # other scalar-like
                    clean_task_data[key] = value.item()
                else:
                    clean_task_data[key] = value
            
            # Special handling for tags field to ensure it's a proper list of strings
            if 'tags' in clean_task_data:
                tags = clean_task_data['tags']
                if isinstance(tags, np.ndarray):
                    clean_task_data['tags'] = tags.tolist()
                else:
                    # Handle all other cases (including non-list types)
                    # Avoid boolean evaluation of numpy arrays
                    try:
                        # Check for None using 'is' operator to avoid NumPy boolean evaluation
                        if tags is None:
                            clean_task_data['tags'] = []
                        elif isinstance(tags, list):
                            # Already a list, keep as is
                            pass
                        else:
                            clean_task_data['tags'] = list(tags)
                    except (TypeError, ValueError):
                        clean_task_data['tags'] = []
                # Ensure all tags are strings - safely handle potential NumPy arrays
                if isinstance(clean_task_data['tags'], list):
                    clean_task_data['tags'] = [str(tag) for tag in clean_task_data['tags']]
                else:
                    clean_task_data['tags'] = []
            
            # Debug logging to see what we're passing to TaskModel
            logger.info(f"Creating TaskModel with data: {clean_task_data}")
            for key, value in clean_task_data.items():
                logger.info(f"  {key}: {type(value)} = {value}")
            
            # Create task with embedding
            try:
                task = TaskModel(
                    **clean_task_data,
                    vector=self._generate_embedding(text_content),
                    updated_at=datetime.now(timezone.utc)
                )
            except Exception as model_error:
                logger.error(f"TaskModel creation failed: {model_error}")
                logger.error(f"Data types being passed:")
                for key, value in clean_task_data.items():
                    logger.error(f"  {key}: {type(value)} = {repr(value)}")
                raise
            
            # Insert into table
            table = self.get_table("Task")
            # Convert task to dict safely to avoid boolean evaluation issues
            try:
                task_dict = task.dict()
                logger.info(f"Task dict created successfully: {task_dict}")
                await self._retry_operation(table.add, [task_dict])
            except Exception as dict_error:
                logger.error(f"Error converting task to dict: {dict_error}")
                # Try manual conversion as fallback
                task_dict = {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'vector': task.vector,
                    'status': task.status,
                    'priority': task.priority,
                    'tags': task.tags,
                    'created_at': task.created_at,
                    'updated_at': task.updated_at,
                    'metadata': task.metadata
                }
                await self._retry_operation(table.add, [task_dict])
            
            logger.info(f"✅ Created task: {task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"❌ Failed to create task: {e}")
            raise
    
    async def search_tasks(
        self, 
        query: str, 
        search_type: SearchType = SearchType.VECTOR,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search tasks with vector similarity."""
        try:
            # Ensure FTS index exists if needed
            if search_type in [SearchType.KEYWORD, SearchType.HYBRID]:
                await self._ensure_fts_index("Task")
            
            table = self.get_table("Task")
            
            if search_type == SearchType.VECTOR:
                # Generate embedding for vector search
                query_embedding = self._generate_embedding(query)
                results = table.search(query_embedding).limit(limit).to_pandas()
            elif search_type == SearchType.KEYWORD:
                if self.config.enable_fts:
                    results = table.search(query, query_type="fts").limit(limit).to_pandas()
                else:
                    results = table.search().where(
                        f"title LIKE '%{query}%' OR description LIKE '%{query}%'"
                    ).limit(limit).to_pandas()
            else:  # HYBRID
                # Generate embedding for vector part of hybrid search
                query_embedding = self._generate_embedding(query)
                vector_results = table.search(query_embedding).limit(limit // 2).to_pandas()
                if self.config.enable_fts:
                    keyword_results = table.search(query, query_type="fts").limit(limit // 2).to_pandas()
                else:
                    keyword_results = table.search().where(
                        f"title LIKE '%{query}%' OR description LIKE '%{query}%'"
                    ).limit(limit // 2).to_pandas()
                
                results = pd.concat([vector_results, keyword_results]).drop_duplicates(subset=['id']).head(limit)
            
            return results.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Failed to search tasks: {e}")
            raise
    
    async def create_search_index(self, index_data: Dict[str, Any]) -> str:
        """Create a search index entry."""
        try:
            # Generate embedding for content
            content = index_data.get('content', '')
            
            # Create search index with embedding
            search_index = SearchIndexModel(
                **index_data,
                vector=self._generate_embedding(content)
            )
            
            # Insert into table
            table = self.get_table("SearchIndex")
            await self._retry_operation(table.add, [search_index.dict()])
            
            logger.info(f"✅ Created search index: {search_index.id}")
            return search_index.id
            
        except Exception as e:
            logger.error(f"❌ Failed to create search index: {e}")
            raise
    
    async def search_content(
        self, 
        query: str, 
        source_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search indexed content."""
        try:
            table = self.get_table("SearchIndex")
            search_query = table.search(query).limit(limit)
            
            # Filter by source type if provided
            if source_type:
                search_query = search_query.where(f"source_type = '{source_type}'")
            
            results = search_query.to_pandas()
            return results.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Failed to search content: {e}")
            raise
    
    async def log_execution(self, log_data: Dict[str, Any]) -> str:
        """Log an execution event."""
        try:
            # Create execution log
            execution_log = ExecutionLogModel(**log_data)
            
            # Insert into table
            table = self.get_table("ExecutionLog")
            await self._retry_operation(table.add, [execution_log.dict()])
            
            logger.info(f"✅ Logged execution: {execution_log.id}")
            return execution_log.id
            
        except Exception as e:
            logger.error(f"❌ Failed to log execution: {e}")
            raise
    
    async def get_execution_logs(
        self, 
        work_item_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution logs, optionally filtered by work item."""
        try:
            table = self.get_table("ExecutionLog")
            
            if work_item_id:
                results = table.search().where(
                    f"work_item_id = '{work_item_id}'"
                ).limit(limit).to_pandas()
            else:
                results = table.search().limit(limit).to_pandas()
            
            # Sort by timestamp descending
            results = results.sort_values('timestamp', ascending=False)
            
            return results.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Failed to get execution logs: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get database health status."""
        try:
            if not self._initialized:
                return {
                    'status': 'not_initialized',
                    'message': 'Database not initialized'
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
                'initialized': self._initialized
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'initialized': self._initialized
            }
    
    async def cleanup(self) -> None:
        """Clean up database connections."""
        try:
            # LanceDB doesn't require explicit cleanup, but we can reset state
            self._initialized = False
            self._tables.clear()
            self.db = None
            self.embedding_func = None
            
            logger.info("✅ LanceDB cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
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
            logger.error(f"❌ Failed to get database size: {e}")
            return 0
    
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        try:
            if not self._initialized:
                return []
            return self.db.table_names()
        except Exception as e:
            logger.error(f"❌ Failed to list tables: {e}")
            return []
    
    async def optimize_tables(self) -> Dict[str, Any]:
        """Optimize database tables for better performance."""
        try:
            optimization_results = {}
            
            for table_name in self.list_tables():
                try:
                    table = self.get_table(table_name)
                    
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
            
            logger.info("✅ Database optimization completed")
            return optimization_results
            
        except Exception as e:
            logger.error(f"❌ Failed to optimize tables: {e}")
            raise

# Compatibility aliases for migration
class WeaviateManager(LanceDBManager):
    """Compatibility alias for gradual migration."""
    
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
        logger.warning("⚠️ Using WeaviateManager compatibility alias. Please update to LanceDBManager.")
    
    async def start(self):
        """Compatibility method for Weaviate start()."""
        await self.initialize()
    
    async def stop(self):
        """Compatibility method for Weaviate stop()."""
        await self.cleanup()
    
    def get_collection(self, collection_name: str):
        """Compatibility method for Weaviate get_collection()."""
        return self.get_table(collection_name)

# Export main classes
__all__ = [
    'LanceDBManager',
    'WeaviateManager',  # Compatibility alias
    'DatabaseConfig',
    'SearchType',
    'WorkItemModel',
    'TaskModel',
    'SearchIndexModel',
    'ExecutionLogModel'
]