# Weaviate Vectorizer Implementation

## Overview

This document describes the implementation of Weaviate vectorizer support and automatic fallback mechanism for semantic search in the MCP Jive project.

## Features Implemented

### 1. Built-in Vectorizer Support
- **Text2Vec-Transformers**: Built-in transformer models (no external API required)
- **Text2Vec-OpenAI**: OpenAI embeddings (requires OPENAI_API_KEY)
- **Configurable**: Enable/disable vectorizer via environment variables

### 2. Automatic Search Fallback
- **Smart Fallback**: Automatically falls back to keyword search when semantic search fails
- **Configurable**: Enable/disable fallback via environment variables
- **Logging**: Detailed logging of search attempts and fallbacks

### 3. Environment Configuration
- **WEAVIATE_ENABLE_VECTORIZER**: Enable/disable vectorizer (default: true)
- **WEAVIATE_VECTORIZER_MODULE**: Choose vectorizer module (default: text2vec-transformers)
- **WEAVIATE_SEARCH_FALLBACK**: Enable/disable automatic fallback (default: true)

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable built-in vectorizer for semantic search capabilities
WEAVIATE_ENABLE_VECTORIZER=true

# Vectorizer module to use
# Options: text2vec-transformers, text2vec-openai
WEAVIATE_VECTORIZER_MODULE=text2vec-transformers

# Enable automatic fallback to keyword search when semantic search fails
WEAVIATE_SEARCH_FALLBACK=true
```

### Vectorizer Options

#### Text2Vec-Transformers (Recommended)
- **Pros**: No external API required, works offline, free
- **Cons**: Larger memory usage, slower startup
- **Use Case**: Development, testing, self-hosted deployments

```bash
WEAVIATE_VECTORIZER_MODULE=text2vec-transformers
```

#### Text2Vec-OpenAI
- **Pros**: High-quality embeddings, fast, low memory usage
- **Cons**: Requires OpenAI API key, costs money, needs internet
- **Use Case**: Production deployments with OpenAI access

```bash
WEAVIATE_VECTORIZER_MODULE=text2vec-openai
OPENAI_API_KEY=your_openai_api_key_here
```

## How It Works

### Search Flow

1. **Semantic Search Requested**
   ```python
   search_work_items(query="E-commerce Platform", search_type="semantic")
   ```

2. **Vectorizer Check**
   - If vectorizer enabled: Attempt semantic search using `near_text`
   - If vectorizer disabled: Skip to keyword search

3. **Fallback Logic**
   - If semantic search fails or returns 0 results
   - AND fallback is enabled
   - Automatically retry with keyword search using `bm25`

4. **Result Return**
   - Return results from successful search method
   - Log which method was used

### Code Implementation

```python
# Semantic search with fallback
if search_type == "semantic":
    try:
        results = collection.query.near_text(query=query, limit=limit)
        if results.objects:
            return format_results(results)
        else:
            logger.warning("Semantic search returned 0 results")
    except Exception as e:
        logger.warning(f"Semantic search failed: {e}")
    
    # Automatic fallback if enabled
    if self.config.weaviate_search_fallback:
        logger.info("Falling back to keyword search")
        search_type = "keyword"

# Keyword search
if search_type == "keyword":
    results = collection.query.bm25(query=query, limit=limit)
    return format_results(results)
```

## Testing

### Test Script

Run the included test script to verify configuration:

```bash
python3 test_vectorizer.py
```

### Expected Output

```
=== Test 1: Configuration Loading ===
Vectorizer enabled: True
Vectorizer module: text2vec-transformers
Search fallback: True

=== Test 2: Weaviate Initialization ===
✅ Weaviate connected successfully

=== Test 3: Collection Vectorizer Check ===
✅ WorkItem collection accessible

=== Test 4: Search Functionality ===
--- Testing Semantic Search ---
✅ Semantic search returned 1 results

--- Testing Keyword Search ---
✅ Keyword search returned 1 results

