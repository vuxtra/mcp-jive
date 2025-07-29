"""Validation and Quality Gate Tools.

Implements the 5 validation and quality gate MCP tools:
- validate_task_completion: Validate task completion against acceptance criteria
- run_quality_gates: Execute quality gate checks for work items
- get_validation_status: Retrieve validation results and approval status
- approve_completion: Mark work items as approved after validation
- request_changes: Request changes with specific feedback for work items
"""

import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from mcp.types import Tool, TextContent

from ..config import ServerConfig
from ..database import WeaviateManager

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class QualityGateType(Enum):
    """Quality gate types."""
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    SECURITY_SCAN = "security_scan"
    PERFORMANCE_TEST = "performance_test"
    DOCUMENTATION = "documentation"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


@dataclass
class ValidationResult:
    """Validation result data structure."""
    id: str
    work_item_id: str
    validation_type: str
    status: str
    score: Optional[float] = None
    passed_checks: int = 0
    total_checks: int = 0
    issues: List[Dict[str, Any]] = None
    recommendations: List[str] = None
    validated_by: Optional[str] = None
    validated_at: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class QualityGate:
    """Quality gate configuration."""
    id: str
    name: str
    gate_type: str
    criteria: List[Dict[str, Any]]
    required: bool = True
    weight: float = 1.0
    timeout_minutes: int = 60
    auto_execute: bool = False


