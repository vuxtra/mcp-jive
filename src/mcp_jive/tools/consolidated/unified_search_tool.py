"""Unified Search Tool - Consolidates all search operations.

This tool replaces:
- jive_search_work_items
- jive_search_tasks
- jive_search_content
"""

import logging
from typing import Dict, Any, List, Optional
try:
    from mcp.types import Tool
except ImportError:
    # Mock Tool type if MCP not available
    Tool = Dict[str, Any]

from ..base import BaseTool, ToolResult
from ...utils.search_query_builder import (
    SearchQueryBuilder, SearchResultRanker, SearchValidator,
    SearchScope, SearchOperator, SortOrder
)

logger = logging.getLogger(__name__)


class UnifiedSearchTool(BaseTool):
    """Unified tool for all content search operations."""
    
    def __init__(self, storage=None):
        """Initialize the unified search tool.
        
        Args:
            storage: Work item storage instance (optional)
        """
        super().__init__()
        self.storage = storage
        self.tool_name = "jive_search_content"
        self.query_builder = SearchQueryBuilder()
        self.result_ranker = SearchResultRanker()
        self.search_validator = SearchValidator()
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return self.tool_name
    
    @property
    def description(self) -> str:
        """Tool description for AI agents."""
        return "Jive: Unified search across all work items, tasks, and content with semantic, keyword, and hybrid search capabilities"
    
    @property
    def category(self):
        """Tool category."""
        from ..base import ToolCategory
        return ToolCategory.WORK_ITEM_MANAGEMENT
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Parameters schema for the tool."""
        return {
            "query": {
                "type": "string",
                "description": "Search query - can be keywords, phrases, or natural language description"
            },
            "search_type": {
                "type": "string",
                "enum": ["semantic", "keyword", "hybrid"],
                "description": "Type of search to perform"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return"
            }
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        try:
            query = kwargs.get("query")
            search_type = kwargs.get("search_type", "hybrid")
            content_types = kwargs.get("content_types", ["work_item", "task", "description", "acceptance_criteria"])
            filters = kwargs.get("filters", {})
            limit = kwargs.get("limit", 20)
            min_score = kwargs.get("min_score", 0.1)
            
            if search_type == "semantic":
                results = await self._semantic_search(query, content_types, filters, limit, min_score)
            elif search_type == "keyword":
                results = await self._keyword_search(query, content_types, filters, limit)
            else:
                results = await self._hybrid_search(query, content_types, filters, limit, min_score)
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "search_type": search_type,
                    "results": results,
                    "total_found": len(results)
                }
            )
        except Exception as e:
            logger.error(f"Error in unified search tool execute: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def get_tools(self) -> List[Tool]:
        """Get the unified search tool."""
        return [
            Tool(
                name="jive_search_content",
                description="Jive: Unified search across all work items, tasks, and content with semantic, keyword, and hybrid search capabilities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query - can be keywords, phrases, or natural language description"
                        },
                        "search_type": {
                            "type": "string",
                            "enum": ["semantic", "keyword", "hybrid"],
                            "default": "hybrid",
                            "description": "Type of search to perform: semantic (meaning-based), keyword (exact matches), or hybrid (combination)"
                        },
                        "content_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["work_item", "task", "description", "acceptance_criteria", "title", "tags"]
                            },
                            "default": ["work_item", "task", "description", "acceptance_criteria"],
                            "description": "Types of content to search within"
                        },
                        "filters": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["initiative", "epic", "feature", "story", "task"]
                                    },
                                    "description": "Filter by work item types"
                                },
                                "status": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["not_started", "in_progress", "completed", "blocked", "cancelled"]
                                    },
                                    "description": "Filter by status values"
                                },
                                "priority": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["low", "medium", "high", "critical"]
                                    },
                                    "description": "Filter by priority levels"
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Filter by tags (work items must have at least one of these tags)"
                                },
                                "created_after": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "Filter work items created after this date"
                                },
                                "created_before": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "Filter work items created before this date"
                                },
                                "assignee_id": {
                                    "type": "string",
                                    "description": "Filter by assignee identifier"
                                }
                            },
                            "description": "Additional filters to apply to search results"
                        },
                        "include_score": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include relevance scores in the results"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20,
                            "description": "Maximum number of results to return"
                        },
                        "min_score": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "default": 0.1,
                            "description": "Minimum relevance score for results (0.0 to 1.0)"
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle unified search calls."""
        if name != "jive_search_content":
            raise ValueError(f"Unknown tool: {name}")
        
        query = arguments["query"]
        search_type = arguments.get("search_type", "hybrid")
        content_types = arguments.get("content_types", ["work_item", "task", "description", "acceptance_criteria"])
        filters = arguments.get("filters", {})
        include_score = arguments.get("include_score", True)
        limit = arguments.get("limit", 20)
        min_score = arguments.get("min_score", 0.1)
        
        try:
            # Execute search based on type
            if search_type == "semantic":
                results = await self._semantic_search(query, content_types, filters, limit, min_score)
            elif search_type == "keyword":
                results = await self._keyword_search(query, content_types, filters, limit)
            else:  # hybrid
                results = await self._hybrid_search(query, content_types, filters, limit, min_score)
            
            # Add scores if requested
            if include_score:
                results = await self._add_relevance_scores(results, query, search_type)
            else:
                # Remove scores if not requested
                for result in results:
                    result.pop("score", None)
                    result.pop("semantic_score", None)
                    result.pop("keyword_score", None)
            
            # Sort by score if available, otherwise by order_index
            if include_score and results:
                results.sort(key=lambda x: x.get("score", 0), reverse=True)
            elif results:
                # Fallback to sorting by order_index for consistent ordering
                results.sort(key=lambda x: x.get("order_index", 0))
            
            logger.info(
                f"Search '{query}' ({search_type}) found {len(results)} results"
            )
            
            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "content_types": content_types,
                "results": results,
                "total_found": len(results),
                "filters_applied": filters
            }
            
        except Exception as e:
            logger.error(f"Error in unified search tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query if 'query' in locals() else "",
                "search_type": search_type if 'search_type' in locals() else "unknown",
                "results": [],
                "total_found": 0
            }
    
    async def _semantic_search(self, query: str, content_types: List[str], 
                              filters: Dict, limit: int, min_score: float) -> List[Dict]:
        """Perform semantic search using vector embeddings."""
        try:
            # Build optimized search query
            query_builder = SearchQueryBuilder()
            search_query = query_builder.add_term(query).set_scope(SearchScope.ALL).build()
            
            # Use storage's search_work_items method for vector search
            if self.storage:
                results = await self.storage.search_work_items(
                    query=query,
                    limit=limit,
                    search_type="vector"
                )
                
                # Filter results by content types and apply filters
                filtered_results = self._apply_content_type_filters(results, content_types, query)
                
                # Apply filters using query builder
                if filters:
                    for key, value in filters.items():
                        if value:
                            search_query.add_filter(key, SearchOperator.EXACT, value)
                    filtered_results = self._apply_query_filters(filtered_results, search_query)
                else:
                    filtered_results = self._apply_additional_filters(filtered_results, filters)
                
                # Rank results using the new ranker
                ranked_search_results = self.result_ranker.rank_results(
                    filtered_results, search_query
                )
                
                # Convert SearchResult objects to dictionaries and add semantic scores
                ranked_results = []
                for search_result in ranked_search_results:
                    result = search_result.item.copy()
                    result["semantic_score"] = search_result.score
                    result["score"] = search_result.score
                    result["matched_content"] = self._extract_matched_content(result, query)
                    ranked_results.append(result)
                
                return ranked_results[:limit]
            else:
                logger.warning("No storage available for semantic search")
                return []
            
        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to keyword: {e}")
            return await self._keyword_search(query, content_types, filters, limit)
    
    async def _keyword_search(self, query: str, content_types: List[str], 
                             filters: Dict, limit: int) -> List[Dict]:
        """Perform keyword-based search."""
        try:
            # Build optimized search query with filters
            query_builder = SearchQueryBuilder()
            query_builder.add_term(query).set_scope(SearchScope.ALL)
            
            # Add filters to the builder before building
            if filters:
                for key, value in filters.items():
                    if value:
                        query_builder.add_filter(key, SearchOperator.EXACT, value)
            
            search_query = query_builder.build()
            
            if not self.storage:
                logger.warning("No storage available for keyword search")
                return []
            
            # Get all work items and filter them
            all_items = await self.storage.list_work_items(limit=1000)  # Get more items for filtering
            
            # Filter by keyword matching with improved sensitivity
            matching_items = []
            query_lower = query.lower().strip()
            query_terms = [term.strip() for term in query_lower.split() if term.strip()]
            
            for item in all_items:
                # Check if item matches query in specified content types
                matches = False
                match_score = 0.0
                matched_content = ""
                
                for content_type in content_types:
                    if content_type in ["work_item", "task", "title"]:
                        title = item.get("title", "").lower()
                        # Exact phrase match (highest priority)
                        if query_lower in title:
                            matches = True
                            match_score += 0.8
                            matched_content = item.get("title", "")
                        # Partial word matches
                        elif any(term in title for term in query_terms):
                            matches = True
                            match_score += 0.5
                            matched_content = item.get("title", "")
                        # Fuzzy matching for single character differences
                        elif len(query_terms) == 1 and len(query_terms[0]) > 3:
                            if self._fuzzy_match(query_terms[0], title):
                                matches = True
                                match_score += 0.3
                                matched_content = item.get("title", "")
                    
                    elif content_type == "description":
                        description = item.get("description", "").lower()
                        if query_lower in description:
                            matches = True
                            match_score += 0.6
                            if not matched_content:
                                matched_content = item.get("description", "")[:100]
                        elif any(term in description for term in query_terms):
                            matches = True
                            match_score += 0.3
                            if not matched_content:
                                matched_content = item.get("description", "")[:100]
                    
                    elif content_type == "acceptance_criteria":
                        criteria = item.get("acceptance_criteria", [])
                        if isinstance(criteria, list):
                            for criterion in criteria:
                                if isinstance(criterion, str):
                                    criterion_lower = criterion.lower()
                                    if query_lower in criterion_lower or any(term in criterion_lower for term in query_terms):
                                        matches = True
                                        match_score += 0.2
                                        if not matched_content:
                                            matched_content = criterion[:100]
                    
                    elif content_type == "tags":
                        tags = item.get("tags", [])
                        if isinstance(tags, list):
                            tag_matches = []
                            for tag in tags:
                                tag_lower = tag.lower()
                                if query_lower in tag_lower or any(term in tag_lower for term in query_terms):
                                    tag_matches.append(tag)
                            if tag_matches:
                                matches = True
                                match_score += 0.2
                                if not matched_content:
                                    matched_content = ", ".join(tag_matches)
                
                if matches:
                    item_copy = item.copy()
                    item_copy["keyword_score"] = min(match_score, 1.0)
                    item_copy["matched_content"] = matched_content
                    matching_items.append(item_copy)
            
            # Apply filters using query builder (filters already added to search_query)
            logger.info(f"Applying filters from search_query: {len(search_query.filters)} filters")
            logger.info(f"Matching items before filtering: {len(matching_items)}")
            filtered_items = self._apply_query_filters(matching_items, search_query)
            logger.info(f"Filtered items after filtering: {len(filtered_items)}")
            
            # Rank results using the new ranker
            ranked_search_results = self.result_ranker.rank_results(
                filtered_items, search_query
            )
            
            # Convert SearchResult objects to dictionaries
            ranked_results = []
            for search_result in ranked_search_results:
                result = search_result.item.copy()
                result["keyword_score"] = search_result.score
                result["score"] = search_result.score
                ranked_results.append(result)
            
            return ranked_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    async def _hybrid_search(self, query: str, content_types: List[str],
                             filters: Dict, limit: int, min_score: float = 0.1) -> List[Dict]:
        """Perform hybrid search combining semantic and keyword approaches."""
        try:
            # Build optimized search query for hybrid approach
            query_builder = SearchQueryBuilder()
            search_query = query_builder.add_term(query).set_scope(SearchScope.ALL).build()
            
            # Get semantic results (70% weight)
            semantic_results = await self._semantic_search(
                query, content_types, filters, limit, min_score
            )
            
            # Get keyword results (30% weight)
            keyword_results = await self._keyword_search(
                query, content_types, filters, limit
            )
            
            # Merge and rank results using enhanced algorithm
            merged_results = self._merge_search_results_enhanced(
                semantic_results, keyword_results, 
                semantic_weight=0.7, keyword_weight=0.3
            )
            
            # Validate search results
            validated_results = self.search_validator.validate_search_results(
                merged_results, query
            )
            
            return validated_results[:limit]
            
        except Exception as e:
            self.logger.error(f"Hybrid search failed: {e}")
            return []
    
    def _merge_search_results_enhanced(self, semantic_results: List[Dict], keyword_results: List[Dict],
                                      semantic_weight: float, keyword_weight: float) -> List[Dict]:
        """Enhanced merge of semantic and keyword search results with weighted scoring."""
        # Create a map to track combined results
        result_map = {}
        
        # Add semantic results
        for result in semantic_results:
            work_item_id = result["id"]
            result_map[work_item_id] = result.copy()
            result_map[work_item_id]["semantic_score"] = result.get("semantic_score", 0)
            result_map[work_item_id]["keyword_score"] = 0
        
        # Add keyword results
        for result in keyword_results:
            work_item_id = result["id"]
            if work_item_id in result_map:
                # Update existing result
                result_map[work_item_id]["keyword_score"] = result.get("keyword_score", 0)
            else:
                # Add new result
                result_map[work_item_id] = result.copy()
                result_map[work_item_id]["semantic_score"] = 0
                result_map[work_item_id]["keyword_score"] = result.get("keyword_score", 0)
        
        # Calculate enhanced combined scores with boost factors
        for result in result_map.values():
            semantic_score = result.get("semantic_score", 0)
            keyword_score = result.get("keyword_score", 0)
            
            # Apply boost for items that appear in both result sets
            boost_factor = 1.2 if semantic_score > 0 and keyword_score > 0 else 1.0
            
            # Apply priority boost
            priority_boost = self._get_priority_boost(result.get("priority", "medium"))
            
            result["score"] = (
                (semantic_score * semantic_weight + keyword_score * keyword_weight) * 
                boost_factor * priority_boost
            )
        
        # Sort by combined score
        merged_results = list(result_map.values())
        merged_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return merged_results
    
    def _get_priority_boost(self, priority: str) -> float:
        """Get priority boost factor for search results."""
        priority_boosts = {
            "critical": 1.3,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.9
        }
        return priority_boosts.get(priority.lower(), 1.0)
    
    def _merge_search_results(self, semantic_results: List[Dict], keyword_results: List[Dict],
                             semantic_weight: float, keyword_weight: float) -> List[Dict]:
        """Legacy merge method for backward compatibility."""
        return self._merge_search_results_enhanced(
            semantic_results, keyword_results, semantic_weight, keyword_weight
        )
    
    def _fuzzy_match(self, query_term: str, text: str, max_distance: int = 1) -> bool:
        """Simple fuzzy matching for single character differences."""
        if not query_term or not text:
            return False
        
        # Check if query_term appears with single character substitution
        for i in range(len(text) - len(query_term) + 1):
            substring = text[i:i + len(query_term)]
            if len(substring) == len(query_term):
                differences = sum(1 for a, b in zip(query_term, substring) if a != b)
                if differences <= max_distance:
                    return True
        return False
    
    def _calculate_keyword_score(self, work_item: Dict, query: str) -> float:
        """Calculate keyword relevance score for a work item."""
        query_terms = set(query.lower().split())
        score = 0.0
        
        # Title matches (highest weight)
        title_terms = set(work_item.get("title", "").lower().split())
        title_matches = len(query_terms.intersection(title_terms))
        score += title_matches * 0.5
        
        # Description matches
        description_terms = set(work_item.get("description", "").lower().split())
        desc_matches = len(query_terms.intersection(description_terms))
        score += desc_matches * 0.3
        
        # Tag matches
        tags = [tag.lower() for tag in work_item.get("tags", [])]
        tag_matches = len(query_terms.intersection(set(tags)))
        score += tag_matches * 0.2
        
        # Normalize score
        max_possible_score = len(query_terms)
        return min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
    
    def _apply_additional_filters(self, items: List[Dict], filters: Dict) -> List[Dict]:
        """Apply additional filters to search results."""
        if not filters:
            return items
        
        filtered_items = []
        
        for item in items:
            include_item = True
            
            # Type filter
            if "type" in filters and filters["type"]:
                try:
                    type_filter = list(filters["type"]) if hasattr(filters["type"], 'tolist') else filters["type"]
                    type_filter = list(type_filter) if not isinstance(type_filter, (list, tuple)) else type_filter
                except Exception:
                    type_filter = filters["type"]
                if item.get("type") not in type_filter:
                    include_item = False
            
            # Status filter
            if "status" in filters and filters["status"]:
                try:
                    status_filter = list(filters["status"]) if hasattr(filters["status"], 'tolist') else filters["status"]
                    status_filter = list(status_filter) if not isinstance(status_filter, (list, tuple)) else status_filter
                except Exception:
                    status_filter = filters["status"]
                if item.get("status") not in status_filter:
                    include_item = False
            
            # Priority filter
            if "priority" in filters and filters["priority"]:
                try:
                    priority_filter = list(filters["priority"]) if hasattr(filters["priority"], 'tolist') else filters["priority"]
                    priority_filter = list(priority_filter) if not isinstance(priority_filter, (list, tuple)) else priority_filter
                except Exception:
                    priority_filter = filters["priority"]
                if item.get("priority") not in priority_filter:
                    include_item = False
            
            # Assignee filter
            if "assignee_id" in filters and filters["assignee_id"]:
                if item.get("assignee_id") != filters["assignee_id"]:
                    include_item = False
            
            # Date filters (simplified for now)
            # TODO: Implement proper date filtering
            
            if include_item:
                filtered_items.append(item)
        
        return filtered_items
    
    def _apply_query_filters(self, items: List[Dict], search_query) -> List[Dict]:
        """Apply filters using the SearchQueryBuilder."""
        if not search_query.filters:
            logger.info("No filters to apply")
            return items
        
        logger.info(f"Applying {len(search_query.filters)} filters to {len(items)} items")
        filtered_items = []
        
        for item in items:
            include_item = True
            logger.debug(f"Checking item: {item.get('title', 'Unknown')} - status: {item.get('status')}, type: {item.get('type')}")
            
            for filter_obj in search_query.filters:
                filter_key = filter_obj.field
                filter_value = filter_obj.value
                logger.debug(f"Checking filter: {filter_key} = {filter_value}")
                
                if filter_key == "type" and filter_value:
                    item_value = item.get("type")
                    logger.debug(f"Item {filter_key}: {item_value}, Filter {filter_key}: {filter_value}")
                    if item_value not in filter_value:
                        logger.debug(f"Filter mismatch: {item_value} not in {filter_value}")
                        include_item = False
                        break
                elif filter_key == "status" and filter_value:
                    item_value = item.get("status")
                    logger.debug(f"Item {filter_key}: {item_value}, Filter {filter_key}: {filter_value}")
                    if item_value not in filter_value:
                        logger.debug(f"Filter mismatch: {item_value} not in {filter_value}")
                        include_item = False
                        break
                elif filter_key == "priority" and filter_value:
                    item_value = item.get("priority")
                    logger.debug(f"Item {filter_key}: {item_value}, Filter {filter_key}: {filter_value}")
                    if item_value not in filter_value:
                        logger.debug(f"Filter mismatch: {item_value} not in {filter_value}")
                        include_item = False
                        break
                elif filter_key == "assignee_id" and filter_value:
                    item_value = item.get("assignee_id")
                    logger.debug(f"Item assignee_id: {item_value}, Filter assignee_id: {filter_value}")
                    if item_value != filter_value:
                        logger.debug(f"Assignee filter mismatch: {item_value} != {filter_value}")
                        include_item = False
                        break
            
            if include_item:
                logger.debug(f"Item matches all filters: {item.get('title', 'Unknown')}")
                filtered_items.append(item)
            else:
                logger.debug(f"Item filtered out: {item.get('title', 'Unknown')}")
        
        logger.info(f"Filtered down to {len(filtered_items)} items")
        return filtered_items
    
    def _calculate_enhanced_keyword_score(self, item: Dict, search_query) -> float:
        """Calculate enhanced keyword score using SearchQueryBuilder."""
        query_terms = search_query.query_text.lower().split()
        score = 0.0
        
        # Title matches (highest weight)
        title = item.get("title", "").lower()
        for term in query_terms:
            if term in title:
                score += 0.5
        
        # Description matches
        description = item.get("description", "").lower()
        for term in query_terms:
            if term in description:
                score += 0.3
        
        # Tag matches
        tags = [tag.lower() for tag in item.get("tags", [])]
        for term in query_terms:
            if any(term in tag for tag in tags):
                score += 0.2
        
        # Normalize score
        max_possible_score = len(query_terms)
        return min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
    
    def _apply_content_type_filters(self, items: List[Dict], content_types: List[str], query: str) -> List[Dict]:
        """Apply content type filters to search results."""
        # For now, return all items as content type filtering is handled in the search logic
        return items
    
    def _extract_matched_content(self, item: Dict, query: str) -> str:
        """Extract the content that matched the search query."""
        query_lower = query.lower()
        
        # Check title first
        title = item.get("title", "")
        if query_lower in title.lower():
            return title
        
        # Check description
        description = item.get("description", "")
        if query_lower in description.lower():
            return description[:100] + "..." if len(description) > 100 else description
        
        # Default to title
        return title
    
    async def _add_relevance_scores(self, results: List[Dict], query: str, search_type: str) -> List[Dict]:
        """Add or update relevance scores for results."""
        for result in results:
            if "score" not in result:
                if search_type == "semantic":
                    result["score"] = result.get("semantic_score", 0)
                elif search_type == "keyword":
                    result["score"] = result.get("keyword_score", 0)
                else:  # hybrid
                    result["score"] = result.get("score", 0)
        
        return results
    
    def _format_search_results(self, search_data: Dict[str, Any]) -> str:
        """Format search results for display."""
        results = search_data["results"]
        query = search_data["query"]
        search_type = search_data["search_type"]
        total_found = search_data["total_found"]
        
        if results is None or len(results) == 0:
            return f"No results found for '{query}' using {search_type} search."
        
        output = f"Found {total_found} results for '{query}' using {search_type} search:\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "Untitled")
            work_type = result.get("type", "unknown")
            status = result.get("status", "unknown")
            priority = result.get("priority", "unknown")
            score = result.get("score", 0)
            
            output += f"{i}. {title} ({work_type})\n"
            output += f"   Status: {status} | Priority: {priority}"
            
            if score > 0:
                output += f" | Score: {score:.3f}"
            
            if result.get("matched_content"):
                output += f"\n   Match: {result['matched_content'][:100]}..."
            
            output += "\n\n"
        
        return output.strip()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for MCP registration."""
        return {
            "name": "jive_search_content",
            "description": "Jive: Unified content search - search work items, tasks, and content using various methods",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query - keywords, phrases, or specific terms to search for"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["semantic", "keyword", "hybrid"],
                        "default": "hybrid",
                        "description": "Type of search to perform"
                    },
                    "filters": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by work item types"
                            },
                            "status": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by status values"
                            },
                            "priority": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by priority levels"
                            }
                        },
                        "description": "Optional filters to apply to search results"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Maximum number of results to return"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["detailed", "summary", "minimal"],
                        "default": "summary",
                        "description": "Response format level"
                    }
                },
                "required": ["query"]
            }
        }