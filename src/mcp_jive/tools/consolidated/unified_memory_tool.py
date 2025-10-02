"""Unified Memory Management Tool - Manages Architecture and Troubleshoot Memory.

This tool extends the consolidated tool architecture to support memory operations
for both Architecture Memory and Troubleshoot Memory systems.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    from mcp.types import Tool
except ImportError:
    # Mock Tool type if MCP not available
    Tool = Dict[str, Any]

from ..base import BaseTool, ToolResult
from ...storage.memory_storage import ArchitectureMemoryStorage, TroubleshootMemoryStorage
from ...models.memory import ArchitectureItem, TroubleshootItem
from ...services.architecture_retrieval import SmartArchitectureRetrieval, RetrievalContext
from ...services.troubleshoot_matching import ProblemSolutionMatcher, MatchingContext
from ...services.memory_markdown import (
    ArchitectureMarkdownExporter,
    ArchitectureMarkdownImporter,
    TroubleshootMarkdownExporter,
    TroubleshootMarkdownImporter,
    FRONTMATTER_AVAILABLE
)

logger = logging.getLogger(__name__)


class UnifiedMemoryTool(BaseTool):
    """Unified tool for Architecture and Troubleshoot Memory operations."""

    def __init__(self, storage=None, arch_storage: ArchitectureMemoryStorage = None,
                 troubleshoot_storage: TroubleshootMemoryStorage = None):
        """Initialize the unified memory tool.

        Args:
            storage: LanceDB manager instance (will be used to create memory storage if needed)
            arch_storage: Architecture Memory storage instance (optional, created from storage if not provided)
            troubleshoot_storage: Troubleshoot Memory storage instance (optional, created from storage if not provided)
        """
        super().__init__()
        self.tool_name = "jive_memory"

        # Initialize storage instances
        if arch_storage is None and storage is not None:
            self.arch_storage = ArchitectureMemoryStorage(storage)
        else:
            self.arch_storage = arch_storage

        if troubleshoot_storage is None and storage is not None:
            self.troubleshoot_storage = TroubleshootMemoryStorage(storage)
        else:
            self.troubleshoot_storage = troubleshoot_storage

        # Initialize smart retrieval services
        if self.arch_storage:
            self.arch_retrieval = SmartArchitectureRetrieval(self.arch_storage)
        else:
            self.arch_retrieval = None

        if self.troubleshoot_storage:
            self.troubleshoot_matcher = ProblemSolutionMatcher(self.troubleshoot_storage)
        else:
            self.troubleshoot_matcher = None

    @property
    def name(self) -> str:
        """Tool name identifier."""
        return self.tool_name

    @property
    def description(self) -> str:
        """Tool description for AI agents."""
        return ("Jive: Unified memory management - create, update, delete, and retrieve "
                "Architecture Memory and Troubleshoot Memory items")

    @property
    def category(self):
        """Tool category."""
        from ..base import ToolCategory
        return ToolCategory.KNOWLEDGE_MANAGEMENT

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Parameters schema for the tool."""
        return {
            "action": {
                "type": "string",
                "enum": ["create", "update", "delete", "get", "list", "search", "get_context", "match_problem", "export", "import", "export_batch", "import_batch"],
                "description": "Action to perform on the memory item"
            },
            "memory_type": {
                "type": "string",
                "enum": ["architecture", "troubleshoot"],
                "description": "Type of memory: 'architecture' or 'troubleshoot'"
            },
            "slug": {
                "type": "string",
                "description": "Unique slug identifier (required for get, update, delete)"
            },
            "item_id": {
                "type": "string",
                "description": "Item ID (alternative to slug)"
            },

            # Architecture Memory specific fields
            "title": {
                "type": "string",
                "description": "Title of the memory item"
            },
            "ai_when_to_use": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 10,
                "description": "When to apply this architecture (Architecture Memory only)"
            },
            "ai_requirements": {
                "type": "string",
                "maxLength": 10000,
                "description": "Detailed architecture specifications in Markdown (Architecture Memory only)"
            },
            "children_slugs": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 50,
                "description": "Child architecture item slugs (Architecture Memory only)"
            },
            "related_slugs": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 20,
                "description": "Related architecture item slugs (Architecture Memory only)"
            },
            "linked_epic_ids": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 20,
                "description": "Epic work item IDs that reference this (Architecture Memory only)"
            },

            # Troubleshoot Memory specific fields
            "ai_use_case": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 10,
                "description": "Problem descriptions for when to use (Troubleshoot Memory only)"
            },
            "ai_solutions": {
                "type": "string",
                "maxLength": 10000,
                "description": "Solutions with tips and steps in Markdown (Troubleshoot Memory only)"
            },

            # Common fields
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 20,
                "description": "Keywords describing this item"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for categorization"
            },

            # Search/List parameters
            "query": {
                "type": "string",
                "description": "Search query for semantic search"
            },
            "limit": {
                "type": "integer",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
                "description": "Maximum number of results"
            },
            "filters": {
                "type": "object",
                "description": "Additional filters for list/search operations"
            },

            # Export/Import parameters
            "file_path": {
                "type": "string",
                "description": "File path for export/import operations"
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory for batch export operations"
            },
            "import_mode": {
                "type": "string",
                "enum": ["create_only", "update_only", "create_or_update", "replace"],
                "default": "create_or_update",
                "description": "Import mode: create_only, update_only, create_or_update, or replace"
            }
        }

    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for MCP registration."""
        return {
            "name": self.tool_name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters_schema,
                "required": ["action", "memory_type"]
            }
        }

    async def handle_tool_call(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unified memory management calls."""
        if name != "jive_memory":
            return {
                "success": False,
                "error": f"Tool '{name}' not handled by UnifiedMemoryTool"
            }

        # Execute the tool and convert ToolResult to dict
        result = await self.execute(**params)

        # Convert ToolResult to dictionary format
        response = {
            "success": result.success,
            "data": result.data if result.success else None
        }

        if not result.success:
            response["error"] = result.error

        if result.metadata:
            response["metadata"] = result.metadata

        return response

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        try:
            action = kwargs.pop("action", None)
            memory_type = kwargs.pop("memory_type", None)

            if not memory_type:
                return ToolResult(
                    success=False,
                    error="memory_type is required (architecture or troubleshoot)"
                )

            # Route to appropriate handler
            if memory_type == "architecture":
                return await self._handle_architecture(action, **kwargs)
            elif memory_type == "troubleshoot":
                return await self._handle_troubleshoot(action, **kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Invalid memory_type: {memory_type}"
                )

        except Exception as e:
            logger.error(f"Error executing memory tool: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to execute memory operation: {str(e)}"
            )

    async def _handle_architecture(self, action: str, **kwargs) -> ToolResult:
        """Handle Architecture Memory operations."""
        try:
            if action == "create":
                return await self._create_architecture(**kwargs)
            elif action == "update":
                return await self._update_architecture(**kwargs)
            elif action == "delete":
                return await self._delete_architecture(**kwargs)
            elif action == "get":
                return await self._get_architecture(**kwargs)
            elif action == "list":
                return await self._list_architecture(**kwargs)
            elif action == "search":
                return await self._search_architecture(**kwargs)
            elif action == "get_context":
                return await self._get_architecture_context(**kwargs)
            elif action == "export":
                return await self._export_architecture(**kwargs)
            elif action == "import":
                return await self._import_architecture(**kwargs)
            elif action == "export_batch":
                return await self._export_architecture_batch(**kwargs)
            elif action == "import_batch":
                return await self._import_architecture_batch(**kwargs)
            else:
                return ToolResult(success=False, error=f"Invalid action: {action}")

        except Exception as e:
            logger.error(f"Error in architecture operation: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))

    async def _handle_troubleshoot(self, action: str, **kwargs) -> ToolResult:
        """Handle Troubleshoot Memory operations."""
        try:
            if action == "create":
                return await self._create_troubleshoot(**kwargs)
            elif action == "update":
                return await self._update_troubleshoot(**kwargs)
            elif action == "delete":
                return await self._delete_troubleshoot(**kwargs)
            elif action == "get":
                return await self._get_troubleshoot(**kwargs)
            elif action == "list":
                return await self._list_troubleshoot(**kwargs)
            elif action == "search":
                return await self._search_troubleshoot(**kwargs)
            elif action == "match_problem":
                return await self._match_problem(**kwargs)
            elif action == "export":
                return await self._export_troubleshoot(**kwargs)
            elif action == "import":
                return await self._import_troubleshoot(**kwargs)
            elif action == "export_batch":
                return await self._export_troubleshoot_batch(**kwargs)
            elif action == "import_batch":
                return await self._import_troubleshoot_batch(**kwargs)
            else:
                return ToolResult(success=False, error=f"Invalid action: {action}")

        except Exception as e:
            logger.error(f"Error in troubleshoot operation: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))

    # Architecture Memory Operations

    async def _create_architecture(self, **kwargs) -> ToolResult:
        """Create new architecture item."""
        slug = kwargs.get("slug")
        title = kwargs.get("title")
        ai_requirements = kwargs.get("ai_requirements")

        if not slug or not title or not ai_requirements:
            return ToolResult(
                success=False,
                error="slug, title, and ai_requirements are required for creating architecture items"
            )

        item = ArchitectureItem(
            unique_slug=slug,
            title=title,
            ai_requirements=ai_requirements,
            ai_when_to_use=kwargs.get("ai_when_to_use", []),
            keywords=kwargs.get("keywords", []),
            children_slugs=kwargs.get("children_slugs", []),
            related_slugs=kwargs.get("related_slugs", []),
            linked_epic_ids=kwargs.get("linked_epic_ids", []),
            tags=kwargs.get("tags", [])
        )

        created = await self.arch_storage.create(item)

        return ToolResult(
            success=True,
            data={
                "id": created.id,
                "slug": created.unique_slug,
                "title": created.title,
                "created_on": created.created_on.isoformat()
            },
            message=f"Architecture item '{created.unique_slug}' created successfully"
        )

    async def _update_architecture(self, **kwargs) -> ToolResult:
        """Update existing architecture item."""
        slug = kwargs.get("slug")
        item_id = kwargs.get("item_id")

        if not slug and not item_id:
            return ToolResult(
                success=False,
                error="Either slug or item_id is required for update"
            )

        # Get existing item
        if slug:
            item = await self.arch_storage.get_by_slug(slug)
        else:
            item = await self.arch_storage.get_by_id(item_id)

        if not item:
            return ToolResult(
                success=False,
                error=f"Architecture item not found"
            )

        # Update fields
        if "title" in kwargs:
            item.title = kwargs["title"]
        if "ai_requirements" in kwargs:
            item.ai_requirements = kwargs["ai_requirements"]
        if "ai_when_to_use" in kwargs:
            item.ai_when_to_use = kwargs["ai_when_to_use"]
        if "keywords" in kwargs:
            item.keywords = kwargs["keywords"]
        if "children_slugs" in kwargs:
            item.children_slugs = kwargs["children_slugs"]
        if "related_slugs" in kwargs:
            item.related_slugs = kwargs["related_slugs"]
        if "linked_epic_ids" in kwargs:
            item.linked_epic_ids = kwargs["linked_epic_ids"]
        if "tags" in kwargs:
            item.tags = kwargs["tags"]

        updated = await self.arch_storage.update(item)

        return ToolResult(
            success=True,
            data={
                "id": updated.id,
                "slug": updated.unique_slug,
                "title": updated.title,
                "last_updated_on": updated.last_updated_on.isoformat()
            },
            message=f"Architecture item '{updated.unique_slug}' updated successfully"
        )

    async def _delete_architecture(self, **kwargs) -> ToolResult:
        """Delete architecture item."""
        slug = kwargs.get("slug")
        item_id = kwargs.get("item_id")

        if not slug and not item_id:
            return ToolResult(
                success=False,
                error="Either slug or item_id is required for delete"
            )

        # Get existing item first
        if slug:
            item = await self.arch_storage.get_by_slug(slug)
            if item:
                item_id = item.id

        if not item_id:
            return ToolResult(
                success=False,
                error=f"Architecture item not found"
            )

        deleted = await self.arch_storage.delete(item_id)

        if deleted:
            return ToolResult(
                success=True,
                message=f"Architecture item deleted successfully"
            )
        else:
            return ToolResult(
                success=False,
                error="Failed to delete architecture item"
            )

    async def _get_architecture(self, **kwargs) -> ToolResult:
        """Get single architecture item."""
        slug = kwargs.get("slug")
        item_id = kwargs.get("item_id")

        if not slug and not item_id:
            return ToolResult(
                success=False,
                error="Either slug or item_id is required"
            )

        if slug:
            item = await self.arch_storage.get_by_slug(slug)
        else:
            item = await self.arch_storage.get_by_id(item_id)

        if not item:
            return ToolResult(
                success=False,
                error="Architecture item not found"
            )

        # Get children and related items for comprehensive view
        children = await self.arch_storage.get_children(item.unique_slug)
        related = await self.arch_storage.get_related(item.unique_slug)

        return ToolResult(
            success=True,
            data={
                "id": item.id,
                "slug": item.unique_slug,
                "title": item.title,
                "ai_when_to_use": item.ai_when_to_use,
                "ai_requirements": item.ai_requirements,
                "keywords": item.keywords,
                "children_slugs": item.children_slugs,
                "children_count": len(children),
                "related_slugs": item.related_slugs,
                "related_count": len(related),
                "linked_epic_ids": item.linked_epic_ids,
                "tags": item.tags,
                "created_on": item.created_on.isoformat(),
                "last_updated_on": item.last_updated_on.isoformat()
            }
        )

    async def _list_architecture(self, **kwargs) -> ToolResult:
        """List architecture items."""
        limit = kwargs.get("limit", 100)
        filters = kwargs.get("filters")

        items = await self.arch_storage.list_all(filters=filters, limit=limit)

        return ToolResult(
            success=True,
            data={
                "items": [
                    {
                        "id": item.id,
                        "slug": item.unique_slug,
                        "title": item.title,
                        "keywords": item.keywords,
                        "children_count": len(item.children_slugs),
                        "related_count": len(item.related_slugs),
                        "tags": item.tags,
                        "last_updated_on": item.last_updated_on.isoformat()
                    }
                    for item in items
                ],
                "total": len(items)
            }
        )

    async def _search_architecture(self, **kwargs) -> ToolResult:
        """Search architecture items."""
        query = kwargs.get("query")
        limit = kwargs.get("limit", 10)
        filters = kwargs.get("filters")

        if not query:
            return ToolResult(
                success=False,
                error="query is required for search"
            )

        results = await self.arch_storage.search(query, limit=limit, filters=filters)

        return ToolResult(
            success=True,
            data={
                "items": [
                    {
                        "id": item.id,
                        "slug": item.unique_slug,
                        "title": item.title,
                        "keywords": item.keywords,
                        "relevance_score": score,
                        "when_to_use": item.ai_when_to_use[:2],  # First 2 use cases
                        "requirements_preview": item.ai_requirements[:200] + "..." if len(item.ai_requirements) > 200 else item.ai_requirements
                    }
                    for item, score in results
                ],
                "total": len(results),
                "query": query
            }
        )

    # Troubleshoot Memory Operations

    async def _create_troubleshoot(self, **kwargs) -> ToolResult:
        """Create new troubleshoot item."""
        slug = kwargs.get("slug")
        title = kwargs.get("title")
        ai_solutions = kwargs.get("ai_solutions")

        if not slug or not title or not ai_solutions:
            return ToolResult(
                success=False,
                error="slug, title, and ai_solutions are required for creating troubleshoot items"
            )

        item = TroubleshootItem(
            unique_slug=slug,
            title=title,
            ai_solutions=ai_solutions,
            ai_use_case=kwargs.get("ai_use_case", []),
            keywords=kwargs.get("keywords", []),
            tags=kwargs.get("tags", [])
        )

        created = await self.troubleshoot_storage.create(item)

        return ToolResult(
            success=True,
            data={
                "id": created.id,
                "slug": created.unique_slug,
                "title": created.title,
                "created_on": created.created_on.isoformat()
            },
            message=f"Troubleshoot item '{created.unique_slug}' created successfully"
        )

    async def _update_troubleshoot(self, **kwargs) -> ToolResult:
        """Update existing troubleshoot item."""
        slug = kwargs.get("slug")
        item_id = kwargs.get("item_id")

        if not slug and not item_id:
            return ToolResult(
                success=False,
                error="Either slug or item_id is required for update"
            )

        # Get existing item
        if slug:
            item = await self.troubleshoot_storage.get_by_slug(slug)
        else:
            item = await self.troubleshoot_storage.get_by_id(item_id)

        if not item:
            return ToolResult(
                success=False,
                error=f"Troubleshoot item not found"
            )

        # Update fields
        if "title" in kwargs:
            item.title = kwargs["title"]
        if "ai_solutions" in kwargs:
            item.ai_solutions = kwargs["ai_solutions"]
        if "ai_use_case" in kwargs:
            item.ai_use_case = kwargs["ai_use_case"]
        if "keywords" in kwargs:
            item.keywords = kwargs["keywords"]
        if "tags" in kwargs:
            item.tags = kwargs["tags"]

        updated = await self.troubleshoot_storage.update(item)

        return ToolResult(
            success=True,
            data={
                "id": updated.id,
                "slug": updated.unique_slug,
                "title": updated.title,
                "last_updated_on": updated.last_updated_on.isoformat()
            },
            message=f"Troubleshoot item '{updated.unique_slug}' updated successfully"
        )

    async def _delete_troubleshoot(self, **kwargs) -> ToolResult:
        """Delete troubleshoot item."""
        slug = kwargs.get("slug")
        item_id = kwargs.get("item_id")

        if not slug and not item_id:
            return ToolResult(
                success=False,
                error="Either slug or item_id is required for delete"
            )

        # Get existing item first
        if slug:
            item = await self.troubleshoot_storage.get_by_slug(slug)
            if item:
                item_id = item.id

        if not item_id:
            return ToolResult(
                success=False,
                error=f"Troubleshoot item not found"
            )

        deleted = await self.troubleshoot_storage.delete(item_id)

        if deleted:
            return ToolResult(
                success=True,
                message=f"Troubleshoot item deleted successfully"
            )
        else:
            return ToolResult(
                success=False,
                error="Failed to delete troubleshoot item"
            )

    async def _get_troubleshoot(self, **kwargs) -> ToolResult:
        """Get single troubleshoot item."""
        slug = kwargs.get("slug")
        item_id = kwargs.get("item_id")

        if not slug and not item_id:
            return ToolResult(
                success=False,
                error="Either slug or item_id is required"
            )

        if slug:
            item = await self.troubleshoot_storage.get_by_slug(slug)
        else:
            item = await self.troubleshoot_storage.get_by_id(item_id)

        if not item:
            return ToolResult(
                success=False,
                error="Troubleshoot item not found"
            )

        return ToolResult(
            success=True,
            data={
                "id": item.id,
                "slug": item.unique_slug,
                "title": item.title,
                "ai_use_case": item.ai_use_case,
                "ai_solutions": item.ai_solutions,
                "keywords": item.keywords,
                "tags": item.tags,
                "usage_count": item.usage_count,
                "success_count": item.success_count,
                "created_on": item.created_on.isoformat(),
                "last_updated_on": item.last_updated_on.isoformat()
            }
        )

    async def _list_troubleshoot(self, **kwargs) -> ToolResult:
        """List troubleshoot items."""
        limit = kwargs.get("limit", 100)
        filters = kwargs.get("filters")

        items = await self.troubleshoot_storage.list_all(filters=filters, limit=limit)

        return ToolResult(
            success=True,
            data={
                "items": [
                    {
                        "id": item.id,
                        "slug": item.unique_slug,
                        "title": item.title,
                        "keywords": item.keywords,
                        "use_cases": item.ai_use_case,
                        "usage_count": item.usage_count,
                        "success_count": item.success_count,
                        "tags": item.tags,
                        "last_updated_on": item.last_updated_on.isoformat()
                    }
                    for item in items
                ],
                "total": len(items)
            }
        )

    async def _search_troubleshoot(self, **kwargs) -> ToolResult:
        """Search troubleshoot items."""
        query = kwargs.get("query")
        limit = kwargs.get("limit", 10)
        filters = kwargs.get("filters")

        if not query:
            return ToolResult(
                success=False,
                error="query is required for search"
            )

        results = await self.troubleshoot_storage.search(query, limit=limit, filters=filters)

        # Increment usage count for retrieved items
        for item, score in results:
            await self.troubleshoot_storage.increment_usage(item.id)

        return ToolResult(
            success=True,
            data={
                "items": [
                    {
                        "id": item.id,
                        "slug": item.unique_slug,
                        "title": item.title,
                        "keywords": item.keywords,
                        "relevance_score": score,
                        "use_cases": item.ai_use_case[:2],  # First 2 use cases
                        "solution_preview": item.ai_solutions[:200] + "..." if len(item.ai_solutions) > 200 else item.ai_solutions,
                        "usage_count": item.usage_count,
                        "success_rate": item.success_count / max(item.usage_count, 1)
                    }
                    for item, score in results
                ],
                "total": len(results),
                "query": query
            }
        )

    # Smart Retrieval Operations

    async def _get_architecture_context(self, **kwargs) -> ToolResult:
        """Get comprehensive context for an architecture item using smart retrieval.

        This provides context-aware, token-limited comprehensive context
        including children and related items.
        """
        slug = kwargs.get("slug")
        if not slug:
            return ToolResult(
                success=False,
                error="slug is required for get_context"
            )

        if not self.arch_retrieval:
            return ToolResult(
                success=False,
                error="Smart retrieval not initialized"
            )

        # Build retrieval context from parameters
        max_tokens = kwargs.get("max_tokens", 4000)
        include_children = kwargs.get("include_children", True)
        include_related = kwargs.get("include_related", True)

        context = RetrievalContext(
            max_tokens=max_tokens,
            include_children=include_children,
            include_related=include_related
        )

        # Get comprehensive context
        result = await self.arch_retrieval.get_comprehensive_context(slug, context)

        if not result.get("success"):
            return ToolResult(
                success=False,
                error=result.get("error", "Failed to retrieve context")
            )

        # Also get the markdown summary
        summary = await self.arch_retrieval.get_smart_summary(slug, context)

        return ToolResult(
            success=True,
            data={
                **result,
                "markdown_summary": summary
            },
            message=f"Retrieved comprehensive context for '{slug}'"
        )

    async def _match_problem(self, **kwargs) -> ToolResult:
        """Match a problem description to troubleshooting solutions.

        Uses semantic search and success rate analysis to find the
        most relevant solutions.
        """
        problem = kwargs.get("query") or kwargs.get("problem")
        if not problem:
            return ToolResult(
                success=False,
                error="query or problem is required for match_problem"
            )

        if not self.troubleshoot_matcher:
            return ToolResult(
                success=False,
                error="Problem matcher not initialized"
            )

        # Build matching context
        max_results = kwargs.get("limit", 5)
        min_relevance = kwargs.get("min_relevance", 0.3)

        context = MatchingContext(
            max_results=max_results,
            min_relevance_score=min_relevance,
            boost_by_success_rate=True
        )

        # Match problem to solutions
        matches = await self.troubleshoot_matcher.match_problem(problem, context)

        return ToolResult(
            success=True,
            data={
                "problem": problem,
                "matches": [
                    {
                        "slug": match.slug,
                        "title": match.title,
                        "relevance_score": match.relevance_score,
                        "matched_use_cases": match.matched_use_cases,
                        "solution_preview": match.solution_preview
                    }
                    for match in matches
                ],
                "total_matches": len(matches)
            },
            message=f"Found {len(matches)} matching solutions"
        )

    # Export/Import Operations

    async def _export_architecture(self, **kwargs) -> ToolResult:
        """Export single architecture item to markdown."""
        if not FRONTMATTER_AVAILABLE:
            return ToolResult(
                success=False,
                error="python-frontmatter package not available. Install with: pip install python-frontmatter"
            )

        slug = kwargs.get("slug")
        item_id = kwargs.get("item_id")
        file_path = kwargs.get("file_path")

        if not slug and not item_id:
            return ToolResult(
                success=False,
                error="Either slug or item_id is required for export"
            )

        # Get the item
        if slug:
            item = await self.arch_storage.get_by_slug(slug)
        else:
            item = await self.arch_storage.get_by_id(item_id)

        if not item:
            return ToolResult(
                success=False,
                error="Architecture item not found"
            )

        # Determine output path
        if file_path:
            output_path = Path(file_path)
        else:
            output_path = Path(f"./exports/architecture_{item.unique_slug}.md")

        # Export to markdown
        result = ArchitectureMarkdownExporter.export_item(item, output_path)

        if result.success:
            return ToolResult(
                success=True,
                data={
                    "file_path": str(result.file_path),
                    "slug": item.unique_slug,
                    "title": item.title
                },
                message=result.message
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or "Export failed"
            )

    async def _import_architecture(self, **kwargs) -> ToolResult:
        """Import single architecture item from markdown."""
        if not FRONTMATTER_AVAILABLE:
            return ToolResult(
                success=False,
                error="python-frontmatter package not available. Install with: pip install python-frontmatter"
            )

        file_path = kwargs.get("file_path")
        import_mode = kwargs.get("import_mode", "create_or_update")

        if not file_path:
            return ToolResult(
                success=False,
                error="file_path is required for import"
            )

        # Parse the markdown file
        result = ArchitectureMarkdownImporter.parse_item(Path(file_path))

        if not result.success:
            return ToolResult(
                success=False,
                error=result.error or "Import failed",
                data={"warnings": result.warnings} if result.warnings else None
            )

        item = result.item

        # Check if item exists
        existing = await self.arch_storage.get_by_slug(item.unique_slug)

        # Handle different import modes
        if import_mode == "create_only":
            if existing:
                return ToolResult(
                    success=False,
                    error=f"Item '{item.unique_slug}' already exists (create_only mode)"
                )
            created = await self.arch_storage.create(item)
            return ToolResult(
                success=True,
                data={
                    "id": created.id,
                    "slug": created.unique_slug,
                    "title": created.title,
                    "action": "created"
                },
                message=f"Architecture item '{created.unique_slug}' imported successfully"
            )

        elif import_mode == "update_only":
            if not existing:
                return ToolResult(
                    success=False,
                    error=f"Item '{item.unique_slug}' not found (update_only mode)"
                )
            # Update existing item with imported data
            existing.title = item.title
            existing.ai_requirements = item.ai_requirements
            existing.ai_when_to_use = item.ai_when_to_use
            existing.keywords = item.keywords
            existing.children_slugs = item.children_slugs
            existing.related_slugs = item.related_slugs
            existing.linked_epic_ids = item.linked_epic_ids
            existing.tags = item.tags
            updated = await self.arch_storage.update(existing)
            return ToolResult(
                success=True,
                data={
                    "id": updated.id,
                    "slug": updated.unique_slug,
                    "title": updated.title,
                    "action": "updated"
                },
                message=f"Architecture item '{updated.unique_slug}' updated successfully"
            )

        elif import_mode == "replace":
            if existing:
                await self.arch_storage.delete(existing.id)
            created = await self.arch_storage.create(item)
            return ToolResult(
                success=True,
                data={
                    "id": created.id,
                    "slug": created.unique_slug,
                    "title": created.title,
                    "action": "replaced"
                },
                message=f"Architecture item '{created.unique_slug}' replaced successfully"
            )

        else:  # create_or_update (default)
            if existing:
                existing.title = item.title
                existing.ai_requirements = item.ai_requirements
                existing.ai_when_to_use = item.ai_when_to_use
                existing.keywords = item.keywords
                existing.children_slugs = item.children_slugs
                existing.related_slugs = item.related_slugs
                existing.linked_epic_ids = item.linked_epic_ids
                existing.tags = item.tags
                updated = await self.arch_storage.update(existing)
                return ToolResult(
                    success=True,
                    data={
                        "id": updated.id,
                        "slug": updated.unique_slug,
                        "title": updated.title,
                        "action": "updated"
                    },
                    message=f"Architecture item '{updated.unique_slug}' updated successfully"
                )
            else:
                created = await self.arch_storage.create(item)
                return ToolResult(
                    success=True,
                    data={
                        "id": created.id,
                        "slug": created.unique_slug,
                        "title": created.title,
                        "action": "created"
                    },
                    message=f"Architecture item '{created.unique_slug}' imported successfully"
                )

    async def _export_architecture_batch(self, **kwargs) -> ToolResult:
        """Export multiple architecture items to markdown files."""
        if not FRONTMATTER_AVAILABLE:
            return ToolResult(
                success=False,
                error="python-frontmatter package not available. Install with: pip install python-frontmatter"
            )

        output_dir = kwargs.get("output_dir")
        filters = kwargs.get("filters")
        limit = kwargs.get("limit", 100)

        if not output_dir:
            output_dir = "./exports/architecture"

        output_path = Path(output_dir)

        # Get items to export
        items = await self.arch_storage.list_all(filters=filters, limit=limit)

        if not items:
            return ToolResult(
                success=True,
                data={"exported_count": 0, "output_dir": str(output_path)},
                message="No items to export"
            )

        # Export batch (returns list of results)
        results = ArchitectureMarkdownExporter.export_batch(items, output_path)

        # Check results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if failed:
            return ToolResult(
                success=False if len(successful) == 0 else True,
                data={
                    "exported_count": len(successful),
                    "failed_count": len(failed),
                    "output_dir": str(output_path),
                    "items": [item.unique_slug for item in items if any(r.success and item.unique_slug in str(r.file_path) for r in results)],
                    "errors": [r.error for r in failed]
                },
                message=f"Batch export completed: {len(successful)} successful, {len(failed)} failed"
            )
        else:
            return ToolResult(
                success=True,
                data={
                    "exported_count": len(successful),
                    "output_dir": str(output_path),
                    "items": [item.unique_slug for item in items]
                },
                message=f"Successfully exported {len(successful)} items"
            )

    async def _import_architecture_batch(self, **kwargs) -> ToolResult:
        """Import multiple architecture items from markdown files in a directory."""
        if not FRONTMATTER_AVAILABLE:
            return ToolResult(
                success=False,
                error="python-frontmatter package not available. Install with: pip install python-frontmatter"
            )

        input_dir = kwargs.get("file_path") or kwargs.get("output_dir")
        import_mode = kwargs.get("import_mode", "create_or_update")

        if not input_dir:
            return ToolResult(
                success=False,
                error="file_path or output_dir is required for batch import"
            )

        input_path = Path(input_dir)

        if not input_path.exists() or not input_path.is_dir():
            return ToolResult(
                success=False,
                error=f"Directory not found: {input_path}"
            )

        # Find all markdown files
        markdown_files = list(input_path.glob("*.md"))

        if not markdown_files:
            return ToolResult(
                success=True,
                data={"imported_count": 0, "failed_count": 0},
                message="No markdown files found in directory"
            )

        # Import each file
        imported = []
        failed = []
        warnings_list = []

        for md_file in markdown_files:
            try:
                # Parse file
                parse_result = ArchitectureMarkdownImporter.parse_item(md_file)

                if not parse_result.success:
                    failed.append({
                        "file": str(md_file),
                        "error": parse_result.error
                    })
                    continue

                if parse_result.warnings:
                    warnings_list.extend([f"{md_file.name}: {w}" for w in parse_result.warnings])

                item = parse_result.item

                # Check if exists
                existing = await self.arch_storage.get_by_slug(item.unique_slug)

                # Handle import mode
                if import_mode == "create_only" and existing:
                    failed.append({
                        "file": str(md_file),
                        "error": f"Item already exists: {item.unique_slug}"
                    })
                    continue
                elif import_mode == "update_only" and not existing:
                    failed.append({
                        "file": str(md_file),
                        "error": f"Item not found: {item.unique_slug}"
                    })
                    continue

                # Create or update
                if existing and import_mode != "replace":
                    existing.title = item.title
                    existing.ai_requirements = item.ai_requirements
                    existing.ai_when_to_use = item.ai_when_to_use
                    existing.keywords = item.keywords
                    existing.children_slugs = item.children_slugs
                    existing.related_slugs = item.related_slugs
                    existing.linked_epic_ids = item.linked_epic_ids
                    existing.tags = item.tags
                    await self.arch_storage.update(existing)
                    imported.append({"slug": item.unique_slug, "action": "updated"})
                else:
                    if existing:
                        await self.arch_storage.delete(existing.id)
                    await self.arch_storage.create(item)
                    imported.append({"slug": item.unique_slug, "action": "created"})

            except Exception as e:
                logger.error(f"Error importing {md_file}: {e}")
                failed.append({
                    "file": str(md_file),
                    "error": str(e)
                })

        return ToolResult(
            success=True,
            data={
                "imported_count": len(imported),
                "failed_count": len(failed),
                "imported_items": imported,
                "failed_items": failed,
                "warnings": warnings_list if warnings_list else None
            },
            message=f"Batch import completed: {len(imported)} imported, {len(failed)} failed"
        )

    async def _export_troubleshoot(self, **kwargs) -> ToolResult:
        """Export single troubleshoot item to markdown."""
        if not FRONTMATTER_AVAILABLE:
            return ToolResult(
                success=False,
                error="python-frontmatter package not available. Install with: pip install python-frontmatter"
            )

        slug = kwargs.get("slug")
        item_id = kwargs.get("item_id")
        file_path = kwargs.get("file_path")

        if not slug and not item_id:
            return ToolResult(
                success=False,
                error="Either slug or item_id is required for export"
            )

        # Get the item
        if slug:
            item = await self.troubleshoot_storage.get_by_slug(slug)
        else:
            item = await self.troubleshoot_storage.get_by_id(item_id)

        if not item:
            return ToolResult(
                success=False,
                error="Troubleshoot item not found"
            )

        # Determine output path
        if file_path:
            output_path = Path(file_path)
        else:
            output_path = Path(f"./exports/troubleshoot_{item.unique_slug}.md")

        # Export to markdown
        result = TroubleshootMarkdownExporter.export_item(item, output_path)

        if result.success:
            return ToolResult(
                success=True,
                data={
                    "file_path": str(result.file_path),
                    "slug": item.unique_slug,
                    "title": item.title
                },
                message=result.message
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or "Export failed"
            )

    async def _import_troubleshoot(self, **kwargs) -> ToolResult:
        """Import single troubleshoot item from markdown."""
        if not FRONTMATTER_AVAILABLE:
            return ToolResult(
                success=False,
                error="python-frontmatter package not available. Install with: pip install python-frontmatter"
            )

        file_path = kwargs.get("file_path")
        import_mode = kwargs.get("import_mode", "create_or_update")

        if not file_path:
            return ToolResult(
                success=False,
                error="file_path is required for import"
            )

        # Parse the markdown file
        result = TroubleshootMarkdownImporter.parse_item(Path(file_path))

        if not result.success:
            return ToolResult(
                success=False,
                error=result.error or "Import failed",
                data={"warnings": result.warnings} if result.warnings else None
            )

        item = result.item

        # Check if item exists
        existing = await self.troubleshoot_storage.get_by_slug(item.unique_slug)

        # Handle different import modes
        if import_mode == "create_only":
            if existing:
                return ToolResult(
                    success=False,
                    error=f"Item '{item.unique_slug}' already exists (create_only mode)"
                )
            created = await self.troubleshoot_storage.create(item)
            return ToolResult(
                success=True,
                data={
                    "id": created.id,
                    "slug": created.unique_slug,
                    "title": created.title,
                    "action": "created"
                },
                message=f"Troubleshoot item '{created.unique_slug}' imported successfully"
            )

        elif import_mode == "update_only":
            if not existing:
                return ToolResult(
                    success=False,
                    error=f"Item '{item.unique_slug}' not found (update_only mode)"
                )
            existing.title = item.title
            existing.ai_solutions = item.ai_solutions
            existing.ai_use_case = item.ai_use_case
            existing.keywords = item.keywords
            existing.tags = item.tags
            # Preserve usage statistics on update
            updated = await self.troubleshoot_storage.update(existing)
            return ToolResult(
                success=True,
                data={
                    "id": updated.id,
                    "slug": updated.unique_slug,
                    "title": updated.title,
                    "action": "updated"
                },
                message=f"Troubleshoot item '{updated.unique_slug}' updated successfully"
            )

        elif import_mode == "replace":
            if existing:
                await self.troubleshoot_storage.delete(existing.id)
            created = await self.troubleshoot_storage.create(item)
            return ToolResult(
                success=True,
                data={
                    "id": created.id,
                    "slug": created.unique_slug,
                    "title": created.title,
                    "action": "replaced"
                },
                message=f"Troubleshoot item '{created.unique_slug}' replaced successfully"
            )

        else:  # create_or_update (default)
            if existing:
                existing.title = item.title
                existing.ai_solutions = item.ai_solutions
                existing.ai_use_case = item.ai_use_case
                existing.keywords = item.keywords
                existing.tags = item.tags
                # Preserve usage statistics
                updated = await self.troubleshoot_storage.update(existing)
                return ToolResult(
                    success=True,
                    data={
                        "id": updated.id,
                        "slug": updated.unique_slug,
                        "title": updated.title,
                        "action": "updated"
                    },
                    message=f"Troubleshoot item '{updated.unique_slug}' updated successfully"
                )
            else:
                created = await self.troubleshoot_storage.create(item)
                return ToolResult(
                    success=True,
                    data={
                        "id": created.id,
                        "slug": created.unique_slug,
                        "title": created.title,
                        "action": "created"
                    },
                    message=f"Troubleshoot item '{created.unique_slug}' imported successfully"
                )

    async def _export_troubleshoot_batch(self, **kwargs) -> ToolResult:
        """Export multiple troubleshoot items to markdown files."""
        if not FRONTMATTER_AVAILABLE:
            return ToolResult(
                success=False,
                error="python-frontmatter package not available. Install with: pip install python-frontmatter"
            )

        output_dir = kwargs.get("output_dir")
        filters = kwargs.get("filters")
        limit = kwargs.get("limit", 100)

        if not output_dir:
            output_dir = "./exports/troubleshoot"

        output_path = Path(output_dir)

        # Get items to export
        items = await self.troubleshoot_storage.list_all(filters=filters, limit=limit)

        if not items:
            return ToolResult(
                success=True,
                data={"exported_count": 0, "output_dir": str(output_path)},
                message="No items to export"
            )

        # Export batch (returns list of results)
        results = TroubleshootMarkdownExporter.export_batch(items, output_path)

        # Check results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if failed:
            return ToolResult(
                success=False if len(successful) == 0 else True,
                data={
                    "exported_count": len(successful),
                    "failed_count": len(failed),
                    "output_dir": str(output_path),
                    "items": [item.unique_slug for item in items if any(r.success and item.unique_slug in str(r.file_path) for r in results)],
                    "errors": [r.error for r in failed]
                },
                message=f"Batch export completed: {len(successful)} successful, {len(failed)} failed"
            )
        else:
            return ToolResult(
                success=True,
                data={
                    "exported_count": len(successful),
                    "output_dir": str(output_path),
                    "items": [item.unique_slug for item in items]
                },
                message=f"Successfully exported {len(successful)} items"
            )

    async def _import_troubleshoot_batch(self, **kwargs) -> ToolResult:
        """Import multiple troubleshoot items from markdown files in a directory."""
        if not FRONTMATTER_AVAILABLE:
            return ToolResult(
                success=False,
                error="python-frontmatter package not available. Install with: pip install python-frontmatter"
            )

        input_dir = kwargs.get("file_path") or kwargs.get("output_dir")
        import_mode = kwargs.get("import_mode", "create_or_update")

        if not input_dir:
            return ToolResult(
                success=False,
                error="file_path or output_dir is required for batch import"
            )

        input_path = Path(input_dir)

        if not input_path.exists() or not input_path.is_dir():
            return ToolResult(
                success=False,
                error=f"Directory not found: {input_path}"
            )

        # Find all markdown files
        markdown_files = list(input_path.glob("*.md"))

        if not markdown_files:
            return ToolResult(
                success=True,
                data={"imported_count": 0, "failed_count": 0},
                message="No markdown files found in directory"
            )

        # Import each file
        imported = []
        failed = []
        warnings_list = []

        for md_file in markdown_files:
            try:
                # Parse file
                parse_result = TroubleshootMarkdownImporter.parse_item(md_file)

                if not parse_result.success:
                    failed.append({
                        "file": str(md_file),
                        "error": parse_result.error
                    })
                    continue

                if parse_result.warnings:
                    warnings_list.extend([f"{md_file.name}: {w}" for w in parse_result.warnings])

                item = parse_result.item

                # Check if exists
                existing = await self.troubleshoot_storage.get_by_slug(item.unique_slug)

                # Handle import mode
                if import_mode == "create_only" and existing:
                    failed.append({
                        "file": str(md_file),
                        "error": f"Item already exists: {item.unique_slug}"
                    })
                    continue
                elif import_mode == "update_only" and not existing:
                    failed.append({
                        "file": str(md_file),
                        "error": f"Item not found: {item.unique_slug}"
                    })
                    continue

                # Create or update
                if existing and import_mode != "replace":
                    existing.title = item.title
                    existing.ai_solutions = item.ai_solutions
                    existing.ai_use_case = item.ai_use_case
                    existing.keywords = item.keywords
                    existing.tags = item.tags
                    # Preserve usage statistics
                    await self.troubleshoot_storage.update(existing)
                    imported.append({"slug": item.unique_slug, "action": "updated"})
                else:
                    if existing:
                        await self.troubleshoot_storage.delete(existing.id)
                    await self.troubleshoot_storage.create(item)
                    imported.append({"slug": item.unique_slug, "action": "created"})

            except Exception as e:
                logger.error(f"Error importing {md_file}: {e}")
                failed.append({
                    "file": str(md_file),
                    "error": str(e)
                })

        return ToolResult(
            success=True,
            data={
                "imported_count": len(imported),
                "failed_count": len(failed),
                "imported_items": imported,
                "failed_items": failed,
                "warnings": warnings_list if warnings_list else None
            },
            message=f"Batch import completed: {len(imported)} imported, {len(failed)} failed"
        )