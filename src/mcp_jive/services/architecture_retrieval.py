"""Smart Architecture Retrieval System.

Provides context-aware, intelligent retrieval of architecture items with:
- Token-aware summarization
- Hierarchical relationship traversal
- Relevance-based content prioritization
- Related item resolution
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..models.memory import ArchitectureItem, ArchitectureItemSummary
from ..storage.memory_storage import ArchitectureMemoryStorage

logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    """Context for architecture retrieval operations."""
    max_tokens: int = 4000  # Conservative token limit
    include_children: bool = True
    include_related: bool = True
    max_depth: int = 3
    summarize_children: bool = True
    prioritize_by_relevance: bool = True


class SmartArchitectureRetrieval:
    """Smart retrieval system for architecture items.

    Provides intelligent, context-aware retrieval that respects token limits
    while maximizing the value of information provided to AI agents.
    """

    # Rough estimates for token counting
    CHARS_PER_TOKEN = 4
    SUMMARY_OVERHEAD_TOKENS = 100
    ITEM_METADATA_TOKENS = 50

    def __init__(self, storage: ArchitectureMemoryStorage):
        """Initialize the smart retrieval system.

        Args:
            storage: Architecture memory storage instance
        """
        self.storage = storage

    async def get_comprehensive_context(
        self,
        slug: str,
        context: Optional[RetrievalContext] = None
    ) -> Dict[str, Any]:
        """Get comprehensive context for an architecture item.

        Intelligently retrieves the item, its children, and related items,
        summarizing as needed to fit within token constraints.

        Args:
            slug: Architecture item slug
            context: Retrieval context with constraints

        Returns:
            Comprehensive context dictionary with prioritized information
        """
        context = context or RetrievalContext()

        # Get the primary item
        item = await self.storage.get_by_slug(slug)
        if not item:
            return {
                "error": f"Architecture item '{slug}' not found",
                "success": False
            }

        # Calculate token budget
        tokens_used = self._estimate_tokens(item.ai_requirements)
        tokens_available = context.max_tokens - tokens_used - self.SUMMARY_OVERHEAD_TOKENS

        result = {
            "success": True,
            "primary_item": self._serialize_item(item, full=True),
            "children": [],
            "related": [],
            "token_usage": {
                "primary_item": tokens_used,
                "children": 0,
                "related": 0,
                "total": tokens_used
            },
            "truncation_applied": False
        }

        # Get and process children if requested
        if context.include_children and item.children_slugs and tokens_available > 0:
            children_data = await self._get_children_context(
                item.children_slugs,
                tokens_available // 2,  # Allocate half to children
                context
            )
            result["children"] = children_data["items"]
            result["token_usage"]["children"] = children_data["tokens_used"]
            result["truncation_applied"] = result["truncation_applied"] or children_data["truncated"]
            tokens_available -= children_data["tokens_used"]

        # Get and process related items if requested
        if context.include_related and item.related_slugs and tokens_available > 0:
            related_data = await self._get_related_context(
                item.related_slugs,
                tokens_available,
                context
            )
            result["related"] = related_data["items"]
            result["token_usage"]["related"] = related_data["tokens_used"]
            result["truncation_applied"] = result["truncation_applied"] or related_data["truncated"]

        # Update total token usage
        result["token_usage"]["total"] = (
            result["token_usage"]["primary_item"] +
            result["token_usage"]["children"] +
            result["token_usage"]["related"]
        )

        return result

    async def get_smart_summary(
        self,
        slug: str,
        context: Optional[RetrievalContext] = None
    ) -> str:
        """Get a smart, token-aware summary of an architecture item.

        Args:
            slug: Architecture item slug
            context: Retrieval context

        Returns:
            Markdown-formatted summary optimized for AI consumption
        """
        comprehensive = await self.get_comprehensive_context(slug, context)

        if not comprehensive["success"]:
            return f"Error: {comprehensive.get('error', 'Unknown error')}"

        return self._format_summary(comprehensive)

    async def search_and_summarize(
        self,
        query: str,
        limit: int = 5,
        context: Optional[RetrievalContext] = None
    ) -> List[Dict[str, Any]]:
        """Search architecture items and return smart summaries.

        Args:
            query: Search query
            limit: Maximum number of results
            context: Retrieval context

        Returns:
            List of search results with smart summaries
        """
        context = context or RetrievalContext()

        # Perform semantic search
        results = await self.storage.search(query, limit=limit)

        summaries = []
        for item, score in results:
            summary = {
                "slug": item.unique_slug,
                "title": item.title,
                "relevance_score": score,
                "when_to_use": item.ai_when_to_use,
                "keywords": item.keywords,
                "requirements_preview": self._create_preview(
                    item.ai_requirements,
                    max_tokens=200
                ),
                "children_count": len(item.children_slugs),
                "related_count": len(item.related_slugs)
            }
            summaries.append(summary)

        return summaries

    async def _get_children_context(
        self,
        children_slugs: List[str],
        token_budget: int,
        context: RetrievalContext
    ) -> Dict[str, Any]:
        """Get context for children items within token budget.

        Args:
            children_slugs: List of child slugs
            token_budget: Available tokens
            context: Retrieval context

        Returns:
            Children data with token usage
        """
        children_items = []
        tokens_used = 0
        truncated = False

        for child_slug in children_slugs:
            if tokens_used >= token_budget:
                truncated = True
                break

            child = await self.storage.get_by_slug(child_slug)
            if not child:
                continue

            # Estimate tokens for this child
            if context.summarize_children:
                child_tokens = self._estimate_tokens(
                    self._create_preview(child.ai_requirements, max_tokens=150)
                )
            else:
                child_tokens = self._estimate_tokens(child.ai_requirements)

            if tokens_used + child_tokens > token_budget:
                # Truncate this child's content to fit
                remaining_tokens = token_budget - tokens_used
                if remaining_tokens > 50:  # Only include if meaningful space left
                    children_items.append(
                        self._serialize_item(
                            child,
                            full=False,
                            max_tokens=remaining_tokens
                        )
                    )
                    tokens_used += remaining_tokens
                truncated = True
                break

            children_items.append(
                self._serialize_item(
                    child,
                    full=not context.summarize_children,
                    max_tokens=child_tokens
                )
            )
            tokens_used += child_tokens

        return {
            "items": children_items,
            "tokens_used": tokens_used,
            "truncated": truncated
        }

    async def _get_related_context(
        self,
        related_slugs: List[str],
        token_budget: int,
        context: RetrievalContext
    ) -> Dict[str, Any]:
        """Get context for related items within token budget.

        Args:
            related_slugs: List of related slugs
            token_budget: Available tokens
            context: Retrieval context

        Returns:
            Related items data with token usage
        """
        related_items = []
        tokens_used = 0
        truncated = False

        for related_slug in related_slugs:
            if tokens_used >= token_budget:
                truncated = True
                break

            related = await self.storage.get_by_slug(related_slug)
            if not related:
                continue

            # Always summarize related items to conserve tokens
            related_tokens = self._estimate_tokens(
                self._create_preview(related.ai_requirements, max_tokens=100)
            )

            if tokens_used + related_tokens > token_budget:
                truncated = True
                break

            related_items.append(
                self._serialize_item(
                    related,
                    full=False,
                    max_tokens=100
                )
            )
            tokens_used += related_tokens

        return {
            "items": related_items,
            "tokens_used": tokens_used,
            "truncated": truncated
        }

    def _serialize_item(
        self,
        item: ArchitectureItem,
        full: bool = True,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Serialize an architecture item for output.

        Args:
            item: Architecture item
            full: Include full requirements or preview
            max_tokens: Maximum tokens for requirements

        Returns:
            Serialized item dictionary
        """
        requirements = item.ai_requirements
        if not full or max_tokens:
            requirements = self._create_preview(
                requirements,
                max_tokens=max_tokens or 200
            )

        return {
            "slug": item.unique_slug,
            "title": item.title,
            "when_to_use": item.ai_when_to_use,
            "requirements": requirements,
            "keywords": item.keywords,
            "children_count": len(item.children_slugs),
            "related_count": len(item.related_slugs),
            "full_content": full
        }

    def _format_summary(self, comprehensive: Dict[str, Any]) -> str:
        """Format comprehensive context as markdown summary.

        Args:
            comprehensive: Comprehensive context dictionary

        Returns:
            Markdown-formatted summary
        """
        primary = comprehensive["primary_item"]
        lines = [
            f"# Architecture: {primary['title']}",
            f"**Slug:** `{primary['slug']}`",
            ""
        ]

        # When to use
        if primary["when_to_use"]:
            lines.append("## When to Use")
            for use_case in primary["when_to_use"]:
                lines.append(f"- {use_case}")
            lines.append("")

        # Requirements
        lines.append("## Requirements")
        lines.append(primary["requirements"])
        lines.append("")

        # Children
        if comprehensive["children"]:
            lines.append("## Child Architecture Items")
            for child in comprehensive["children"]:
                lines.append(f"### {child['title']} (`{child['slug']}`)")
                lines.append(child["requirements"])
                lines.append("")

        # Related
        if comprehensive["related"]:
            lines.append("## Related Architecture Items")
            for related in comprehensive["related"]:
                lines.append(f"- **{related['title']}** (`{related['slug']}`): {related['requirements'][:100]}...")
            lines.append("")

        # Token usage footer
        if comprehensive.get("truncation_applied"):
            lines.append("---")
            lines.append("*Note: Content was truncated to fit token constraints.*")

        return "\n".join(lines)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // self.CHARS_PER_TOKEN

    def _create_preview(self, text: str, max_tokens: int) -> str:
        """Create a preview of text within token limit.

        Args:
            text: Full text
            max_tokens: Maximum tokens

        Returns:
            Truncated preview
        """
        max_chars = max_tokens * self.CHARS_PER_TOKEN

        if len(text) <= max_chars:
            return text

        # Truncate at sentence boundary if possible
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')

        # Use the latest sentence or paragraph boundary
        boundary = max(last_period, last_newline)
        if boundary > max_chars * 0.7:  # Only if we're not losing too much
            truncated = text[:boundary + 1]

        return truncated.rstrip() + "\n\n[... content truncated for brevity ...]"


