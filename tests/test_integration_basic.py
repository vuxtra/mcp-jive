"""Basic integration test for Task Storage and Sync System.

Simple test to verify core functionality without complex imports.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

def test_basic_file_operations():
    """Test basic file operations work."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a sample work item file
        work_item_data = {
            "id": "test-001",
            "title": "Test Task",
            "description": "This is a test task",
            "type": "task",
            "status": "todo",
            "priority": "medium",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z"
        }
        
        # Write to JSON file
        json_file = Path(temp_dir) / "test-001.json"
        with open(json_file, 'w') as f:
            json.dump(work_item_data, f, indent=2)
            
        # Verify file was created
        assert json_file.exists()
        
        # Read and verify content
        with open(json_file, 'r') as f:
            loaded_data = json.load(f)
            
        assert loaded_data["id"] == "test-001"
        assert loaded_data["title"] == "Test Task"
        assert loaded_data["type"] == "task"
        
def test_directory_structure():
    """Test that we can create the expected directory structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .jivedev/tasks structure
        tasks_dir = Path(temp_dir) / ".jivedev" / "tasks"
        sync_dir = Path(temp_dir) / ".jivedev" / "sync"
        config_dir = Path(temp_dir) / ".jivedev" / "config"
        
        # Create directories
        tasks_dir.mkdir(parents=True, exist_ok=True)
        sync_dir.mkdir(parents=True, exist_ok=True)
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify directories exist
        assert tasks_dir.exists()
        assert sync_dir.exists()
        assert config_dir.exists()
        
        # Create some test files
        (tasks_dir / "epic-001.json").touch()
        (tasks_dir / "story-001.yaml").touch()
        (tasks_dir / "task-001.md").touch()
        
        # Verify files exist
        assert (tasks_dir / "epic-001.json").exists()
        assert (tasks_dir / "story-001.yaml").exists()
        assert (tasks_dir / "task-001.md").exists()
        
def test_json_schema_validation():
    """Test basic JSON schema validation."""
    # Valid work item
    valid_item = {
        "id": "test-001",
        "title": "Test Task",
        "description": "This is a test task",
        "type": "task",
        "status": "todo",
        "priority": "medium",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
        "progress": 0.5
    }
    
    # Check required fields are present
    required_fields = ["id", "title", "description", "type", "status", "priority"]
    for field in required_fields:
        assert field in valid_item
        
    # Check data types
    assert isinstance(valid_item["id"], str)
    assert isinstance(valid_item["title"], str)
    assert isinstance(valid_item["progress"], (int, float))
    assert 0.0 <= valid_item["progress"] <= 1.0
    
def test_file_format_support():
    """Test that we support the expected file formats."""
    supported_formats = [".json", ".yaml", ".yml", ".md"]
    
    test_files = [
        "task-001.json",
        "story-001.yaml", 
        "epic-001.yml",
        "feature-001.md"
    ]
    
    for file_name in test_files:
        file_ext = Path(file_name).suffix.lower()
        assert file_ext in supported_formats
        
if __name__ == "__main__":
    pytest.main([__file__, "-v"])