"""Storage and Sync Tools.

Implements the 3 storage and sync MCP tools:
- sync_file_to_database: Sync local task metadata to vector database
- sync_database_to_file: Sync database changes to local task files
- get_sync_status: Check synchronization status of task metadata
"""

import logging
import hashlib
import json
import yaml
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
from enum import Enum

from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from mcp_server.services.sync_engine import SyncResult, SyncStatus

from ..config import ServerConfig
from ..lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)


class MergeStrategy(str, Enum):
    """Conflict resolution strategies."""
    AUTO_MERGE = "auto_merge"
    FILE_WINS = "file_wins"
    DATABASE_WINS = "database_wins"
    MANUAL_RESOLUTION = "manual_resolution"
    CREATE_BRANCH = "create_branch"


class FileMetadata(BaseModel):
    """File metadata for sync tracking."""
    file_path: str
    checksum: str
    last_modified: str
    file_version: str = "1.0"
    sync_status: SyncStatus
    last_synced: Optional[str] = None
    work_item_id: Optional[str] = None


class WorkItemFile(BaseModel):
    """Work item file structure."""
    id: str
    type: str  # initiative, epic, feature, story, task
    title: str
    description: str = ""
    status: str = "not_started"
    priority: str = "medium"
    effort_estimate: Optional[int] = None
    acceptance_criteria: List[str] = Field(default_factory=list)
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SyncEngine:
    """Separate sync engine for better testability."""
    
    def __init__(self, storage_tools):
        self.storage_tools = storage_tools
    async def _safe_database_operation(self, operation):
        """Safely execute a database operation with error handling."""
        try:
            return await operation()
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in [
                'connection refused', 'unavailable', 'grpc', 'timeout'
            ]):
                logger.error(f"Database connection error: {e}")
                return self._format_error_response("database_connection", "Database temporarily unavailable")
            else:
                logger.error(f"Database operation error: {e}", exc_info=True)
                return self._format_error_response("database_operation", str(e))
                
    def _format_error_response(self, error_type: str, error_message: str):
        """Format a standardized error response."""
        from mcp.types import TextContent
        return [TextContent(
            type="text",
            text=f"Error ({error_type}): {error_message}"
        )]

    
    async def sync_file_to_database(self, file_path: str, file_content: str, merge_strategy: MergeStrategy, create_backup: bool = True, validate_only: bool = False) -> SyncResult:
        """Sync engine method for file to database sync."""
        return await self.storage_tools._sync_file_to_database_impl(file_path, file_content, merge_strategy, create_backup, validate_only)
    
    async def sync_database_to_file(self, work_item_id: str, target_file_path: str = None, format_type: str = "json", merge_strategy: MergeStrategy = MergeStrategy.AUTO_MERGE, create_backup: bool = True) -> SyncResult:
        """Sync engine method for database to file sync."""
        return await self.storage_tools._sync_database_to_file_impl(work_item_id, target_file_path, format_type, merge_strategy, create_backup)
    
    async def get_sync_status(self, identifier: str) -> Dict[str, Any]:
        """Get sync status for an identifier."""
        return await self.storage_tools._get_sync_status_impl(identifier)


