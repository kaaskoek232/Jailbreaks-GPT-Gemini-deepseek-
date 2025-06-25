# Advanced Search Engine

## Overview

The Advanced Search Engine is a comprehensive multi-engine search system that integrates with the Unified MCP Agent System. It provides intelligent search capabilities across multiple sources including web search, academic papers, code repositories, and local files.

## Features

### 🔍 Multi-Engine Search
- **Brave Search**: Web search with privacy focus
- **GitHub**: Code repository search
- **Wikipedia**: Knowledge base search
- **ArXiv**: Academic paper search
- **StackOverflow**: Programming Q&A search

### 🚀 Advanced Capabilities
- **Parallel Processing**: Multi-threaded search across engines
- **Intelligent Caching**: 24-hour cache with MD5 hashing
- **Relevance Scoring**: Smart result ranking
- **Local File Search**: Search through local directories
- **Search History**: Track and analyze search patterns

### 💾 Caching System
- Persistent cache storage in JSON format
- Automatic cache invalidation (24 hours)
- Thread-safe cache operations
- MD5-based cache keys for efficiency

## Usage

### Basic Search
```python
from advanced_search_engine import search_engine

# Search across all engines
results = search_engine.search("python async programming", max_results=10)

# Search specific engines
results = search_engine.search("machine learning", 
                              engines=['wikipedia', 'arxiv'], 
                              max_results=5)
```

### Combi Fetch (Multi-Engine Results)
```python
# Get combined results from multiple engines
combi_results = search_engine.combi_fetch("AI agents", 
                                         engines=['brave', 'github', 'wikipedia'], 
                                         max_results=15)

for result in combi_results:
    print(f"[{result.source}] {result.title}")
    print(f"URL: {result.url}")
    print(f"Relevance: {result.relevance_score}")
    print(f"Snippet: {result.snippet[:200]}...")
    print("-" * 50)
```

### Local File Search
```python
# Search through local files
local_results = search_engine.folder_fetch("function", 
                                          folder_path="./my_project", 
                                          max_results=10)

for result in local_results:
    print(f"File: {result.title}")
    print(f"Path: {result.url}")
    print(f"Relevance: {result.relevance_score}")
    print(f"Context: {result.snippet}")
```

## Search Result Object

Each search result contains:
- `title`: Result title/name
- `url`: Source URL or file path
- `snippet`: Content preview
- `source`: Search engine source
- `relevance_score`: Calculated relevance (0.0-1.0)
- `timestamp`: When the result was retrieved

## Engine Status

Check the status of all search engines:
```python
status = search_engine.get_engine_status()
for engine, is_working in status.items():
    print(f"{engine}: {'✅' if is_working else '❌'}")
```

## Cache Management

```python
# Clear all cached results
search_engine.clear_cache()

# Get search history
history = search_engine.get_search_history()
for entry in history:
    print(f"Query: {entry['query']}")
    print(f"Engines: {entry['engines']}")
    print(f"Results: {entry['result_count']}")
    print(f"Time: {entry['timestamp']}")
```

## Integration with UI

The search engine integrates seamlessly with the Unified MCP Agent System UI:

1. **Search Tab**: Access all search functionality
2. **Engine Selection**: Choose which engines to use
3. **Result Display**: View formatted search results
4. **Cache Management**: Clear cache and view history
5. **Local Search**: Browse and search local folders

## Configuration

### API Keys (Optional)
Some engines may require API keys for enhanced functionality:
- Brave Search: No API key required
- GitHub: Optional for higher rate limits
- Wikipedia: No API key required
- ArXiv: No API key required
- StackOverflow: No API key required

### Rate Limiting
The search engine includes built-in rate limiting and error handling:
- Automatic retry on failures
- Timeout protection (10 seconds)
- Graceful degradation when engines are unavailable

## Performance

- **Parallel Processing**: All engines search simultaneously
- **Caching**: Reduces API calls and improves response time
- **Smart Filtering**: Only searches relevant engines
- **Memory Efficient**: Streams results without loading everything into memory

## Error Handling

The search engine gracefully handles:
- Network timeouts
- API rate limits
- Invalid responses
- Missing files
- Encoding issues

## Future Enhancements

Planned features:
- [ ] Semantic search capabilities
- [ ] Result clustering and deduplication
- [ ] Advanced filtering options
- [ ] Search result export
- [ ] Custom search engine integration
- [ ] Real-time search suggestions
- [ ] Search analytics dashboard

## Dependencies

```
requests>=2.28.0
urllib3>=1.26.0
lxml>=4.9.0
beautifulsoup4>=4.11.0
aiohttp>=3.8.0
asyncio-throttle>=1.0.0
```

## Testing

Run the built-in tests:
```bash
python advanced_search_engine.py
```

This will test basic search functionality across multiple engines.

## Contributing

To add a new search engine:

1. Create a new class inheriting from `SearchEngine`
2. Implement the `search()` method
3. Add the engine to the `engines` dictionary in `AdvancedSearchEngine`
4. Update the UI to include the new engine option

## License

This search engine is part of the Unified MCP Agent System and follows the same licensing terms. 