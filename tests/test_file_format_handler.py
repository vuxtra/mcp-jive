"""Tests for File Format Handler.

Tests parsing and formatting of work item files in various formats.
"""

import pytest
import json
import yaml
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, mock_open
import tempfile
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the classes to test directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "file_format_handler", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'mcp_server', 'services', 'file_format_handler.py')
)
file_format_handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(file_format_handler_module)

FileFormatHandler = file_format_handler_module.FileFormatHandler
WorkItemSchema = file_format_handler_module.WorkItemSchema

@pytest.fixture
def file_handler():
    """Create FileFormatHandler instance."""
    return FileFormatHandler()

@pytest.fixture
def sample_work_item_data():
    """Sample work item data for testing."""
    return {
        "id": "task-001",
        "title": "Test Task",
        "description": "This is a test task for validation",
        "type": "task",
        "status": "todo",
        "priority": "medium",
        "assignee": "john.doe",
        "parent_id": "epic-001",
        "children": ["subtask-001", "subtask-002"],
        "dependencies": ["task-000"],
        "tags": ["backend", "api"],
        "metadata": {"sprint": "sprint-1", "points": 5},
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "estimated_hours": 8.0,
        "actual_hours": 6.5,
        "progress": 0.75
    }

@pytest.fixture
def sample_work_item(sample_work_item_data):
    """Create WorkItemSchema instance."""
    return WorkItemSchema(**sample_work_item_data)

