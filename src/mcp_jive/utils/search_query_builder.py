"""Search Query Builder for MCP Jive.

This module provides utilities for building robust search queries,
ranking results, and validating search functionality.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SearchScope(Enum):
    """Search scope options."""
    ALL = "all"
    WORK_ITEMS = "work_items"
    EXECUTIONS = "executions"
    NOTES = "notes"
    COMMENTS = "comments"
    ATTACHMENTS = "attachments"


class SearchOperator(Enum):
    """Search operators for query building."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    EXACT = "EXACT"
    FUZZY = "FUZZY"
    WILDCARD = "WILDCARD"


class SortOrder(Enum):
    """Sort order options."""
    RELEVANCE = "relevance"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"
    PRIORITY_DESC = "priority_desc"
    STATUS_ASC = "status_asc"


@dataclass
class SearchFilter:
    """Search filter configuration."""
    field: str
    operator: SearchOperator
    value: Any
    weight: float = 1.0


@dataclass
class SearchQuery:
    """Structured search query."""
    terms: List[str]
    filters: List[SearchFilter]
    scope: SearchScope
    sort_order: SortOrder
    limit: int = 50
    offset: int = 0
    include_archived: bool = False
    fuzzy_threshold: float = 0.8
    boost_recent: bool = True


@dataclass
class SearchResult:
    """Search result with ranking information."""
    item: Dict[str, Any]
    score: float
    relevance_factors: Dict[str, float]
    highlighted_fields: Dict[str, str]
    match_summary: str


