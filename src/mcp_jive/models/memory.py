"""Memory System Data Models.

Defines the data structures for the Jive Memory system including:
- Architecture Memory: Storage and retrieval of architecture items
- Troubleshoot Memory: Storage and retrieval of troubleshooting solutions

These models enable AI agents to store, retrieve, and leverage institutional knowledge
across sessions and contexts.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ArchitectureItem(BaseModel):
    """Architecture Memory item model.

    Stores individual pieces of architecture requirements and design decisions.
    Supports hierarchical relationships and keyword-based retrieval.
    """

    # Core identification
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    unique_slug: str = Field(..., min_length=1, max_length=100, description="Unique short slug for identification")

    # Core content
    title: str = Field(..., min_length=1, max_length=200, description="Human-friendly short name")
    ai_when_to_use: List[str] = Field(
        default_factory=list,
        description="AI-friendly instructions for when to apply this architecture",
        max_length=10
    )
    ai_requirements: str = Field(
        ...,
        max_length=10000,
        description="AI-friendly detailed specifications of the architecture (Markdown format)"
    )

    # Categorization and discovery
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that describe this architecture item",
        max_length=20
    )

    # Relationships
    children_slugs: List[str] = Field(
        default_factory=list,
        description="Array of slugs that are children of this architecture item",
        max_length=50
    )
    related_slugs: List[str] = Field(
        default_factory=list,
        description="Array of slugs that are related to this architecture item",
        max_length=20
    )

    # Metadata
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date item was originally created"
    )
    last_updated_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date item was last updated"
    )

    # Integration with work items
    linked_epic_ids: List[str] = Field(
        default_factory=list,
        description="Epic work item IDs that reference this architecture",
        max_length=20
    )

    # Additional metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('unique_slug')
    @classmethod
    def validate_slug(cls, v):
        """Validate slug format - alphanumeric, hyphens, and underscores only."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()

    @field_validator('ai_requirements')
    @classmethod
    def validate_requirements_length(cls, v):
        """Validate requirements length and encourage shorter content."""
        if len(v) > 10000:
            raise ValueError("AI Requirements must not exceed 10,000 characters")
        if len(v) > 5000:
            logger.warning(f"AI Requirements length ({len(v)} chars) exceeds recommended 5,000 characters. Consider breaking into smaller architecture items.")
        return v

    @field_validator('last_updated_on', mode='before')
    @classmethod
    def set_updated_on(cls, v):
        """Always update the timestamp when the model is modified."""
        return datetime.now(timezone.utc)


class TroubleshootItem(BaseModel):
    """Troubleshoot Memory item model.

    Stores troubleshooting tips and solutions for common problems.
    Optimized for problem-solution matching and AI-friendly retrieval.
    """

    # Core identification
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    unique_slug: str = Field(..., min_length=1, max_length=100, description="Unique short slug for identification")

    # Core content
    title: str = Field(..., min_length=1, max_length=200, description="Human-friendly short name")
    ai_use_case: List[str] = Field(
        default_factory=list,
        description="AI-friendly short problem descriptions when this troubleshooting item should be applied",
        max_length=10
    )
    ai_solutions: str = Field(
        ...,
        max_length=10000,
        description="AI-friendly solution with tips, steps, or instructions (Markdown format)"
    )

    # Categorization and discovery
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that describe this troubleshooting item",
        max_length=20
    )

    # Metadata
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date item was originally created"
    )
    last_updated_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date item was last updated"
    )

    # Usage tracking
    usage_count: int = Field(default=0, description="Number of times this solution has been retrieved")
    success_count: int = Field(default=0, description="Number of times this solution was marked as successful")

    # Additional metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('unique_slug')
    @classmethod
    def validate_slug(cls, v):
        """Validate slug format - alphanumeric, hyphens, and underscores only."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()

    @field_validator('ai_solutions')
    @classmethod
    def validate_solutions_length(cls, v):
        """Validate solutions length and encourage shorter content."""
        if len(v) > 10000:
            raise ValueError("AI Solutions must not exceed 10,000 characters")
        if len(v) > 5000:
            logger.warning(f"AI Solutions length ({len(v)} chars) exceeds recommended 5,000 characters. Consider breaking into multiple troubleshooting items.")
        return v

    @field_validator('last_updated_on', mode='before')
    @classmethod
    def set_updated_on(cls, v):
        """Always update the timestamp when the model is modified."""
        return datetime.now(timezone.utc)


class ArchitectureItemSummary(BaseModel):
    """Summary of an architecture item for context-aware retrieval.

    Provides condensed information respecting token limits while maintaining
    essential architectural guidance.
    """

    slug: str = Field(..., description="Architecture item slug")
    title: str = Field(..., description="Architecture item title")
    when_to_use: List[str] = Field(..., description="When to apply this architecture")
    key_requirements: str = Field(..., description="Condensed key requirements")
    children_count: int = Field(default=0, description="Number of child items")
    related_count: int = Field(default=0, description="Number of related items")


class TroubleshootItemMatch(BaseModel):
    """Matched troubleshoot item with relevance scoring.

    Represents a troubleshooting solution matched to a problem description.
    """

    slug: str = Field(..., description="Troubleshoot item slug")
    title: str = Field(..., description="Troubleshoot item title")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Match relevance score (0-1)")
    matched_use_cases: List[str] = Field(..., description="Use cases that matched the problem")
    solution_preview: str = Field(..., description="Preview of the solution")


class MemoryExportMetadata(BaseModel):
    """Metadata for memory system exports.

    Tracks export information for both Architecture and Troubleshoot Memory.
    """

    export_type: str = Field(..., description="Type: 'architecture' or 'troubleshoot'")
    namespace: str = Field(..., description="Namespace of exported data")
    export_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the export was created"
    )
    total_items: int = Field(..., description="Total number of items exported")
    format: str = Field(default="markdown", description="Export format")
    version: str = Field(default="1.0", description="Export format version")