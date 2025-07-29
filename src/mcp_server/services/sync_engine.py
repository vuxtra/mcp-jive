"""Sync Engine for Task Storage and Sync System.

Handles bidirectional synchronization between local file system and Weaviate database.
Manages conflict resolution, change detection, and sync state tracking.
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from ..database import WeaviateManager
from ..config import ServerConfig
from .file_format_handler import FileFormatHandler, WorkItemSchema

logger = logging.getLogger(__name__)

class SyncDirection(Enum):
    """Sync direction enumeration."""
    FILE_TO_DB = "file_to_db"
    DB_TO_FILE = "db_to_file"
    BIDIRECTIONAL = "bidirectional"

class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    AUTO_MERGE = "auto_merge"
    FILE_WINS = "file_wins"
    DATABASE_WINS = "database_wins"
    MANUAL_RESOLUTION = "manual_resolution"
    CREATE_BRANCH = "create_branch"

class SyncStatus(Enum):
    """Sync operation status."""
    SUCCESS = "success"
    CONFLICT = "conflict"
    ERROR = "error"
    SKIPPED = "skipped"
    PENDING = "pending"

class SyncResult:
    """Result of a sync operation."""
    
    def __init__(self, 
                 status: SyncStatus,
                 message: str,
                 file_path: Optional[str] = None,
                 work_item_id: Optional[str] = None,
                 conflicts: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.status = status
        self.message = message
        self.file_path = file_path
        self.work_item_id = work_item_id
        self.conflicts = conflicts or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "status": self.status.value,
            "message": self.message,
            "file_path": self.file_path,
            "work_item_id": self.work_item_id,
            "conflicts": self.conflicts,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

class SyncEngine:
    """Core synchronization engine."""
    
    def __init__(self, config: ServerConfig, weaviate_manager: WeaviateManager):
        self.config = config
        self.weaviate_manager = weaviate_manager
        self.file_handler = FileFormatHandler()
        self.logger = logging.getLogger(__name__)
        
        # Sync state tracking
        self.sync_state: Dict[str, Dict[str, Any]] = {}
        self.active_syncs: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> None:
        """Initialize the sync engine."""
        try:
            self.logger.info("Initializing Sync Engine...")
            
            # Load existing sync state if available
            await self._load_sync_state()
            
            self.logger.info("Sync Engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Sync Engine: {e}")
            raise
            
    async def sync_file_to_database(self, 
                                   file_path: str, 
                                   file_content: str,
                                   conflict_resolution: ConflictResolution = ConflictResolution.AUTO_MERGE) -> SyncResult:
        """Sync a file to the database.
        
        Args:
            file_path: Path to the file
            file_content: Content of the file
            conflict_resolution: Strategy for handling conflicts
            
        Returns:
            SyncResult with operation details
        """
        try:
            self.logger.info(f"Syncing file to database: {file_path}")
            
            # Parse file content
            work_item = await self.file_handler.parse_file_content(file_content, file_path)
            if not work_item:
                return SyncResult(
                    status=SyncStatus.ERROR,
                    message=f"Failed to parse file content: {file_path}",
                    file_path=file_path
                )
                
            # Check if work item exists in database
            existing_item = await self._get_work_item_from_db(work_item.id)
            
            if existing_item:
                # Handle potential conflict
                conflict_result = await self._handle_conflict(
                    work_item, existing_item, conflict_resolution, SyncDirection.FILE_TO_DB
                )
                if conflict_result.status == SyncStatus.CONFLICT:
                    return conflict_result
                work_item = conflict_result.metadata.get("resolved_item", work_item)
                
            # Update database
            await self._update_work_item_in_db(work_item)
            
            # Update sync state
            await self._update_sync_state(file_path, work_item.id, file_content)
            
            return SyncResult(
                status=SyncStatus.SUCCESS,
                message=f"Successfully synced file to database: {file_path}",
                file_path=file_path,
                work_item_id=work_item.id
            )
            
        except Exception as e:
            self.logger.error(f"Error syncing file to database: {e}")
            return SyncResult(
                status=SyncStatus.ERROR,
                message=f"Error syncing file to database: {str(e)}",
                file_path=file_path
            )
            
    async def sync_database_to_file(self, 
                                   work_item_id: str,
                                   target_format: str = ".json",
                                   conflict_resolution: ConflictResolution = ConflictResolution.AUTO_MERGE) -> SyncResult:
        """Sync a work item from database to file.
        
        Args:
            work_item_id: ID of the work item to sync
            target_format: Target file format
            conflict_resolution: Strategy for handling conflicts
            
        Returns:
            SyncResult with operation details and file content
        """
        try:
            self.logger.info(f"Syncing database to file: {work_item_id}")
            
            # Get work item from database
            work_item_data = await self._get_work_item_from_db(work_item_id)
            if not work_item_data:
                return SyncResult(
                    status=SyncStatus.ERROR,
                    message=f"Work item not found in database: {work_item_id}",
                    work_item_id=work_item_id
                )
                
            work_item = WorkItemSchema(**work_item_data)
            
            # Generate file path
            file_path = await self._generate_file_path(work_item, target_format)
            
            # Check for existing file conflicts
            existing_file_content = await self._get_existing_file_content(file_path)
            if existing_file_content:
                existing_work_item = await self.file_handler.parse_file_content(
                    existing_file_content, file_path
                )
                if existing_work_item:
                    conflict_result = await self._handle_conflict(
                        work_item, existing_work_item.dict(), conflict_resolution, SyncDirection.DB_TO_FILE
                    )
                    if conflict_result.status == SyncStatus.CONFLICT:
                        return conflict_result
                    work_item = WorkItemSchema(**conflict_result.metadata.get("resolved_item", work_item.dict()))
                    
            # Format work item content
            file_content = await self.file_handler.format_work_item(work_item, target_format)
            
            # Update sync state
            await self._update_sync_state(file_path, work_item_id, file_content)
            
            return SyncResult(
                status=SyncStatus.SUCCESS,
                message=f"Successfully synced database to file: {file_path}",
                file_path=file_path,
                work_item_id=work_item_id,
                metadata={"file_content": file_content}
            )
            
        except Exception as e:
            self.logger.error(f"Error syncing database to file: {e}")
            return SyncResult(
                status=SyncStatus.ERROR,
                message=f"Error syncing database to file: {str(e)}",
                work_item_id=work_item_id
            )
            
    async def get_sync_status(self, identifier: str) -> Dict[str, Any]:
        """Get sync status for a file path or work item ID.
        
        Args:
            identifier: File path or work item ID
            
        Returns:
            Sync status information
        """
        try:
            # Check if identifier is in sync state
            if identifier in self.sync_state:
                state = self.sync_state[identifier]
                return {
                    "identifier": identifier,
                    "last_sync": state.get("last_sync"),
                    "checksum": state.get("checksum"),
                    "work_item_id": state.get("work_item_id"),
                    "file_path": state.get("file_path"),
                    "sync_direction": state.get("sync_direction"),
                    "status": "synced"
                }
                
            # Check active syncs
            if identifier in self.active_syncs:
                return {
                    "identifier": identifier,
                    "status": "syncing",
                    "started_at": self.active_syncs[identifier].get("started_at"),
                    "operation": self.active_syncs[identifier].get("operation")
                }
                
            # Check if it's a work item ID in database
            work_item = await self._get_work_item_from_db(identifier)
            if work_item:
                return {
                    "identifier": identifier,
                    "status": "database_only",
                    "work_item_id": identifier,
                    "last_updated": work_item.get("updated_at")
                }
                
            return {
                "identifier": identifier,
                "status": "not_found",
                "message": "No sync information found for identifier"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting sync status: {e}")
            return {
                "identifier": identifier,
                "status": "error",
                "message": str(e)
            }
            
    async def _handle_conflict(self, 
                              new_item: Union[WorkItemSchema, Dict[str, Any]], 
                              existing_item: Dict[str, Any],
                              resolution: ConflictResolution,
                              direction: SyncDirection) -> SyncResult:
        """Handle conflicts between file and database versions."""
        try:
            new_data = new_item.dict() if isinstance(new_item, WorkItemSchema) else new_item
            
            # Detect conflicts
            conflicts = await self._detect_conflicts(new_data, existing_item)
            
            if not conflicts:
                return SyncResult(
                    status=SyncStatus.SUCCESS,
                    message="No conflicts detected",
                    metadata={"resolved_item": new_data}
                )
                
            # Apply resolution strategy
            if resolution == ConflictResolution.AUTO_MERGE:
                resolved_item = await self._auto_merge(new_data, existing_item)
            elif resolution == ConflictResolution.FILE_WINS:
                resolved_item = new_data if direction == SyncDirection.FILE_TO_DB else existing_item
            elif resolution == ConflictResolution.DATABASE_WINS:
                resolved_item = existing_item if direction == SyncDirection.FILE_TO_DB else new_data
            elif resolution == ConflictResolution.MANUAL_RESOLUTION:
                return SyncResult(
                    status=SyncStatus.CONFLICT,
                    message="Manual resolution required",
                    conflicts=conflicts,
                    metadata={"new_item": new_data, "existing_item": existing_item}
                )
            else:
                return SyncResult(
                    status=SyncStatus.CONFLICT,
                    message=f"Unsupported resolution strategy: {resolution.value}",
                    conflicts=conflicts
                )
                
            return SyncResult(
                status=SyncStatus.SUCCESS,
                message=f"Conflicts resolved using {resolution.value}",
                conflicts=conflicts,
                metadata={"resolved_item": resolved_item}
            )
            
        except Exception as e:
            self.logger.error(f"Error handling conflict: {e}")
            return SyncResult(
                status=SyncStatus.ERROR,
                message=f"Error handling conflict: {str(e)}"
            )
            
    async def _detect_conflicts(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> List[str]:
        """Detect conflicts between two work items."""
        conflicts = []
        
        # Compare key fields
        conflict_fields = ['title', 'description', 'status', 'priority', 'assignee']
        
        for field in conflict_fields:
            if item1.get(field) != item2.get(field):
                conflicts.append(f"Field '{field}' differs: '{item1.get(field)}' vs '{item2.get(field)}'")
                
        # Check timestamps
        item1_updated = item1.get('updated_at', '')
        item2_updated = item2.get('updated_at', '')
        
        if item1_updated and item2_updated and item1_updated != item2_updated:
            conflicts.append(f"Update timestamps differ: {item1_updated} vs {item2_updated}")
            
        return conflicts
        
    async def _auto_merge(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically merge two work items."""
        # Use the most recent version as base
        item1_updated = item1.get('updated_at', '')
        item2_updated = item2.get('updated_at', '')
        
        if item1_updated > item2_updated:
            base_item = item1.copy()
            other_item = item2
        else:
            base_item = item2.copy()
            other_item = item1
            
        # Merge arrays (tags, children, dependencies)
        for field in ['tags', 'children', 'dependencies']:
            base_list = set(base_item.get(field, []))
            other_list = set(other_item.get(field, []))
            base_item[field] = list(base_list.union(other_list))
            
        # Update timestamp
        base_item['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        return base_item
        
    async def _calculate_checksum(self, content: str) -> str:
        """Calculate checksum for content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
        
    async def _update_sync_state(self, file_path: str, work_item_id: str, content: str) -> None:
        """Update sync state tracking."""
        checksum = await self._calculate_checksum(content)
        
        self.sync_state[file_path] = {
            "work_item_id": work_item_id,
            "file_path": file_path,
            "checksum": checksum,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "sync_direction": "bidirectional"
        }
        
        # Also track by work item ID
        self.sync_state[work_item_id] = self.sync_state[file_path].copy()
        
    async def _load_sync_state(self) -> None:
        """Load sync state from storage."""
        # In a real implementation, this would load from a persistent store
        # For now, initialize empty state
        self.sync_state = {}
        
    async def _get_work_item_from_db(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get work item from Weaviate database."""
        try:
            # Query Weaviate for the work item
            query = f"""
            {{
                Get {{
                    Task(where: {{path: ["id"], operator: Equal, valueText: "{work_item_id}"}}) {{
                        id
                        title
                        description
                        type
                        status
                        priority
                        assignee
                        parent_id
                        children
                        dependencies
                        tags
                        metadata
                        created_at
                        updated_at
                        estimated_hours
                        actual_hours
                        progress
                    }}
                }}
            }}
            """
            
            result = await self.weaviate_manager.query(query)
            
            if result and 'data' in result and 'Get' in result['data'] and 'Task' in result['data']['Get']:
                tasks = result['data']['Get']['Task']
                if tasks:
                    return tasks[0]
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting work item from database: {e}")
            return None
            
    async def _update_work_item_in_db(self, work_item: WorkItemSchema) -> None:
        """Update work item in Weaviate database."""
        try:
            # Convert to database format
            data = work_item.dict()
            
            # Update timestamp
            data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Use Weaviate manager to update
            await self.weaviate_manager.upsert_object(
                class_name="Task",
                object_id=work_item.id,
                properties=data
            )
            
        except Exception as e:
            self.logger.error(f"Error updating work item in database: {e}")
            raise
            
    async def _generate_file_path(self, work_item: WorkItemSchema, format_ext: str) -> str:
        """Generate file path for work item."""
        # Create path based on work item type and ID
        safe_title = "".join(c for c in work_item.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_').lower()
        
        filename = f"{work_item.id}_{safe_title}{format_ext}"
        return f".jivedev/tasks/{work_item.type}/{filename}"
        
    async def _get_existing_file_content(self, file_path: str) -> Optional[str]:
        """Get existing file content if it exists."""
        # This would be implemented by the MCP client
        # For now, return None to indicate no existing file
        return None
        
    async def cleanup(self) -> None:
        """Cleanup sync engine resources."""
        try:
            self.logger.info("Cleaning up Sync Engine...")
            
            # Clear active syncs
            self.active_syncs.clear()
            
            # Save sync state if needed
            # In a real implementation, this would persist the state
            
            self.logger.info("Sync Engine cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during Sync Engine cleanup: {e}")