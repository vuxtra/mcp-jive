"""Status validation utility for MCP Jive work items.

This module provides comprehensive status validation and transition management
for work items in the MCP Jive system.
"""

import logging
from datetime import datetime
from typing import Dict, Set, List, Optional, Any
from enum import Enum


class WorkItemStatus(Enum):
    """Enumeration of valid work item statuses."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    ON_HOLD = "on_hold"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class StatusValidator:
    """Utility class for validating work item status transitions."""
    
    # Valid status values
    VALID_STATUSES: Set[str] = {
        status.value for status in WorkItemStatus
    }
    
    # Valid status transitions mapping
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        WorkItemStatus.NOT_STARTED.value: {
            WorkItemStatus.IN_PROGRESS.value,
            WorkItemStatus.CANCELLED.value,
            WorkItemStatus.ON_HOLD.value
        },
        WorkItemStatus.IN_PROGRESS.value: {
            WorkItemStatus.COMPLETED.value,
            WorkItemStatus.FAILED.value,
            WorkItemStatus.BLOCKED.value,
            WorkItemStatus.ON_HOLD.value,
            WorkItemStatus.CANCELLED.value,
            WorkItemStatus.UNDER_REVIEW.value
        },
        WorkItemStatus.BLOCKED.value: {
            WorkItemStatus.IN_PROGRESS.value,
            WorkItemStatus.CANCELLED.value,
            WorkItemStatus.ON_HOLD.value
        },
        WorkItemStatus.ON_HOLD.value: {
            WorkItemStatus.IN_PROGRESS.value,
            WorkItemStatus.CANCELLED.value,
            WorkItemStatus.NOT_STARTED.value
        },
        WorkItemStatus.UNDER_REVIEW.value: {
            WorkItemStatus.APPROVED.value,
            WorkItemStatus.REJECTED.value,
            WorkItemStatus.IN_PROGRESS.value,
            WorkItemStatus.CANCELLED.value
        },
        WorkItemStatus.APPROVED.value: {
            WorkItemStatus.COMPLETED.value,
            WorkItemStatus.IN_PROGRESS.value
        },
        WorkItemStatus.REJECTED.value: {
            WorkItemStatus.IN_PROGRESS.value,
            WorkItemStatus.CANCELLED.value
        },
        WorkItemStatus.COMPLETED.value: {
            # Terminal state - can only reopen for corrections
            WorkItemStatus.IN_PROGRESS.value
        },
        WorkItemStatus.FAILED.value: {
            # Can retry or cancel
            WorkItemStatus.IN_PROGRESS.value,
            WorkItemStatus.CANCELLED.value
        },
        WorkItemStatus.CANCELLED.value: {
            # Terminal state - can only restart
            WorkItemStatus.NOT_STARTED.value,
            WorkItemStatus.IN_PROGRESS.value
        }
    }
    
    # Terminal statuses that typically don't change
    TERMINAL_STATUSES: Set[str] = {
        WorkItemStatus.COMPLETED.value,
        WorkItemStatus.CANCELLED.value
    }
    
    # Active statuses that indicate work is ongoing
    ACTIVE_STATUSES: Set[str] = {
        WorkItemStatus.IN_PROGRESS.value,
        WorkItemStatus.UNDER_REVIEW.value
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def is_valid_status(cls, status: str) -> bool:
        """Check if a status is valid.
        
        Args:
            status: The status to validate
            
        Returns:
            True if the status is valid, False otherwise
        """
        return status in cls.VALID_STATUSES
    
    @classmethod
    def is_valid_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid.
        
        Args:
            from_status: The current status
            to_status: The target status
            
        Returns:
            True if the transition is valid, False otherwise
        """
        if not cls.is_valid_status(from_status) or not cls.is_valid_status(to_status):
            return False
        
        # Same status is always valid
        if from_status == to_status:
            return True
        
        return to_status in cls.VALID_TRANSITIONS.get(from_status, set())
    
    @classmethod
    def get_valid_transitions(cls, from_status: str) -> Set[str]:
        """Get all valid transitions from a given status.
        
        Args:
            from_status: The current status
            
        Returns:
            Set of valid target statuses
        """
        if not cls.is_valid_status(from_status):
            return set()
        
        return cls.VALID_TRANSITIONS.get(from_status, set())
    
    @classmethod
    def is_terminal_status(cls, status: str) -> bool:
        """Check if a status is terminal (typically doesn't change).
        
        Args:
            status: The status to check
            
        Returns:
            True if the status is terminal, False otherwise
        """
        return status in cls.TERMINAL_STATUSES
    
    @classmethod
    def is_active_status(cls, status: str) -> bool:
        """Check if a status indicates active work.
        
        Args:
            status: The status to check
            
        Returns:
            True if the status indicates active work, False otherwise
        """
        return status in cls.ACTIVE_STATUSES
    
    def validate_status_update(self, current_status: str, new_status: str, 
                              reason: Optional[str] = None) -> Dict[str, Any]:
        """Validate a status update with detailed feedback.
        
        Args:
            current_status: The current status
            new_status: The proposed new status
            reason: Optional reason for the status change
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': False,
            'current_status': current_status,
            'new_status': new_status,
            'reason': reason,
            'error_message': None,
            'warnings': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if current status is valid
        if not self.is_valid_status(current_status):
            validation_result['error_message'] = f"Invalid current status: {current_status}"
            return validation_result
        
        # Check if new status is valid
        if not self.is_valid_status(new_status):
            validation_result['error_message'] = f"Invalid new status: {new_status}"
            return validation_result
        
        # Check if transition is valid
        if not self.is_valid_transition(current_status, new_status):
            valid_transitions = self.get_valid_transitions(current_status)
            validation_result['error_message'] = (
                f"Invalid transition from '{current_status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(sorted(valid_transitions))}"
            )
            return validation_result
        
        # Add warnings for potentially problematic transitions
        if self.is_terminal_status(current_status) and current_status != new_status:
            validation_result['warnings'].append(
                f"Changing from terminal status '{current_status}' - ensure this is intentional"
            )
        
        if new_status == WorkItemStatus.FAILED.value and not reason:
            validation_result['warnings'].append(
                "Status changed to 'failed' without a reason - consider providing details"
            )
        
        if (current_status == WorkItemStatus.IN_PROGRESS.value and 
            new_status == WorkItemStatus.CANCELLED.value and not reason):
            validation_result['warnings'].append(
                "Cancelling in-progress work without reason - consider providing details"
            )
        
        validation_result['is_valid'] = True
        return validation_result
    
    def create_status_history_entry(self, old_status: str, new_status: str, 
                                   reason: Optional[str] = None, 
                                   updated_by: str = "system") -> Dict[str, Any]:
        """Create a status history entry.
        
        Args:
            old_status: The previous status
            new_status: The new status
            reason: Optional reason for the change
            updated_by: Who made the change
            
        Returns:
            Dictionary representing the status history entry
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'from_status': old_status,
            'to_status': new_status,
            'reason': reason,
            'updated_by': updated_by,
            'transition_valid': self.is_valid_transition(old_status, new_status)
        }
    
    def get_status_summary(self, status_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of status changes.
        
        Args:
            status_history: List of status history entries
            
        Returns:
            Dictionary with status summary information
        """
        if not status_history:
            return {
                'total_changes': 0,
                'current_status': None,
                'time_in_current_status': None,
                'most_common_status': None,
                'invalid_transitions': 0
            }
        
        # Sort by timestamp
        sorted_history = sorted(status_history, key=lambda x: x['timestamp'])
        
        current_entry = sorted_history[-1]
        current_status = current_entry['to_status']
        
        # Calculate time in current status
        current_time = datetime.now()
        last_change_time = datetime.fromisoformat(current_entry['timestamp'].replace('Z', '+00:00'))
        time_in_current = current_time - last_change_time.replace(tzinfo=None)
        
        # Count status occurrences
        status_counts = {}
        invalid_transitions = 0
        
        for entry in sorted_history:
            to_status = entry['to_status']
            status_counts[to_status] = status_counts.get(to_status, 0) + 1
            
            if not entry.get('transition_valid', True):
                invalid_transitions += 1
        
        most_common_status = max(status_counts.items(), key=lambda x: x[1])[0] if status_counts else None
        
        return {
            'total_changes': len(sorted_history),
            'current_status': current_status,
            'time_in_current_status': str(time_in_current),
            'most_common_status': most_common_status,
            'invalid_transitions': invalid_transitions,
            'status_distribution': status_counts
        }