--- Testing Fallback Mechanism ---
✅ Fallback mechanism returned 0 results
```

### MCP Tool Testing

```bash
# Test semantic search (may fallback to keyword)
jive_search_work_items({
  "query": "E-commerce Platform Modernization",
  "search_type": "semantic",
  "limit": 5
})

# Test keyword search (direct)
jive_search_work_items({
  "query": "E-commerce Platform Modernization",
  "search_type": "keyword",
  "limit": 5
})
```

## Troubleshooting

### Semantic Search Always Returns 0 Results

**Cause**: Vectorizer not properly configured or collections created without vectorizer

**Solution**:
1. Check environment variables are set correctly
2. Restart MCP server to pick up new configuration
3. Delete Weaviate data directory to recreate collections with vectorizer:
   ```bash
   rm -rf data/weaviate
   ```
4. Restart server to recreate collections with vectorizer enabled

### Fallback Not Working

**Cause**: `WEAVIATE_SEARCH_FALLBACK=false` or server not restarted

**Solution**:
1. Set `WEAVIATE_SEARCH_FALLBACK=true` in `.env`
2. Restart MCP server

### Text2Vec-Transformers Startup Issues

**Cause**: Insufficient memory or network issues downloading models

**Solution**:
1. Increase available memory
2. Ensure internet connection for initial model download
3. Consider using `text2vec-openai` for production

### OpenAI Vectorizer Issues

**Cause**: Missing or invalid OpenAI API key

**Solution**:
1. Set valid `OPENAI_API_KEY` in `.env`
2. Verify API key has sufficient credits
3. Check network connectivity to OpenAI API

## Performance Considerations

### Memory Usage
- **Text2Vec-Transformers**: ~500MB-2GB depending on model
- **Text2Vec-OpenAI**: Minimal memory usage

### Startup Time
- **Text2Vec-Transformers**: 30-120 seconds (model download + loading)
- **Text2Vec-OpenAI**: <5 seconds

### Search Performance
- **Semantic Search**: Slower but more intelligent matching
- **Keyword Search**: Faster but requires exact keyword matches
- **Fallback**: Adds minimal overhead when semantic search succeeds

## Migration Guide

### From No Vectorizer to Vectorizer

1. **Update Configuration**
   ```bash
   WEAVIATE_ENABLE_VECTORIZER=true
   WEAVIATE_VECTORIZER_MODULE=text2vec-transformers
   WEAVIATE_SEARCH_FALLBACK=true
   ```

2. **Recreate Collections**
   ```bash
   # Stop server
   # Delete data directory
   rm -rf data/weaviate
   # Restart server (will recreate with vectorizer)
   ```

3. **Re-import Data**
   - Existing data will need to be re-imported to generate embeddings
   - Use sync tools to re-populate from files

### From External to Embedded Weaviate

1. **Update Configuration**
   ```bash
   WEAVIATE_USE_EMBEDDED=true
   WEAVIATE_ENABLE_VECTORIZER=true
   ```

2. **Export/Import Data**
   - Export data from external Weaviate
   - Import to new embedded instance

## Best Practices

### Development
- Use `text2vec-transformers` for offline development
- Enable fallback for robust search experience
- Use test script to verify configuration

### Production
- Consider `text2vec-openai` for better performance
- Monitor search performance and fallback rates
- Set appropriate memory limits

### Monitoring
- Check logs for fallback frequency
- Monitor memory usage with transformers
- Track search response times

## Files Modified

- `src/mcp_server/config.py`: Added vectorizer configuration
- `src/mcp_server/database.py`: Implemented vectorizer and fallback
- `.env.example`: Added vectorizer environment variables
- `test_vectorizer.py`: Test script for verification

## Future Enhancements

- **Hybrid Search**: Combine semantic and keyword search results
- **Custom Models**: Support for custom transformer models
- **Performance Metrics**: Track search performance and accuracy
- **Auto-tuning**: Automatically adjust search parameters based on results