class SearchQueryBuilder:
    """Builder for constructing robust search queries."""
    
    def __init__(self):
        self.query = SearchQuery(
            terms=[],
            filters=[],
            scope=SearchScope.ALL,
            sort_order=SortOrder.RELEVANCE
        )
        self._stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 
            'that', 'the', 'to', 'was', 'will', 'with'
        }
    
    def add_term(self, term: str, operator: SearchOperator = SearchOperator.AND) -> 'SearchQueryBuilder':
        """Add a search term.
        
        Args:
            term: Search term to add
            operator: How to combine with other terms
            
        Returns:
            Self for method chaining
        """
        if term and term.strip():
            cleaned_term = self._clean_term(term.strip())
            if cleaned_term:
                self.query.terms.append(cleaned_term)
        return self
    
    def add_terms(self, terms: List[str]) -> 'SearchQueryBuilder':
        """Add multiple search terms.
        
        Args:
            terms: List of search terms
            
        Returns:
            Self for method chaining
        """
        for term in terms:
            self.add_term(term)
        return self
    
    def add_filter(self, field: str, operator: SearchOperator, 
                   value: Any, weight: float = 1.0) -> 'SearchQueryBuilder':
        """Add a search filter.
        
        Args:
            field: Field to filter on
            operator: Filter operator
            value: Filter value
            weight: Weight for relevance scoring
            
        Returns:
            Self for method chaining
        """
        filter_obj = SearchFilter(field, operator, value, weight)
        self.query.filters.append(filter_obj)
        return self
    
    def set_scope(self, scope: SearchScope) -> 'SearchQueryBuilder':
        """Set search scope.
        
        Args:
            scope: Search scope
            
        Returns:
            Self for method chaining
        """
        self.query.scope = scope
        return self
    
    def set_sort_order(self, sort_order: SortOrder) -> 'SearchQueryBuilder':
        """Set sort order.
        
        Args:
            sort_order: Sort order
            
        Returns:
            Self for method chaining
        """
        self.query.sort_order = sort_order
        return self
    
    def set_limit(self, limit: int) -> 'SearchQueryBuilder':
        """Set result limit.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            Self for method chaining
        """
        self.query.limit = max(1, min(limit, 1000))  # Reasonable bounds
        return self
    
    def set_offset(self, offset: int) -> 'SearchQueryBuilder':
        """Set result offset for pagination.
        
        Args:
            offset: Number of results to skip
            
        Returns:
            Self for method chaining
        """
        self.query.offset = max(0, offset)
        return self
    
    def include_archived(self, include: bool = True) -> 'SearchQueryBuilder':
        """Include archived items in search.
        
        Args:
            include: Whether to include archived items
            
        Returns:
            Self for method chaining
        """
        self.query.include_archived = include
        return self
    
    def set_fuzzy_threshold(self, threshold: float) -> 'SearchQueryBuilder':
        """Set fuzzy matching threshold.
        
        Args:
            threshold: Fuzzy matching threshold (0.0 to 1.0)
            
        Returns:
            Self for method chaining
        """
        self.query.fuzzy_threshold = max(0.0, min(1.0, threshold))
        return self
    
    def boost_recent(self, boost: bool = True) -> 'SearchQueryBuilder':
        """Boost recent items in search results.
        
        Args:
            boost: Whether to boost recent items
            
        Returns:
            Self for method chaining
        """
        self.query.boost_recent = boost
        return self
    
    def parse_natural_query(self, query_string: str) -> 'SearchQueryBuilder':
        """Parse a natural language query string.
        
        Args:
            query_string: Natural language query
            
        Returns:
            Self for method chaining
        """
        if not query_string or not query_string.strip():
            return self
        
        # Extract quoted phrases
        quoted_phrases = re.findall(r'"([^"]+)"', query_string)
        for phrase in quoted_phrases:
            self.add_filter("content", SearchOperator.EXACT, phrase, weight=2.0)
        
        # Remove quoted phrases from main query
        cleaned_query = re.sub(r'"[^"]+"', '', query_string)
        
        # Extract field-specific searches (field:value)
        field_searches = re.findall(r'(\w+):(\S+)', cleaned_query)
        for field, value in field_searches:
            self.add_filter(field, SearchOperator.FUZZY, value, weight=1.5)
        
        # Remove field searches from main query
        cleaned_query = re.sub(r'\w+:\S+', '', cleaned_query)
        
        # Extract remaining terms
        terms = [term.strip() for term in cleaned_query.split() if term.strip()]
        self.add_terms(terms)
        
        return self
    
    def build(self) -> SearchQuery:
        """Build the final search query.
        
        Returns:
            Constructed SearchQuery object
        """
        # Validate and optimize query
        self._optimize_query()
        return self.query
    
    def _clean_term(self, term: str) -> str:
        """Clean and normalize a search term.
        
        Args:
            term: Raw search term
            
        Returns:
            Cleaned search term
        """
        # Remove special characters but keep alphanumeric and basic punctuation
        cleaned = re.sub(r'[^\w\s\-_.]', '', term.lower())
        
        # Remove stop words
        if cleaned.lower() in self._stop_words:
            return ""
        
        # Minimum length check
        if len(cleaned) < 2:
            return ""
        
        return cleaned
    
    def _optimize_query(self) -> None:
        """Optimize the query for better performance."""
        # Remove duplicate terms
        self.query.terms = list(dict.fromkeys(self.query.terms))
        
        # Remove empty terms
        self.query.terms = [term for term in self.query.terms if term.strip()]
        
        # Limit number of terms to prevent performance issues
        if len(self.query.terms) > 20:
            self.query.terms = self.query.terms[:20]
            logger.warning("Search query truncated to 20 terms for performance")
        
        # Remove duplicate filters
        unique_filters = []
        seen_filters = set()
        for filter_obj in self.query.filters:
            filter_key = (filter_obj.field, filter_obj.operator.value, str(filter_obj.value))
            if filter_key not in seen_filters:
                unique_filters.append(filter_obj)
                seen_filters.add(filter_key)
        self.query.filters = unique_filters


