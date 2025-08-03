#!/usr/bin/env python3
"""
Category 4: Progress Tracking Tools Test Suite

Tests the 4 progress tracking tools:
- jive_track_progress
- jive_get_progress_report
- jive_set_milestone
- jive_get_analytics
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.tools.progress_tracking import ProgressTrackingTools
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.config import ServerConfig

async def test_category_4_progress_tracking():
    """Test Category 4: Progress Tracking Tools."""
    print("\n=== Category 4: Progress Tracking Tools Test ===")
    
    try:
        # Initialize components
        server_config = ServerConfig()
        db_config = DatabaseConfig()
        lancedb_manager = LanceDBManager(db_config)
        await lancedb_manager.initialize()
        
        progress_tools = ProgressTrackingTools(server_config, lancedb_manager)
        await progress_tools.initialize()
        
        # Test 4.1: jive_track_progress
        print("\n--- Test 4.1: jive_track_progress ---")
        
        # Track progress for a task
        track_args = {
            "entity_id": "task-001",
            "entity_type": "task",
            "progress_percentage": 25.0,
            "status": "in_progress",
            "notes": "Initial implementation started",
            "estimated_completion": (datetime.now() + timedelta(days=7)).isoformat() + "Z",
            "blockers": ["Waiting for API documentation"],
            "auto_calculate_status": False
        }
        
        result = await progress_tools.handle_tool_call("jive_track_progress", track_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            progress_id_1 = response.get("progress_id")
            print(f"✅ Test 4.1a PASSED: Task progress tracked at 25% with ID {progress_id_1}")
        else:
            print(f"❌ Test 4.1a FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Track progress for a workflow
        workflow_track_args = {
            "entity_id": "workflow-001",
            "entity_type": "workflow",
            "progress_percentage": 75.0,
            "status": "on_track",
            "notes": "Most tasks completed successfully",
            "estimated_completion": (datetime.now() + timedelta(days=3)).isoformat() + "Z",
            "auto_calculate_status": True
        }
        
        result = await progress_tools.handle_tool_call("jive_track_progress", workflow_track_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            progress_id_2 = response.get("progress_id")
            print(f"✅ Test 4.1b PASSED: Workflow progress tracked at 75% with ID {progress_id_2}")
        else:
            print(f"❌ Test 4.1b FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Test 4.2: jive_get_progress_report
        print("\n--- Test 4.2: jive_get_progress_report ---")
        
        report_args = {
            "entity_ids": [],  # Get all entities
            "entity_type": "all",
            "time_range": {
                "start_date": (datetime.now() - timedelta(days=1)).isoformat() + "Z",
                "end_date": (datetime.now() + timedelta(days=1)).isoformat() + "Z"
            },
            "include_history": True,
            "include_analytics": True,
            "group_by": "entity_type"
        }
        
        result = await progress_tools.handle_tool_call("jive_get_progress_report", report_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            print(f"✅ Test 4.2 PASSED: Progress report generated with {response.get('total_entries', 0)} entries")
        else:
            print(f"❌ Test 4.2 FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Test 4.3: jive_set_milestone
        print("\n--- Test 4.3: jive_set_milestone ---")
        
        milestone_args = {
            "title": "Beta Release",
            "description": "Complete beta version with core features",
            "milestone_type": "delivery",
            "target_date": (datetime.now() + timedelta(days=30)).isoformat() + "Z",
            "associated_tasks": ["task-001", "task-002", "task-003"],
            "success_criteria": [
                "All core features implemented",
                "Unit tests passing",
                "Performance benchmarks met",
                "Security review completed"
            ],
            "priority": "high"
        }
        
        result = await progress_tools.handle_tool_call("jive_set_milestone", milestone_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            milestone_id = response.get("milestone_id")
            print(f"✅ Test 4.3a PASSED: Beta Release milestone created with ID {milestone_id}")
        else:
            print(f"❌ Test 4.3a FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Create another milestone
        security_milestone_args = {
            "title": "Security Audit",
            "description": "Complete security audit and penetration testing",
            "milestone_type": "review_point",
            "target_date": (datetime.now() + timedelta(days=45)).isoformat() + "Z",
            "associated_tasks": ["security-001", "security-002"],
            "success_criteria": [
                "Penetration testing completed",
                "Vulnerability assessment passed",
                "Security documentation updated"
            ],
            "priority": "critical"
        }
        
        result = await progress_tools.handle_tool_call("jive_set_milestone", security_milestone_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            security_milestone_id = response.get("milestone_id")
            print(f"✅ Test 4.3b PASSED: Security Audit milestone created with ID {security_milestone_id}")
        else:
            print(f"❌ Test 4.3b FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Test 4.4: jive_get_analytics
        print("\n--- Test 4.4: jive_get_analytics ---")
        
        # Test overview analytics
        analytics_args = {
            "analysis_type": "overview",
            "time_period": "last_month",
            "entity_filter": {
                "entity_type": "all",
                "status": ["in_progress", "on_track", "completed"]
            },
            "include_predictions": True,
            "detail_level": "detailed"
        }
        
        result = await progress_tools.handle_tool_call("jive_get_analytics", analytics_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            print(f"✅ Test 4.4a PASSED: Overview analytics generated with {response.get('data_points', 0)} data points")
        else:
            print(f"❌ Test 4.4a FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Test milestone analytics
        milestone_analytics_args = {
            "analysis_type": "milestones",
            "time_period": "all_time",
            "include_predictions": False,
            "detail_level": "comprehensive"
        }
        
        result = await progress_tools.handle_tool_call("jive_get_analytics", milestone_analytics_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            analytics = response.get("analytics", {})
            milestones_data = analytics.get("milestones", {})
            print(f"✅ Test 4.4b PASSED: Milestone analytics generated - {milestones_data.get('total_milestones', 0)} total milestones")
        else:
            print(f"❌ Test 4.4b FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        # Test trends analytics
        trends_analytics_args = {
            "analysis_type": "trends",
            "time_period": "last_week",
            "entity_filter": {
                "entity_type": "task"
            },
            "include_predictions": True,
            "detail_level": "summary"
        }
        
        result = await progress_tools.handle_tool_call("jive_get_analytics", trends_analytics_args)
        response = json.loads(result[0].text)
        
        if response.get("success"):
            print("✅ Test 4.4c PASSED: Trends analytics generated successfully")
        else:
            print(f"❌ Test 4.4c FAILED: {response.get('error', 'Unknown error')}")
            return False
            
        print("\n🎉 All Category 4 tests (4.1, 4.2, 4.3, 4.4) completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Category 4 tests failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    try:
        success = await test_category_4_progress_tracking()
        if success:
            print("\n✅ Category 4: Progress Tracking Tools - All tests passed!")
        else:
            print("\n❌ Category 4: Progress Tracking Tools - Some tests failed!")
            return False
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)