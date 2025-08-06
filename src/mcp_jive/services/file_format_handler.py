"""File Format Handler for Task Storage and Sync System.

Handles parsing and formatting of work item files in various formats (JSON, YAML, Markdown).
Ensures consistent data structure and validation across file formats.
"""

import json
import yaml
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, ValidationError, field_validator

logger = logging.getLogger(__name__)

class WorkItemSchema(BaseModel):
    """Schema for work item data structure."""
    id: str
    title: str
    description: str
    type: str  # epic, feature, story, task, bug
    status: str  # todo, in_progress, done, blocked
    priority: str  # low, medium, high, critical
    assignee: Optional[str] = None
    parent_id: Optional[str] = None
    children: List[str] = []
    dependencies: List[str] = []
    tags: List[str] = []
    # AI Optimization Parameters
    context_tags: List[str] = []
    complexity: Optional[str] = None
    notes: Optional[str] = None
    acceptance_criteria: List[str] = []
    metadata: Dict[str, Any] = {}
    created_at: str
    updated_at: str
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    progress: float = 0.0
    
    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Progress must be between 0.0 and 1.0')
        return v
    
class FileFormatHandler:
    """Handles file format operations for work items."""
    
    SUPPORTED_FORMATS = ['.json', '.yaml', '.yml', '.md']
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def parse_file_content(self, content: str, file_path: str) -> Optional[WorkItemSchema]:
        """Parse file content based on file extension.
        
        Args:
            content: Raw file content
            file_path: Path to the file (used to determine format)
            
        Returns:
            Parsed WorkItemSchema or None if parsing fails
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.json':
                return await self._parse_json(content)
            elif file_ext in ['.yaml', '.yml']:
                return await self._parse_yaml(content)
            elif file_ext == '.md':
                return await self._parse_markdown(content)
            else:
                self.logger.warning(f"Unsupported file format: {file_ext}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing file {file_path}: {e}")
            return None
            
    async def format_work_item(self, work_item: WorkItemSchema, format_type: str) -> str:
        """Format work item data to specified format.
        
        Args:
            work_item: WorkItemSchema instance
            format_type: Target format (.json, .yaml, .md)
            
        Returns:
            Formatted string content
        """
        try:
            if format_type == '.json':
                return await self._format_json(work_item)
            elif format_type in ['.yaml', '.yml']:
                return await self._format_yaml(work_item)
            elif format_type == '.md':
                return await self._format_markdown(work_item)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
                
        except Exception as e:
            self.logger.error(f"Error formatting work item to {format_type}: {e}")
            raise
            
    async def validate_work_item(self, data: Dict[str, Any]) -> bool:
        """Validate work item data against schema.
        
        Args:
            data: Work item data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            WorkItemSchema(**data)
            return True
        except ValidationError as e:
            self.logger.warning(f"Work item validation failed: {e}")
            return False
            
    async def _parse_json(self, content: str) -> Optional[WorkItemSchema]:
        """Parse JSON content."""
        try:
            data = json.loads(content)
            return WorkItemSchema(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            self.logger.error(f"JSON parsing error: {e}")
            return None
            
    async def _parse_yaml(self, content: str) -> Optional[WorkItemSchema]:
        """Parse YAML content."""
        try:
            data = yaml.safe_load(content)
            return WorkItemSchema(**data)
        except (yaml.YAMLError, ValidationError) as e:
            self.logger.error(f"YAML parsing error: {e}")
            return None
            
    async def _parse_markdown(self, content: str) -> Optional[WorkItemSchema]:
        """Parse Markdown content with YAML frontmatter."""
        try:
            # Split frontmatter and content
            if content.startswith('---\n'):
                parts = content.split('---\n', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    description = parts[2].strip()
                    
                    # Parse YAML frontmatter
                    data = yaml.safe_load(frontmatter)
                    if 'description' not in data:
                        data['description'] = description
                        
                    return WorkItemSchema(**data)
                    
            # Fallback: treat entire content as description
            self.logger.warning("Markdown file missing frontmatter, treating as description only")
            return None
            
        except (yaml.YAMLError, ValidationError) as e:
            self.logger.error(f"Markdown parsing error: {e}")
            return None
            
    async def _format_json(self, work_item: WorkItemSchema) -> str:
        """Format work item as JSON."""
        return json.dumps(work_item.model_dump(), indent=2, ensure_ascii=False)
        
    async def _format_yaml(self, work_item: WorkItemSchema) -> str:
        """Format work item as YAML."""
        return yaml.dump(work_item.model_dump(), default_flow_style=False, allow_unicode=True)
        
    async def _format_markdown(self, work_item: WorkItemSchema) -> str:
        """Format work item as Markdown with YAML frontmatter."""
        # Extract description for content
        data = work_item.model_dump()
        description = data.pop('description', '')
        
        # Create frontmatter
        frontmatter = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        
        # Combine frontmatter and content
        return f"---\n{frontmatter}---\n\n{description}"
        
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return self.SUPPORTED_FORMATS.copy()
        
    def is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported."""
        return Path(file_path).suffix.lower() in self.SUPPORTED_FORMATS
        
    async def create_default_work_item(self, 
                                     work_item_id: str, 
                                     title: str, 
                                     work_item_type: str = "task") -> WorkItemSchema:
        """Create a default work item with minimal required fields.
        
        Args:
            work_item_id: Unique identifier
            title: Work item title
            work_item_type: Type of work item
            
        Returns:
            WorkItemSchema with default values
        """
        now = datetime.now().isoformat()
        
        return WorkItemSchema(
            id=work_item_id,
            title=title,
            description=f"Auto-generated {work_item_type}: {title}",
            type=work_item_type,
            status="todo",
            priority="medium",
            created_at=now,
            updated_at=now,
            metadata={"auto_generated": True}
        )