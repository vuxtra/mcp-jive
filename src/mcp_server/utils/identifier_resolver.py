"""Work Item Identifier Resolver.

Provides flexible work item identification that supports:
- Exact UUID matching
- Title-based lookup
- Keyword search with automatic selection

This allows AI agents to use human-readable identifiers instead of always needing UUIDs.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)


class IdentifierResolver:
    """Resolves flexible work item identifiers to UUIDs."""
    
    def __init__(self, lancedb_manager: LanceDBManager):
        self.lancedb_manager = lancedb_manager
    
    async def resolve_work_item_id(self, identifier: str) -> Optional[str]:
        """Resolve a flexible identifier to a work item UUID.
        
        Args:
            identifier: Can be:
                - Exact UUID (e.g., "079b61d5-bdd8-4341-8537-935eda5931c7")
                - Exact title (e.g., "E-commerce Platform Modernization")
                - Keyword search (e.g., "ecommerce platform")
        
        Returns:
            UUID string if found, None if not found or ambiguous
        """
        try:
            # Step 1: Check if it's already a valid UUID
            if self._is_valid_uuid(identifier):
                # Verify the UUID exists in the database
                work_item = await self.lancedb_manager.get_work_item(identifier)
                if work_item:
                    logger.info(f"Resolved UUID directly: {identifier}")
                    return identifier
                else:
                    logger.warning(f"UUID {identifier} not found in database")
                    return None
            
            # Step 2: Try exact title match
            exact_match = await self._find_by_exact_title(identifier)
            if exact_match:
                logger.info(f"Resolved by exact title: '{identifier}' -> {exact_match}")
                return exact_match
            
            # Step 3: Try keyword search
            search_match = await self._find_by_keyword_search(identifier)
            if search_match:
                logger.info(f"Resolved by keyword search: '{identifier}' -> {search_match}")
                return search_match
            
            logger.warning(f"Could not resolve identifier: '{identifier}'")
            return None
            
        except Exception as e:
            logger.error(f"Error resolving identifier '{identifier}': {e}")
            return None
    
    def _is_valid_uuid(self, identifier: str) -> bool:
        """Check if the identifier is a valid UUID format."""
        try:
            uuid.UUID(identifier)
            return True
        except (ValueError, TypeError):
            return False
    
    async def _find_by_exact_title(self, title: str) -> Optional[str]:
        """Find work item by exact title match, selecting the most recent if multiple."""
        try:
            logger.info(f"Searching for exact title match: '{title}'")
            # Use keyword search to find exact title matches
            results = await self.lancedb_manager.search_work_items(
                query=f'"{title}"',  # Quoted for exact match
                search_type="keyword",
                limit=10
            )
            
            logger.info(f"Found {len(results)} potential matches for '{title}'")
            
            exact_matches = []
            for i, result in enumerate(results):
                work_item = result.get("work_item", {})
                result_title = work_item.get("title", "")
                result_id = work_item.get("id")
                logger.info(f"Result {i+1}: ID={result_id}, Title='{result_title}'")
                
                if result_title.strip().lower() == title.strip().lower():
                    updated_at_str = work_item.get("updated_at")
                    logger.info(f"Exact match found: ID={result_id}, updated_at={updated_at_str}")
                    try:
                        updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else datetime.min
                        logger.info(f"Parsed updated_at to datetime: {updated_at}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse updated_at '{updated_at_str}': {e}")
                        updated_at = datetime.min
                    
                    exact_matches.append({
                        "id": result_id,
                        "updated_at": updated_at
                    })
            
            if not exact_matches:
                logger.warning(f"No exact title matches found for '{title}'")
                return None
            
            if len(exact_matches) == 1:
                logger.info(f"Single exact match found, returning ID: {exact_matches[0]['id']}")
                return exact_matches[0]["id"]
            
            # Select the most recent based on updated_at
            logger.info(f"Found {len(exact_matches)} exact matches, sorting by updated_at")
            for match in exact_matches:
                logger.info(f"Match before sort: ID={match['id']}, updated_at={match['updated_at']}")
                
            exact_matches.sort(key=lambda x: x["updated_at"], reverse=True)
            
            for match in exact_matches:
                logger.info(f"Match after sort: ID={match['id']}, updated_at={match['updated_at']}")
                
            selected_id = exact_matches[0]["id"]
            logger.info(f"Multiple exact matches found for '{title}', selected most recent: {selected_id}")
            return selected_id
            
        except Exception as e:
            logger.error(f"Error in exact title search: {e}")
            return None
    
    async def _find_by_keyword_search(self, keywords: str) -> Optional[str]:
        """Find work item by keyword search with automatic selection."""
        try:
            # Perform keyword search
            results = await self.lancedb_manager.search_work_items(
                query=keywords,
                search_type="keyword",
                limit=5
            )
            
            if not results:
                return None
            
            # If only one result, return it
            if len(results) == 1:
                work_item = results[0].get("work_item", {})
                return work_item.get("id")
            
            # Multiple results - look for best match
            # Prefer results where keywords appear in title
            keywords_lower = keywords.lower()
            best_match = None
            best_score = 0
            
            for result in results:
                work_item = result.get("work_item", {})
                title = work_item.get("title", "").lower()
                description = work_item.get("description", "").lower()
                
                # Calculate simple relevance score
                score = 0
                if keywords_lower in title:
                    score += 10  # Title match is most important
                if keywords_lower in description:
                    score += 5   # Description match is secondary
                
                # Add relevance score from search if available
                relevance = result.get("relevance_score", 0)
                score += relevance * 2
                
                if score > best_score:
                    best_score = score
                    best_match = work_item.get("id")
            
            if best_match:
                logger.info(f"Selected best match with score {best_score}")
                return best_match
            
            # If no clear best match, log ambiguity and return None
            titles = [r.get("work_item", {}).get("title", "Unknown") for r in results]
            logger.warning(f"Ambiguous search '{keywords}' found {len(results)} results: {titles}")
            return None
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return None
    
    async def resolve_multiple_ids(self, identifiers: List[str]) -> List[str]:
        """Resolve multiple identifiers to UUIDs.
        
        Args:
            identifiers: List of flexible identifiers
        
        Returns:
            List of resolved UUIDs (skips unresolvable identifiers)
        """
        resolved_ids = []
        
        for identifier in identifiers:
            resolved_id = await self.resolve_work_item_id(identifier)
            if resolved_id:
                resolved_ids.append(resolved_id)
            else:
                logger.warning(f"Could not resolve identifier: '{identifier}'")
        
        return resolved_ids
    
    async def get_resolution_info(self, identifier: str) -> Dict[str, Any]:
        """Get detailed information about identifier resolution.
        
        Returns:
            Dictionary with resolution details for debugging/logging
        """
        info = {
            "original_identifier": identifier,
            "is_uuid": self._is_valid_uuid(identifier),
            "resolved_id": None,
            "resolution_method": None,
            "candidates": []
        }
        
        try:
            # Try UUID first
            if info["is_uuid"]:
                work_item = await self.lancedb_manager.get_work_item(identifier)
                if work_item:
                    info["resolved_id"] = identifier
                    info["resolution_method"] = "direct_uuid"
                    return info
            
            # Try exact title
            exact_id = await self._find_by_exact_title(identifier)
            if exact_id:
                info["resolved_id"] = exact_id
                info["resolution_method"] = "exact_title"
                return info
            
            # Try keyword search and collect candidates
            results = await self.lancedb_manager.search_work_items(
                query=identifier,
                search_type="keyword",
                limit=5
            )
            
            info["candidates"] = [
                {
                    "id": r.get("work_item", {}).get("id"),
                    "title": r.get("work_item", {}).get("title"),
                    "relevance_score": r.get("relevance_score", 0)
                }
                for r in results
            ]
            
            # Try to resolve via keyword search
            search_id = await self._find_by_keyword_search(identifier)
            if search_id:
                info["resolved_id"] = search_id
                info["resolution_method"] = "keyword_search"
            
            return info
            
        except Exception as e:
            info["error"] = str(e)
            return info