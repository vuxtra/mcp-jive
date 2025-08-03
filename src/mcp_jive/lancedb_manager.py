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
    """LanceDB configuration for MCP Jive."""
    data_path: str = "./data/lancedb_jive"
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
    acceptance_criteria: Optional[str] = Field(description="Completion criteria", default=None)
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

class LanceDBManager:
    """LanceDB database manager for MCP Jive."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db = None
        self.embedding_func = None
        self._initialized = False
        self._tables = {}
        
        # Table model mapping for MCP Jive
        self.table_models = {
            'WorkItem': WorkItemModel,
            'ExecutionLog': ExecutionLogModel
        }
    
    async def initialize(self) -> None:
        """Initialize LanceDB connection and embedding function."""
        if self._initialized:
            return
        
        try:
            # Create data directory
            os.makedirs(self.config.data_path, exist_ok=True)
            
            # Connect to LanceDB
            self.db = lancedb.connect(self.config.data_path)
            
            # Initialize embedding function
            self.embedding_func = SentenceTransformerEmbeddings(
                model_name=self.config.embedding_model,
                device=self.config.device,
                normalize=self.config.normalize_embeddings
            )
            
            # Initialize tables
            await self._initialize_tables()
            
            # Create full-text search indexes after everything is initialized
            if self.config.enable_fts:
                await self._create_fts_indexes()
            
            self._initialized = True
            logger.info(f"✅ MCP Jive LanceDB initialized at {self.config.data_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP Jive LanceDB: {e}")
            raise
    
    async def _initialize_tables(self) -> None:
        """Initialize all required tables with proper schemas."""
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
                        # Fallback: create with empty DataFrame
                        empty_df = pd.DataFrame()
                        self.db.create_table(table_name, data=empty_df, schema=model_class)
                    
                    logger.info(f"✅ Table {table_name} created successfully")
                else:
                    logger.info(f"📋 Table {table_name} already exists")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize table {table_name}: {e}")
                raise
    
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
    
    def get_collection(self, collection_name: str):
        """Get a LanceDB table (compatibility method)."""
        if not self._initialized:
            raise RuntimeError("LanceDB not initialized. Call initialize() first.")
        
        try:
            return self.db.open_table(collection_name)
        except Exception as e:
            logger.error(f"❌ Failed to get collection {collection_name}: {e}")
            raise
    
    def get_table(self, table_name: str):
        """Get a LanceDB table."""
        return self.get_collection(table_name)
    
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
            table = self.get_table("WorkItem")
            
            # Get existing item
            existing = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            
            if existing.empty:
                # Try searching by item_id as fallback
                existing = table.search().where(f"item_id = '{work_item_id}'").limit(1).to_pandas()
                
                if existing.empty:
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
            
            logger.info(f"✅ Updated MCP Jive work item: {work_item_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update MCP Jive work item {work_item_id}: {e}")
            raise
    
    async def get_work_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get a work item by ID or item_id."""
        try:
            table = self.get_table("WorkItem")
            
            # Try by primary id first
            result = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            
            if result.empty:
                # Try by item_id as fallback
                result = table.search().where(f"item_id = '{work_item_id}'").limit(1).to_pandas()
            
            if result.empty:
                return None
            
            return result.iloc[0].to_dict()
            
        except Exception as e:
            logger.error(f"❌ Failed to get MCP Jive work item {work_item_id}: {e}")
            raise
    
    async def delete_work_item(self, work_item_id: str) -> bool:
        """Delete a work item."""
        try:
            table = self.get_table("WorkItem")
            
            # Check if item exists by id
            existing = table.search().where(f"id = '{work_item_id}'").limit(1).to_pandas()
            
            if existing.empty:
                # Try by item_id
                existing = table.search().where(f"item_id = '{work_item_id}'").limit(1).to_pandas()
                
                if existing.empty:
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
                # Combine vector and keyword search
                query_embedding = self._generate_embedding(query)
                vector_results = table.search(query_embedding).limit(limit // 2).to_pandas()
                
                if self.config.enable_fts:
                    keyword_results = table.search(query, query_type="fts").limit(limit // 2).to_pandas()
                else:
                    keyword_results = table.search().where(
                        f"title LIKE '%{query}%' OR description LIKE '%{query}%' OR status LIKE '%{query}%' OR priority LIKE '%{query}%'"
                    ).limit(limit // 2).to_pandas()
                
                # Combine and deduplicate
                combined = pd.concat([vector_results, keyword_results]).drop_duplicates(subset=['id'])
                return combined.head(limit).to_dict('records')
            
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
            return results.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Failed to search MCP Jive work items: {e}")
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
            
            # Handle filtering
            if filters:
                # Build filter conditions
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Handle array filters (e.g., status in ['active', 'pending'])
                        if value:  # Only add if list is not empty
                            condition_parts = [f"{key} = '{v}'" for v in value]
                            filter_conditions.append(f"({' OR '.join(condition_parts)})")
                    elif isinstance(value, str):
                        filter_conditions.append(f"{key} = '{value}'")
                    elif isinstance(value, (int, float)):
                        filter_conditions.append(f"{key} = {value}")
                    elif isinstance(value, bool):
                        filter_conditions.append(f"{key} = {str(value).lower()}")
                
                if filter_conditions:
                    filter_expr = " AND ".join(filter_conditions)
                    df = table.search().where(filter_expr).to_pandas()
                else:
                    df = table.to_pandas()
            else:
                df = table.to_pandas()
            
            # Handle sorting
            if sort_by in df.columns:
                ascending = sort_order.lower() == "asc"
                df = df.sort_values(by=sort_by, ascending=ascending)
            
            # Handle pagination
            total_count = len(df)
            df = df.iloc[offset:offset + limit]
            
            # Convert to list of dictionaries
            work_items = df.to_dict('records')
            
            # Convert numpy types to native Python types for JSON serialization
            for item in work_items:
                for key, value in item.items():
                    if hasattr(value, 'item'):  # numpy scalar
                        item[key] = value.item()
                    elif pd.isna(value):  # pandas NaN
                        item[key] = None
            
            logger.info(f"✅ Listed {len(work_items)} work items (total: {total_count})")
            return work_items
            
        except Exception as e:
            logger.error(f"Error listing work items: {e}")
            raise
    
    async def get_work_item_children(self, work_item_id: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """Get child work items for a given parent work item."""
        try:
            table = self.get_table("WorkItem")
            
            # Get all work items and filter by parent_id
            df = table.to_pandas()
            
            # Filter for direct children
            children_df = df[df['parent_id'] == work_item_id]
            
            # Convert to list of dictionaries
            children = children_df.to_dict('records')
            
            # Convert numpy types to native Python types for JSON serialization
            for child in children:
                for key, value in child.items():
                    if hasattr(value, 'item'):  # numpy scalar
                        child[key] = value.item()
                    elif pd.isna(value):  # pandas NaN
                        child[key] = None
            
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
            table = self.get_table("ExecutionLog")
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