class TestWorkItemSchema:
    """Test WorkItemSchema validation."""
    
    def test_valid_work_item_creation(self, sample_work_item_data):
        """Test creating valid work item."""
        work_item = WorkItemSchema(**sample_work_item_data)
        assert work_item.id == "task-001"
        assert work_item.title == "Test Task"
        assert work_item.type == "task"
        assert work_item.status == "todo"
        assert work_item.priority == "medium"
        
    def test_minimal_work_item_creation(self):
        """Test creating work item with minimal required fields."""
        minimal_data = {
            "id": "task-minimal",
            "title": "Minimal Task",
            "description": "Minimal description",
            "type": "task",
            "status": "todo",
            "priority": "medium",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z"
        }
        
        work_item = WorkItemSchema(**minimal_data)
        assert work_item.id == "task-minimal"
        assert work_item.children == []
        assert work_item.dependencies == []
        assert work_item.tags == []
        assert work_item.metadata == {}
        assert work_item.progress == 0.0
        
    def test_invalid_work_item_creation(self):
        """Test validation errors for invalid work item data."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):  # Missing required fields
            WorkItemSchema(id="test")
            
        with pytest.raises(ValidationError):  # Invalid progress value
            WorkItemSchema(
                id="test",
                title="Test",
                description="Test",
                type="task",
                status="todo",
                priority="medium",
                created_at="2024-01-01T10:00:00Z",
                updated_at="2024-01-01T10:00:00Z",
                progress=1.5  # Invalid: > 1.0
            )

class TestFileFormatHandler:
    """Test FileFormatHandler functionality."""
    
    @pytest.mark.asyncio
    async def test_supported_formats(self, file_handler):
        """Test supported file formats."""
        formats = file_handler.get_supported_formats()
        assert '.json' in formats
        assert '.yaml' in formats
        assert '.yml' in formats
        assert '.md' in formats
        
        assert file_handler.is_supported_format('test.json')
        assert file_handler.is_supported_format('test.yaml')
        assert file_handler.is_supported_format('test.yml')
        assert file_handler.is_supported_format('test.md')
        assert not file_handler.is_supported_format('test.txt')
        
    @pytest.mark.asyncio
    async def test_validate_work_item(self, file_handler, sample_work_item_data):
        """Test work item validation."""
        # Valid data
        assert await file_handler.validate_work_item(sample_work_item_data)
        
        # Invalid data - missing required field
        invalid_data = sample_work_item_data.copy()
        del invalid_data['title']
        assert not await file_handler.validate_work_item(invalid_data)
        
    @pytest.mark.asyncio
    async def test_create_default_work_item(self, file_handler):
        """Test creating default work item."""
        work_item = await file_handler.create_default_work_item(
            "test-001", "Test Title", "story"
        )
        
        assert work_item.id == "test-001"
        assert work_item.title == "Test Title"
        assert work_item.type == "story"
        assert work_item.status == "todo"
        assert work_item.priority == "medium"
        assert work_item.metadata["auto_generated"] is True
        
class TestJSONFormatting:
    """Test JSON format parsing and formatting."""
    
    @pytest.mark.asyncio
    async def test_parse_json_content(self, file_handler, sample_work_item_data):
        """Test parsing JSON content."""
        json_content = json.dumps(sample_work_item_data, indent=2)
        
        work_item = await file_handler.parse_file_content(json_content, "test.json")
        
        assert work_item is not None
        assert work_item.id == "task-001"
        assert work_item.title == "Test Task"
        assert work_item.type == "task"
        
    @pytest.mark.asyncio
    async def test_parse_invalid_json(self, file_handler):
        """Test parsing invalid JSON content."""
        invalid_json = "{ invalid json content"
        
        work_item = await file_handler.parse_file_content(invalid_json, "test.json")
        assert work_item is None
        
    @pytest.mark.asyncio
    async def test_format_json(self, file_handler, sample_work_item):
        """Test formatting work item as JSON."""
        json_content = await file_handler.format_work_item(sample_work_item, ".json")
        
        # Parse back to verify
        parsed_data = json.loads(json_content)
        assert parsed_data["id"] == "task-001"
        assert parsed_data["title"] == "Test Task"
        
class TestYAMLFormatting:
    """Test YAML format parsing and formatting."""
    
    @pytest.mark.asyncio
    async def test_parse_yaml_content(self, file_handler, sample_work_item_data):
        """Test parsing YAML content."""
        yaml_content = yaml.dump(sample_work_item_data, default_flow_style=False)
        
        work_item = await file_handler.parse_file_content(yaml_content, "test.yaml")
        
        assert work_item is not None
        assert work_item.id == "task-001"
        assert work_item.title == "Test Task"
        
    @pytest.mark.asyncio
    async def test_parse_yml_extension(self, file_handler, sample_work_item_data):
        """Test parsing .yml extension."""
        yaml_content = yaml.dump(sample_work_item_data, default_flow_style=False)
        
        work_item = await file_handler.parse_file_content(yaml_content, "test.yml")
        
        assert work_item is not None
        assert work_item.id == "task-001"
        
    @pytest.mark.asyncio
    async def test_parse_invalid_yaml(self, file_handler):
        """Test parsing invalid YAML content."""
        invalid_yaml = "invalid: yaml: content: ["
        
        work_item = await file_handler.parse_file_content(invalid_yaml, "test.yaml")
        assert work_item is None
        
    @pytest.mark.asyncio
    async def test_format_yaml(self, file_handler, sample_work_item):
        """Test formatting work item as YAML."""
        yaml_content = await file_handler.format_work_item(sample_work_item, ".yaml")
        
        # Parse back to verify
        parsed_data = yaml.safe_load(yaml_content)
        assert parsed_data["id"] == "task-001"
        assert parsed_data["title"] == "Test Task"
        
class TestMarkdownFormatting:
    """Test Markdown format parsing and formatting."""
    
    @pytest.mark.asyncio
    async def test_parse_markdown_with_frontmatter(self, file_handler, sample_work_item_data):
        """Test parsing Markdown with YAML frontmatter."""
        # Create frontmatter without description
        frontmatter_data = sample_work_item_data.copy()
        description = frontmatter_data.pop('description')
        
        frontmatter = yaml.dump(frontmatter_data, default_flow_style=False)
        markdown_content = f"---\n{frontmatter}---\n\n{description}"
        
        work_item = await file_handler.parse_file_content(markdown_content, "test.md")
        
        assert work_item is not None
        assert work_item.id == "task-001"
        assert work_item.title == "Test Task"
        assert work_item.description == description
        
    @pytest.mark.asyncio
    async def test_parse_markdown_without_frontmatter(self, file_handler):
        """Test parsing Markdown without frontmatter."""
        markdown_content = "# Test Title\n\nThis is just markdown content without frontmatter."
        
        work_item = await file_handler.parse_file_content(markdown_content, "test.md")
        assert work_item is None  # Should fail without frontmatter
        
    @pytest.mark.asyncio
    async def test_format_markdown(self, file_handler, sample_work_item):
        """Test formatting work item as Markdown."""
        markdown_content = await file_handler.format_work_item(sample_work_item, ".md")
        
        # Should start with frontmatter
        assert markdown_content.startswith("---\n")
        assert "---\n\n" in markdown_content
        
        # Should contain description after frontmatter
        parts = markdown_content.split("---\n\n", 1)
        assert len(parts) == 2
        assert "This is a test task for validation" in parts[1]
        
    @pytest.mark.asyncio
    async def test_roundtrip_markdown(self, file_handler, sample_work_item):
        """Test roundtrip: format to markdown and parse back."""
        # Format to markdown
        markdown_content = await file_handler.format_work_item(sample_work_item, ".md")
        
        # Parse back
        parsed_item = await file_handler.parse_file_content(markdown_content, "test.md")
        
        assert parsed_item is not None
        assert parsed_item.id == sample_work_item.id
        assert parsed_item.title == sample_work_item.title
        assert parsed_item.description == sample_work_item.description
        
class TestUnsupportedFormats:
    """Test handling of unsupported formats."""
    
    @pytest.mark.asyncio
    async def test_parse_unsupported_format(self, file_handler, sample_work_item_data):
        """Test parsing unsupported file format."""
        content = "some content"
        
        work_item = await file_handler.parse_file_content(content, "test.txt")
        assert work_item is None
        
    @pytest.mark.asyncio
    async def test_format_unsupported_format(self, file_handler, sample_work_item):
        """Test formatting to unsupported format."""
        with pytest.raises(ValueError, match="Unsupported format type"):
            await file_handler.format_work_item(sample_work_item, ".txt")
            
class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_parse_empty_content(self, file_handler):
        """Test parsing empty content."""
        work_item = await file_handler.parse_file_content("", "test.json")
        assert work_item is None
        
    @pytest.mark.asyncio
    async def test_parse_malformed_json(self, file_handler):
        """Test parsing malformed JSON."""
        malformed_json = '{"id": "test", "title":}'
        
        work_item = await file_handler.parse_file_content(malformed_json, "test.json")
        assert work_item is None
        
    @pytest.mark.asyncio
    async def test_parse_incomplete_data(self, file_handler):
        """Test parsing JSON with missing required fields."""
        incomplete_data = {"id": "test", "title": "Test"}
        json_content = json.dumps(incomplete_data)
        
        work_item = await file_handler.parse_file_content(json_content, "test.json")
        assert work_item is None  # Should fail validation