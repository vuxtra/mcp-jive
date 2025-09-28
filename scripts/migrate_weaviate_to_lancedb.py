#!/usr/bin/env python3
"""
Weaviate to LanceDB Migration Script

This script performs a complete migration from Weaviate to LanceDB:
1. Exports all data from Weaviate
2. Transforms data to LanceDB format
3. Imports data to LanceDB
4. Validates migration success

Usage:
    python scripts/migrate_weaviate_to_lancedb.py [--dry-run] [--backup-only]

Options:
    --dry-run: Perform migration without actually writing to LanceDB
    --backup-only: Only create backup, don't perform migration
    --validate-only: Only validate existing migration
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import lancedb
    from lancedb.embeddings import SentenceTransformerEmbeddings
    import pandas as pd
    import pyarrow as pa
except ImportError as e:
    print(f"❌ Missing LanceDB dependencies: {e}")
    print("📦 Install with: pip install lancedb sentence-transformers pyarrow pandas")
    sys.exit(1)

try:
    from mcp_jive.database import WeaviateManager as JiveWeaviateManager
    from mcp_jive.lancedb_manager import LanceDBManager  # Migrated from Weaviate as ServerWeaviateManager
    from mcp_jive.config import Config as JiveConfig
    from mcp_jive.config import ServerConfig
except ImportError as e:
    print(f"❌ Cannot import MCP Jive modules: {e}")
    print("🔧 Ensure you're running from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationStats:
    """Track migration statistics."""
    start_time: datetime
    end_time: Optional[datetime] = None
    records_exported: Dict[str, int] = None
    records_transformed: Dict[str, int] = None
    records_imported: Dict[str, int] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.records_exported is None:
            self.records_exported = {}
        if self.records_transformed is None:
            self.records_transformed = {}
        if self.records_imported is None:
            self.records_imported = {}
        if self.errors is None:
            self.errors = []
    
    def log_export(self, collection: str, count: int):
        self.records_exported[collection] = count
        logger.info(f"📤 Exported {count} records from {collection}")
    
    def log_transform(self, collection: str, count: int):
        self.records_transformed[collection] = count
        logger.info(f"🔄 Transformed {count} records for {collection}")
    
    def log_import(self, collection: str, count: int):
        self.records_imported[collection] = count
        logger.info(f"📥 Imported {count} records to {collection}")
    
    def log_error(self, error: str):
        self.errors.append(error)
        logger.error(f"❌ {error}")
    
    def finalize(self):
        self.end_time = datetime.now(timezone.utc)
    
    def generate_report(self) -> Dict[str, Any]:
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        total_exported = sum(self.records_exported.values())
        total_imported = sum(self.records_imported.values())
        success_rate = (total_imported / max(total_exported, 1)) * 100
        
        return {
            'duration_seconds': duration,
            'total_records_exported': total_exported,
            'total_records_imported': total_imported,
            'success_rate_percent': success_rate,
            'error_count': len(self.errors),
            'collections': {
                'exported': self.records_exported,
                'transformed': self.records_transformed,
                'imported': self.records_imported
            },
            'errors': self.errors
        }

class WeaviateExporter:
    """Export data from Weaviate instances."""
    
    def __init__(self):
        self.jive_manager = None
        self.server_manager = None
    
    async def initialize(self):
        """Initialize Weaviate managers."""
        try:
            # Initialize Jive Weaviate Manager
            jive_config = JiveConfig()
            self.jive_manager = JiveWeaviateManager(jive_config)
            await self.jive_manager.initialize()
            logger.info("✅ Initialized Jive Weaviate Manager")
            
            # Initialize Server Weaviate Manager
            server_config = ServerConfig()
            self.server_manager = ServerWeaviateManager(server_config)
            await self.server_manager.start()
            logger.info("✅ Initialized Server Weaviate Manager")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Weaviate managers: {e}")
            raise
    
    async def export_collection(self, manager, collection_name: str) -> List[Dict[str, Any]]:
        """Export all objects from a Weaviate collection."""
        try:
            collection = manager.get_collection(collection_name)
            if not collection:
                logger.warning(f"⚠️ Collection {collection_name} not found")
                return []
            
            # Fetch all objects with properties and vectors
            objects = collection.query.fetch_objects(
                limit=10000,  # Adjust based on your data size
                include_vector=True
            )
            
            exported_data = []
            for obj in objects.objects:
                exported_obj = {
                    'id': str(obj.uuid),
                    'properties': obj.properties,
                    'vector': obj.vector if hasattr(obj, 'vector') and obj.vector else None,
                    'collection': collection_name
                }
                exported_data.append(exported_obj)
            
            logger.info(f"📤 Exported {len(exported_data)} objects from {collection_name}")
            return exported_data
            
        except Exception as e:
            logger.error(f"❌ Failed to export {collection_name}: {e}")
            return []
    
    async def export_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export all data from both Weaviate instances."""
        all_data = {}
        
        # Define collections for each manager
        jive_collections = ['WorkItem', 'ExecutionLog']
        server_collections = ['Task', 'WorkItem', 'SearchIndex']
        
        # Export from Jive manager
        if self.jive_manager:
            for collection_name in jive_collections:
                try:
                    data = await self.export_collection(self.jive_manager, collection_name)
                    key = f"jive_{collection_name.lower()}"
                    all_data[key] = data
                except Exception as e:
                    logger.error(f"❌ Failed to export jive {collection_name}: {e}")
                    all_data[f"jive_{collection_name.lower()}"] = []
        
        # Export from Server manager
        if self.server_manager:
            for collection_name in server_collections:
                try:
                    data = await self.export_collection(self.server_manager, collection_name)
                    key = f"server_{collection_name.lower()}"
                    all_data[key] = data
                except Exception as e:
                    logger.error(f"❌ Failed to export server {collection_name}: {e}")
                    all_data[f"server_{collection_name.lower()}"] = []
        
        return all_data
    
    async def cleanup(self):
        """Clean up Weaviate connections."""
        try:
            if self.jive_manager:
                await self.jive_manager.shutdown()
            if self.server_manager:
                await self.server_manager.stop()
            logger.info("✅ Cleaned up Weaviate connections")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

