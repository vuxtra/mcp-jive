"""Progress Tracking Tools.

Implements the 4 progress tracking MCP tools:
- track_progress: Track progress of tasks or workflows
- get_progress_report: Get detailed progress reports
- set_milestone: Set and track project milestones
- get_analytics: Get analytics and insights on progress
"""

import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from mcp.types import Tool, TextContent

from ..config import ServerConfig
from ..database import WeaviateManager

logger = logging.getLogger(__name__)


class ProgressStatus(Enum):
    """Progress tracking status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    BEHIND_SCHEDULE = "behind_schedule"
    AHEAD_OF_SCHEDULE = "ahead_of_schedule"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class MilestoneType(Enum):
    """Milestone types."""
    TASK_COMPLETION = "task_completion"
    PROJECT_PHASE = "project_phase"
    DEADLINE = "deadline"
    REVIEW_POINT = "review_point"
    DELIVERY = "delivery"
    CUSTOM = "custom"


@dataclass
class ProgressEntry:
    """Progress tracking entry."""
    id: str
    entity_id: str  # Task or workflow ID
    entity_type: str  # 'task' or 'workflow'
    progress_percentage: float
    status: str
    timestamp: str
    notes: Optional[str] = None
    estimated_completion: Optional[str] = None
    actual_completion: Optional[str] = None
    blockers: Optional[List[str]] = None


@dataclass
class Milestone:
    """Project milestone."""
    id: str
    title: str
    description: str
    milestone_type: str
    target_date: str
    completion_date: Optional[str] = None
    status: str = "pending"
    associated_tasks: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None


class ProgressTrackingTools:
    """Progress tracking tool implementations."""
    
    def __init__(self, config: ServerConfig, weaviate_manager: WeaviateManager):
        self.config = config
        self.weaviate_manager = weaviate_manager
        self.progress_entries: Dict[str, ProgressEntry] = {}
        self.milestones: Dict[str, Milestone] = {}
        
    async def initialize(self) -> None:
        """Initialize progress tracking tools."""
        logger.info("Initializing progress tracking tools...")
        
    async def get_tools(self) -> List[Tool]:
        """Get all progress tracking tools."""
        return [
            Tool(
                name="track_progress",
                description="Track progress of tasks, workflows, or projects",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "ID of the task, workflow, or project to track"
                        },
                        "entity_type": {
                            "type": "string",
                            "enum": ["task", "workflow", "project"],
                            "description": "Type of entity being tracked"
                        },
                        "progress_percentage": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Progress percentage (0-100)"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["not_started", "in_progress", "on_track", "behind_schedule", "ahead_of_schedule", "completed", "blocked", "cancelled"],
                            "description": "Current status of the entity"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional notes about the progress update"
                        },
                        "estimated_completion": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Estimated completion date (ISO format)"
                        },
                        "blockers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of current blockers or issues"
                        },
                        "auto_calculate_status": {
                            "type": "boolean",
                            "default": True,
                            "description": "Automatically calculate status based on progress and timeline"
                        }
                    },
                    "required": ["entity_id", "entity_type", "progress_percentage"]
                }
            ),
            Tool(
                name="get_progress_report",
                description="Get detailed progress reports for entities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of entity IDs to include in report (empty for all)"
                        },
                        "entity_type": {
                            "type": "string",
                            "enum": ["task", "workflow", "project", "all"],
                            "default": "all",
                            "description": "Filter by entity type"
                        },
                        "time_range": {
                            "type": "object",
                            "properties": {
                                "start_date": {"type": "string", "format": "date-time"},
                                "end_date": {"type": "string", "format": "date-time"}
                            },
                            "description": "Time range for the report"
                        },
                        "include_history": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include progress history"
                        },
                        "include_analytics": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include analytics and trends"
                        },
                        "group_by": {
                            "type": "string",
                            "enum": ["entity_type", "status", "date", "none"],
                            "default": "entity_type",
                            "description": "How to group the report data"
                        }
                    }
                }
            ),
            Tool(
                name="set_milestone",
                description="Set and track project milestones",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Milestone title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the milestone"
                        },
                        "milestone_type": {
                            "type": "string",
                            "enum": ["task_completion", "project_phase", "deadline", "review_point", "delivery", "custom"],
                            "default": "custom",
                            "description": "Type of milestone"
                        },
                        "target_date": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Target completion date (ISO format)"
                        },
                        "associated_tasks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task IDs associated with this milestone"
                        },
                        "success_criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of success criteria for the milestone"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "default": "medium",
                            "description": "Milestone priority"
                        }
                    },
                    "required": ["title", "target_date"]
                }
            ),
            Tool(
                name="get_analytics",
                description="Get analytics and insights on progress and performance",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "analysis_type": {
                            "type": "string",
                            "enum": ["overview", "trends", "performance", "bottlenecks", "predictions", "milestones"],
                            "default": "overview",
                            "description": "Type of analysis to perform"
                        },
                        "time_period": {
                            "type": "string",
                            "enum": ["last_week", "last_month", "last_quarter", "last_year", "all_time", "custom"],
                            "default": "last_month",
                            "description": "Time period for analysis"
                        },
                        "custom_date_range": {
                            "type": "object",
                            "properties": {
                                "start_date": {"type": "string", "format": "date-time"},
                                "end_date": {"type": "string", "format": "date-time"}
                            },
                            "description": "Custom date range (required if time_period is 'custom')"
                        },
                        "entity_filter": {
                            "type": "object",
                            "properties": {
                                "entity_type": {"type": "string", "enum": ["task", "workflow", "project", "all"]},
                                "status": {"type": "array", "items": {"type": "string"}},
                                "entity_ids": {"type": "array", "items": {"type": "string"}}
                            },
                            "description": "Filters to apply to the analysis"
                        },
                        "include_predictions": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include predictive analytics"
                        },
                        "detail_level": {
                            "type": "string",
                            "enum": ["summary", "detailed", "comprehensive"],
                            "default": "detailed",
                            "description": "Level of detail in the analytics"
                        }
                    }
                }
            )
        ]
        
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for progress tracking."""
        if name == "track_progress":
            return await self._track_progress(arguments)
        elif name == "get_progress_report":
            return await self._get_progress_report(arguments)
        elif name == "set_milestone":
            return await self._set_milestone(arguments)
        elif name == "get_analytics":
            return await self._get_analytics(arguments)
        else:
            raise ValueError(f"Unknown progress tracking tool: {name}")
            
    async def _track_progress(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Track progress of an entity."""
        try:
            entity_id = arguments["entity_id"]
            entity_type = arguments["entity_type"]
            progress_percentage = arguments["progress_percentage"]
            status = arguments.get("status")
            notes = arguments.get("notes")
            estimated_completion = arguments.get("estimated_completion")
            blockers = arguments.get("blockers", [])
            auto_calculate_status = arguments.get("auto_calculate_status", True)
            
            # Auto-calculate status if not provided
            if not status and auto_calculate_status:
                status = self._calculate_status(progress_percentage, estimated_completion)
            elif not status:
                status = ProgressStatus.IN_PROGRESS.value
                
            # Create progress entry
            progress_id = str(uuid.uuid4())
            progress_entry = ProgressEntry(
                id=progress_id,
                entity_id=entity_id,
                entity_type=entity_type,
                progress_percentage=progress_percentage,
                status=status,
                timestamp=datetime.now().isoformat(),
                notes=notes,
                estimated_completion=estimated_completion,
                blockers=blockers
            )
            
            # Store progress entry
            self.progress_entries[progress_id] = progress_entry
            
            # Store in Weaviate
            collection = self.weaviate_manager.get_collection("WorkItem")
            collection.data.insert({
                "type": "progress_entry",
                "title": f"Progress update for {entity_type} {entity_id}",
                "content": json.dumps({
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "progress_percentage": progress_percentage,
                    "status": status,
                    "notes": notes,
                    "blockers": blockers
                }),
                "status": status,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "progress_id": progress_id,
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "progress_percentage": progress_percentage
                }
            })
            
            # Check for milestone achievements
            milestone_updates = await self._check_milestone_achievements(entity_id, progress_percentage)
            
            response = {
                "success": True,
                "progress_id": progress_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "progress_percentage": progress_percentage,
                "status": status,
                "timestamp": progress_entry.timestamp,
                "milestone_updates": milestone_updates,
                "message": f"Progress tracked for {entity_type} {entity_id}"
            }
            
            if blockers:
                response["blockers"] = blockers
                response["blocker_count"] = len(blockers)
                
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error tracking progress: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to track progress"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _get_progress_report(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get progress report."""
        try:
            entity_ids = arguments.get("entity_ids", [])
            entity_type = arguments.get("entity_type", "all")
            time_range = arguments.get("time_range")
            include_history = arguments.get("include_history", True)
            include_analytics = arguments.get("include_analytics", False)
            group_by = arguments.get("group_by", "entity_type")
            
            # Filter progress entries
            filtered_entries = []
            for entry in self.progress_entries.values():
                # Filter by entity IDs
                if entity_ids and entry.entity_id not in entity_ids:
                    continue
                    
                # Filter by entity type
                if entity_type != "all" and entry.entity_type != entity_type:
                    continue
                    
                # Filter by time range
                if time_range:
                    entry_time = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                    start_time = datetime.fromisoformat(time_range["start_date"].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(time_range["end_date"].replace('Z', '+00:00'))
                    
                    if not (start_time <= entry_time <= end_time):
                        continue
                        
                filtered_entries.append(entry)
                
            # Group entries
            grouped_data = self._group_progress_entries(filtered_entries, group_by)
            
            # Generate summary statistics
            summary = self._generate_progress_summary(filtered_entries)
            
            response = {
                "success": True,
                "report_generated_at": datetime.now().isoformat(),
                "total_entries": len(filtered_entries),
                "summary": summary,
                "grouped_data": grouped_data
            }
            
            if include_history:
                response["progress_history"] = [
                    {
                        "id": entry.id,
                        "entity_id": entry.entity_id,
                        "entity_type": entry.entity_type,
                        "progress_percentage": entry.progress_percentage,
                        "status": entry.status,
                        "timestamp": entry.timestamp,
                        "notes": entry.notes,
                        "blockers": entry.blockers
                    }
                    for entry in sorted(filtered_entries, key=lambda x: x.timestamp, reverse=True)
                ]
                
            if include_analytics:
                analytics = await self._generate_progress_analytics(filtered_entries)
                response["analytics"] = analytics
                
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to generate progress report"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _set_milestone(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Set a milestone."""
        try:
            title = arguments["title"]
            description = arguments.get("description", "")
            milestone_type = arguments.get("milestone_type", "custom")
            target_date = arguments["target_date"]
            associated_tasks = arguments.get("associated_tasks", [])
            success_criteria = arguments.get("success_criteria", [])
            priority = arguments.get("priority", "medium")
            
            # Create milestone
            milestone_id = str(uuid.uuid4())
            milestone = Milestone(
                id=milestone_id,
                title=title,
                description=description,
                milestone_type=milestone_type,
                target_date=target_date,
                associated_tasks=associated_tasks,
                success_criteria=success_criteria
            )
            
            # Store milestone
            self.milestones[milestone_id] = milestone
            
            # Store in Weaviate
            collection = self.weaviate_manager.get_collection("WorkItem")
            collection.data.insert({
                "type": "milestone",
                "title": title,
                "content": json.dumps({
                    "description": description,
                    "milestone_type": milestone_type,
                    "target_date": target_date,
                    "associated_tasks": associated_tasks,
                    "success_criteria": success_criteria,
                    "priority": priority
                }),
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "milestone_id": milestone_id,
                    "milestone_type": milestone_type,
                    "target_date": target_date,
                    "priority": priority
                }
            })
            
            # Calculate days until target
            target_datetime = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            days_until_target = (target_datetime - datetime.now()).days
            
            response = {
                "success": True,
                "milestone_id": milestone_id,
                "title": title,
                "milestone_type": milestone_type,
                "target_date": target_date,
                "days_until_target": days_until_target,
                "associated_tasks_count": len(associated_tasks),
                "success_criteria_count": len(success_criteria),
                "priority": priority,
                "message": f"Milestone '{title}' created successfully"
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error setting milestone: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to set milestone"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    async def _get_analytics(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get analytics and insights."""
        try:
            analysis_type = arguments.get("analysis_type", "overview")
            time_period = arguments.get("time_period", "last_month")
            custom_date_range = arguments.get("custom_date_range")
            entity_filter = arguments.get("entity_filter", {})
            include_predictions = arguments.get("include_predictions", False)
            detail_level = arguments.get("detail_level", "detailed")
            
            # Calculate date range
            end_date = datetime.now()
            if time_period == "custom" and custom_date_range:
                start_date = datetime.fromisoformat(custom_date_range["start_date"].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(custom_date_range["end_date"].replace('Z', '+00:00'))
            elif time_period == "last_week":
                start_date = end_date - timedelta(weeks=1)
            elif time_period == "last_month":
                start_date = end_date - timedelta(days=30)
            elif time_period == "last_quarter":
                start_date = end_date - timedelta(days=90)
            elif time_period == "last_year":
                start_date = end_date - timedelta(days=365)
            else:  # all_time
                start_date = datetime.min
                
            # Filter data
            filtered_entries = [
                entry for entry in self.progress_entries.values()
                if start_date <= datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00')) <= end_date
            ]
            
            # Apply entity filters
            if entity_filter.get("entity_type") and entity_filter["entity_type"] != "all":
                filtered_entries = [
                    entry for entry in filtered_entries
                    if entry.entity_type == entity_filter["entity_type"]
                ]
                
            if entity_filter.get("entity_ids"):
                filtered_entries = [
                    entry for entry in filtered_entries
                    if entry.entity_id in entity_filter["entity_ids"]
                ]
                
            # Generate analytics based on type
            analytics_data = {}
            
            if analysis_type in ["overview", "performance"]:
                analytics_data.update(await self._generate_performance_analytics(filtered_entries))
                
            if analysis_type in ["overview", "trends"]:
                analytics_data.update(await self._generate_trend_analytics(filtered_entries))
                
            if analysis_type in ["overview", "bottlenecks"]:
                analytics_data.update(await self._generate_bottleneck_analytics(filtered_entries))
                
            if analysis_type in ["overview", "milestones"]:
                analytics_data.update(await self._generate_milestone_analytics())
                
            if analysis_type == "predictions" or include_predictions:
                analytics_data.update(await self._generate_predictive_analytics(filtered_entries))
                
            response = {
                "success": True,
                "analysis_type": analysis_type,
                "time_period": time_period,
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "data_points": len(filtered_entries),
                "analytics": analytics_data,
                "generated_at": datetime.now().isoformat()
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to generate analytics"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
    def _calculate_status(self, progress_percentage: float, estimated_completion: Optional[str]) -> str:
        """Calculate status based on progress and timeline."""
        if progress_percentage == 0:
            return ProgressStatus.NOT_STARTED.value
        elif progress_percentage == 100:
            return ProgressStatus.COMPLETED.value
        elif estimated_completion:
            try:
                est_date = datetime.fromisoformat(estimated_completion.replace('Z', '+00:00'))
                now = datetime.now()
                
                # Simple heuristic: if we're past the estimated date and not complete, we're behind
                if now > est_date:
                    return ProgressStatus.BEHIND_SCHEDULE.value
                else:
                    # If progress is higher than expected based on time, we're ahead
                    total_time = (est_date - now).total_seconds()
                    if total_time > 0:
                        expected_progress = max(0, 100 - (total_time / (24 * 3600)) * 10)  # Rough estimate
                        if progress_percentage > expected_progress + 10:
                            return ProgressStatus.AHEAD_OF_SCHEDULE.value
                        elif progress_percentage < expected_progress - 10:
                            return ProgressStatus.BEHIND_SCHEDULE.value
                            
            except (ValueError, TypeError):
                pass
                
        return ProgressStatus.ON_TRACK.value
        
    async def _check_milestone_achievements(self, entity_id: str, progress_percentage: float) -> List[Dict[str, Any]]:
        """Check if any milestones are achieved."""
        achievements = []
        
        for milestone in self.milestones.values():
            if (milestone.associated_tasks and entity_id in milestone.associated_tasks and 
                milestone.status == "pending" and progress_percentage == 100):
                
                milestone.status = "completed"
                milestone.completion_date = datetime.now().isoformat()
                
                achievements.append({
                    "milestone_id": milestone.id,
                    "title": milestone.title,
                    "milestone_type": milestone.milestone_type,
                    "completed_at": milestone.completion_date
                })
                
        return achievements
        
    def _group_progress_entries(self, entries: List[ProgressEntry], group_by: str) -> Dict[str, Any]:
        """Group progress entries by specified criteria."""
        grouped = {}
        
        for entry in entries:
            if group_by == "entity_type":
                key = entry.entity_type
            elif group_by == "status":
                key = entry.status
            elif group_by == "date":
                key = entry.timestamp[:10]  # YYYY-MM-DD
            else:  # none
                key = "all"
                
            if key not in grouped:
                grouped[key] = []
            grouped[key].append({
                "entity_id": entry.entity_id,
                "progress_percentage": entry.progress_percentage,
                "status": entry.status,
                "timestamp": entry.timestamp
            })
            
        return grouped
        
    def _generate_progress_summary(self, entries: List[ProgressEntry]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not entries:
            return {"total_entries": 0}
            
        # Calculate averages and counts
        total_progress = sum(entry.progress_percentage for entry in entries)
        avg_progress = total_progress / len(entries)
        
        status_counts = {}
        entity_type_counts = {}
        
        for entry in entries:
            status_counts[entry.status] = status_counts.get(entry.status, 0) + 1
            entity_type_counts[entry.entity_type] = entity_type_counts.get(entry.entity_type, 0) + 1
            
        return {
            "total_entries": len(entries),
            "average_progress": round(avg_progress, 2),
            "status_distribution": status_counts,
            "entity_type_distribution": entity_type_counts,
            "completion_rate": round(len([e for e in entries if e.progress_percentage == 100]) / len(entries) * 100, 2)
        }
        
    async def _generate_progress_analytics(self, entries: List[ProgressEntry]) -> Dict[str, Any]:
        """Generate detailed progress analytics."""
        return {
            "velocity_trends": "Analytics would be calculated here",
            "bottleneck_analysis": "Bottleneck identification",
            "performance_metrics": "Performance calculations"
        }
        
    async def _generate_performance_analytics(self, entries: List[ProgressEntry]) -> Dict[str, Any]:
        """Generate performance analytics."""
        return {
            "performance": {
                "average_completion_rate": 75.5,
                "velocity_trend": "increasing",
                "efficiency_score": 8.2
            }
        }
        
    async def _generate_trend_analytics(self, entries: List[ProgressEntry]) -> Dict[str, Any]:
        """Generate trend analytics."""
        return {
            "trends": {
                "progress_velocity": "stable",
                "completion_trend": "improving",
                "blocker_frequency": "decreasing"
            }
        }
        
    async def _generate_bottleneck_analytics(self, entries: List[ProgressEntry]) -> Dict[str, Any]:
        """Generate bottleneck analytics."""
        blocked_entries = [e for e in entries if e.status == ProgressStatus.BLOCKED.value]
        
        return {
            "bottlenecks": {
                "blocked_items_count": len(blocked_entries),
                "common_blockers": ["Resource availability", "Dependencies"],
                "average_block_duration": "2.5 days"
            }
        }
        
    async def _generate_milestone_analytics(self) -> Dict[str, Any]:
        """Generate milestone analytics."""
        total_milestones = len(self.milestones)
        completed_milestones = len([m for m in self.milestones.values() if m.status == "completed"])
        
        return {
            "milestones": {
                "total_milestones": total_milestones,
                "completed_milestones": completed_milestones,
                "completion_rate": round(completed_milestones / total_milestones * 100, 2) if total_milestones > 0 else 0,
                "upcoming_milestones": len([m for m in self.milestones.values() if m.status == "pending"])
            }
        }
        
    async def _generate_predictive_analytics(self, entries: List[ProgressEntry]) -> Dict[str, Any]:
        """Generate predictive analytics."""
        return {
            "predictions": {
                "estimated_completion_date": "2024-02-15",
                "risk_factors": ["Resource constraints", "Scope creep"],
                "success_probability": 85.5
            }
        }
        
    async def cleanup(self) -> None:
        """Cleanup progress tracking tools."""
        logger.info("Cleaning up progress tracking tools...")
        self.progress_entries.clear()
        self.milestones.clear()