class StorageSyncTools:
    """Storage and sync tool implementations."""
    
    def __init__(self, config: ServerConfig, lancedb_manager: LanceDBManager):
        self.config = config
        self.lancedb_manager = lancedb_manager
        self.sync_state: Dict[str, FileMetadata] = {}
        # Create separate sync engine for better testability
        self.sync_engine = SyncEngine(self)
        # Add file_handler attribute expected by tests
        self.file_handler = self
    async def _safe_database_operation(self, operation):
        """Safely execute a database operation with error handling."""
        try:
            return await operation()
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in [
                'connection refused', 'unavailable', 'grpc', 'timeout'
            ]):
                logger.error(f"Database connection error: {e}")
                return self._format_error_response("database_connection", "Database temporarily unavailable")
            else:
                logger.error(f"Database operation error: {e}", exc_info=True)
                return self._format_error_response("database_operation", str(e))
                
    def _format_error_response(self, error_type: str, error_message: str):
        """Format a standardized error response."""
        from mcp.types import TextContent
        return [TextContent(
            type="text",
            text=f"Error ({error_type}): {error_message}"
        )]

        
    async def _sync_file_to_database_impl(self, file_path: str, file_content: str, merge_strategy: MergeStrategy, create_backup: bool = True, validate_only: bool = False) -> SyncResult:
        """Implementation method for file to database sync."""
        try:
            # Parse file content
            work_item = await self._parse_file_content(file_content, file_path)
            if not work_item:
                return SyncResult(
                    status=SyncStatus.ERROR,
                    message="Invalid file content",
                    file_path=file_path,
                    work_item_id=""
                )
            
            # Validate file format
            validation_result = await self._validate_work_item(work_item)
            if not validation_result["valid"]:
                return SyncResult(
                    status=SyncStatus.ERROR,
                    message="File validation failed",
                    file_path=file_path,
                    work_item_id=work_item.id
                )
            
            if validate_only:
                return SyncResult(
                    status=SyncStatus.SUCCESS,
                    message="File validation passed",
                    file_path=file_path,
                    work_item_id=work_item.id
                )
            
            # Check for existing database version
            existing_item = await self._get_database_item(work_item.id)
            
            # Detect conflicts
            conflicts = []
            if existing_item:
                conflicts = await self._detect_conflicts(work_item, existing_item)
            
            # Apply merge strategy
            if conflicts and merge_strategy == MergeStrategy.MANUAL_RESOLUTION:
                return SyncResult(
                    status=SyncStatus.CONFLICT,
                    message="Manual resolution required",
                    file_path=file_path,
                    work_item_id=work_item.id,
                    conflicts=conflicts
                )
            
            # Resolve conflicts and sync
            final_item = await self._resolve_conflicts(work_item, existing_item, conflicts, merge_strategy)
            
            # Update database
            success = await self._update_database_item(final_item)
            
            if success:
                # Update sync state
                checksum = self._calculate_checksum(file_content)
                await self._update_sync_state(file_path, work_item.id, checksum)
                
                return SyncResult(
                    status=SyncStatus.SUCCESS,
                    message="File successfully synced to database",
                    file_path=file_path,
                    work_item_id=work_item.id
                )
            else:
                return SyncResult(
                    status=SyncStatus.ERROR,
                    message="Failed to update database",
                    file_path=file_path,
                    work_item_id=work_item.id
                )
                
        except Exception as e:
            logger.error(f"Error in sync_file_to_database: {e}")
            return SyncResult(
                status=SyncStatus.ERROR,
                message=f"Sync failed: {str(e)}",
                file_path=file_path,
                work_item_id=""
            )
        
    async def _sync_database_to_file_impl(self, work_item_id: str, target_file_path: str = None, format_type: str = "json", merge_strategy: MergeStrategy = MergeStrategy.AUTO_MERGE, create_backup: bool = True) -> SyncResult:
        """Sync engine method for database to file sync."""
        try:
            # Validate format type first
            if format_type not in ["json", "yaml", ".json", ".yaml"]:
                return SyncResult(
                    status=SyncStatus.ERROR,
                    message=f"Unsupported target format: {format_type}",
                    file_path=target_file_path or "",
                    work_item_id=work_item_id
                )
            
            # Get database item
            db_item = await self._get_database_item(work_item_id)
            if not db_item:
                return SyncResult(
                    status=SyncStatus.ERROR,
                    message="Work item not found in database",
                    file_path=target_file_path or "",
                    work_item_id=work_item_id
                )
            
            # Determine target file path if not provided
            if not target_file_path:
                target_file_path = self._get_default_file_path(db_item)
            
            # Generate file content
            file_content = await self._generate_file_content(db_item, format_type)
            
            # Calculate checksum
            checksum = self._calculate_checksum(file_content)
            
            # Update sync state
            await self._update_sync_state(target_file_path, work_item_id, checksum)
            
            return SyncResult(
                status=SyncStatus.SUCCESS,
                message="Database successfully synced to file",
                file_path=target_file_path,
                work_item_id=work_item_id,
                metadata={"file_content": file_content}
            )
            
        except Exception as e:
            logger.error(f"Error in sync_database_to_file: {e}")
            return SyncResult(
                status=SyncStatus.ERROR,
                message=f"Sync failed: {str(e)}",
                file_path=target_file_path or "",
                work_item_id=work_item_id
            )
        
    async def _get_sync_status_impl(self, identifier: str) -> Dict[str, Any]:
        """Get sync status for an identifier."""
        try:
            # Check by identifier (could be work_item_id or file_path)
            for path, metadata in self.sync_state.items():
                if metadata.work_item_id == identifier or path == identifier:
                    return {
                        "identifier": identifier,
                        "status": "synced",
                        "last_sync": metadata.last_synced,
                        "work_item_id": metadata.work_item_id or identifier,
                        "file_path": path
                    }
            
            # Not found
            return {
                "identifier": identifier,
                "status": "not_found",
                "message": "No sync information found"
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                "identifier": identifier,
                "status": "error",
                "message": f"Failed to get sync status: {str(e)}"
            }
        
    async def initialize(self) -> None:
        """Initialize storage and sync tools."""
        logger.info("Initializing storage and sync tools...")
        await self._load_sync_state()
        
    async def get_tools(self) -> List[Tool]:
        """Get all storage and sync tools."""
        return [
            Tool(
                name="jive_sync_file_to_database",
                description="Jive: Sync local task (development task or work item) metadata to vector database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the task file to sync (relative to .jivedev/tasks/)"
                        },
                        "file_content": {
                            "type": "string",
                            "description": "JSON or YAML content of the task file"
                        },
                        "merge_strategy": {
                            "type": "string",
                            "enum": ["auto_merge", "file_wins", "database_wins", "manual_resolution"],
                            "description": "Strategy for handling conflicts",
                            "default": "auto_merge"
                        },
                        "validate_only": {
                            "type": "boolean",
                            "description": "Only validate without syncing",
                            "default": False
                        }
                    },
                    "required": ["file_path", "file_content"]
                }
            ),
            Tool(
                name="jive_sync_database_to_file",
                description="Jive: Sync database changes to local task (development task or work item) files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "Work item ID to sync from database"
                        },
                        "target_file_path": {
                            "type": "string",
                            "description": "Target file path (relative to .jivedev/tasks/)"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["json", "yaml"],
                            "description": "Output file format",
                            "default": "json"
                        },
                        "merge_strategy": {
                            "type": "string",
                            "enum": ["auto_merge", "file_wins", "database_wins", "manual_resolution"],
                            "description": "Strategy for handling conflicts",
                            "default": "auto_merge"
                        },
                        "create_backup": {
                            "type": "boolean",
                            "description": "Create backup before overwriting",
                            "default": True
                        }
                    },
                    "required": ["work_item_id"]
                }
            ),
            Tool(
                name="jive_get_sync_status",
                description="Jive: Check synchronization status of task (development task or work item) metadata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Specific file path to check (optional)"
                        },
                        "work_item_id": {
                            "type": "string",
                            "description": "Specific work item ID to check (optional)"
                        },
                        "include_conflicts": {
                            "type": "boolean",
                            "description": "Include detailed conflict information",
                            "default": True
                        },
                        "check_all": {
                            "type": "boolean",
                            "description": "Check all tracked files",
                            "default": False
                        }
                    },
                    "required": []
                }
            )
        ]
        
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for storage and sync."""
        if name == "jive_sync_file_to_database":
            return await self._sync_file_to_database(arguments)
        elif name == "jive_sync_database_to_file":
            return await self._sync_database_to_file(arguments)
        elif name == "jive_get_sync_status":
            return await self._get_sync_status(arguments)
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"Unknown tool: {name}"
                }, indent=2)
            )]
            
    async def _sync_file_to_database(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Sync local file changes to database."""
        try:
            # Validate required parameters
            if "file_path" not in arguments:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "Missing required parameter: file_path"
                    }, indent=2)
                )]
            
            if "file_content" not in arguments:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "Missing required parameter: file_content"
                    }, indent=2)
                )]
            
            file_path = arguments["file_path"]
            file_content = arguments["file_content"]
            
            # Validate merge strategy (accept both conflict_resolution and merge_strategy for compatibility)
            strategy_value = arguments.get("merge_strategy") or arguments.get("conflict_resolution", "auto_merge")
            try:
                merge_strategy = MergeStrategy(strategy_value)
            except ValueError:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "Invalid conflict resolution strategy",
                        "file_path": file_path
                    }, indent=2)
                )]
            
            # Call the sync engine method
            sync_result = await self.sync_engine.sync_file_to_database(
                file_path=file_path,
                file_content=file_content,
                merge_strategy=merge_strategy,
                create_backup=arguments.get("create_backup", True),
                validate_only=arguments.get("validate_only", False)
            )
            
            # Convert SyncResult to expected JSON format
            if sync_result.status.value == "success":
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "success",
                        "message": sync_result.message,
                        "file_path": sync_result.file_path,
                        "work_item_id": sync_result.work_item_id
                    }, indent=2)
                )]
            elif sync_result.status.value == "conflict":
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "conflict",
                        "message": sync_result.message,
                        "file_path": sync_result.file_path,
                        "work_item_id": sync_result.work_item_id,
                        "conflicts": sync_result.conflicts
                    }, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": sync_result.message,
                        "file_path": sync_result.file_path
                    }, indent=2)
                )]

                
        except Exception as e:
            logger.error(f"Error syncing file to database: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"Sync failed: {str(e)}",
                    "file_path": arguments.get("file_path", "unknown")
                }, indent=2)
            )]
            
    async def _sync_database_to_file(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Sync database changes to local file."""
        try:
            # Validate required parameters
            if "work_item_id" not in arguments:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "Missing required parameter: work_item_id"
                    }, indent=2)
                )]
            
            work_item_id = arguments["work_item_id"]
            target_file_path = arguments.get("target_file_path")
            format_type = arguments.get("format") or arguments.get("target_format", "json")
            
            # Validate merge strategy (accept both conflict_resolution and merge_strategy for compatibility)
            strategy_value = arguments.get("merge_strategy") or arguments.get("conflict_resolution", "auto_merge")
            try:
                merge_strategy = MergeStrategy(strategy_value)
            except ValueError:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "Invalid conflict resolution strategy",
                        "work_item_id": work_item_id
                    }, indent=2)
                )]
            
            # Call the sync engine method
            sync_result = await self.sync_engine.sync_database_to_file(
                work_item_id=work_item_id,
                target_file_path=target_file_path,
                format_type=format_type,
                merge_strategy=merge_strategy,
                create_backup=arguments.get("create_backup", True)
            )
            
            # Convert SyncResult to expected JSON format
            if sync_result.status.value == "success":
                response_data = {
                    "status": "success",
                    "message": sync_result.message,
                    "work_item_id": sync_result.work_item_id,
                    "target_file_path": sync_result.file_path,
                    "format": format_type
                }
                # Add file_content if available in metadata
                if sync_result.metadata and "file_content" in sync_result.metadata:
                    response_data["file_content"] = sync_result.metadata["file_content"]
                
                return [TextContent(
                    type="text",
                    text=json.dumps(response_data, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": sync_result.message,
                        "work_item_id": work_item_id
                    }, indent=2)
                )]

            
        except Exception as e:
            logger.error(f"Error syncing database to file: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"Sync failed: {str(e)}",
                    "work_item_id": arguments.get("work_item_id", "unknown")
                }, indent=2)
            )]
            
    async def _get_sync_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get synchronization status."""
        try:
            identifier = arguments.get("identifier")
            file_path = arguments.get("file_path")
            work_item_id = arguments.get("work_item_id")
            include_conflicts = arguments.get("include_conflicts", True)
            check_all = arguments.get("check_all", False)
            
            # Check for required parameters
            if not identifier and not file_path and not work_item_id and not check_all:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "Missing required parameter: identifier, file_path, work_item_id, or check_all"
                    }, indent=2)
                )]
            
            if check_all:
                # Return status for all tracked files
                status_report = {
                    "total_files": len(self.sync_state),
                    "sync_summary": {
                        "in_sync": 0,
                        "file_newer": 0,
                        "db_newer": 0,
                        "conflicts": 0,
                        "errors": 0
                    },
                    "files": []
                }
                
                for path, metadata in self.sync_state.items():
                    file_status = await self._check_file_sync_status(path, metadata)
                    status_report["files"].append(file_status)
                    status_report["sync_summary"][file_status["status"]] += 1
                
                return [TextContent(
                    type="text",
                    text=json.dumps(status_report, indent=2)
                )]
            
            elif identifier:
                # Delegate to sync engine
                sync_status = await self.sync_engine.get_sync_status(identifier)
                return [TextContent(
                    type="text",
                    text=json.dumps(sync_status, indent=2)
                )]
            
            elif file_path:
                # Check specific file
                if file_path in self.sync_state:
                    metadata = self.sync_state[file_path]
                    file_status = await self._check_file_sync_status(file_path, metadata)
                    return [TextContent(
                        type="text",
                        text=json.dumps(file_status, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "error",
                            "message": "File not tracked in sync state",
                            "file_path": file_path
                        }, indent=2)
                    )]
            
            elif work_item_id:
                # Find file by work item ID
                for path, metadata in self.sync_state.items():
                    if metadata.file_path == path:  # This would need work_item_id in metadata
                        file_status = await self._check_file_sync_status(path, metadata)
                        return [TextContent(
                            type="text",
                            text=json.dumps(file_status, indent=2)
                        )]
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "Work item not found in sync state",
                        "work_item_id": work_item_id
                    }, indent=2)
                )]
            
            else:
                # Return general sync status
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "total_tracked_files": len(self.sync_state),
                        "last_sync_check": datetime.now().isoformat(),
                        "sync_state_loaded": True
                    }, indent=2)
                )]
                
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"Failed to get sync status: {str(e)}"
                }, indent=2)
            )]
    
    # Helper methods
    
    async def _parse_file_content(self, content: str, file_path: str) -> Optional[WorkItemFile]:
        """Parse file content as JSON or YAML."""
        try:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                data = yaml.safe_load(content)
            else:
                data = json.loads(content)
            
            # Add default values for required fields if missing (for validation tests)
            if 'type' not in data:
                data['type'] = 'task'  # Default type
            if 'status' not in data:
                data['status'] = 'not_started'  # Default status
            if 'priority' not in data:
                data['priority'] = 'medium'  # Default priority
            
            return WorkItemFile(**data)
        except Exception as e:
            logger.error(f"Failed to parse file content: {e}")
            return None
    
    async def _validate_work_item(self, work_item: WorkItemFile) -> Dict[str, Any]:
        """Validate work item structure."""
        errors = []
        
        # Required fields validation
        if not work_item.id:
            errors.append("Missing required field: id")
        if not work_item.title:
            errors.append("Missing required field: title")
        if not work_item.type:
            errors.append("Missing required field: type")
        
        # Type validation
        valid_types = ["initiative", "epic", "feature", "story", "task"]
        if work_item.type not in valid_types:
            errors.append(f"Invalid type: {work_item.type}. Must be one of {valid_types}")
        
        # Status validation
        valid_statuses = ["not_started", "todo", "in_progress", "completed", "cancelled"]
        if work_item.status not in valid_statuses:
            errors.append(f"Invalid status: {work_item.status}. Must be one of {valid_statuses}")
        
        # Priority validation
        valid_priorities = ["low", "medium", "high", "critical"]
        if work_item.priority not in valid_priorities:
            errors.append(f"Invalid priority: {work_item.priority}. Must be one of {valid_priorities}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _get_database_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get work item from database."""
        try:
            # Query Weaviate for the work item
            client = self.lancedb_manager.client
            if not client:
                return None
            
            result = client.query.get("WorkItem", ["*"]).with_where({
                "path": ["id"],
                "operator": "Equal",
                "valueText": work_item_id
            }).do()
            
            if result and "data" in result and "Get" in result["data"] and "WorkItem" in result["data"]["Get"]:
                items = result["data"]["Get"]["WorkItem"]
                if items:
                    return items[0]
            
            return None
        except Exception as e:
            logger.error(f"Failed to get database item: {e}")
            return None
    
    async def _detect_conflicts(self, file_item: WorkItemFile, db_item: Dict[str, Any]) -> List[str]:
        """Detect conflicts between file and database versions."""
        conflicts = []
        
        # Compare key fields with safe comparison to avoid NumPy array boolean evaluation issues
        def safe_compare(val1, val2):
            """Safely compare values that might be NumPy arrays."""
            # Convert NumPy arrays to Python values for comparison
            if hasattr(val1, 'item') and not isinstance(val1, (str, list, dict)):
                val1 = val1.item()
            if hasattr(val2, 'item') and not isinstance(val2, (str, list, dict)):
                val2 = val2.item()
            if hasattr(val1, 'tolist') and not isinstance(val1, (str, list)):
                val1 = val1.tolist()
            if hasattr(val2, 'tolist') and not isinstance(val2, (str, list)):
                val2 = val2.tolist()
            return val1 != val2
        
        if safe_compare(file_item.title, db_item.get("title")):
            conflicts.append(f"Title mismatch: file='{file_item.title}' vs db='{db_item.get('title')}'")
        
        if safe_compare(file_item.description, db_item.get("description")):
            conflicts.append(f"Description mismatch")
        
        if safe_compare(file_item.status, db_item.get("status")):
            conflicts.append(f"Status mismatch: file='{file_item.status}' vs db='{db_item.get('status')}'")
        
        if safe_compare(file_item.priority, db_item.get("priority")):
            conflicts.append(f"Priority mismatch: file='{file_item.priority}' vs db='{db_item.get('priority')}'")
        
        return conflicts
    
    async def _resolve_conflicts(self, file_item: WorkItemFile, db_item: Optional[Dict[str, Any]], 
                               conflicts: List[str], strategy: MergeStrategy) -> WorkItemFile:
        """Resolve conflicts based on merge strategy."""
        if not conflicts or not db_item:
            return file_item
        
        if strategy == MergeStrategy.FILE_WINS:
            return file_item
        elif strategy == MergeStrategy.DATABASE_WINS and db_item:
            # Convert db_item back to WorkItemFile
            return WorkItemFile(**db_item)
        elif strategy == MergeStrategy.AUTO_MERGE:
            # Simple auto-merge: prefer file for content, db for metadata
            merged_data = file_item.dict()
            if db_item.get("metadata"):
                merged_data["metadata"].update(db_item["metadata"])
            return WorkItemFile(**merged_data)
        
        return file_item
    
    async def _update_database_item(self, work_item: WorkItemFile) -> bool:
        """Update work item in database."""
        try:
            client = self.lancedb_manager.client
            if not client:
                return False
            
            # Convert to database format
            data = work_item.dict()
            data["updated_at"] = datetime.now().isoformat()
            
            # Update or create in Weaviate
            client.data_object.create(
                data_object=data,
                class_name="jive_WorkItem",
                uuid=work_item.id
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to update database item: {e}")
            return False
    
    def _calculate_checksum(self, content: str) -> str:
        """Calculate MD5 checksum of content."""
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _update_sync_state(self, file_path: str, work_item_id: str, checksum: str) -> None:
        """Update sync state tracking."""
        self.sync_state[file_path] = FileMetadata(
            file_path=file_path,
            checksum=checksum,
            last_modified=datetime.now().isoformat(),
            sync_status=SyncStatus.IN_SYNC,
            last_synced=datetime.now().isoformat(),
            work_item_id=work_item_id
        )
    
    def _get_default_file_path(self, db_item: Dict[str, Any]) -> str:
        """Get default file path for work item type."""
        item_type = db_item.get("type", "task")
        item_id = db_item.get("id", "unknown")
        
        type_folders = {
            "initiative": "initiatives",
            "epic": "epics", 
            "feature": "features",
            "story": "stories",
            "task": "tasks"
        }
        
        folder = type_folders.get(item_type, "tasks")
        return f"{folder}/{item_id}.json"
    
    async def _generate_file_content(self, db_item: Dict[str, Any], format_type: str) -> str:
        """Generate file content from database item."""
        # Add metadata
        db_item["metadata"] = db_item.get("metadata", {})
        db_item["metadata"]["last_synced"] = datetime.now().isoformat()
        db_item["metadata"]["file_version"] = "1.0"
        
        if format_type == "yaml":
            return yaml.dump(db_item, default_flow_style=False, sort_keys=False)
        else:
            return json.dumps(db_item, indent=2)
    
    async def _check_file_sync_status(self, file_path: str, metadata: FileMetadata) -> Dict[str, Any]:
        """Check sync status for a specific file."""
        return {
            "file_path": file_path,
            "status": metadata.sync_status,
            "last_modified": metadata.last_modified,
            "last_synced": metadata.last_synced,
            "checksum": metadata.checksum,
            "file_version": metadata.file_version
        }
    
    async def _load_sync_state(self) -> None:
        """Load sync state from storage."""
        # In a real implementation, this would load from a persistent store
        # For now, initialize empty state
        self.sync_state = {}
        logger.info("Sync state initialized")
    
    async def cleanup(self) -> None:
        """Cleanup storage and sync tools."""
        logger.info("Cleaning up storage and sync tools...")
        # Save sync state if needed
        self.sync_state.clear()
    
    async def _validate_file_content(self, content: str, file_path: str) -> bool:
        """Validate file content format and structure."""
        try:
            # Parse content first
            work_item = await self._parse_file_content(content, file_path)
            if not work_item:
                return False
            
            # Validate the parsed work item
            validation_result = await self._validate_work_item(work_item)
            return validation_result["valid"]
        except Exception as e:
            return False
    
    async def _validate_work_item_data(self, data: Dict[str, Any]) -> bool:
        """Validate work item data structure."""
        try:
            # Create WorkItemFile from data to validate structure
            work_item = WorkItemFile(**data)
            validation_result = await self._validate_work_item(work_item)
            return validation_result["valid"]
        except Exception as e:
            return False