class ArchitectureGuidanceGenerator:
    """Generate AI-friendly guidance from architecture items.

    Specialized in creating actionable, concise guidance for AI agents
    based on architecture items and their relationships.
    """

    def __init__(self, retrieval_system: SmartArchitectureRetrieval):
        """Initialize the guidance generator.

        Args:
            retrieval_system: Smart retrieval system instance
        """
        self.retrieval = retrieval_system

    async def generate_implementation_guidance(
        self,
        slugs: List[str],
        context: Optional[RetrievalContext] = None
    ) -> str:
        """Generate implementation guidance for multiple architecture items.

        Args:
            slugs: List of architecture item slugs
            context: Retrieval context

        Returns:
            Comprehensive implementation guidance
        """
        context = context or RetrievalContext(max_tokens=8000)

        guidance_parts = [
            "# Implementation Guidance",
            "",
            "This guidance combines multiple architecture items to provide comprehensive implementation direction.",
            ""
        ]

        tokens_per_item = context.max_tokens // len(slugs)
        item_context = RetrievalContext(
            max_tokens=tokens_per_item,
            include_children=True,
            include_related=False,  # Skip related to save tokens
            summarize_children=True
        )

        for i, slug in enumerate(slugs, 1):
            summary = await self.retrieval.get_smart_summary(slug, item_context)
            guidance_parts.append(f"## Architecture {i}: {slug}")
            guidance_parts.append(summary)
            guidance_parts.append("")

        return "\n".join(guidance_parts)

    async def generate_when_to_use_guide(
        self,
        query: str,
        limit: int = 3
    ) -> str:
        """Generate a guide showing when to use matching architectures.

        Args:
            query: Search query describing the use case
            limit: Maximum architectures to include

        Returns:
            When-to-use guide
        """
        results = await self.retrieval.search_and_summarize(query, limit=limit)

        if not results:
            return f"No architecture items found matching: {query}"

        guide = [
            "# Architecture Selection Guide",
            f"**Use Case:** {query}",
            "",
            "## Recommended Architectures",
            ""
        ]

        for i, result in enumerate(results, 1):
            guide.append(f"### {i}. {result['title']} (Relevance: {result['relevance_score']:.2f})")
            guide.append("")
            guide.append("**When to use:**")
            for use_case in result["when_to_use"]:
                guide.append(f"- {use_case}")
            guide.append("")
            guide.append("**Overview:**")
            guide.append(result["requirements_preview"])
            guide.append("")
            guide.append(f"**Full details:** Use slug `{result['slug']}`")
            guide.append("")

        return "\n".join(guide)