class SearchResultRanker:
    """Ranks and scores search results."""
    
    def __init__(self):
        self.field_weights = {
            'title': 3.0,
            'description': 2.0,
            'content': 1.5,
            'notes': 1.0,
            'tags': 2.5,
            'comments': 0.8
        }
        self.status_weights = {
            'active': 1.2,
            'in_progress': 1.1,
            'completed': 0.9,
            'blocked': 1.0,
            'cancelled': 0.5,
            'archived': 0.3
        }
        self.priority_weights = {
            'critical': 1.5,
            'high': 1.3,
            'medium': 1.0,
            'low': 0.8
        }
    
    def rank_results(self, results: List[Dict[str, Any]], 
                    query: SearchQuery) -> List[SearchResult]:
        """Rank search results by relevance.
        
        Args:
            results: Raw search results
            query: Original search query
            
        Returns:
            Ranked and scored search results
        """
        scored_results = []
        
        for item in results:
            score, factors, highlights = self._calculate_score(item, query)
            match_summary = self._generate_match_summary(item, query, factors)
            
            search_result = SearchResult(
                item=item,
                score=score,
                relevance_factors=factors,
                highlighted_fields=highlights,
                match_summary=match_summary
            )
            scored_results.append(search_result)
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x.score, reverse=True)
        
        return scored_results
    
    def _calculate_score(self, item: Dict[str, Any], 
                        query: SearchQuery) -> Tuple[float, Dict[str, float], Dict[str, str]]:
        """Calculate relevance score for an item.
        
        Args:
            item: Item to score
            query: Search query
            
        Returns:
            Tuple of (score, relevance_factors, highlighted_fields)
        """
        base_score = 0.0
        factors = {}
        highlights = {}
        
        # Text matching score
        text_score, text_highlights = self._calculate_text_score(item, query.terms)
        base_score += text_score
        factors['text_match'] = text_score
        highlights.update(text_highlights)
        
        # Filter matching score
        filter_score = self._calculate_filter_score(item, query.filters)
        base_score += filter_score
        factors['filter_match'] = filter_score
        
        # Status weight
        status = item.get('status', 'unknown').lower()
        status_weight = self.status_weights.get(status, 1.0)
        base_score *= status_weight
        factors['status_weight'] = status_weight
        
        # Priority weight
        priority = item.get('priority', 'medium').lower()
        priority_weight = self.priority_weights.get(priority, 1.0)
        base_score *= priority_weight
        factors['priority_weight'] = priority_weight
        
        # Recency boost
        if query.boost_recent:
            recency_boost = self._calculate_recency_boost(item)
            base_score *= recency_boost
            factors['recency_boost'] = recency_boost
        
        return base_score, factors, highlights
    
    def _calculate_text_score(self, item: Dict[str, Any], 
                             terms: List[str]) -> Tuple[float, Dict[str, str]]:
        """Calculate text matching score.
        
        Args:
            item: Item to score
            terms: Search terms
            
        Returns:
            Tuple of (score, highlighted_fields)
        """
        if not terms:
            return 0.0, {}
        
        total_score = 0.0
        highlights = {}
        
        for field, weight in self.field_weights.items():
            field_value = str(item.get(field, '')).lower()
            if not field_value:
                continue
            
            field_score = 0.0
            field_highlights = []
            
            for term in terms:
                term_lower = term.lower()
                
                # Exact match (highest score)
                if term_lower in field_value:
                    field_score += 2.0
                    field_highlights.append(term)
                
                # Fuzzy match (lower score)
                elif self._fuzzy_match(term_lower, field_value):
                    field_score += 1.0
                    field_highlights.append(term)
            
            # Apply field weight
            weighted_score = field_score * weight
            total_score += weighted_score
            
            # Store highlights
            if field_highlights:
                highlights[field] = self._highlight_text(field_value, field_highlights)
        
        return total_score, highlights
    
    def _calculate_filter_score(self, item: Dict[str, Any], 
                               filters: List[SearchFilter]) -> float:
        """Calculate filter matching score.
        
        Args:
            item: Item to score
            filters: Search filters
            
        Returns:
            Filter matching score
        """
        if not filters:
            return 0.0
        
        total_score = 0.0
        
        for filter_obj in filters:
            field_value = item.get(filter_obj.field)
            if field_value is None:
                continue
            
            match_score = 0.0
            
            if filter_obj.operator == SearchOperator.EXACT:
                if str(field_value).lower() == str(filter_obj.value).lower():
                    match_score = 2.0
            elif filter_obj.operator == SearchOperator.FUZZY:
                if self._fuzzy_match(str(filter_obj.value).lower(), str(field_value).lower()):
                    match_score = 1.5
            elif filter_obj.operator == SearchOperator.WILDCARD:
                if re.search(str(filter_obj.value), str(field_value), re.IGNORECASE):
                    match_score = 1.0
            
            total_score += match_score * filter_obj.weight
        
        return total_score
    
    def _calculate_recency_boost(self, item: Dict[str, Any]) -> float:
        """Calculate recency boost factor.
        
        Args:
            item: Item to calculate boost for
            
        Returns:
            Recency boost factor (1.0 = no boost)
        """
        try:
            # Try different date fields
            date_fields = ['updated_at', 'created_at', 'modified_at', 'last_activity']
            item_date = None
            
            for field in date_fields:
                if field in item and item[field]:
                    try:
                        item_date = datetime.fromisoformat(str(item[field]).replace('Z', '+00:00'))
                        break
                    except (ValueError, TypeError):
                        continue
            
            if not item_date:
                return 1.0  # No boost if no date found
            
            # Calculate days since last update
            days_old = (datetime.now() - item_date.replace(tzinfo=None)).days
            
            # Boost recent items (within 30 days)
            if days_old <= 7:
                return 1.3  # 30% boost for items within a week
            elif days_old <= 30:
                return 1.1  # 10% boost for items within a month
            elif days_old <= 90:
                return 1.0  # No boost for items within 3 months
            else:
                return 0.9  # Slight penalty for older items
        
        except Exception:
            return 1.0  # No boost on error
    
    def _fuzzy_match(self, term: str, text: str, threshold: float = 0.8) -> bool:
        """Check if term fuzzy matches text.
        
        Args:
            term: Search term
            text: Text to search in
            threshold: Similarity threshold
            
        Returns:
            True if fuzzy match found
        """
        # Simple fuzzy matching - check if term is substring or similar
        if term in text:
            return True
        
        # Check for partial matches
        if len(term) >= 3:
            for i in range(len(text) - len(term) + 1):
                substring = text[i:i + len(term)]
                similarity = self._calculate_similarity(term, substring)
                if similarity >= threshold:
                    return True
        
        return False
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not str1 or not str2:
            return 0.0
        
        # Simple Levenshtein-like similarity
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0
        
        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(str1, str2))
        return matches / max_len
    
    def _highlight_text(self, text: str, terms: List[str]) -> str:
        """Highlight search terms in text.
        
        Args:
            text: Text to highlight
            terms: Terms to highlight
            
        Returns:
            Text with highlighted terms
        """
        highlighted = text
        for term in terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(f'**{term}**', highlighted)
        return highlighted
    
    def _generate_match_summary(self, item: Dict[str, Any], 
                               query: SearchQuery, 
                               factors: Dict[str, float]) -> str:
        """Generate a summary of why this item matched.
        
        Args:
            item: Matched item
            query: Search query
            factors: Relevance factors
            
        Returns:
            Match summary string
        """
        summary_parts = []
        
        if factors.get('text_match', 0) > 0:
            summary_parts.append(f"Text match (score: {factors['text_match']:.1f})")
        
        if factors.get('filter_match', 0) > 0:
            summary_parts.append(f"Filter match (score: {factors['filter_match']:.1f})")
        
        if factors.get('status_weight', 1.0) != 1.0:
            status = item.get('status', 'unknown')
            summary_parts.append(f"Status: {status}")
        
        if factors.get('priority_weight', 1.0) != 1.0:
            priority = item.get('priority', 'medium')
            summary_parts.append(f"Priority: {priority}")
        
        if factors.get('recency_boost', 1.0) != 1.0:
            summary_parts.append("Recent activity")
        
        return "; ".join(summary_parts) if summary_parts else "General match"