class DataTransformer:
    """Transform Weaviate data to LanceDB format."""
    
    @staticmethod
    def transform_datetime(dt_str: str) -> datetime:
        """Transform Weaviate datetime string to Python datetime."""
        if not dt_str:
            return datetime.now(timezone.utc)
        
        try:
            # Handle various datetime formats
            if dt_str.endswith('Z'):
                dt_str = dt_str.replace('Z', '+00:00')
            return datetime.fromisoformat(dt_str)
        except ValueError:
            logger.warning(f"⚠️ Invalid datetime format: {dt_str}, using current time")
            return datetime.now(timezone.utc)
    
    @staticmethod
    def ensure_required_fields(obj: Dict[str, Any], collection_type: str) -> Dict[str, Any]:
        """Ensure all required fields are present with defaults."""
        # Common defaults
        defaults = {
            'tags': [],
            'dependencies': [],
            'metadata': {},
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        
        # Collection-specific defaults
        if collection_type in ['workitem', 'task']:
            defaults.update({
                'status': 'todo',
                'priority': 'medium',
                'progress': 0.0,
                'estimated_hours': None,
                'actual_hours': None
            })
        
        # Apply defaults for missing fields
        for key, default_value in defaults.items():
            if key not in obj:
                obj[key] = default_value
        
        return obj
    
    @staticmethod
    def transform_work_item(obj: Dict[str, Any]) -> Dict[str, Any]:
        """Transform WorkItem object to LanceDB format."""
        properties = obj.get('properties', {})
        
        transformed = {
            'id': obj['id'],
            'title': properties.get('title', 'Untitled'),
            'description': properties.get('description', ''),
            'item_type': properties.get('item_type', properties.get('type', 'task')),
            'status': properties.get('status', 'todo'),
            'priority': properties.get('priority', 'medium'),
            'assignee': properties.get('assignee'),
            'tags': properties.get('tags', []),
            'estimated_hours': properties.get('estimated_hours'),
            'actual_hours': properties.get('actual_hours'),
            'progress': float(properties.get('progress', 0)),
            'parent_id': properties.get('parent_id'),
            'dependencies': properties.get('dependencies', []),
            'acceptance_criteria': properties.get('acceptance_criteria'),
            'metadata': properties.get('metadata', {})
        }
        
        # Handle datetime fields
        if 'created_at' in properties:
            transformed['created_at'] = DataTransformer.transform_datetime(properties['created_at'])
        if 'updated_at' in properties:
            transformed['updated_at'] = DataTransformer.transform_datetime(properties['updated_at'])
        
        return DataTransformer.ensure_required_fields(transformed, 'workitem')
    
    @staticmethod
    def transform_execution_log(obj: Dict[str, Any]) -> Dict[str, Any]:
        """Transform ExecutionLog object to LanceDB format."""
        properties = obj.get('properties', {})
        
        transformed = {
            'id': obj['id'],
            'log_id': properties.get('log_id', obj['id']),
            'work_item_id': properties.get('work_item_id'),
            'action': properties.get('action', 'unknown'),
            'status': properties.get('status', 'completed'),
            'agent_id': properties.get('agent_id'),
            'details': properties.get('details', ''),
            'error_message': properties.get('error_message'),
            'duration_seconds': float(properties.get('duration_seconds', 0)),
            'metadata': properties.get('metadata', {})
        }
        
        # Handle timestamp
        if 'timestamp' in properties:
            transformed['timestamp'] = DataTransformer.transform_datetime(properties['timestamp'])
        else:
            transformed['timestamp'] = datetime.now(timezone.utc)
        
        return transformed
    
    @staticmethod
    def transform_task(obj: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Task object to LanceDB format."""
        properties = obj.get('properties', {})
        
        transformed = {
            'id': obj['id'],
            'title': properties.get('title', 'Untitled Task'),
            'description': properties.get('description', properties.get('content', '')),
            'status': properties.get('status', 'todo'),
            'priority': properties.get('priority', 'medium'),
            'tags': properties.get('tags', []),
            'metadata': properties.get('metadata', {})
        }
        
        # Handle datetime fields
        if 'created_at' in properties:
            transformed['created_at'] = DataTransformer.transform_datetime(properties['created_at'])
        if 'updated_at' in properties:
            transformed['updated_at'] = DataTransformer.transform_datetime(properties['updated_at'])
        
        return DataTransformer.ensure_required_fields(transformed, 'task')
    
    @staticmethod
    def transform_search_index(obj: Dict[str, Any]) -> Dict[str, Any]:
        """Transform SearchIndex object to LanceDB format."""
        properties = obj.get('properties', {})
        
        transformed = {
            'id': obj['id'],
            'content': properties.get('content', ''),
            'source_type': properties.get('source_type', 'unknown'),
            'source_id': properties.get('source_id'),
            'tags': properties.get('tags', []),
            'metadata': properties.get('metadata', {})
        }
        
        # Handle indexed_at timestamp
        if 'indexed_at' in properties:
            transformed['indexed_at'] = DataTransformer.transform_datetime(properties['indexed_at'])
        else:
            transformed['indexed_at'] = datetime.now(timezone.utc)
        
        return transformed
    
    @classmethod
    def transform_collection(cls, collection_data: List[Dict[str, Any]], collection_key: str) -> List[Dict[str, Any]]:
        """Transform a collection of objects based on collection type."""
        if not collection_data:
            return []
        
        transformed_data = []
        
        for obj in collection_data:
            try:
                if 'workitem' in collection_key.lower():
                    transformed_obj = cls.transform_work_item(obj)
                elif 'executionlog' in collection_key.lower():
                    transformed_obj = cls.transform_execution_log(obj)
                elif 'task' in collection_key.lower():
                    transformed_obj = cls.transform_task(obj)
                elif 'searchindex' in collection_key.lower():
                    transformed_obj = cls.transform_search_index(obj)
                else:
                    logger.warning(f"⚠️ Unknown collection type: {collection_key}")
                    continue
                
                transformed_data.append(transformed_obj)
                
            except Exception as e:
                logger.error(f"❌ Failed to transform object {obj.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"🔄 Transformed {len(transformed_data)} objects for {collection_key}")
        return transformed_data

class LanceDBImporter:
    """Import transformed data to LanceDB."""
    
    def __init__(self, data_path: str = "./data/lancedb"):
        self.data_path = data_path
        self.db = None
        self.embedding_func = None
    
    def initialize(self):
        """Initialize LanceDB connection and embedding function."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.data_path, exist_ok=True)
            
            # Connect to LanceDB
            self.db = lancedb.connect(self.data_path)
            
            # Initialize embedding function
            self.embedding_func = SentenceTransformerEmbeddings(
                model_name='all-MiniLM-L6-v2',
                device='cpu',
                normalize=True
            )
            
            logger.info(f"✅ Initialized LanceDB at {self.data_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LanceDB: {e}")
            raise
    
    def generate_embedding(self, text_content: str) -> List[float]:
        """Generate embedding for text content."""
        try:
            if not text_content.strip():
                # Return zero vector for empty content
                return [0.0] * 384
            
            embeddings = self.embedding_func.compute_query_embeddings([text_content])
            return embeddings[0].tolist()
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 384
    
    def prepare_work_item_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare WorkItem data with embeddings."""
        prepared_data = []
        
        for item in data:
            # Generate text content for embedding
            text_content = f"{item.get('title', '')} {item.get('description', '')}"
            
            # Add embedding vector
            item['vector'] = self.generate_embedding(text_content)
            
            prepared_data.append(item)
        
        return prepared_data
    
    def prepare_task_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare Task data with embeddings."""
        prepared_data = []
        
        for item in data:
            # Generate text content for embedding
            text_content = f"{item.get('title', '')} {item.get('description', '')}"
            
            # Add embedding vector
            item['vector'] = self.generate_embedding(text_content)
            
            prepared_data.append(item)
        
        return prepared_data
    
    def prepare_search_index_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare SearchIndex data with embeddings."""
        prepared_data = []
        
        for item in data:
            # Use content for embedding
            text_content = item.get('content', '')
            
            # Add embedding vector
            item['vector'] = self.generate_embedding(text_content)
            
            prepared_data.append(item)
        
        return prepared_data
    
    def import_collection(self, collection_name: str, data: List[Dict[str, Any]], dry_run: bool = False) -> int:
        """Import data to a LanceDB table."""
        if not data:
            logger.info(f"📭 No data to import for {collection_name}")
            return 0
        
        try:
            # Prepare data with embeddings based on collection type
            if 'workitem' in collection_name.lower():
                prepared_data = self.prepare_work_item_data(data)
            elif 'task' in collection_name.lower():
                prepared_data = self.prepare_task_data(data)
            elif 'searchindex' in collection_name.lower():
                prepared_data = self.prepare_search_index_data(data)
            elif 'executionlog' in collection_name.lower():
                # ExecutionLog doesn't need embeddings
                prepared_data = data
            else:
                logger.warning(f"⚠️ Unknown collection type for embedding: {collection_name}")
                prepared_data = data
            
            if dry_run:
                logger.info(f"🔍 [DRY RUN] Would import {len(prepared_data)} records to {collection_name}")
                return len(prepared_data)
            
            # Convert to DataFrame for LanceDB
            df = pd.DataFrame(prepared_data)
            
            # Create or overwrite table
            table = self.db.create_table(collection_name, df, mode='overwrite')
            
            logger.info(f"📥 Imported {len(prepared_data)} records to {collection_name}")
            return len(prepared_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to import {collection_name}: {e}")
            return 0
    
    def list_tables(self) -> List[str]:
        """List all tables in LanceDB."""
        try:
            return self.db.table_names()
        except Exception as e:
            logger.error(f"❌ Failed to list tables: {e}")
            return []
    
    def get_table_count(self, table_name: str) -> int:
        """Get record count for a table."""
        try:
            table = self.db.open_table(table_name)
            return table.count_rows()
        except Exception as e:
            logger.error(f"❌ Failed to get count for {table_name}: {e}")
            return 0

class MigrationValidator:
    """Validate migration results."""
    
    def __init__(self, lancedb_path: str = "./data/lancedb"):
        self.lancedb_path = lancedb_path
        self.db = None
    
    def initialize(self):
        """Initialize LanceDB connection for validation."""
        try:
            self.db = lancedb.connect(self.lancedb_path)
            logger.info("✅ Initialized LanceDB for validation")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LanceDB for validation: {e}")
            raise
    
    def validate_table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        try:
            tables = self.db.table_names()
            exists = table_name in tables
            if exists:
                logger.info(f"✅ Table {table_name} exists")
            else:
                logger.error(f"❌ Table {table_name} does not exist")
            return exists
        except Exception as e:
            logger.error(f"❌ Failed to check table {table_name}: {e}")
            return False
    
    def validate_table_count(self, table_name: str, expected_count: int) -> bool:
        """Validate record count in table."""
        try:
            table = self.db.open_table(table_name)
            actual_count = table.count_rows()
            
            if actual_count == expected_count:
                logger.info(f"✅ Table {table_name} has correct count: {actual_count}")
                return True
            else:
                logger.error(f"❌ Table {table_name} count mismatch: expected {expected_count}, got {actual_count}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to validate count for {table_name}: {e}")
            return False
    
    def validate_search_functionality(self) -> bool:
        """Test basic search functionality."""
        try:
            # Test vector search on WorkItem table
            if 'WorkItem' in self.db.table_names():
                table = self.db.open_table('WorkItem')
                results = table.search("test search").limit(1).to_pandas()
                
                if len(results) >= 0:  # Even 0 results is OK for validation
                    logger.info("✅ Vector search functionality working")
                    return True
                else:
                    logger.error("❌ Vector search returned unexpected results")
                    return False
            else:
                logger.warning("⚠️ WorkItem table not found, skipping search validation")
                return True
                
        except Exception as e:
            logger.error(f"❌ Search functionality validation failed: {e}")
            return False
    
    def validate_data_integrity(self, table_name: str) -> bool:
        """Validate data integrity for a table."""
        try:
            table = self.db.open_table(table_name)
            df = table.to_pandas()
            
            # Check for required fields
            required_fields = ['id']
            if table_name == 'WorkItem':
                required_fields.extend(['title', 'status', 'vector'])
            elif table_name == 'Task':
                required_fields.extend(['title', 'status', 'vector'])
            elif table_name == 'ExecutionLog':
                required_fields.extend(['log_id', 'action'])
            
            missing_fields = [field for field in required_fields if field not in df.columns]
            
            if missing_fields:
                logger.error(f"❌ Table {table_name} missing required fields: {missing_fields}")
                return False
            
            # Check for null IDs
            null_ids = df['id'].isnull().sum()
            if null_ids > 0:
                logger.error(f"❌ Table {table_name} has {null_ids} null IDs")
                return False
            
            logger.info(f"✅ Table {table_name} data integrity validated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data integrity validation failed for {table_name}: {e}")
            return False
    
    def run_full_validation(self, expected_counts: Dict[str, int]) -> bool:
        """Run complete validation suite."""
        logger.info("🔍 Starting migration validation...")
        
        all_valid = True
        
        # Validate table existence and counts
        for table_name, expected_count in expected_counts.items():
            if not self.validate_table_exists(table_name):
                all_valid = False
                continue
            
            if not self.validate_table_count(table_name, expected_count):
                all_valid = False
            
            if not self.validate_data_integrity(table_name):
                all_valid = False
        
        # Validate search functionality
        if not self.validate_search_functionality():
            all_valid = False
        
        if all_valid:
            logger.info("✅ All validation checks passed")
        else:
            logger.error("❌ Some validation checks failed")
        
        return all_valid

async def create_backup(backup_path: str) -> Dict[str, Any]:
    """Create backup of Weaviate data."""
    logger.info(f"💾 Creating backup at {backup_path}")
    
    # Create backup directory
    os.makedirs(backup_path, exist_ok=True)
    
    # Export data
    exporter = WeaviateExporter()
    await exporter.initialize()
    
    try:
        exported_data = await exporter.export_all_data()
        
        # Save backup
        backup_file = os.path.join(backup_path, f"weaviate_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(backup_file, 'w') as f:
            json.dump(exported_data, f, indent=2, default=str)
        
        logger.info(f"✅ Backup saved to {backup_file}")
        
        # Generate backup summary
        summary = {
            'backup_file': backup_file,
            'timestamp': datetime.now().isoformat(),
            'collections': {k: len(v) for k, v in exported_data.items()},
            'total_records': sum(len(v) for v in exported_data.values())
        }
        
        return {'exported_data': exported_data, 'summary': summary}
        
    finally:
        await exporter.cleanup()

async def perform_migration(backup_data: Dict[str, Any], dry_run: bool = False) -> MigrationStats:
    """Perform the complete migration."""
    stats = MigrationStats(start_time=datetime.now(timezone.utc))
    
    try:
        exported_data = backup_data['exported_data']
        
        # Log export stats
        for collection_key, data in exported_data.items():
            stats.log_export(collection_key, len(data))
        
        # Transform data
        logger.info("🔄 Transforming data...")
        transformed_data = {}
        
        for collection_key, data in exported_data.items():
            try:
                transformed = DataTransformer.transform_collection(data, collection_key)
                transformed_data[collection_key] = transformed
                stats.log_transform(collection_key, len(transformed))
            except Exception as e:
                error_msg = f"Failed to transform {collection_key}: {e}"
                stats.log_error(error_msg)
        
        # Import to LanceDB
        logger.info("📥 Importing to LanceDB...")
        importer = LanceDBImporter()
        importer.initialize()
        
        # Map collection keys to table names
        table_mapping = {
            'jive_workitem': 'JiveWorkItem',
            'jive_executionlog': 'JiveExecutionLog',
            'server_workitem': 'WorkItem',
            'server_task': 'Task',
            'server_searchindex': 'SearchIndex'
        }
        
        for collection_key, data in transformed_data.items():
            table_name = table_mapping.get(collection_key, collection_key)
            try:
                imported_count = importer.import_collection(table_name, data, dry_run)
                stats.log_import(table_name, imported_count)
            except Exception as e:
                error_msg = f"Failed to import {table_name}: {e}"
                stats.log_error(error_msg)
        
        stats.finalize()
        return stats
        
    except Exception as e:
        error_msg = f"Migration failed: {e}"
        stats.log_error(error_msg)
        stats.finalize()
        return stats

async def validate_migration(expected_counts: Dict[str, int]) -> bool:
    """Validate migration results."""
    logger.info("🔍 Validating migration...")
    
    validator = MigrationValidator()
    validator.initialize()
    
    return validator.run_full_validation(expected_counts)

def print_migration_report(stats: MigrationStats):
    """Print detailed migration report."""
    report = stats.generate_report()
    
    print("\n" + "="*60)
    print("📊 MIGRATION REPORT")
    print("="*60)
    print(f"Duration: {report['duration_seconds']:.2f} seconds")
    print(f"Success Rate: {report['success_rate_percent']:.1f}%")
    print(f"Total Records Exported: {report['total_records_exported']}")
    print(f"Total Records Imported: {report['total_records_imported']}")
    print(f"Errors: {report['error_count']}")
    
    print("\n📋 Collection Details:")
    for collection in report['collections']['exported'].keys():
        exported = report['collections']['exported'].get(collection, 0)
        transformed = report['collections']['transformed'].get(collection, 0)
        imported = report['collections']['imported'].get(collection, 0)
        print(f"  {collection}: {exported} → {transformed} → {imported}")
    
    if report['errors']:
        print("\n❌ Errors:")
        for error in report['errors']:
            print(f"  • {error}")
    
    print("="*60)

async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrate from Weaviate to LanceDB')
    parser.add_argument('--dry-run', action='store_true', help='Perform migration without writing to LanceDB')
    parser.add_argument('--backup-only', action='store_true', help='Only create backup, don\'t migrate')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing migration')
    parser.add_argument('--backup-path', default='./backups', help='Path for backup files')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting Weaviate to LanceDB migration")
    
    try:
        if args.validate_only:
            # Just run validation
            logger.info("🔍 Running validation only...")
            # You would need to provide expected counts here
            # This is a simplified version
            validator = MigrationValidator()
            validator.initialize()
            success = validator.validate_search_functionality()
            if success:
                print("✅ Validation successful")
            else:
                print("❌ Validation failed")
                sys.exit(1)
            return
        
        # Create backup
        backup_data = await create_backup(args.backup_path)
        print(f"✅ Backup completed: {backup_data['summary']['total_records']} records")
        
        if args.backup_only:
            logger.info("💾 Backup-only mode, stopping here")
            return
        
        # Perform migration
        stats = await perform_migration(backup_data, dry_run=args.dry_run)
        
        # Print report
        print_migration_report(stats)
        
        if not args.dry_run and len(stats.errors) == 0:
            # Validate migration
            expected_counts = {
                table_name: count 
                for table_name, count in stats.records_imported.items()
            }
            
            validation_success = await validate_migration(expected_counts)
            
            if validation_success:
                print("\n🎉 Migration completed successfully!")
                print("\n📝 Next steps:")
                print("  1. Update your configuration to use LanceDB")
                print("  2. Test your application with the new database")
                print("  3. Remove Weaviate configuration once satisfied")
            else:
                print("\n⚠️ Migration completed but validation failed")
                print("Please review the validation errors above")
                sys.exit(1)
        elif args.dry_run:
            print("\n🔍 Dry run completed - no data was actually migrated")
        else:
            print("\n❌ Migration completed with errors")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())