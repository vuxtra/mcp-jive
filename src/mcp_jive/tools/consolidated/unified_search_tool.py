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

from ..base import BaseTool

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
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        query = kwargs.get("query")
        search_type = kwargs.get("search_type", "hybrid")
        
        if search_type == "semantic":
            return await self._semantic_search(query, **kwargs)
        elif search_type == "keyword":
            return await self._keyword_search(query, **kwargs)
        else:
            return await self._hybrid_search(query, **kwargs)
    
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
            
            # Sort by score if available
            if include_score and results:
                results.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            logger.info(
                f"Search '{query}' ({search_type}) found {len(results)} results"
            )
            
            return [{
                "type": "text",
                "text": self._format_search_results({
                    "success": True,
                    "query": query,
                    "search_type": search_type,
                    "content_types": content_types,
                    "results": results,
                    "total_found": len(results),
                    "filters_applied": filters
                })
            }]
            
        except Exception as e:
            logger.error(f"Error in unified search tool: {e}")
            return [{
                "type": "text",
                "text": f"Search error: {str(e)}"
            }]
    
    async def _semantic_search(self, query: str, content_types: List[str], 
                              filters: Dict, limit: int, min_score: float) -> List[Dict]:
        """Perform semantic search using vector embeddings."""
        try:
            # Use search engine for semantic search
            results = await self.search_engine.semantic_search(
                query=query,
                content_types=content_types,
                filters=filters,
                limit=limit,
                min_score=min_score
            )
            
            # Enhance results with full work item data
            enhanced_results = []
            for result in results:
                work_item = await self.storage.get_work_item(result["id"])
                if work_item:
                    enhanced_result = work_item.copy()
                    enhanced_result["semantic_score"] = result.get("score", 0)
                    enhanced_result["matched_content"] = result.get("matched_content", "")
                    enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to keyword: {e}")
            return await self._keyword_search(query, content_types, filters, limit)
    
    async def _keyword_search(self, query: str, content_types: List[str], 
                             filters: Dict, limit: int) -> List[Dict]:
        """Perform keyword-based search."""
        # Build search query for keyword matching
        search_conditions = []
        
        # Search in different content types
        query_terms = query.lower().split()
        
        for content_type in content_types:
            if content_type in ["work_item", "task", "title"]:
                search_conditions.append({
                    "title": {"$regex": query, "$options": "i"}
                })
            elif content_type == "description":
                search_conditions.append({
                    "description": {"$regex": query, "$options": "i"}
                })
            elif content_type == "acceptance_criteria":
                search_conditions.append({
                    "acceptance_criteria": {"$elemMatch": {"$regex": query, "$options": "i"}}
                })
            elif content_type == "tags":
                search_conditions.append({
                    "tags": {"$in": query_terms}
                })
        
        # Combine search conditions
        if search_conditions:
            query_filter = {"$or": search_conditions}
        else:
            query_filter = {
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}}
                ]
            }
        
        # Add additional filters
        combined_filters = self._combine_filters(query_filter, filters)
        
        # Execute search
        results = await self.storage.query_work_items(
            query=combined_filters,
            limit=limit,
            sort_by="updated_date",
            sort_order="desc"
        )
        
        # Add keyword scores
        for result in results:
            result["keyword_score"] = self._calculate_keyword_score(result, query)
        
        return results
    
    async def _hybrid_search(self, query: str, content_types: List[str], 
                            filters: Dict, limit: int, min_score: float) -> List[Dict]:
        """Combine semantic and keyword search results."""
        # Get semantic results (70% weight)
        semantic_results = await self._semantic_search(
            query, content_types, filters, limit, min_score
        )
        
        # Get keyword results (30% weight)
        keyword_results = await self._keyword_search(
            query, content_types, filters, limit
        )
        
        # Merge and rank results
        merged_results = self._merge_search_results(
            semantic_results, keyword_results, 
            semantic_weight=0.7, keyword_weight=0.3
        )
        
        return merged_results[:limit]
    
    def _merge_search_results(self, semantic_results: List[Dict], keyword_results: List[Dict],
                             semantic_weight: float, keyword_weight: float) -> List[Dict]:
        """Merge semantic and keyword search results with weighted scoring."""
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
        
        # Calculate combined scores
        for result in result_map.values():
            semantic_score = result.get("semantic_score", 0)
            keyword_score = result.get("keyword_score", 0)
            result["score"] = (
                semantic_score * semantic_weight + 
                keyword_score * keyword_weight
            )
        
        # Sort by combined score
        merged_results = list(result_map.values())
        merged_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return merged_results
    
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
    
    def _combine_filters(self, query_filter: Dict, additional_filters: Dict) -> Dict:
        """Combine search query with additional filters."""
        if not additional_filters:
            return query_filter
        
        combined = {"$and": [query_filter]}
        
        # Add type filter
        if "type" in additional_filters and additional_filters["type"]:
            combined["$and"].append({"type": {"$in": additional_filters["type"]}})
        
        # Add status filter
        if "status" in additional_filters and additional_filters["status"]:
            combined["$and"].append({"status": {"$in": additional_filters["status"]}})
        
        # Add priority filter
        if "priority" in additional_filters and additional_filters["priority"]:
            combined["$and"].append({"priority": {"$in": additional_filters["priority"]}})
        
        # Add other filters as needed
        for field in ["assignee_id", "created_after", "created_before"]:
            if field in additional_filters and additional_filters[field]:
                if field.endswith("_after"):
                    date_field = field.replace("_after", "_at")
                    combined["$and"].append({date_field: {"$gte": additional_filters[field]}})
                elif field.endswith("_before"):
                    date_field = field.replace("_before", "_at")
                    combined["$and"].append({date_field: {"$lte": additional_filters[field]}})
                else:
                    combined["$and"].append({field: additional_filters[field]})
        
        return combined
    
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
        
        if not results:
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