class SearchValidator:
    """Validates search functionality and results."""
    
    def validate_query(self, query: SearchQuery) -> Dict[str, Any]:
        """Validate a search query.
        
        Args:
            query: Query to validate
            
        Returns:
            Validation result
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Check for empty query
        if not query.terms and not query.filters:
            validation_result['warnings'].append("Empty search query - will return all results")
        
        # Check term count
        if len(query.terms) > 20:
            validation_result['warnings'].append("Too many search terms - query may be slow")
        
        # Check limit bounds
        if query.limit > 1000:
            validation_result['errors'].append("Result limit too high (max: 1000)")
            validation_result['is_valid'] = False
        
        if query.limit < 1:
            validation_result['errors'].append("Result limit must be at least 1")
            validation_result['is_valid'] = False
        
        # Check offset bounds
        if query.offset < 0:
            validation_result['errors'].append("Offset cannot be negative")
            validation_result['is_valid'] = False
        
        # Check fuzzy threshold
        if not 0.0 <= query.fuzzy_threshold <= 1.0:
            validation_result['errors'].append("Fuzzy threshold must be between 0.0 and 1.0")
            validation_result['is_valid'] = False
        
        # Suggest improvements
        if len(query.terms) == 1 and len(query.terms[0]) < 3:
            validation_result['suggestions'].append("Consider using longer search terms for better results")
        
        if not query.filters and query.scope == SearchScope.ALL:
            validation_result['suggestions'].append("Consider adding filters or narrowing scope for more precise results")
        
        return validation_result
    
    def validate_results(self, results: List[SearchResult], 
                        query: SearchQuery) -> Dict[str, Any]:
        """Validate search results.
        
        Args:
            results: Search results to validate
            query: Original query
            
        Returns:
            Validation result
        """
        validation_result = {
            'is_valid': True,
            'result_count': len(results),
            'quality_metrics': {},
            'warnings': [],
            'suggestions': []
        }
        
        if not results:
            validation_result['warnings'].append("No results found")
            validation_result['suggestions'].append("Try broader search terms or remove filters")
            return validation_result
        
        # Calculate quality metrics
        scores = [r.score for r in results]
        validation_result['quality_metrics'] = {
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'score_variance': self._calculate_variance(scores)
        }
        
        # Check score distribution
        if validation_result['quality_metrics']['score_variance'] < 0.1:
            validation_result['warnings'].append("Low score variance - results may not be well differentiated")
        
        # Check for very low scores
        if validation_result['quality_metrics']['max_score'] < 1.0:
            validation_result['warnings'].append("Low relevance scores - consider adjusting search terms")
        
        return validation_result
    
    def validate_search_results(self, results: List[Dict[str, Any]], 
                                query_text: str) -> List[Dict[str, Any]]:
        """Validate and filter search results.
        
        Args:
            results: Raw search results
            query_text: Original query text
            
        Returns:
            Validated and filtered results
        """
        if not results:
            return results
        
        validated_results = []
        
        for result in results:
            # Basic validation
            if not isinstance(result, dict):
                continue
            
            # Must have required fields
            if 'id' not in result:
                continue
            
            # Must have some content
            has_content = any([
                result.get('title', '').strip(),
                result.get('description', '').strip(),
                result.get('content', '').strip()
            ])
            
            if not has_content:
                continue
            
            # Score validation
            score = result.get('score', 0)
            if score < 0:
                result['score'] = 0
            elif score > 10:  # Cap unreasonably high scores
                result['score'] = 10
            
            # Add relevance indicators
            result['relevance_indicators'] = self._get_relevance_indicators(
                result, query_text
            )
            
            validated_results.append(result)
        
        # Sort by score if not already sorted
        validated_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return validated_results
    
    def _get_relevance_indicators(self, result: Dict[str, Any], 
                                 query_text: str) -> List[str]:
        """Get relevance indicators for a search result.
        
        Args:
            result: Search result
            query_text: Original query
            
        Returns:
            List of relevance indicators
        """
        indicators = []
        query_lower = query_text.lower()
        
        # Check title match
        title = result.get('title', '').lower()
        if query_lower in title:
            indicators.append('title_match')
        
        # Check description match
        description = result.get('description', '').lower()
        if query_lower in description:
            indicators.append('description_match')
        
        # Check tag match
        tags = [tag.lower() for tag in result.get('tags', [])]
        if any(query_lower in tag for tag in tags):
            indicators.append('tag_match')
        
        # Check high score
        if result.get('score', 0) > 5:
            indicators.append('high_relevance')
        
        # Check priority
        priority = result.get('priority', '').lower()
        if priority in ['critical', 'high']:
            indicators.append('high_priority')
        
        return indicators
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Variance
        """
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance