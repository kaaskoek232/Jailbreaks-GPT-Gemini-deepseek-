#!/usr/bin/env python3

import requests
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib
import os
import re
from urllib.parse import quote_plus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchResult:
    def __init__(self, title: str, url: str, snippet: str, source: str, relevance_score: float = 0.0):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.relevance_score = relevance_score
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'source': self.source,
            'relevance_score': self.relevance_score,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        return f"[{self.source}] {self.title} - {self.url}"

class SearchCache:
    def __init__(self, cache_file: str = "search_cache.json"):
        self.cache_file = cache_file
        self.cache = self.load_cache()
        self.cache_lock = threading.Lock()
    
    def load_cache(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
        return {}
    
    def save_cache(self):
        try:
            with self.cache_lock:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def get_cache_key(self, query: str, engine: str) -> str:
        return hashlib.md5(f"{query}_{engine}".encode()).hexdigest()
    
    def get(self, query: str, engine: str) -> Optional[List[Dict[str, Any]]]:
        cache_key = self.get_cache_key(query, engine)
        cached_data = self.cache.get(cache_key)
        if cached_data:
            # Check if cache is still valid (24 hours)
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if (datetime.now() - cache_time).total_seconds() < 86400:
                return cached_data['results']
        return None
    
    def set(self, query: str, engine: str, results: List[Dict[str, Any]]):
        cache_key = self.get_cache_key(query, engine)
        self.cache[cache_key] = {
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        self.save_cache()

class SearchEngine:
    def __init__(self, name: str, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.name = name
        self.base_url = base_url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Base search method - should be overridden by specific engines"""
        raise NotImplementedError
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[requests.Response]:
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Error making request to {self.name}: {e}")
            return None

class BraveSearchEngine(SearchEngine):
    def __init__(self):
        super().__init__("Brave", "https://api.search.brave.com/res/v1/web/search")
    
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        params = {
            'q': query,
            'count': min(max_results, 20)
        }
        
        response = self._make_request(self.base_url, params)
        if not response:
            return []
        
        try:
            data = response.json()
            results = []
            
            for item in data.get('web', {}).get('results', [])[:max_results]:
                result = SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    snippet=item.get('description', ''),
                    source='Brave',
                    relevance_score=float(item.get('score', 0))
                )
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error parsing Brave results: {e}")
            return []

class GitHubSearchEngine(SearchEngine):
    def __init__(self):
        super().__init__("GitHub", "https://api.github.com/search/repositories")
    
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': min(max_results, 30)
        }
        
        response = self._make_request(self.base_url, params)
        if not response:
            return []
        
        try:
            data = response.json()
            results = []
            
            for item in data.get('items', [])[:max_results]:
                result = SearchResult(
                    title=f"{item.get('full_name', '')} - {item.get('description', '')}",
                    url=item.get('html_url', ''),
                    snippet=item.get('description', ''),
                    source='GitHub',
                    relevance_score=float(item.get('stargazers_count', 0)) / 1000
                )
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error parsing GitHub results: {e}")
            return []

class WikipediaSearchEngine(SearchEngine):
    def __init__(self):
        super().__init__("Wikipedia", "https://en.wikipedia.org/api/rest_v1/page/summary")
    
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        # First, search for pages
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query,
            'srlimit': min(max_results, 10)
        }
        
        response = self._make_request(search_url, search_params)
        if not response:
            return []
        
        try:
            data = response.json()
            results = []
            
            for item in data.get('query', {}).get('search', [])[:max_results]:
                page_title = item.get('title', '')
                page_id = item.get('pageid', '')
                
                # Get page summary
                summary_url = f"{self.base_url}/{quote_plus(page_title)}"
                summary_response = self._make_request(summary_url)
                
                if summary_response:
                    try:
                        summary_data = summary_response.json()
                        result = SearchResult(
                            title=page_title,
                            url=summary_data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                            snippet=summary_data.get('extract', ''),
                            source='Wikipedia',
                            relevance_score=float(item.get('score', 0)) / 100
                        )
                        results.append(result)
                    except:
                        # Fallback to basic info
                        result = SearchResult(
                            title=page_title,
                            url=f"https://en.wikipedia.org/wiki/{quote_plus(page_title)}",
                            snippet=item.get('snippet', ''),
                            source='Wikipedia',
                            relevance_score=float(item.get('score', 0)) / 100
                        )
                        results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error parsing Wikipedia results: {e}")
            return []

class ArxivSearchEngine(SearchEngine):
    def __init__(self):
        super().__init__("ArXiv", "http://export.arxiv.org/api/query")
    
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        params = {
            'search_query': f'all:"{query}"',
            'start': 0,
            'max_results': min(max_results, 20),
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        response = self._make_request(self.base_url, params)
        if not response:
            return []
        
        try:
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            results = []
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry')[:max_results]:
                title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                summary_elem = entry.find('.//{http://www.w3.org/2005/Atom}summary')
                id_elem = entry.find('.//{http://www.w3.org/2005/Atom}id')
                
                title = title_elem.text if title_elem is not None and title_elem.text else "No Title"
                summary = summary_elem.text if summary_elem is not None and summary_elem.text else "No Summary"
                url = id_elem.text if id_elem is not None and id_elem.text else ""
                
                result = SearchResult(
                    title=title,
                    url=url,
                    snippet=summary,
                    source='ArXiv',
                    relevance_score=0.8  # Default score for academic papers
                )
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error parsing ArXiv results: {e}")
            return []

class StackOverflowSearchEngine(SearchEngine):
    def __init__(self):
        super().__init__("StackOverflow", "https://api.stackexchange.com/2.3/search/advanced")
    
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        params = {
            'order': 'desc',
            'sort': 'relevance',
            'q': query,
            'site': 'stackoverflow',
            'pagesize': min(max_results, 20)
        }
        
        response = self._make_request(self.base_url, params)
        if not response:
            return []
        
        try:
            data = response.json()
            results = []
            
            for item in data.get('items', [])[:max_results]:
                result = SearchResult(
                    title=item.get('title', ''),
                    url=item.get('link', ''),
                    snippet=item.get('body', '')[:200] + '...' if len(item.get('body', '')) > 200 else item.get('body', ''),
                    source='StackOverflow',
                    relevance_score=float(item.get('score', 0)) / 10
                )
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error parsing StackOverflow results: {e}")
            return []

class AdvancedSearchEngine:
    def __init__(self):
        self.cache = SearchCache()
        self.engines = {
            'brave': BraveSearchEngine(),
            'github': GitHubSearchEngine(),
            'wikipedia': WikipediaSearchEngine(),
            'arxiv': ArxivSearchEngine(),
            'stackoverflow': StackOverflowSearchEngine()
        }
        self.search_history = []
    
    def search(self, query: str, engines: Optional[List[str]] = None, max_results: int = 10) -> Dict[str, List[SearchResult]]:
        """Perform search across multiple engines"""
        if engines is None:
            engines = list(self.engines.keys())
        
        results = {}
        threads = []
        
        def search_engine(engine_name: str):
            if engine_name in self.engines:
                # Check cache first
                cached_results = self.cache.get(query, engine_name)
                if cached_results:
                    results[engine_name] = [SearchResult(**r) for r in cached_results]
                    return
                
                # Perform search
                engine_results = self.engines[engine_name].search(query, max_results)
                results[engine_name] = engine_results
                
                # Cache results
                self.cache.set(query, engine_name, [r.to_dict() for r in engine_results])
        
        # Start threads for parallel search
        for engine in engines:
            if engine in self.engines:
                thread = threading.Thread(target=search_engine, args=(engine,))
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Add to search history
        self.search_history.append({
            'query': query,
            'engines': engines,
            'timestamp': datetime.now().isoformat(),
            'result_count': sum(len(r) for r in results.values())
        })
        
        return results
    
    def combi_fetch(self, query: str, engines: Optional[List[str]] = None, max_results: int = 10) -> List[SearchResult]:
        """Fetch results from multiple engines and combine them intelligently"""
        if engines is None:
            engines = list(self.engines.keys())
            
        engine_results = self.search(query, engines, max_results)
        
        # Combine all results
        all_results = []
        for engine_name, results in engine_results.items():
            for result in results:
                result.source = f"{engine_name.title()}: {result.source}"
                all_results.append(result)
        
        # Sort by relevance score
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return all_results[:max_results]
    
    def folder_fetch(self, query: str, folder_path: str, max_results: int = 10) -> List[SearchResult]:
        """Search through local files in a folder"""
        if not os.path.exists(folder_path):
            return []
        
        results = []
        query_lower = query.lower()
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.txt', '.md', '.py', '.js', '.html', '.css', '.json')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if query_lower in content.lower():
                                # Calculate relevance score
                                content_lower = content.lower()
                                relevance = content_lower.count(query_lower) / len(content_lower) * 100
                                
                                # Extract snippet
                                start_pos = content_lower.find(query_lower)
                                snippet_start = max(0, start_pos - 100)
                                snippet_end = min(len(content), start_pos + len(query_lower) + 100)
                                snippet = content[snippet_start:snippet_end]
                                
                                result = SearchResult(
                                    title=f"File: {file}",
                                    url=f"file://{file_path}",
                                    snippet=snippet,
                                    source='Local Files',
                                    relevance_score=min(relevance, 1.0)
                                )
                                results.append(result)
                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {e}")
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]
    
    def get_search_history(self) -> List[Dict[str, Any]]:
        """Get search history"""
        return self.search_history[-50:]  # Last 50 searches
    
    def clear_cache(self):
        """Clear search cache"""
        self.cache.cache.clear()
        self.cache.save_cache()
    
    def get_engine_status(self) -> Dict[str, bool]:
        """Check status of all search engines"""
        status = {}
        for engine_name, engine in self.engines.items():
            try:
                # Simple test query
                test_results = engine.search("test", 1)
                status[engine_name] = len(test_results) >= 0
            except Exception as e:
                logger.error(f"Engine {engine_name} test failed: {e}")
                status[engine_name] = False
        return status

# Global search engine instance
search_engine = AdvancedSearchEngine()

if __name__ == "__main__":
    # Test the search engine
    print("Testing Advanced Search Engine...")
    
    # Test basic search
    results = search_engine.search("python async programming", ['brave', 'github'], 5)
    for engine, engine_results in results.items():
        print(f"\n{engine.upper()} Results:")
        for result in engine_results:
            print(f"  - {result}")
    
    # Test combi fetch
    print("\n\nCombi Fetch Results:")
    combi_results = search_engine.combi_fetch("machine learning", ['wikipedia', 'arxiv'], 5)
    for result in combi_results:
        print(f"  - {result}")
