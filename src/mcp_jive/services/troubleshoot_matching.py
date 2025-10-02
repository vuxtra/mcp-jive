"""Problem-Solution Matching Engine.

Intelligent matching system for troubleshooting items that:
- Analyzes problem descriptions
- Matches to relevant solutions using semantic search
- Ranks solutions by relevance and success rate
- Provides AI-friendly solution formatting
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..models.memory import TroubleshootItem, TroubleshootItemMatch
from ..storage.memory_storage import TroubleshootMemoryStorage

logger = logging.getLogger(__name__)


@dataclass
class MatchingContext:
    """Context for problem-solution matching."""
    max_results: int = 5
    min_relevance_score: float = 0.3
    boost_by_success_rate: bool = True
    include_usage_stats: bool = True


class ProblemSolutionMatcher:
    """Intelligent problem-solution matching engine.

    Uses semantic search, keyword matching, and success rate analysis
    to find the most relevant troubleshooting solutions.
    """

    def __init__(self, storage: TroubleshootMemoryStorage):
        """Initialize the matching engine.

        Args:
            storage: Troubleshoot memory storage instance
        """
        self.storage = storage

    async def match_problem(
        self,
        problem_description: str,
        context: Optional[MatchingContext] = None
    ) -> List[TroubleshootItemMatch]:
        """Match a problem description to relevant solutions.

        Args:
            problem_description: Description of the problem
            context: Matching context with constraints

        Returns:
            List of matched solutions with relevance scores
        """
        context = context or MatchingContext()

        # Perform semantic search
        search_results = await self.storage.search(
            problem_description,
            limit=context.max_results * 2  # Get extra for filtering
        )

        matches = []
        for item, distance in search_results:
            # Convert distance to relevance score (0-1, higher is better)
            # LanceDB returns distance, so lower is better - invert it
            relevance_score = 1.0 / (1.0 + distance)

            # Filter by minimum relevance
            if relevance_score < context.min_relevance_score:
                continue

            # Boost by success rate if enabled
            if context.boost_by_success_rate and item.usage_count > 0:
                success_rate = item.success_count / item.usage_count
                # Boost relevance by up to 20% based on success rate
                relevance_score = relevance_score * (1.0 + 0.2 * success_rate)

            # Find which use cases matched
            matched_use_cases = self._find_matching_use_cases(
                problem_description,
                item.ai_use_case
            )

            # Create solution preview
            solution_preview = self._create_solution_preview(item.ai_solutions)

            match = TroubleshootItemMatch(
                slug=item.unique_slug,
                title=item.title,
                relevance_score=min(relevance_score, 1.0),  # Cap at 1.0
                matched_use_cases=matched_use_cases or item.ai_use_case[:2],
                solution_preview=solution_preview
            )
            matches.append(match)

        # Sort by relevance score (highest first)
        matches.sort(key=lambda m: m.relevance_score, reverse=True)

        # Return top matches
        return matches[:context.max_results]

    async def get_detailed_solution(
        self,
        slug: str,
        mark_as_used: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get detailed solution for a troubleshooting item.

        Args:
            slug: Troubleshoot item slug
            mark_as_used: Whether to increment usage counter

        Returns:
            Detailed solution dictionary or None if not found
        """
        item = await self.storage.get_by_slug(slug)
        if not item:
            return None

        # Increment usage if requested
        if mark_as_used:
            await self.storage.increment_usage(item.id)

        return {
            "slug": item.unique_slug,
            "title": item.title,
            "use_cases": item.ai_use_case,
            "solutions": item.ai_solutions,
            "keywords": item.keywords,
            "usage_stats": {
                "total_uses": item.usage_count + (1 if mark_as_used else 0),
                "successful_uses": item.success_count,
                "success_rate": item.success_count / max(item.usage_count, 1)
            },
            "created_on": item.created_on.isoformat(),
            "last_updated_on": item.last_updated_on.isoformat()
        }

    async def mark_solution_success(
        self,
        slug: str,
        success: bool = True
    ) -> bool:
        """Mark a solution as successful or unsuccessful.

        Args:
            slug: Troubleshoot item slug
            success: Whether the solution was successful

        Returns:
            True if marked successfully, False otherwise
        """
        item = await self.storage.get_by_slug(slug)
        if not item:
            return False

        await self.storage.increment_usage(item.id, success=success)
        logger.info(f"Marked solution '{slug}' as {'successful' if success else 'used'}")
        return True

    async def suggest_similar_problems(
        self,
        slug: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Suggest similar problems based on a troubleshooting item.

        Args:
            slug: Troubleshoot item slug
            limit: Maximum number of suggestions

        Returns:
            List of similar problems
        """
        item = await self.storage.get_by_slug(slug)
        if not item:
            return []

        # Search using the item's use cases
        search_query = " ".join(item.ai_use_case)
        results = await self.storage.search(search_query, limit=limit + 1)

        similar = []
        for search_item, distance in results:
            # Skip the original item
            if search_item.id == item.id:
                continue

            relevance_score = 1.0 / (1.0 + distance)
            similar.append({
                "slug": search_item.unique_slug,
                "title": search_item.title,
                "use_cases": search_item.ai_use_case,
                "relevance_score": relevance_score,
                "success_rate": search_item.success_count / max(search_item.usage_count, 1)
            })

        return similar[:limit]

    def _find_matching_use_cases(
        self,
        problem: str,
        use_cases: List[str]
    ) -> List[str]:
        """Find which use cases match the problem description.

        Args:
            problem: Problem description
            use_cases: List of use cases

        Returns:
            List of matching use cases
        """
        problem_lower = problem.lower()
        matched = []

        for use_case in use_cases:
            # Simple keyword matching - can be enhanced with more sophisticated NLP
            use_case_words = set(use_case.lower().split())
            problem_words = set(problem_lower.split())

            # Check for word overlap
            overlap = use_case_words.intersection(problem_words)
            if len(overlap) >= 2:  # At least 2 words in common
                matched.append(use_case)

        return matched

    def _create_solution_preview(self, solutions: str, max_length: int = 200) -> str:
        """Create a preview of the solution text.

        Args:
            solutions: Full solution text
            max_length: Maximum preview length

        Returns:
            Solution preview
        """
        if len(solutions) <= max_length:
            return solutions

        # Try to truncate at sentence boundary
        preview = solutions[:max_length]
        last_period = preview.rfind('.')
        last_newline = preview.rfind('\n')

        boundary = max(last_period, last_newline)
        if boundary > max_length * 0.7:
            preview = solutions[:boundary + 1]

        return preview.rstrip() + "..."


class TroubleshootingGuideGenerator:
    """Generate comprehensive troubleshooting guides.

    Creates AI-friendly guides that combine multiple troubleshooting
    solutions into actionable workflows.
    """

    def __init__(self, matcher: ProblemSolutionMatcher):
        """Initialize the guide generator.

        Args:
            matcher: Problem-solution matcher instance
        """
        self.matcher = matcher

    async def generate_troubleshooting_workflow(
        self,
        problem: str,
        max_steps: int = 5
    ) -> str:
        """Generate a troubleshooting workflow for a problem.

        Args:
            problem: Problem description
            max_steps: Maximum troubleshooting steps

        Returns:
            Markdown-formatted troubleshooting workflow
        """
        # Match solutions
        matches = await self.matcher.match_problem(
            problem,
            MatchingContext(max_results=max_steps)
        )

        if not matches:
            return f"# Troubleshooting: {problem}\n\nNo matching solutions found."

        workflow = [
            f"# Troubleshooting Workflow: {problem}",
            "",
            "Follow these steps to resolve the issue:",
            ""
        ]

        for i, match in enumerate(matches, 1):
            workflow.append(f"## Step {i}: {match.title} (Relevance: {match.relevance_score:.2f})")
            workflow.append("")

            # Get detailed solution
            details = await self.matcher.get_detailed_solution(
                match.slug,
                mark_as_used=False  # Don't mark as used for guide generation
            )

            if details:
                workflow.append("**When to try this:**")
                for use_case in match.matched_use_cases:
                    workflow.append(f"- {use_case}")
                workflow.append("")

                workflow.append("**Solution:**")
                workflow.append(details["solutions"])
                workflow.append("")

                if details["usage_stats"]["total_uses"] > 0:
                    success_rate = details["usage_stats"]["success_rate"] * 100
                    workflow.append(
                        f"*Success rate: {success_rate:.1f}% "
                        f"({details['usage_stats']['successful_uses']}/{details['usage_stats']['total_uses']} attempts)*"
                    )
                    workflow.append("")

        workflow.append("---")
        workflow.append("**Next Steps:**")
        workflow.append("- Try the solutions in order, starting with the highest relevance")
        workflow.append("- Mark successful solutions to improve future recommendations")
        workflow.append("- If all steps fail, consider creating a new troubleshooting item for this specific case")

        return "\n".join(workflow)

    async def generate_diagnostic_guide(
        self,
        keywords: List[str],
        limit: int = 5
    ) -> str:
        """Generate a diagnostic guide based on keywords.

        Args:
            keywords: List of diagnostic keywords
            limit: Maximum solutions to include

        Returns:
            Markdown-formatted diagnostic guide
        """
        # Search using keywords
        query = " ".join(keywords)
        results = await self.matcher.storage.search(query, limit=limit)

        guide = [
            "# Diagnostic Guide",
            f"**Keywords:** {', '.join(keywords)}",
            "",
            "## Potential Issues and Solutions",
            ""
        ]

        for i, (item, distance) in enumerate(results, 1):
            relevance = 1.0 / (1.0 + distance)
            success_rate = item.success_count / max(item.usage_count, 1) * 100

            guide.append(f"### {i}. {item.title}")
            guide.append(f"*Relevance: {relevance:.2f} | Success Rate: {success_rate:.1f}%*")
            guide.append("")

            guide.append("**Symptoms:**")
            for use_case in item.ai_use_case[:3]:
                guide.append(f"- {use_case}")
            guide.append("")

            guide.append("**Quick Solution:**")
            preview = self.matcher._create_solution_preview(item.ai_solutions, 150)
            guide.append(preview)
            guide.append("")
            guide.append(f"*Full solution: Use slug `{item.unique_slug}`*")
            guide.append("")

        return "\n".join(guide)