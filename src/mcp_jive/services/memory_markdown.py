"""Memory System Markdown Export/Import Utilities.

This module provides functionality to export and import Architecture Memory
and Troubleshoot Memory items in markdown format with YAML front matter.

Format specification: docs/MEMORY_MARKDOWN_FORMAT_SPEC.md
"""

import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

try:
    import frontmatter  # python-frontmatter package
    FRONTMATTER_AVAILABLE = True
except ImportError:
    FRONTMATTER_AVAILABLE = False
    logging.warning("python-frontmatter not available, markdown export/import disabled")

from ..models.memory import (
    ArchitectureItem,
    TroubleshootItem,
    MemoryExportMetadata
)

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    message: str
    file_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ImportResult:
    """Result of an import operation."""
    success: bool
    message: str
    item: Optional[Any] = None
    warnings: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ArchitectureMarkdownExporter:
    """Export Architecture Memory items to markdown format."""

    @staticmethod
    def export_item(item: ArchitectureItem, output_path: Optional[Path] = None) -> ExportResult:
        """Export a single architecture item to markdown.

        Args:
            item: Architecture item to export
            output_path: Optional output file path (auto-generated if not provided)

        Returns:
            ExportResult with success status and file path
        """
        if not FRONTMATTER_AVAILABLE:
            return ExportResult(
                success=False,
                message="python-frontmatter package not installed",
                error="Missing dependency"
            )

        try:
            # Generate filename if not provided
            if output_path is None:
                output_path = Path(f"architecture_{item.unique_slug}.md")

            # Build front matter
            metadata = {
                'type': 'architecture',
                'slug': item.unique_slug,
                'version': '1.0',
                'created_on': item.created_on.isoformat(),
                'last_updated_on': item.last_updated_on.isoformat(),
            }

            # Build markdown content
            content_parts = []

            # Title
            content_parts.append(f"# {item.title}\n")

            # When to Use section
            if item.ai_when_to_use:
                content_parts.append("## When to Use\n")
                for use_case in item.ai_when_to_use:
                    content_parts.append(f"- {use_case}")
                content_parts.append("")  # Empty line

            # Keywords section
            if item.keywords:
                content_parts.append("## Keywords\n")
                keywords_str = ", ".join([f"`{kw}`" for kw in item.keywords])
                content_parts.append(f"{keywords_str}\n")

            # Requirements section (main content)
            content_parts.append("## Requirements\n")
            content_parts.append(item.ai_requirements)
            content_parts.append("")  # Empty line

            # Relationships section
            if item.children_slugs or item.related_slugs:
                content_parts.append("## Relationships\n")

                if item.children_slugs:
                    content_parts.append("### Children\n")
                    for child in item.children_slugs:
                        content_parts.append(f"- `{child}`")
                    content_parts.append("")

                if item.related_slugs:
                    content_parts.append("### Related\n")
                    for related in item.related_slugs:
                        content_parts.append(f"- `{related}`")
                    content_parts.append("")

            # Epic Links section
            if item.linked_epic_ids:
                content_parts.append("## Epic Links\n")
                for epic_id in item.linked_epic_ids:
                    content_parts.append(f"- `{epic_id}`")
                content_parts.append("")

            # Tags section
            if item.tags:
                content_parts.append("## Tags\n")
                tags_str = ", ".join([f"`{tag}`" for tag in item.tags])
                content_parts.append(f"{tags_str}\n")

            # Footer
            content_parts.append("---")
            content_parts.append(f"*Last updated: {item.last_updated_on.strftime('%Y-%m-%d')}*")

            # Combine content
            markdown_content = "\n".join(content_parts)

            # Create frontmatter post
            post = frontmatter.Post(markdown_content, **metadata)

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            return ExportResult(
                success=True,
                message=f"Exported architecture item '{item.unique_slug}'",
                file_path=str(output_path)
            )

        except Exception as e:
            logger.error(f"Error exporting architecture item: {e}", exc_info=True)
            return ExportResult(
                success=False,
                message="Export failed",
                error=str(e)
            )

    @staticmethod
    def export_batch(items: List[ArchitectureItem], output_dir: Path) -> List[ExportResult]:
        """Export multiple architecture items to markdown files.

        Args:
            items: List of architecture items to export
            output_dir: Directory to write files to

        Returns:
            List of ExportResult for each item
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []

        for item in items:
            output_path = output_dir / f"architecture_{item.unique_slug}.md"
            result = ArchitectureMarkdownExporter.export_item(item, output_path)
            results.append(result)

        return results


class ArchitectureMarkdownImporter:
    """Import Architecture Memory items from markdown format."""

    @staticmethod
    def parse_item(file_path: Path) -> ImportResult:
        """Parse a markdown file and extract architecture item data.

        Args:
            file_path: Path to markdown file

        Returns:
            ImportResult with parsed item or error
        """
        if not FRONTMATTER_AVAILABLE:
            return ImportResult(
                success=False,
                message="python-frontmatter package not installed",
                error="Missing dependency"
            )

        try:
            # Read and parse file
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            warnings = []

            # Validate front matter
            metadata = post.metadata
            if metadata.get('type') != 'architecture':
                return ImportResult(
                    success=False,
                    message="Invalid file type",
                    error=f"Expected type 'architecture', got '{metadata.get('type')}'"
                )

            # Extract required fields
            slug = metadata.get('slug')
            if not slug:
                return ImportResult(
                    success=False,
                    message="Missing required field",
                    error="'slug' field is required in front matter"
                )

            # Validate slug format
            if not re.match(r'^[a-z0-9-]+$', slug):
                return ImportResult(
                    success=False,
                    message="Invalid slug format",
                    error=f"Slug '{slug}' must contain only lowercase letters, numbers, and hyphens"
                )

            # Parse content
            content = post.content

            # Extract title (first H1)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if not title_match:
                return ImportResult(
                    success=False,
                    message="Missing title",
                    error="No H1 title found in markdown content"
                )
            title = title_match.group(1).strip()

            # Extract when to use (bullet list under ## When to Use)
            when_to_use = []
            when_match = re.search(r'##\s+When\s+to\s+Use\s*\n((?:- .+\n?)+)', content, re.IGNORECASE)
            if when_match:
                when_lines = when_match.group(1).strip().split('\n')
                when_to_use = [line.lstrip('- ').strip() for line in when_lines if line.strip().startswith('-')]

            # Extract keywords (inline code blocks)
            keywords = []
            keywords_match = re.search(r'##\s+Keywords\s*\n(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL | re.IGNORECASE)
            if keywords_match:
                keywords_text = keywords_match.group(1).strip()
                # Find all inline code blocks
                keywords = re.findall(r'`([^`]+)`', keywords_text)

            # Extract requirements (content under ## Requirements)
            requirements_match = re.search(
                r'##\s+Requirements\s*\n(.+?)(?=\n##\s+Relationships|\n##\s+Epic|\n##\s+Tags|\n---|\Z)',
                content,
                re.DOTALL | re.IGNORECASE
            )
            if not requirements_match:
                return ImportResult(
                    success=False,
                    message="Missing requirements",
                    error="No ## Requirements section found"
                )
            requirements = requirements_match.group(1).strip()

            # Extract children slugs
            children_slugs = []
            children_match = re.search(r'###\s+Children\s*\n((?:- .+\n?)+)', content, re.IGNORECASE)
            if children_match:
                children_lines = children_match.group(1).strip().split('\n')
                children_slugs = [
                    re.sub(r'`([^`]+)`', r'\1', line.lstrip('- ').strip())
                    for line in children_lines if line.strip().startswith('-')
                ]

            # Extract related slugs
            related_slugs = []
            related_match = re.search(r'###\s+Related\s*\n((?:- .+\n?)+)', content, re.IGNORECASE)
            if related_match:
                related_lines = related_match.group(1).strip().split('\n')
                related_slugs = [
                    re.sub(r'`([^`]+)`', r'\1', line.lstrip('- ').strip())
                    for line in related_lines if line.strip().startswith('-')
                ]

            # Extract epic links
            epic_ids = []
            epic_match = re.search(r'##\s+Epic\s+Links?\s*\n((?:- .+\n?)+)', content, re.IGNORECASE)
            if epic_match:
                epic_lines = epic_match.group(1).strip().split('\n')
                epic_ids = [
                    re.sub(r'`([^`]+)`', r'\1', line.lstrip('- ').strip())
                    for line in epic_lines if line.strip().startswith('-')
                ]

            # Extract tags
            tags = []
            tags_match = re.search(r'##\s+Tags\s*\n(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL | re.IGNORECASE)
            if tags_match:
                tags_text = tags_match.group(1).strip()
                tags = re.findall(r'`([^`]+)`', tags_text)

            # Parse timestamps
            created_on = datetime.fromisoformat(metadata['created_on'].replace('Z', '+00:00'))
            last_updated_on = datetime.fromisoformat(metadata['last_updated_on'].replace('Z', '+00:00'))

            # Create ArchitectureItem
            item = ArchitectureItem(
                unique_slug=slug,
                title=title,
                ai_requirements=requirements,
                ai_when_to_use=when_to_use,
                keywords=keywords,
                children_slugs=children_slugs,
                related_slugs=related_slugs,
                linked_epic_ids=epic_ids,
                tags=tags,
                created_on=created_on,
                last_updated_on=last_updated_on
            )

            return ImportResult(
                success=True,
                message=f"Successfully parsed architecture item '{slug}'",
                item=item,
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Error parsing architecture item: {e}", exc_info=True)
            return ImportResult(
                success=False,
                message="Parse failed",
                error=str(e)
            )


class TroubleshootMarkdownExporter:
    """Export Troubleshoot Memory items to markdown format."""

    @staticmethod
    def export_item(item: TroubleshootItem, output_path: Optional[Path] = None) -> ExportResult:
        """Export a single troubleshoot item to markdown.

        Args:
            item: Troubleshoot item to export
            output_path: Optional output file path

        Returns:
            ExportResult with success status and file path
        """
        if not FRONTMATTER_AVAILABLE:
            return ExportResult(
                success=False,
                message="python-frontmatter package not installed",
                error="Missing dependency"
            )

        try:
            # Generate filename if not provided
            if output_path is None:
                output_path = Path(f"troubleshoot_{item.unique_slug}.md")

            # Build front matter
            metadata = {
                'type': 'troubleshoot',
                'slug': item.unique_slug,
                'version': '1.0',
                'created_on': item.created_on.isoformat(),
                'last_updated_on': item.last_updated_on.isoformat(),
                'usage_count': item.usage_count,
                'success_count': item.success_count,
            }

            # Build markdown content
            content_parts = []

            # Title
            content_parts.append(f"# {item.title}\n")

            # Problem / Use Cases section
            if item.ai_use_case:
                content_parts.append("## Problem / Use Cases\n")
                for use_case in item.ai_use_case:
                    content_parts.append(f"- {use_case}")
                content_parts.append("")  # Empty line

            # Keywords section
            if item.keywords:
                content_parts.append("## Keywords\n")
                keywords_str = ", ".join([f"`{kw}`" for kw in item.keywords])
                content_parts.append(f"{keywords_str}\n")

            # Solutions section (main content)
            content_parts.append("## Solutions\n")
            content_parts.append(item.ai_solutions)
            content_parts.append("")  # Empty line

            # Tags section
            if item.tags:
                content_parts.append("## Tags\n")
                tags_str = ", ".join([f"`{tag}`" for tag in item.tags])
                content_parts.append(f"{tags_str}\n")

            # Footer with statistics
            success_rate = (item.success_count / item.usage_count * 100) if item.usage_count > 0 else 0
            content_parts.append("---")
            content_parts.append(
                f"*Last updated: {item.last_updated_on.strftime('%Y-%m-%d')} | "
                f"Usage: {item.usage_count} times | "
                f"Success Rate: {success_rate:.0f}%*"
            )

            # Combine content
            markdown_content = "\n".join(content_parts)

            # Create frontmatter post
            post = frontmatter.Post(markdown_content, **metadata)

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            return ExportResult(
                success=True,
                message=f"Exported troubleshoot item '{item.unique_slug}'",
                file_path=str(output_path)
            )

        except Exception as e:
            logger.error(f"Error exporting troubleshoot item: {e}", exc_info=True)
            return ExportResult(
                success=False,
                message="Export failed",
                error=str(e)
            )

    @staticmethod
    def export_batch(items: List[TroubleshootItem], output_dir: Path) -> List[ExportResult]:
        """Export multiple troubleshoot items to markdown files.

        Args:
            items: List of troubleshoot items to export
            output_dir: Directory to write files to

        Returns:
            List of ExportResult for each item
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []

        for item in items:
            output_path = output_dir / f"troubleshoot_{item.unique_slug}.md"
            result = TroubleshootMarkdownExporter.export_item(item, output_path)
            results.append(result)

        return results


class TroubleshootMarkdownImporter:
    """Import Troubleshoot Memory items from markdown format."""

    @staticmethod
    def parse_item(file_path: Path) -> ImportResult:
        """Parse a markdown file and extract troubleshoot item data.

        Args:
            file_path: Path to markdown file

        Returns:
            ImportResult with parsed item or error
        """
        if not FRONTMATTER_AVAILABLE:
            return ImportResult(
                success=False,
                message="python-frontmatter package not installed",
                error="Missing dependency"
            )

        try:
            # Read and parse file
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            warnings = []

            # Validate front matter
            metadata = post.metadata
            if metadata.get('type') != 'troubleshoot':
                return ImportResult(
                    success=False,
                    message="Invalid file type",
                    error=f"Expected type 'troubleshoot', got '{metadata.get('type')}'"
                )

            # Extract required fields
            slug = metadata.get('slug')
            if not slug:
                return ImportResult(
                    success=False,
                    message="Missing required field",
                    error="'slug' field is required in front matter"
                )

            # Validate slug format
            if not re.match(r'^[a-z0-9-]+$', slug):
                return ImportResult(
                    success=False,
                    message="Invalid slug format",
                    error=f"Slug '{slug}' must contain only lowercase letters, numbers, and hyphens"
                )

            # Parse content
            content = post.content

            # Extract title (first H1)
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if not title_match:
                return ImportResult(
                    success=False,
                    message="Missing title",
                    error="No H1 title found in markdown content"
                )
            title = title_match.group(1).strip()

            # Extract use cases (bullet list under ## Problem / Use Cases)
            use_cases = []
            use_case_match = re.search(
                r'##\s+Problem\s*/?\s*Use\s+Cases?\s*\n((?:- .+\n?)+)',
                content,
                re.IGNORECASE
            )
            if use_case_match:
                use_case_lines = use_case_match.group(1).strip().split('\n')
                use_cases = [line.lstrip('- ').strip() for line in use_case_lines if line.strip().startswith('-')]

            # Extract keywords (inline code blocks)
            keywords = []
            keywords_match = re.search(r'##\s+Keywords\s*\n(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL | re.IGNORECASE)
            if keywords_match:
                keywords_text = keywords_match.group(1).strip()
                keywords = re.findall(r'`([^`]+)`', keywords_text)

            # Extract solutions (content under ## Solutions)
            solutions_match = re.search(
                r'##\s+Solutions?\s*\n(.+?)(?=\n##\s+Tags|\n---|\Z)',
                content,
                re.DOTALL | re.IGNORECASE
            )
            if not solutions_match:
                return ImportResult(
                    success=False,
                    message="Missing solutions",
                    error="No ## Solutions section found"
                )
            solutions = solutions_match.group(1).strip()

            # Extract tags
            tags = []
            tags_match = re.search(r'##\s+Tags\s*\n(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL | re.IGNORECASE)
            if tags_match:
                tags_text = tags_match.group(1).strip()
                tags = re.findall(r'`([^`]+)`', tags_text)

            # Parse timestamps and statistics
            created_on = datetime.fromisoformat(metadata['created_on'].replace('Z', '+00:00'))
            last_updated_on = datetime.fromisoformat(metadata['last_updated_on'].replace('Z', '+00:00'))
            usage_count = metadata.get('usage_count', 0)
            success_count = metadata.get('success_count', 0)

            # Create TroubleshootItem
            item = TroubleshootItem(
                unique_slug=slug,
                title=title,
                ai_solutions=solutions,
                ai_use_case=use_cases,
                keywords=keywords,
                tags=tags,
                usage_count=usage_count,
                success_count=success_count,
                created_on=created_on,
                last_updated_on=last_updated_on
            )

            return ImportResult(
                success=True,
                message=f"Successfully parsed troubleshoot item '{slug}'",
                item=item,
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Error parsing troubleshoot item: {e}", exc_info=True)
            return ImportResult(
                success=False,
                message="Parse failed",
                error=str(e)
            )