class ValidationTools:
    """Validation and quality gate tool implementations."""
    
    def __init__(self, config: ServerConfig, weaviate_manager: WeaviateManager):
        self.config = config
        self.weaviate_manager = weaviate_manager
        self.validation_results: Dict[str, ValidationResult] = {}
        self.quality_gates: Dict[str, QualityGate] = {}
        self._initialize_default_quality_gates()
        
    def _initialize_default_quality_gates(self):
        """Initialize default quality gates."""
        default_gates = [
            QualityGate(
                id="acceptance_criteria",
                name="Acceptance Criteria Validation",
                gate_type=QualityGateType.ACCEPTANCE_CRITERIA.value,
                criteria=[
                    {"name": "all_criteria_met", "description": "All acceptance criteria are satisfied", "required": True},
                    {"name": "user_story_complete", "description": "User story is fully implemented", "required": True}
                ],
                required=True,
                weight=2.0
            ),
            QualityGate(
                id="code_review",
                name="Code Review",
                gate_type=QualityGateType.CODE_REVIEW.value,
                criteria=[
                    {"name": "code_quality", "description": "Code meets quality standards", "required": True},
                    {"name": "best_practices", "description": "Follows coding best practices", "required": True},
                    {"name": "documentation", "description": "Code is properly documented", "required": False}
                ],
                required=True,
                weight=1.5
            ),
            QualityGate(
                id="testing",
                name="Testing Validation",
                gate_type=QualityGateType.TESTING.value,
                criteria=[
                    {"name": "unit_tests", "description": "Unit tests pass", "required": True},
                    {"name": "integration_tests", "description": "Integration tests pass", "required": True},
                    {"name": "coverage_threshold", "description": "Code coverage meets threshold", "required": True}
                ],
                required=True,
                weight=1.8
            )
        ]
        
        for gate in default_gates:
            self.quality_gates[gate.id] = gate
    
    async def initialize(self) -> None:
        """Initialize validation tools."""
        logger.info("Initializing validation and quality gate tools...")
        
    async def get_tools(self) -> List[Tool]:
        """Get all validation and quality gate tools."""
        return [
            Tool(
                name="validate_task_completion",
                description="Validate task completion against acceptance criteria and quality standards",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "ID of the work item to validate"
                        },
                        "validation_type": {
                            "type": "string",
                            "enum": ["acceptance_criteria", "code_review", "testing", "security", "performance", "documentation", "compliance", "custom"],
                            "default": "acceptance_criteria",
                            "description": "Type of validation to perform"
                        },
                        "acceptance_criteria": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "criterion": {"type": "string"},
                                    "met": {"type": "boolean"},
                                    "evidence": {"type": "string"},
                                    "notes": {"type": "string"}
                                },
                                "required": ["criterion", "met"]
                            },
                            "description": "List of acceptance criteria to validate against"
                        },
                        "custom_checks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "required": {"type": "boolean", "default": True}
                                },
                                "required": ["name", "description"]
                            },
                            "description": "Custom validation checks to perform"
                        },
                        "auto_approve_threshold": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "default": 95,
                            "description": "Automatic approval threshold percentage"
                        },
                        "validator_id": {
                            "type": "string",
                            "description": "ID of the validator (user or system)"
                        }
                    },
                    "required": ["work_item_id"]
                }
            ),
            Tool(
                name="run_quality_gates",
                description="Execute quality gate checks for work items",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "ID of the work item to run quality gates for"
                        },
                        "gate_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific quality gate IDs to run (empty for all applicable gates)"
                        },
                        "execution_mode": {
                            "type": "string",
                            "enum": ["sequential", "parallel", "fail_fast"],
                            "default": "sequential",
                            "description": "How to execute multiple quality gates"
                        },
                        "timeout_minutes": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 480,
                            "default": 60,
                            "description": "Timeout for quality gate execution in minutes"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for quality gate execution",
                            "properties": {
                                "environment": {"type": "string"},
                                "branch": {"type": "string"},
                                "commit_hash": {"type": "string"},
                                "test_data": {"type": "object"}
                            }
                        },
                        "notify_on_completion": {
                            "type": "boolean",
                            "default": True,
                            "description": "Send notifications when quality gates complete"
                        }
                    },
                    "required": ["work_item_id"]
                }
            ),
            Tool(
                name="get_validation_status",
                description="Retrieve validation results and approval status for work items",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of work item IDs to get validation status for"
                        },
                        "validation_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by specific validation types"
                        },
                        "status_filter": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "passed", "failed", "requires_review", "approved", "rejected"]
                            },
                            "description": "Filter by validation status"
                        },
                        "include_details": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include detailed validation results"
                        },
                        "include_history": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include validation history"
                        },
                        "group_by": {
                            "type": "string",
                            "enum": ["work_item", "validation_type", "status", "validator"],
                            "default": "work_item",
                            "description": "How to group the results"
                        }
                    }
                }
            ),
            Tool(
                name="approve_completion",
                description="Mark work items as approved after validation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "ID of the work item to approve"
                        },
                        "validation_id": {
                            "type": "string",
                            "description": "ID of the specific validation to approve (optional)"
                        },
                        "approver_id": {
                            "type": "string",
                            "description": "ID of the approver"
                        },
                        "approval_type": {
                            "type": "string",
                            "enum": ["full_approval", "conditional_approval", "partial_approval"],
                            "default": "full_approval",
                            "description": "Type of approval being granted"
                        },
                        "conditions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Conditions that must be met for conditional approval"
                        },
                        "approval_notes": {
                            "type": "string",
                            "description": "Notes about the approval decision"
                        },
                        "expires_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Expiration date for the approval (ISO format)"
                        },
                        "auto_proceed": {
                            "type": "boolean",
                            "default": True,
                            "description": "Automatically proceed to next workflow step after approval"
                        }
                    },
                    "required": ["work_item_id", "approver_id"]
                }
            ),
            Tool(
                name="request_changes",
                description="Request changes with specific feedback for work items",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "string",
                            "description": "ID of the work item requiring changes"
                        },
                        "validation_id": {
                            "type": "string",
                            "description": "ID of the validation that failed (optional)"
                        },
                        "reviewer_id": {
                            "type": "string",
                            "description": "ID of the reviewer requesting changes"
                        },
                        "change_requests": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "category": {
                                        "type": "string",
                                        "enum": ["functionality", "code_quality", "testing", "documentation", "security", "performance", "design", "other"]
                                    },
                                    "severity": {
                                        "type": "string",
                                        "enum": ["critical", "major", "minor", "suggestion"]
                                    },
                                    "description": {"type": "string"},
                                    "location": {"type": "string"},
                                    "suggested_fix": {"type": "string"},
                                    "blocking": {"type": "boolean", "default": True}
                                },
                                "required": ["category", "severity", "description"]
                            },
                            "description": "List of specific change requests"
                        },
                        "overall_feedback": {
                            "type": "string",
                            "description": "Overall feedback and summary of required changes"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "default": "medium",
                            "description": "Priority of the change requests"
                        },
                        "due_date": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Due date for addressing the changes (ISO format)"
                        },
                        "reassign_to": {
                            "type": "string",
                            "description": "Reassign work item to specific person for changes"
                        },
                        "notify_stakeholders": {
                            "type": "boolean",
                            "default": True,
                            "description": "Notify relevant stakeholders about change requests"
                        }
                    },
                    "required": ["work_item_id", "reviewer_id", "change_requests"]
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle validation tool calls."""
        try:
            if name == "validate_task_completion":
                return await self._validate_task_completion(arguments)
            elif name == "run_quality_gates":
                return await self._run_quality_gates(arguments)
            elif name == "get_validation_status":
                return await self._get_validation_status(arguments)
            elif name == "approve_completion":
                return await self._approve_completion(arguments)
            elif name == "request_changes":
                return await self._request_changes(arguments)
            else:
                error_response = {
                    "success": False,
                    "error": f"Unknown validation tool: {name}",
                    "message": "Tool not found"
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
        except Exception as e:
            logger.error(f"Error in validation tool {name}: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "message": f"Failed to execute {name}"
            }
            return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
    
    async def _validate_task_completion(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Validate task completion against acceptance criteria."""
        work_item_id = arguments["work_item_id"]
        validation_type = arguments.get("validation_type", "acceptance_criteria")
        acceptance_criteria = arguments.get("acceptance_criteria", [])
        custom_checks = arguments.get("custom_checks", [])
        auto_approve_threshold = arguments.get("auto_approve_threshold", 95)
        validator_id = arguments.get("validator_id", "system")
        
        # Create validation result
        validation_id = str(uuid.uuid4())
        
        # Perform validation checks
        passed_checks = 0
        total_checks = 0
        issues = []
        recommendations = []
        
        # Validate acceptance criteria
        if acceptance_criteria:
            for criterion in acceptance_criteria:
                total_checks += 1
                if criterion.get("met", False):
                    passed_checks += 1
                else:
                    issues.append({
                        "type": "acceptance_criteria",
                        "criterion": criterion["criterion"],
                        "severity": "major",
                        "description": f"Acceptance criterion not met: {criterion['criterion']}",
                        "evidence": criterion.get("evidence", "No evidence provided"),
                        "notes": criterion.get("notes", "")
                    })
        
        # Perform custom checks
        if custom_checks:
            for check in custom_checks:
                total_checks += 1
                # Simulate check execution (in real implementation, this would call actual validation logic)
                check_passed = True  # Placeholder - would be actual validation logic
                if check_passed:
                    passed_checks += 1
                else:
                    issues.append({
                        "type": "custom_check",
                        "check_name": check["name"],
                        "severity": "major" if check.get("required", True) else "minor",
                        "description": f"Custom check failed: {check['description']}"
                    })
        
        # Calculate score and status
        score = (passed_checks / total_checks * 100) if total_checks > 0 else 100
        
        if score >= auto_approve_threshold:
            status = ValidationStatus.APPROVED.value
        elif score >= 80:
            status = ValidationStatus.REQUIRES_REVIEW.value
        elif score >= 60:
            status = ValidationStatus.FAILED.value
        else:
            status = ValidationStatus.FAILED.value
        
        # Generate recommendations
        if issues:
            recommendations.append("Address all failed acceptance criteria before proceeding")
            if score < 80:
                recommendations.append("Consider reviewing implementation approach")
        
        # Create validation result
        validation_result = ValidationResult(
            id=validation_id,
            work_item_id=work_item_id,
            validation_type=validation_type,
            status=status,
            score=score,
            passed_checks=passed_checks,
            total_checks=total_checks,
            issues=issues,
            recommendations=recommendations,
            validated_by=validator_id,
            validated_at=datetime.now().isoformat()
        )
        
        # Store validation result
        self.validation_results[validation_id] = validation_result
        
        # Store in Weaviate
        collection = self.weaviate_manager.get_collection("WorkItem")
        collection.data.insert({
            "type": "validation_result",
            "title": f"Validation result for {work_item_id}",
            "content": json.dumps({
                "work_item_id": work_item_id,
                "validation_type": validation_type,
                "status": status,
                "score": score,
                "issues": issues,
                "recommendations": recommendations
            }),
            "status": status,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "validation_id": validation_id,
                "work_item_id": work_item_id,
                "validation_type": validation_type,
                "score": score,
                "passed_checks": passed_checks,
                "total_checks": total_checks
            }
        })
        
        response = {
            "success": True,
            "validation_id": validation_id,
            "work_item_id": work_item_id,
            "validation_type": validation_type,
            "status": status,
            "score": score,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "issues": issues,
            "recommendations": recommendations,
            "validated_by": validator_id,
            "validated_at": validation_result.validated_at,
            "message": f"Validation completed with {score:.1f}% score"
        }
        
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    
    async def _run_quality_gates(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute quality gate checks for work items."""
        work_item_id = arguments["work_item_id"]
        gate_ids = arguments.get("gate_ids", [])
        execution_mode = arguments.get("execution_mode", "sequential")
        timeout_minutes = arguments.get("timeout_minutes", 60)
        context = arguments.get("context", {})
        notify_on_completion = arguments.get("notify_on_completion", True)
        
        # Determine which gates to run
        gates_to_run = []
        if gate_ids:
            gates_to_run = [self.quality_gates[gate_id] for gate_id in gate_ids if gate_id in self.quality_gates]
        else:
            gates_to_run = list(self.quality_gates.values())
        
        execution_id = str(uuid.uuid4())
        gate_results = []
        overall_status = "passed"
        overall_score = 0.0
        
        # Execute quality gates
        for gate in gates_to_run:
            gate_result = await self._execute_quality_gate(gate, work_item_id, context)
            gate_results.append(gate_result)
            
            # Update overall status
            if gate_result["status"] == "failed" and gate.required:
                overall_status = "failed"
            elif gate_result["status"] == "requires_review":
                if overall_status != "failed":
                    overall_status = "requires_review"
            
            # Calculate weighted score
            overall_score += gate_result["score"] * gate.weight
        
        # Normalize overall score
        total_weight = sum(gate.weight for gate in gates_to_run)
        overall_score = overall_score / total_weight if total_weight > 0 else 0
        
        # Store execution result
        execution_result = {
            "execution_id": execution_id,
            "work_item_id": work_item_id,
            "overall_status": overall_status,
            "overall_score": overall_score,
            "gates_executed": len(gates_to_run),
            "gates_passed": sum(1 for result in gate_results if result["status"] == "passed"),
            "gate_results": gate_results,
            "execution_mode": execution_mode,
            "executed_at": datetime.now().isoformat(),
            "context": context
        }
        
        # Store in Weaviate
        collection = self.weaviate_manager.get_collection("WorkItem")
        collection.data.insert({
            "type": "quality_gate_execution",
            "title": f"Quality gate execution for {work_item_id}",
            "content": json.dumps(execution_result),
            "status": overall_status,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "execution_id": execution_id,
                "work_item_id": work_item_id,
                "overall_score": overall_score,
                "gates_executed": len(gates_to_run)
            }
        })
        
        response = {
            "success": True,
            "execution_id": execution_id,
            "work_item_id": work_item_id,
            "overall_status": overall_status,
            "overall_score": overall_score,
            "gates_executed": len(gates_to_run),
            "gates_passed": sum(1 for result in gate_results if result["status"] == "passed"),
            "gate_results": gate_results,
            "execution_time_minutes": 2,  # Placeholder
            "message": f"Quality gates executed with {overall_status} status"
        }
        
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    
    async def _execute_quality_gate(self, gate: QualityGate, work_item_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single quality gate."""
        # Simulate quality gate execution
        # In a real implementation, this would call actual validation services
        
        passed_criteria = 0
        total_criteria = len(gate.criteria)
        issues = []
        
        for criterion in gate.criteria:
            # Simulate criterion check
            criterion_passed = True  # Placeholder - would be actual validation logic
            
            if criterion_passed:
                passed_criteria += 1
            else:
                issues.append({
                    "criterion": criterion["name"],
                    "description": criterion["description"],
                    "severity": "major" if criterion.get("required", True) else "minor"
                })
        
        score = (passed_criteria / total_criteria * 100) if total_criteria > 0 else 100
        
        if score >= 95:
            status = "passed"
        elif score >= 80:
            status = "requires_review"
        else:
            status = "failed"
        
        return {
            "gate_id": gate.id,
            "gate_name": gate.name,
            "gate_type": gate.gate_type,
            "status": status,
            "score": score,
            "passed_criteria": passed_criteria,
            "total_criteria": total_criteria,
            "issues": issues,
            "execution_time_seconds": 5,  # Placeholder
            "executed_at": datetime.now().isoformat()
        }
    
    async def _get_validation_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Retrieve validation results and approval status."""
        work_item_ids = arguments.get("work_item_ids", [])
        validation_types = arguments.get("validation_types", [])
        status_filter = arguments.get("status_filter", [])
        include_details = arguments.get("include_details", True)
        include_history = arguments.get("include_history", False)
        group_by = arguments.get("group_by", "work_item")
        
        # Filter validation results
        filtered_results = []
        for result in self.validation_results.values():
            # Apply filters
            if work_item_ids and result.work_item_id not in work_item_ids:
                continue
            if validation_types and result.validation_type not in validation_types:
                continue
            if status_filter and result.status not in status_filter:
                continue
            
            filtered_results.append(result)
        
        # Group results
        grouped_results = {}
        if group_by == "work_item":
            for result in filtered_results:
                if result.work_item_id not in grouped_results:
                    grouped_results[result.work_item_id] = []
                grouped_results[result.work_item_id].append(result)
        elif group_by == "validation_type":
            for result in filtered_results:
                if result.validation_type not in grouped_results:
                    grouped_results[result.validation_type] = []
                grouped_results[result.validation_type].append(result)
        elif group_by == "status":
            for result in filtered_results:
                if result.status not in grouped_results:
                    grouped_results[result.status] = []
                grouped_results[result.status].append(result)
        
        # Format response
        response_data = {
            "success": True,
            "total_results": len(filtered_results),
            "group_by": group_by,
            "grouped_results": {},
            "summary": {
                "by_status": {},
                "by_type": {},
                "average_score": 0.0
            }
        }
        
        # Process grouped results
        for group_key, results in grouped_results.items():
            group_data = {
                "count": len(results),
                "results": []
            }
            
            for result in results:
                result_data = {
                    "validation_id": result.id,
                    "work_item_id": result.work_item_id,
                    "validation_type": result.validation_type,
                    "status": result.status,
                    "score": result.score,
                    "validated_at": result.validated_at
                }
                
                if include_details:
                    result_data.update({
                        "passed_checks": result.passed_checks,
                        "total_checks": result.total_checks,
                        "issues": result.issues,
                        "recommendations": result.recommendations,
                        "validated_by": result.validated_by,
                        "notes": result.notes
                    })
                
                group_data["results"].append(result_data)
            
            response_data["grouped_results"][group_key] = group_data
        
        # Calculate summary statistics
        status_counts = {}
        type_counts = {}
        total_score = 0
        score_count = 0
        
        for result in filtered_results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
            type_counts[result.validation_type] = type_counts.get(result.validation_type, 0) + 1
            if result.score is not None:
                total_score += result.score
                score_count += 1
        
        response_data["summary"] = {
            "by_status": status_counts,
            "by_type": type_counts,
            "average_score": total_score / score_count if score_count > 0 else 0.0
        }
        
        return [TextContent(type="text", text=json.dumps(response_data, indent=2))]
    
    async def _approve_completion(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Mark work items as approved after validation."""
        work_item_id = arguments["work_item_id"]
        validation_id = arguments.get("validation_id")
        approver_id = arguments["approver_id"]
        approval_type = arguments.get("approval_type", "full_approval")
        conditions = arguments.get("conditions", [])
        approval_notes = arguments.get("approval_notes", "")
        expires_at = arguments.get("expires_at")
        auto_proceed = arguments.get("auto_proceed", True)
        
        approval_id = str(uuid.uuid4())
        approval_timestamp = datetime.now().isoformat()
        
        # Update validation result if specific validation_id provided
        if validation_id and validation_id in self.validation_results:
            self.validation_results[validation_id].status = ValidationStatus.APPROVED.value
        
        # Create approval record
        approval_record = {
            "approval_id": approval_id,
            "work_item_id": work_item_id,
            "validation_id": validation_id,
            "approver_id": approver_id,
            "approval_type": approval_type,
            "conditions": conditions,
            "approval_notes": approval_notes,
            "approved_at": approval_timestamp,
            "expires_at": expires_at,
            "auto_proceed": auto_proceed,
            "status": "active"
        }
        
        # Store in Weaviate
        collection = self.weaviate_manager.get_collection("WorkItem")
        collection.data.insert({
            "type": "approval",
            "title": f"Approval for {work_item_id}",
            "content": json.dumps(approval_record),
            "status": "approved",
            "created_at": approval_timestamp,
            "metadata": {
                "approval_id": approval_id,
                "work_item_id": work_item_id,
                "approver_id": approver_id,
                "approval_type": approval_type
            }
        })
        
        response = {
            "success": True,
            "approval_id": approval_id,
            "work_item_id": work_item_id,
            "validation_id": validation_id,
            "approval_type": approval_type,
            "approver_id": approver_id,
            "approved_at": approval_timestamp,
            "conditions": conditions,
            "auto_proceed": auto_proceed,
            "message": f"Work item {work_item_id} approved with {approval_type}"
        }
        
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    
    async def _request_changes(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Request changes with specific feedback for work items."""
        work_item_id = arguments["work_item_id"]
        validation_id = arguments.get("validation_id")
        reviewer_id = arguments["reviewer_id"]
        change_requests = arguments["change_requests"]
        overall_feedback = arguments.get("overall_feedback", "")
        priority = arguments.get("priority", "medium")
        due_date = arguments.get("due_date")
        reassign_to = arguments.get("reassign_to")
        notify_stakeholders = arguments.get("notify_stakeholders", True)
        
        change_request_id = str(uuid.uuid4())
        request_timestamp = datetime.now().isoformat()
        
        # Update validation result if specific validation_id provided
        if validation_id and validation_id in self.validation_results:
            self.validation_results[validation_id].status = ValidationStatus.REJECTED.value
        
        # Categorize change requests by severity
        critical_issues = [req for req in change_requests if req.get("severity") == "critical"]
        major_issues = [req for req in change_requests if req.get("severity") == "major"]
        minor_issues = [req for req in change_requests if req.get("severity") == "minor"]
        suggestions = [req for req in change_requests if req.get("severity") == "suggestion"]
        
        # Create change request record
        change_request_record = {
            "change_request_id": change_request_id,
            "work_item_id": work_item_id,
            "validation_id": validation_id,
            "reviewer_id": reviewer_id,
            "change_requests": change_requests,
            "overall_feedback": overall_feedback,
            "priority": priority,
            "due_date": due_date,
            "reassign_to": reassign_to,
            "requested_at": request_timestamp,
            "status": "pending",
            "summary": {
                "total_requests": len(change_requests),
                "critical_issues": len(critical_issues),
                "major_issues": len(major_issues),
                "minor_issues": len(minor_issues),
                "suggestions": len(suggestions),
                "blocking_issues": len([req for req in change_requests if req.get("blocking", True)])
            }
        }
        
        # Store in Weaviate
        collection = self.weaviate_manager.get_collection("WorkItem")
        collection.data.insert({
            "type": "change_request",
            "title": f"Change request for {work_item_id}",
            "content": json.dumps(change_request_record),
            "status": "pending",
            "created_at": request_timestamp,
            "metadata": {
                "change_request_id": change_request_id,
                "work_item_id": work_item_id,
                "reviewer_id": reviewer_id,
                "priority": priority,
                "total_requests": len(change_requests)
            }
        })
        
        response = {
            "success": True,
            "change_request_id": change_request_id,
            "work_item_id": work_item_id,
            "validation_id": validation_id,
            "reviewer_id": reviewer_id,
            "priority": priority,
            "requested_at": request_timestamp,
            "due_date": due_date,
            "reassign_to": reassign_to,
            "summary": change_request_record["summary"],
            "change_requests": change_requests,
            "overall_feedback": overall_feedback,
            "message": f"Change request created with {len(change_requests)} items"
        }
        
        return [TextContent(type="text", text=json.dumps(response, indent=2))]