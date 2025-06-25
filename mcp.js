

import { Server
} from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport
} from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs/promises';
import path from 'path';
import fetch from 'node-fetch';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';

class CustomMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'custom-mcp-server',
        version: '1.0.0',
    },
    {
        capabilities: {
          tools: {}
      },
    }
    );

    this.memory = new Map();
    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {        tools: [
          {
            name: 'memory_store',
            description: 'Store information in persistent memory',
            inputSchema: {
              type: 'object',
              properties: {
                key: {
                  type: 'string',
                  description: 'Memory key identifier',
                },
                value: {
                  type: 'string',
                  description: 'Value to store in memory',
                },
              },
              required: ['key', 'value'
              ],
            },
          },
          {
            name: 'memory_retrieve',
            description: 'Retrieve information from persistent memory',
            inputSchema: {
              type: 'object',
              properties: {
                key: {
                  type: 'string',
                  description: 'Memory key to retrieve',
                },
              },
              required: ['key'
              ],
            },
          },
          {
            name: 'memory_list',
            description: 'List all stored memory keys',
            inputSchema: {
              type: 'object',
              properties: {},
            },
          },
          {
            name: 'file_read',
            description: 'Read file contents from the workspace',
            inputSchema: {
              type: 'object',
              properties: {
                path: {
                  type: 'string',
                  description: 'Relative file path from workspace root',
                },
              },
              required: ['path'
              ],
            },
          },
          {
            name: 'file_write',
            description: 'Write content to a file in the workspace',
            inputSchema: {
              type: 'object',
              properties: {
                path: {
                  type: 'string',
                  description: 'Relative file path from workspace root',
                },
                content: {
                  type: 'string',
                  description: 'Content to write to the file',
                },
              },
              required: ['path', 'content'
              ],
            },
          },
          {
            name: 'file_list',
            description: 'List files and directories in the workspace',            inputSchema: {
              type: 'object',
              properties: {
                path: {
                  type: 'string',
                  description: 'Relative directory path from workspace root (default: ".")',
                  default: '.',
                },
              },
            },
          },
          {
            name: 'fetch_model_config',
            description: 'Fetch model or config files using Brave search with intelligent source detection',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query for model/config (e.g., "SAM 2.1 HQ config", "YOLO12 download")',
                },
                file_type: {
                  type: 'string',
                  description: 'Type of file to fetch (model, config, checkpoint, etc.)',
                  enum: ['model', 'config', 'checkpoint', 'weights', 'yaml', 'json', 'any'
                  ],
                  default: 'any'
                },
                repository_type: {
                  type: 'string',
                  description: 'Preferred repository type',
                  enum: ['huggingface', 'github', 'civitai', 'any'
                  ],
                  default: 'any'
                }
              },
              required: ['query'
              ],
            },
          },
          {
            name: 'combined_search',
            description: 'Comprehensive search combining Brave web search and Context7 documentation',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query to run across both web and documentation sources',
                },
                search_scope: {
                  type: 'string',
                  description: 'Scope of search results',
                  enum: ['both', 'web_only', 'docs_only'
                  ],  
                  default: 'both'
                },
                focus_area: {
                  type: 'string',
                  description: 'Focus area for enhanced results',
                  enum: ['technical', 'tutorials', 'downloads', 'documentation', 'general'
                  ],
                  default: 'general'
                }
              },
              required: ['query'
              ],
            },
          },
        ],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args
      } = request.params;

      try {        switch (name) {
          
          case 'memory_store':
            return await this.handleMemoryStore(args.key, args.value);
          
          case 'memory_retrieve':
            return await this.handleMemoryRetrieve(args.key);
          
          case 'memory_list':
            return await this.handleMemoryList();
          
          case 'file_read':
            return await this.handleFileRead(args.path);
            case 'file_write':
            return await this.handleFileWrite(args.path, args.content);
          
          case 'file_list':
            return await this.handleFileList(args.path || '.');
          
          case 'fetch_model_config':
            return await this.handleFetchModelConfig(args.query, args.file_type, args.repository_type);
          
          case 'combined_search':
            return await this.handleCombinedSearch(args.query, args.search_scope, args.focus_area);
          
          default:
            throw new Error(`Unknown tool: ${name
          }`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error executing ${name
              }: ${error.message
              }`,
            },
          ],
          isError: true,
        };
      }
    });
  }
  async handleContext7Search(query) {
    try {
      console.log(`📚 Context7 Search: ${query
      } (MOCK - API not yet available)`);
      
      // Mock response until Context7 API becomes available
      const mockResults = [
        {
          title: `Documentation for: ${query
          }`,
          content: `Here are the search results for "${query}". This is a mock response from Context7 search. The actual Context7 API integration will be enabled when available via @upstash/context7-mcp.`,
          url: `https: //docs.example.com/search?q=${encodeURIComponent(query)}`,
          source: 'Context7 Documentation (Mock)',
          relevance: 0.95
        },
        {
          title: `Technical Reference: ${query
          }`,
          content: `Technical documentation and API references for "${query}". This will be replaced with real Context7 results when the service becomes available.`,
          url: `https: //docs.example.com/api/search?q=${encodeURIComponent(query)}`,
          source: 'Technical Docs (Mock)',
          relevance: 0.88
        }
      ];
      
      let responseText = `📚 Context7 Documentation Search Results for "${query}":\n`;
      responseText += `⚠️ Note: Using mock data - Context7 API not yet available\n`;
      responseText += `🔄 Will be enabled via: npx -y @upstash/context7-mcp\n\n`;
      
      mockResults.forEach((result, index) => {
        responseText += `${index + 1
        }. **${result.title
        }**\n`;
        responseText += `   📊 Relevance: ${(result.relevance * 100).toFixed(1)
        }%\n`;
        responseText += `   📝 ${result.content
        }\n`;
        responseText += `   🔗 ${result.url
        }\n`;
        responseText += `   📚 Source: ${result.source
        }\n\n`;
      });
      
      return {
        content: [
          {
            type: 'text',
            text: responseText,
          },
        ],
      };
    } catch (error) {
      console.error(`❌ Context7 search error: ${error.message
      }`);
      throw new Error(`Context7 search failed: ${error.message
      }`);
    }
  }
  async handleWebSearch(query) {
    try {
      console.log(`🔍 Brave Search: ${query
      }`);
      
      // Brave Search API configuration
      const BRAVE_API_KEY = 'BSAETbHcrj5O1Kju1aSWt-_BdhltP1x';
      const BRAVE_API_URL = 'https: //api.search.brave.com/res/v1/web/search';
      // Prepare search parameters
      const searchParams = new URLSearchParams({
        q: query,
        count: '10',
        offset: '0',
        mkt: 'en-US',
        safesearch: 'moderate',
        search_lang: 'en',
        country: 'US',
        spellcheck: '1',
        result_filter: 'web',
        goggles_id: '',
        units: 'metric',
        extra_snippets: '1',
        summary: '1'
      });
      
      const response = await fetch(`${BRAVE_API_URL
      }?${searchParams
      }`,
      {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Accept-Encoding': 'gzip',
          'X-Subscription-Token': BRAVE_API_KEY,
          'User-Agent': 'DEMONCORE-QUANTUM-SYSTEM/1.0'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Brave API error: ${response.status
        } ${response.statusText
        }`);
      }
      
      const data = await response.json();
      console.log(`✅ Brave Search: ${data.web?.results?.length || 0
      } results`);
      
      // Format results
      const results = data.web?.results || [];
      const formattedResults = results.map(result => ({
        title: result.title || 'No title',
        snippet: result.snippet || result.description || 'No description',
        url: result.url || '',
        age: result.age || 'Unknown',
        language: result.language || 'en',
        family_friendly: result.family_friendly || true
      }));
      
      // Include search summary if available
      let responseText = `🔍 Brave Search Results for "${query}":\n`;
      responseText += `Found ${formattedResults.length
      } results\n\n`;
      
      if (data.summarizer?.key) {
        responseText += `📋 Summary: ${data.summarizer.key
        }\n\n`;
      }
      
      formattedResults.forEach((result, index) => {
        responseText += `${index + 1
        }. **${result.title
        }**\n`;
        responseText += `   ${result.snippet
        }\n`;
        responseText += `   🔗 ${result.url
        }\n`;
        if (result.age !== 'Unknown') {
          responseText += `   📅 ${result.age
          }\n`;
        }
        responseText += '\n';
      });
      
      return {
        content: [
          {
            type: 'text',
            text: responseText,
          },
        ],
      };
    } catch (error) {      console.error(`❌ Brave Search error: ${error.message
      }`);
      throw new Error(`Brave Search failed: ${error.message
      }`);
    }
  }

  async handleFetchModelConfig(query, fileType = 'any', repositoryType = 'any') {
    try {
      console.log(`🔄 Fetch Model/Config: ${query
      } (${fileType
      }, ${repositoryType
      })`);
      
      // Enhanced search query based on file type and repository
      let enhancedQuery = query;
      
      if (fileType !== 'any') {
        enhancedQuery += ` ${fileType
        }`;
      }
      
      if (repositoryType !== 'any') {
        enhancedQuery += ` site:${this.getRepositoryDomain(repositoryType)
        }`;
      }
      // Add specific terms for better model/config finding
      const searchTerms = [
        'download', 'checkpoint', 'weights', 'model', 'config',
        'huggingface.co', 'github.com', 'civitai.com'
      ];
      
      if (!searchTerms.some(term => enhancedQuery.toLowerCase().includes(term))) {
        enhancedQuery += ' download';
      }
      
      console.log(`🔍 Enhanced query: ${enhancedQuery
      }`);
      
      // Use Brave search to find relevant sources
      const searchResults = await this.performBraveSearch(enhancedQuery);
      
      // Filter and rank results based on relevance for model/config files
      const filteredResults = this.filterModelConfigResults(searchResults, fileType, repositoryType);
      
      // Format response
      let responseText = `🎯 Model/Config Fetch Results for "${query}":\n`;
      responseText += `File Type: ${fileType
      } | Repository: ${repositoryType
      }\n`;
      responseText += `Found ${filteredResults.length
      } relevant sources\n\n`;
      
      filteredResults.forEach((result, index) => {
        responseText += `${index + 1
        }. **${result.title
        }**\n`;
        responseText += `   📊 Relevance: ${result.relevanceScore
        }/10\n`;
        responseText += `   📝 ${result.snippet
        }\n`;
        responseText += `   🔗 ${result.url
        }\n`;
        responseText += `   🏷️ Type: ${result.detectedType
        }\n`;
        responseText += `   🏪 Source: ${result.repository
        }\n`;
        if (result.directDownload) {
          responseText += `   ⬇️ Direct Download: ${result.directDownload
          }\n`;
        }
        responseText += '\n';
      });
      
      if (filteredResults.length === 0) {
        responseText += '⚠️ No relevant model/config sources found. Try refining your search query.\n';
        responseText += '\n📝 Suggestions:\n';
        responseText += '- Include specific model version numbers\n';
        responseText += '- Add terms like "checkpoint",
        "weights",
        "config"\n';
        responseText += '- Specify the framework (pytorch, tensorflow, onnx)\n';
      }
      
      return {
        content: [
          {
            type: 'text',
            text: responseText,
          },
        ],
      };
    } catch (error) {
      console.error(`❌ Model/Config fetch error: ${error.message
      }`);
      throw new Error(`Model/Config fetch failed: ${error.message
      }`);
    }
  }

  getRepositoryDomain(repositoryType) {
    const domains = {
      'huggingface': 'huggingface.co',
      'github': 'github.com',
      'civitai': 'civitai.com'
    };
    return domains[repositoryType
    ] || '';
  }

  async performBraveSearch(query) {
    const BRAVE_API_KEY = 'BSAETbHcrj5O1Kju1aSWt-_BdhltP1x';
    const BRAVE_API_URL = 'https: //api.search.brave.com/res/v1/web/search';
    
    const searchParams = new URLSearchParams({
      q: query,
      count: '15',
      offset: '0',
      mkt: 'en-US',
      safesearch: 'moderate',
      search_lang: 'en',
      country: 'US',
      spellcheck: '1',
      result_filter: 'web',
      units: 'metric',
      extra_snippets: '1'
    });
    
    const response = await fetch(`${BRAVE_API_URL
    }?${searchParams
    }`,
    {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': BRAVE_API_KEY,
        'User-Agent': 'DEMONCORE-QUANTUM-SYSTEM/1.0'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Brave API error: ${response.status
      } ${response.statusText
      }`);
    }
    
    const data = await response.json();
    return data.web?.results || [];
  }

  filterModelConfigResults(results, fileType, repositoryType) {
    return results.map(result => {
      const url = result.url.toLowerCase();
      const title = result.title.toLowerCase();
      const snippet = (result.snippet || '').toLowerCase();
      const combined = `${title
      } ${snippet
      } ${url
      }`;
      
      // Calculate relevance score
      let relevanceScore = 0;
      
      // Repository preference scoring
      if (repositoryType !== 'any') {
        const domain = this.getRepositoryDomain(repositoryType);
        if (url.includes(domain)) relevanceScore += 3;
      } else {
        // Boost known good repositories
        if (url.includes('huggingface.co')) relevanceScore += 2;
        if (url.includes('github.com')) relevanceScore += 2;
        if (url.includes('civitai.com')) relevanceScore += 1;
      }
      // File type scoring
      const fileExtensions = {
        'model': ['.bin', '.safetensors', '.ckpt', '.pth', '.pt', '.pb', '.onnx'
        ],
        'config': ['.json', '.yaml', '.yml', '.cfg', '.ini'
        ],
        'checkpoint': ['.ckpt', '.pth', '.pt', '.safetensors'
        ],
        'weights': ['.bin', '.safetensors', '.pth', '.pt'
        ],
        'yaml': ['.yaml', '.yml'
        ],
        'json': ['.json'
        ]
      };
      
      if (fileType !== 'any' && fileExtensions[fileType
      ]) {
        const hasExtension = fileExtensions[fileType
        ].some(ext => combined.includes(ext));
        if (hasExtension) relevanceScore += 2;
      }
      // Content relevance scoring
      const relevantTerms = [
        'download', 'checkpoint', 'weights', 'model', 'config',
        'pretrained', 'pytorch', 'tensorflow', 'onnx', 'safetensors'
      ];
      
      relevantTerms.forEach(term => {
        if (combined.includes(term)) relevanceScore += 0.5;
      });
      
      // Detect file type and repository
      let detectedType = 'unknown';
      let repository = 'unknown';
      
      if (url.includes('huggingface.co')) repository = 'HuggingFace';
      else if (url.includes('github.com')) repository = 'GitHub';
      else if (url.includes('civitai.com')) repository = 'CivitAI';
      
      if (combined.includes('.bin') || combined.includes('.safetensors')) detectedType = 'model';
      else if (combined.includes('.json') || combined.includes('.yaml')) detectedType = 'config';
      else if (combined.includes('.ckpt') || combined.includes('.pth')) detectedType = 'checkpoint';
      
      // Look for direct download links
      let directDownload = null;
      if (url.includes('/resolve/main/') || url.includes('/download/') || url.includes('/releases/')) {
        directDownload = result.url;
      }
      
      return {
        ...result,
        relevanceScore: Math.min(10, Math.round(relevanceScore)),
        detectedType,
        repository,
        directDownload
      };
    })
    .filter(result => result.relevanceScore > 0)
    .sort((a, b) => b.relevanceScore - a.relevanceScore)
    .slice(0,
    10); // Top 10 results
  }

  async handleMemoryStore(key, value) {
    this.memory.set(key,
    {
      value,
      timestamp: new Date().toISOString(),
    });
    
    return {
      content: [
        {
          type: 'text',
          text: `✅ Stored in memory:\nKey: "${key}"\nValue: "${value}"\nTimestamp: ${new Date().toISOString()
          }`,
        },
      ],
    };
  }

  async handleMemoryRetrieve(key) {
    const item = this.memory.get(key);
    
    if (!item) {
      return {
        content: [
          {
            type: 'text',
            text: `❌ Key "${key}" not found in memory.`,
          },
        ],
      };
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `✅ Retrieved from memory:\nKey: "${key}"\nValue: "${item.value}"\nStored: ${item.timestamp
          }`,
        },
      ],
    };
  }

  async handleMemoryList() {
    const keys = Array.from(this.memory.keys());
    
    if (keys.length === 0) {
      return {
        content: [
          {
            type: 'text',
            text: '📝 Memory is empty. No keys stored.',
          },
        ],
      };
    }
    
    const memoryList = keys.map(key => {
      const item = this.memory.get(key);
      return `• ${key
      }: "${item.value}" (${item.timestamp
      })`;
    }).join('\n');
    
    return {
      content: [
        {
          type: 'text',
          text: `📝 Memory contents (${keys.length
          } items):\n\n${memoryList
          }`,
        },
      ],
    };
  }

  async handleFileRead(filePath) {
    try {
      const workspaceRoot = process.cwd();
      const fullPath = path.resolve(workspaceRoot, filePath);
      
      // Security check: ensure path is within workspace
      if (!fullPath.startsWith(workspaceRoot)) {
        throw new Error('Access denied: Path is outside workspace');
      }
      
      const content = await fs.readFile(fullPath, 'utf-8');
      const stats = await fs.stat(fullPath);
      
      return {
        content: [
          {
            type: 'text',
            text: `📄 File: ${filePath
            }\nSize: ${stats.size
            } bytes\nModified: ${stats.mtime.toISOString()
            }\n\n--- Content ---\n${content
            }`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to read file "${filePath}": ${error.message
      }`);
    }
  }

  async handleFileWrite(filePath, content) {
    try {
      const workspaceRoot = process.cwd();
      const fullPath = path.resolve(workspaceRoot, filePath);
      
      // Security check: ensure path is within workspace
      if (!fullPath.startsWith(workspaceRoot)) {
        throw new Error('Access denied: Path is outside workspace');
      }
      // Ensure directory exists
      const dir = path.dirname(fullPath);
      await fs.mkdir(dir,
      { recursive: true
      });
      
      await fs.writeFile(fullPath, content, 'utf-8');
      const stats = await fs.stat(fullPath);
      
      return {
        content: [
          {
            type: 'text',
            text: `✅ Successfully wrote to "${filePath}"\nSize: ${stats.size
            } bytes\nModified: ${stats.mtime.toISOString()
            }`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to write file "${filePath}": ${error.message
      }`);
    }
  }

  async handleFileList(dirPath) {
    try {
      const workspaceRoot = process.cwd();
      const fullPath = path.resolve(workspaceRoot, dirPath);
      
      // Security check: ensure path is within workspace
      if (!fullPath.startsWith(workspaceRoot)) {
        throw new Error('Access denied: Path is outside workspace');
      }
      
      const entries = await fs.readdir(fullPath,
      { withFileTypes: true
      });
      
      const files = [];
      const directories = [];
      
      for (const entry of entries) {
        if (entry.isDirectory()) {
          directories.push(`📁 ${entry.name
          }/`);
        } else {
          const stats = await fs.stat(path.join(fullPath, entry.name));
          files.push(`📄 ${entry.name
          } (${stats.size
          } bytes)`);
        }
      }
      
      const listing = [
        ...directories.sort(),
        ...files.sort(),
      ].join('\n');
      
      return {
        content: [
          {
            type: 'text',
            text: `📂 Directory listing: ${dirPath
            }\n\n${listing || '(empty directory)'
            }`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to list directory "${dirPath}": ${error.message
      }`);
    }
  }

  async handleCombinedSearch(query, searchScope = 'both', focusArea = 'general') {
    try {
      console.log(`🔍📚 Combined Search: ${query
      } (${searchScope
      }, ${focusArea
      })`);
      
      const results = {
        web: [],
        docs: [],
        combined: []
      };
      
      // Execute searches based on scope
      if (searchScope === 'both' || searchScope === 'web_only') {
        try {
          const webResults = await this.performBraveSearch(query, focusArea);
          results.web = this.formatWebResults(webResults, focusArea);
        } catch (error) {
          console.error(`❌ Web search failed: ${error.message
          }`);
          results.web = [
            { error: `Web search failed: ${error.message
              }`
            }
          ];
        }
      }
      
      if (searchScope === 'both' || searchScope === 'docs_only') {
        try {
          const docResults = await this.performContext7Search(query, focusArea);
          results.docs = docResults;
        } catch (error) {
          console.error(`❌ Documentation search failed: ${error.message
          }`);
          results.docs = [
            { error: `Documentation search failed: ${error.message
              }`
            }
          ];
        }
      }
      // Combine and deduplicate results
      results.combined = this.combineSearchResults(results.web, results.docs, focusArea);
      
      // Format comprehensive response
      let responseText = `🔍📚 Combined Search Results for "${query}":\n`;
      responseText += `Scope: ${searchScope
      } | Focus: ${focusArea
      }\n`;
      responseText += `Found ${results.combined.length
      } total results\n\n`;
      
      if (results.combined.length === 0) {
        responseText += '⚠️ No results found. Try:\n';
        responseText += '- Different search terms\n';
        responseText += '- Broader focus area\n';
        responseText += '- Different search scope\n';
      } else {
        results.combined.forEach((result, index) => {
          responseText += `${index + 1
          }. **${result.title
          }**\n`;
          responseText += `   🏷️ Source: ${result.source
          } | Relevance: ${result.relevance
          }/10\n`;
          responseText += `   📝 ${result.snippet
          }\n`;
          responseText += `   🔗 ${result.url
          }\n`;
          if (result.directDownload) {
            responseText += `   ⬇️ Direct: ${result.directDownload
            }\n`;
          }
          if (result.tags && result.tags.length > 0) {
            responseText += `   🏷️ Tags: ${result.tags.join(', ')
            }\n`;
          }
          responseText += '\n';
        });
      }
      // Add search suggestions based on focus area
      responseText += this.getSearchSuggestions(query, focusArea, results.combined.length);
      
      return {
        content: [
          {
            type: 'text',
            text: responseText,
          },
        ],
      };
    } catch (error) {
      console.error(`❌ Combined search error: ${error.message
      }`);
      throw new Error(`Combined search failed: ${error.message
      }`);
    }
  }

  async performBraveSearch(query, focusArea) {
    const BRAVE_API_KEY = 'BSAETbHcrj5O1Kju1aSWt-_BdhltP1x';
    const BRAVE_API_URL = 'https: //api.search.brave.com/res/v1/web/search';
    // Enhance query based on focus area
    let enhancedQuery = query;
    const focusTerms = {
      'technical': ' documentation API reference',
      'tutorials': ' tutorial guide how-to',
      'downloads': ' download install setup',
      'documentation': ' docs documentation manual',
      'general': ''
    };
    
    if (focusTerms[focusArea
    ]) {
      enhancedQuery += focusTerms[focusArea
      ];
    }
    
    const searchParams = new URLSearchParams({
      q: enhancedQuery,
      count: '12',
      offset: '0',
      mkt: 'en-US',
      safesearch: 'moderate',
      search_lang: 'en',
      country: 'US',
      spellcheck: '1',
      result_filter: 'web',
      units: 'metric',
      extra_snippets: '1',
      summary: '1'
    });
    
    const response = await fetch(`${BRAVE_API_URL
    }?${searchParams
    }`,
    {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': BRAVE_API_KEY,
        'User-Agent': 'DEMONCORE-QUANTUM-SYSTEM/1.0'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Brave API error: ${response.status
      } ${response.statusText
      }`);
    }
    
    const data = await response.json();
    return data.web?.results || [];
  }

  async performContext7Search(query, focusArea) {
    console.log(`📚 Context7 Search: ${query
    } (${focusArea
    }) - Mock implementation`);
    
    // Enhanced mock responses based on focus area
    const focusResults = {
      'technical': [
        {
          title: `Technical Documentation: ${query
          }`,
          content: `Comprehensive technical documentation for "${query}" including API references, implementation details, and code examples.`,
          url: `https: //docs.example.com/technical/${encodeURIComponent(query)}`,
          source: 'Technical Docs',
          relevance: 9,
          tags: ['technical', 'api', 'documentation'
          ]
        },
        {
          title: `Developer Reference: ${query
          }`,
          content: `Developer-focused reference materials for "${query}" with integration guides and best practices.`,
          url: `https: //dev.example.com/reference/${encodeURIComponent(query)}`,
          source: 'Dev Reference',
          relevance: 8,
          tags: ['developer', 'reference', 'integration'
          ]
        }
      ],
      'tutorials': [
        {
          title: `Tutorial: Getting Started with ${query
          }`,
          content: `Step-by-step tutorial for "${query}" covering basic setup, configuration, and common use cases.`,
          url: `https: //learn.example.com/tutorials/${encodeURIComponent(query)}`,
          source: 'Learning Center',
          relevance: 9,
          tags: ['tutorial', 'beginner', 'guide'
          ]
        },
        {
          title: `Advanced Guide: ${query
          }`,
          content: `Advanced techniques and best practices for "${query}" with real-world examples and optimization tips.`,
          url: `https: //learn.example.com/advanced/${encodeURIComponent(query)}`,
          source: 'Advanced Guides',
          relevance: 8,
          tags: ['advanced', 'best-practices', 'optimization'
          ]
        }
      ],
      'downloads': [
        {
          title: `Download: ${query
          }`,
          content: `Official download page for "${query}" with latest versions, installation instructions, and system requirements.`,
          url: `https: //downloads.example.com/${encodeURIComponent(query)}`,
          source: 'Downloads',
          relevance: 10,
          tags: ['download', 'installation', 'official'
          ],
          directDownload: `https: //cdn.example.com/downloads/${query}-latest.zip`
        }
      ],
      'documentation': [
        {
          title: `Documentation: ${query
          }`,
          content: `Complete documentation for "${query}" including user guides, API documentation, and troubleshooting.`,
          url: `https: //docs.example.com/${encodeURIComponent(query)}`,
          source: 'Official Docs',
          relevance: 9,
          tags: ['documentation', 'official', 'comprehensive'
          ]
        }
      ],
      'general': [
        {
          title: `Overview: ${query
          }`,
          content: `General information and overview of "${query}" with key features and use cases.`,
          url: `https: //info.example.com/${encodeURIComponent(query)}`,
          source: 'General Info',
          relevance: 7,
          tags: ['overview', 'general', 'introduction'
          ]
        }
      ]
    };
    
    return focusResults[focusArea
    ] || focusResults['general'
    ];
  }

  formatWebResults(webResults, focusArea) {
    return webResults.map(result => {
      const url = result.url?.toLowerCase() || '';
      const title = result.title?.toLowerCase() || '';
      const snippet = result.snippet?.toLowerCase() || '';
      const combined = `${title
      } ${snippet
      } ${url
      }`;
      
      // Calculate relevance based on focus area
      let relevance = 5; // Base relevance
      
      const focusKeywords = {
        'technical': ['api', 'documentation', 'reference', 'sdk', 'library'
        ],
        'tutorials': ['tutorial', 'guide', 'how-to', 'step-by-step', 'learn'
        ],
        'downloads': ['download', 'install', 'setup', 'binary', 'release'
        ],
        'documentation': ['docs', 'manual', 'guide', 'documentation', 'help'
        ],
        'general': ['overview', 'about', 'introduction', 'what-is'
        ]
      };
      
      const keywords = focusKeywords[focusArea
      ] || [];
      keywords.forEach(keyword => {
        if (combined.includes(keyword)) relevance += 1;
      });
      
      // Boost known good sources
      if (url.includes('github.com') || url.includes('docs.') || url.includes('developer.')) {
        relevance += 1;
      }
      // Detect tags
      const tags = [];
      if (combined.includes('tutorial') || combined.includes('guide')) tags.push('tutorial');
      if (combined.includes('download') || combined.includes('install')) tags.push('download');
      if (combined.includes('api') || combined.includes('reference')) tags.push('technical');
      if (combined.includes('docs') || combined.includes('documentation')) tags.push('documentation');
      
      return {
        title: result.title || 'No title',
        snippet: result.snippet || result.description || 'No description',
        url: result.url || '',
        source: 'Web Search',
        relevance: Math.min(10, relevance),
        tags,
        age: result.age || 'Unknown',
        directDownload: this.extractDirectDownload(result.url)
      };
    }).filter(result => result.relevance >= 5); // Filter low-relevance results
  }

  combineSearchResults(webResults, docResults, focusArea) {
    const allResults = [...webResults, ...docResults
    ];
    
    // Remove duplicates based on URL similarity
    const uniqueResults = [];
    const seenUrls = new Set();
    
    allResults.forEach(result => {
      if (result.error) return; // Skip error results
      
      const urlKey = this.normalizeUrl(result.url);
      if (!seenUrls.has(urlKey)) {
        seenUrls.add(urlKey);
        uniqueResults.push(result);
      }
    });
    
    // Sort by relevance and source preference
    return uniqueResults
      .sort((a, b) => {
      // Prioritize by relevance first
        if (b.relevance !== a.relevance) {
          return b.relevance - a.relevance;
      }
      // Then by source preference
        const sourceOrder = { 'Official Docs': 4, 'Technical Docs': 3, 'Downloads': 2, 'Web Search': 1
      };
        return (sourceOrder[b.source
      ] || 0) - (sourceOrder[a.source
      ] || 0);
    })
      .slice(0,
    15); // Top 15 results
  }

  normalizeUrl(url) {
    try {
      const parsed = new URL(url);
      return `${parsed.hostname
      }${parsed.pathname
      }`.toLowerCase();
    } catch {
      return url.toLowerCase();
    }
  }

  extractDirectDownload(url) {
    if (!url) return null;
    
    const downloadPatterns = [
      '/releases/download/',
      '/resolve/main/',
      '/archive/',
      '.zip',
      '.tar.gz',
      '.exe',
      '.msi',
      '.deb',
      '.rpm'
    ];
    
    return downloadPatterns.some(pattern => url.includes(pattern)) ? url : null;
  }

  getSearchSuggestions(query, focusArea, resultCount) {
    if (resultCount > 5) return '';
    
    let suggestions = '\n💡 Search Suggestions:\n';
    
    if (focusArea === 'general') {
      suggestions += '- Try a more specific focus area (technical, tutorials, downloads, documentation)\n';
    }
    
    suggestions += '- Add version numbers or specific terms\n';
    suggestions += '- Try alternative keywords or synonyms\n';
    suggestions += '- Use quotes for exact phrases\n';
    
    const focusAlternatives = {
      'technical': 'Try "tutorials" or "downloads" focus',
      'tutorials': 'Try "technical" or "documentation" focus',
      'downloads': 'Try "technical" or "general" focus',
      'documentation': 'Try "tutorials" or "technical" focus',
      'general': 'Try "technical",
      "tutorials", or "downloads" focus'
    };
    
    if (focusAlternatives[focusArea
    ]) {
      suggestions += `- ${focusAlternatives[focusArea
        ]
      }\n`;
    }
    
    return suggestions;
  }

  setupErrorHandling() {
    // Handle server errors
    this.server.onerror = (error) => {
      console.error('[MCP Server
      ] Error:', error);
    };

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      console.error('[MCP Server
      ] Uncaught Exception:', error);
      process.exit(1);
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      console.error('[MCP Server
      ] Unhandled Rejection at:', promise, 'reason:', reason);
      process.exit(1);
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('[MCP Server
    ] Custom MCP Server running on stdio');
  }
  // ...existing code...
}
// Start the server
const server = new CustomMCPServer();
server.run().catch((error) => {
  console.error('[MCP Server
  ] Failed to start:', error);
  process.exit(1);
});class CustomMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'custom-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {}
        },
      }
    );

    this.memory = new Map();
    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'memory_store',
            description: 'Store information in persistent memory',
            inputSchema: {
              type: 'object',
              properties: {
                key: {
                  type: 'string',
                  description: 'Memory key identifier',
                },
                value: {
                  type: 'string',
                  description: 'Value to store in memory',
                },
              },
              required: ['key', 'value'],
            },
          },
          {
            name: 'memory_retrieve',
            description: 'Retrieve information from persistent memory',
            inputSchema: {
              type: 'object',
              properties: {
                key: {
                  type: 'string',
                  description: 'Memory key to retrieve',
                },
              },
              required: ['key'],
            },
          },
          {
            name: 'memory_list',
            description: 'List all stored memory keys',
            inputSchema: {
              type: 'object',
              properties: {},
            },
          },
          {
            name: 'file_read',
            description: 'Read file contents from the workspace',
            inputSchema: {
              type: 'object',
              properties: {
                path: {
                  type: 'string',
                  description: 'Relative file path from workspace root',
                },
              },
              required: ['path'],
            },
          },
          {
            name: 'file_write',
            description: 'Write content to a file in the workspace',
            inputSchema: {
              type: 'object',
              properties: {
                path: {
                  type: 'string',
                  description: 'Relative file path from workspace root',
                },
                content: {
                  type: 'string',
                  description: 'Content to write to the file',
                },
              },
              required: ['path', 'content'],
            },
          },
          {
            name: 'file_list',
            description: 'List files and directories in the workspace', inputSchema: {
              type: 'object',
              properties: {
                path: {
                  type: 'string',
                  description: 'Relative directory path from workspace root (default: ".")',
                  default: '.',
                },
              },
            },
          }, {
            name: 'fetch_model_config',
            description: 'Fetch model or config files using Brave search with intelligent source detection',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query for model/config (e.g., "SAM 2.1 HQ config", "YOLO12 download")',
                },
                file_type: {
                  type: 'string',
                  description: 'Type of file to fetch (model, config, checkpoint, etc.)',
                  enum: ['model', 'config', 'checkpoint', 'weights', 'yaml', 'json', 'any'],
                  default: 'any'
                },
                repository_type: {
                  type: 'string',
                  description: 'Preferred repository type',
                  enum: ['huggingface', 'github', 'civitai', 'any'],
                  default: 'any'
                }
              },
              required: ['query'],
            },
          },
          {
            name: 'combined_search',
            description: 'Comprehensive search combining Brave web search and Context7 documentation',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query to run across both web and documentation sources',
                },
                search_scope: {
                  type: 'string',
                  description: 'Scope of search results',
                  enum: ['both', 'web_only', 'docs_only'],
                  default: 'both'
                },
                focus_area: {
                  type: 'string',
                  description: 'Focus area for enhanced results',
                  enum: ['technical', 'tutorials', 'downloads', 'documentation', 'general'],
                  default: 'general'
                }
              },
              required: ['query'],
            },
          },
        ],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {

          case 'memory_store':
            return await this.handleMemoryStore(args.key, args.value);

          case 'memory_retrieve':
            return await this.handleMemoryRetrieve(args.key);

          case 'memory_list':
            return await this.handleMemoryList();

          case 'file_read':
            return await this.handleFileRead(args.path);
          case 'file_write':
            return await this.handleFileWrite(args.path, args.content);

          case 'file_list':
            return await this.handleFileList(args.path || '.');

          case 'fetch_model_config':
            return await this.handleFetchModelConfig(args.query, args.file_type, args.repository_type);

          case 'combined_search':
            return await this.handleCombinedSearch(args.query, args.search_scope, args.focus_area);

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error executing ${name}: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }
  async handleContext7Search(query) {
    try {
      console.log(`📚 Context7 Search: ${query} (MOCK - API not yet available)`);

      // Mock response until Context7 API becomes available
      const mockResults = [
        {
          title: `Documentation for: ${query}`,
          content: `Here are the search results for "${query}". This is a mock response from Context7 search. The actual Context7 API integration will be enabled when available via @upstash/context7-mcp.`,
          url: `https://docs.example.com/search?q=${encodeURIComponent(query)}`,
          source: 'Context7 Documentation (Mock)',
          relevance: 0.95
        },
        {
          title: `Technical Reference: ${query}`,
          content: `Technical documentation and API references for "${query}". This will be replaced with real Context7 results when the service becomes available.`,
          url: `https://docs.example.com/api/search?q=${encodeURIComponent(query)}`,
          source: 'Technical Docs (Mock)',
          relevance: 0.88
        }
      ];

      let responseText = `📚 Context7 Documentation Search Results for "${query}":\n`;
      responseText += `⚠️ Note: Using mock data - Context7 API not yet available\n`;
      responseText += `🔄 Will be enabled via: npx -y @upstash/context7-mcp\n\n`;

      mockResults.forEach((result, index) => {
        responseText += `${index + 1}. **${result.title}**\n`;
        responseText += `   📊 Relevance: ${(result.relevance * 100).toFixed(1)}%\n`;
        responseText += `   📝 ${result.content}\n`;
        responseText += `   🔗 ${result.url}\n`;
        responseText += `   📚 Source: ${result.source}\n\n`;
      });

      return {
        content: [
          {
            type: 'text',
            text: responseText,
          },
        ],
      };
    } catch (error) {
      console.error(`❌ Context7 search error: ${error.message}`);
      throw new Error(`Context7 search failed: ${error.message}`);
    }
  }
  async handleWebSearch(query) {
    try {
      console.log(`🔍 Brave Search: ${query}`);

      // Brave Search API configuration
      const BRAVE_API_KEY = 'BSAETbHcrj5O1Kju1aSWt-_BdhltP1x';
      const BRAVE_API_URL = 'https://api.search.brave.com/res/v1/web/search';

      // Prepare search parameters
      const searchParams = new URLSearchParams({
        q: query,
        count: '10',
        offset: '0',
        mkt: 'en-US',
        safesearch: 'moderate',
        search_lang: 'en',
        country: 'US',
        spellcheck: '1',
        result_filter: 'web',
        goggles_id: '',
        units: 'metric',
        extra_snippets: '1',
        summary: '1'
      });

      const response = await fetch(`${BRAVE_API_URL}?${searchParams}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Accept-Encoding': 'gzip',
          'X-Subscription-Token': BRAVE_API_KEY,
          'User-Agent': 'DEMONCORE-QUANTUM-SYSTEM/1.0'
        }
      });

      if (!response.ok) {
        throw new Error(`Brave API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log(`✅ Brave Search: ${data.web?.results?.length || 0} results`);

      // Format results
      const results = data.web?.results || [];
      const formattedResults = results.map(result => ({
        title: result.title || 'No title',
        snippet: result.snippet || result.description || 'No description',
        url: result.url || '',
        age: result.age || 'Unknown',
        language: result.language || 'en',
        family_friendly: result.family_friendly || true
      }));

      // Include search summary if available
      let responseText = `🔍 Brave Search Results for "${query}":\n`;
      responseText += `Found ${formattedResults.length} results\n\n`;

      if (data.summarizer?.key) {
        responseText += `📋 Summary: ${data.summarizer.key}\n\n`;
      }

      formattedResults.forEach((result, index) => {
        responseText += `${index + 1}. **${result.title}**\n`;
        responseText += `   ${result.snippet}\n`;
        responseText += `   🔗 ${result.url}\n`;
        if (result.age !== 'Unknown') {
          responseText += `   📅 ${result.age}\n`;
        }
        responseText += '\n';
      });

      return {
        content: [
          {
            type: 'text',
            text: responseText,
          },
        ],
      };
    } catch (error) {
      console.error(`❌ Brave Search error: ${error.message}`);
      throw new Error(`Brave Search failed: ${error.message}`);
    }
  }

  async handleFetchModelConfig(query, fileType = 'any', repositoryType = 'any') {
    try {
      console.log(`🔄 Fetch Model/Config: ${query} (${fileType}, ${repositoryType})`);

      // Enhanced search query based on file type and repository
      let enhancedQuery = query;

      if (fileType !== 'any') {
        enhancedQuery += ` ${fileType}`;
      }

      if (repositoryType !== 'any') {
        enhancedQuery += ` site:${this.getRepositoryDomain(repositoryType)}`;
      }

      // Add specific terms for better model/config finding
      const searchTerms = [
        'download', 'checkpoint', 'weights', 'model', 'config',
        'huggingface.co', 'github.com', 'civitai.com'
      ];

      if (!searchTerms.some(term => enhancedQuery.toLowerCase().includes(term))) {
        enhancedQuery += ' download';
      }

      console.log(`🔍 Enhanced query: ${enhancedQuery}`);

      // Use Brave search to find relevant sources
      const searchResults = await this.performBraveSearch(enhancedQuery);

      // Filter and rank results based on relevance for model/config files
      const filteredResults = this.filterModelConfigResults(searchResults, fileType, repositoryType);

      // Format response
      let responseText = `🎯 Model/Config Fetch Results for "${query}":\n`;
      responseText += `File Type: ${fileType} | Repository: ${repositoryType}\n`;
      responseText += `Found ${filteredResults.length} relevant sources\n\n`;

      filteredResults.forEach((result, index) => {
        responseText += `${index + 1}. **${result.title}**\n`;
        responseText += `   📊 Relevance: ${result.relevanceScore}/10\n`;
        responseText += `   📝 ${result.snippet}\n`;
        responseText += `   🔗 ${result.url}\n`;
        responseText += `   🏷️ Type: ${result.detectedType}\n`;
        responseText += `   🏪 Source: ${result.repository}\n`;
        if (result.directDownload) {
          responseText += `   ⬇️ Direct Download: ${result.directDownload}\n`;
        }
        responseText += '\n';
      });

      if (filteredResults.length === 0) {
        responseText += '⚠️ No relevant model/config sources found. Try refining your search query.\n';
        responseText += '\n📝 Suggestions:\n';
        responseText += '- Include specific model version numbers\n';
        responseText += '- Add terms like "checkpoint", "weights", "config"\n';
        responseText += '- Specify the framework (pytorch, tensorflow, onnx)\n';
      }

      return {
        content: [
          {
            type: 'text',
            text: responseText,
          },
        ],
      };
    } catch (error) {
      console.error(`❌ Model/Config fetch error: ${error.message}`);
      throw new Error(`Model/Config fetch failed: ${error.message}`);
    }
  }

  getRepositoryDomain(repositoryType) {
    const domains = {
      'huggingface': 'huggingface.co',
      'github': 'github.com',
      'civitai': 'civitai.com'
    };
    return domains[repositoryType] || '';
  }

  async performBraveSearch(query) {
    const BRAVE_API_KEY = 'BSAETbHcrj5O1Kju1aSWt-_BdhltP1x';
    const BRAVE_API_URL = 'https://api.search.brave.com/res/v1/web/search';

    const searchParams = new URLSearchParams({
      q: query,
      count: '15',
      offset: '0',
      mkt: 'en-US',
      safesearch: 'moderate',
      search_lang: 'en',
      country: 'US',
      spellcheck: '1',
      result_filter: 'web',
      units: 'metric',
      extra_snippets: '1'
    });

    const response = await fetch(`${BRAVE_API_URL}?${searchParams}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': BRAVE_API_KEY,
        'User-Agent': 'DEMONCORE-QUANTUM-SYSTEM/1.0'
      }
    });

    if (!response.ok) {
      throw new Error(`Brave API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.web?.results || [];
  }

  filterModelConfigResults(results, fileType, repositoryType) {
    return results.map(result => {
      const url = result.url.toLowerCase();
      const title = result.title.toLowerCase();
      const snippet = (result.snippet || '').toLowerCase();
      const combined = `${title} ${snippet} ${url}`;

      // Calculate relevance score
      let relevanceScore = 0;

      // Repository preference scoring
      if (repositoryType !== 'any') {
        const domain = this.getRepositoryDomain(repositoryType);
        if (url.includes(domain)) relevanceScore += 3;
      } else {
        // Boost known good repositories
        if (url.includes('huggingface.co')) relevanceScore += 2;
        if (url.includes('github.com')) relevanceScore += 2;
        if (url.includes('civitai.com')) relevanceScore += 1;
      }

      // File type scoring
      const fileExtensions = {
        'model': ['.bin', '.safetensors', '.ckpt', '.pth', '.pt', '.pb', '.onnx'],
        'config': ['.json', '.yaml', '.yml', '.cfg', '.ini'],
        'checkpoint': ['.ckpt', '.pth', '.pt', '.safetensors'],
        'weights': ['.bin', '.safetensors', '.pth', '.pt'],
        'yaml': ['.yaml', '.yml'],
        'json': ['.json']
      };

      if (fileType !== 'any' && fileExtensions[fileType]) {
        const hasExtension = fileExtensions[fileType].some(ext => combined.includes(ext));
        if (hasExtension) relevanceScore += 2;
      }

      // Content relevance scoring
      const relevantTerms = [
        'download', 'checkpoint', 'weights', 'model', 'config',
        'pretrained', 'pytorch', 'tensorflow', 'onnx', 'safetensors'
      ];

      relevantTerms.forEach(term => {
        if (combined.includes(term)) relevanceScore += 0.5;
      });

      // Detect file type and repository
      let detectedType = 'unknown';
      let repository = 'unknown';

      if (url.includes('huggingface.co')) repository = 'HuggingFace';
      else if (url.includes('github.com')) repository = 'GitHub';
      else if (url.includes('civitai.com')) repository = 'CivitAI';

      if (combined.includes('.bin') || combined.includes('.safetensors')) detectedType = 'model';
      else if (combined.includes('.json') || combined.includes('.yaml')) detectedType = 'config';
      else if (combined.includes('.ckpt') || combined.includes('.pth')) detectedType = 'checkpoint';

      // Look for direct download links
      let directDownload = null;
      if (url.includes('/resolve/main/') || url.includes('/download/') || url.includes('/releases/')) {
        directDownload = result.url;
      }

      return {
        ...result,
        relevanceScore: Math.min(10, Math.round(relevanceScore)),
        detectedType,
        repository,
        directDownload
      };
    })
      .filter(result => result.relevanceScore > 0)
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, 10); // Top 10 results
  }

  async handleMemoryStore(key, value) {
    this.memory.set(key, {
      value,
      timestamp: new Date().toISOString(),
    });

    return {
      content: [
        {
          type: 'text',
          text: `✅ Stored in memory:\nKey: "${key}"\nValue: "${value}"\nTimestamp: ${new Date().toISOString()}`,
        },
      ],
    };
  }

  async handleMemoryRetrieve(key) {
    const item = this.memory.get(key);

    if (!item) {
      return {
        content: [
          {
            type: 'text',
            text: `❌ Key "${key}" not found in memory.`,
          },
        ],
      };
    }

    return {
      content: [
        {
          type: 'text',
          text: `✅ Retrieved from memory:\nKey: "${key}"\nValue: "${item.value}"\nStored: ${item.timestamp}`,
        },
      ],
    };
  }

  async handleMemoryList() {
    const keys = Array.from(this.memory.keys());

    if (keys.length === 0) {
      return {
        content: [
          {
            type: 'text',
            text: '📝 Memory is empty. No keys stored.',
          },
        ],
      };
    }

    const memoryList = keys.map(key => {
      const item = this.memory.get(key);
      return `• ${key}: "${item.value}" (${item.timestamp})`;
    }).join('\n');

    return {
      content: [
        {
          type: 'text',
          text: `📝 Memory contents (${keys.length} items):\n\n${memoryList}`,
        },
      ],
    };
  }

  async handleFileRead(filePath) {
    try {
      const workspaceRoot = process.cwd();
      const fullPath = path.resolve(workspaceRoot, filePath);

      // Security check: ensure path is within workspace
      if (!fullPath.startsWith(workspaceRoot)) {
        throw new Error('Access denied: Path is outside workspace');
      }

      const content = await fs.readFile(fullPath, 'utf-8');
      const stats = await fs.stat(fullPath);

      return {
        content: [
          {
            type: 'text',
            text: `📄 File: ${filePath}\nSize: ${stats.size} bytes\nModified: ${stats.mtime.toISOString()}\n\n--- Content ---\n${content}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to read file "${filePath}": ${error.message}`);
    }
  }

  async handleFileWrite(filePath, content) {
    try {
      const workspaceRoot = process.cwd();
      const fullPath = path.resolve(workspaceRoot, filePath);

      // Security check: ensure path is within workspace
      if (!fullPath.startsWith(workspaceRoot)) {
        throw new Error('Access denied: Path is outside workspace');
      }

      // Ensure directory exists
      const dir = path.dirname(fullPath);
      await fs.mkdir(dir, { recursive: true });

      await fs.writeFile(fullPath, content, 'utf-8');
      const stats = await fs.stat(fullPath);

      return {
        content: [
          {
            type: 'text',
            text: `✅ Successfully wrote to "${filePath}"\nSize: ${stats.size} bytes\nModified: ${stats.mtime.toISOString()}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to write file "${filePath}": ${error.message}`);
    }
  }

  async handleFileList(dirPath) {
    try {
      const workspaceRoot = process.cwd();
      const fullPath = path.resolve(workspaceRoot, dirPath);

      // Security check: ensure path is within workspace
      if (!fullPath.startsWith(workspaceRoot)) {
        throw new Error('Access denied: Path is outside workspace');
      }

      const entries = await fs.readdir(fullPath, { withFileTypes: true });

      const files = [];
      const directories = [];

      for (const entry of entries) {
        if (entry.isDirectory()) {
          directories.push(`📁 ${entry.name}/`);
        } else {
          const stats = await fs.stat(path.join(fullPath, entry.name));
          files.push(`📄 ${entry.name} (${stats.size} bytes)`);
        }
      }

      const listing = [
        ...directories.sort(),
        ...files.sort(),
      ].join('\n');

      return {
        content: [
          {
            type: 'text',
            text: `📂 Directory listing: ${dirPath}\n\n${listing || '(empty directory)'}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to list directory "${dirPath}": ${error.message}`);
    }
  }

  async handleCombinedSearch(query, searchScope = 'both', focusArea = 'general') {
    try {
      console.log(`🔍📚 Combined Search: ${query} (${searchScope}, ${focusArea})`);

      const results = {
        web: [],
        docs: [],
        combined: []
      };

      // Execute searches based on scope
      if (searchScope === 'both' || searchScope === 'web_only') {
        try {
          const webResults = await this.performBraveSearch(query, focusArea);
          results.web = this.formatWebResults(webResults, focusArea);
        } catch (error) {
          console.error(`❌ Web search failed: ${error.message}`);
          results.web = [{ error: `Web search failed: ${error.message}` }];
        }
      }

      if (searchScope === 'both' || searchScope === 'docs_only') {
        try {
          const docResults = await this.performContext7Search(query, focusArea);
          results.docs = docResults;
        } catch (error) {
          console.error(`❌ Documentation search failed: ${error.message}`);
          results.docs = [{ error: `Documentation search failed: ${error.message}` }];
        }
      }

      // Combine and deduplicate results
      results.combined = this.combineSearchResults(results.web, results.docs, focusArea);

      // Format comprehensive response
      let responseText = `🔍📚 Combined Search Results for "${query}":\n`;
      responseText += `Scope: ${searchScope} | Focus: ${focusArea}\n`;
      responseText += `Found ${results.combined.length} total results\n\n`;

      if (results.combined.length === 0) {
        responseText += '⚠️ No results found. Try:\n';
        responseText += '- Different search terms\n';
        responseText += '- Broader focus area\n';
        responseText += '- Different search scope\n';
      } else {
        results.combined.forEach((result, index) => {
          responseText += `${index + 1}. **${result.title}**\n`;
          responseText += `   🏷️ Source: ${result.source} | Relevance: ${result.relevance}/10\n`;
          responseText += `   📝 ${result.snippet}\n`;
          responseText += `   🔗 ${result.url}\n`;
          if (result.directDownload) {
            responseText += `   ⬇️ Direct: ${result.directDownload}\n`;
          }
          if (result.tags && result.tags.length > 0) {
            responseText += `   🏷️ Tags: ${result.tags.join(', ')}\n`;
          }
          responseText += '\n';
        });
      }

      // Add search suggestions based on focus area
      responseText += this.getSearchSuggestions(query, focusArea, results.combined.length);

      return {
        content: [
          {
            type: 'text',
            text: responseText,
          },
        ],
      };
    } catch (error) {
      console.error(`❌ Combined search error: ${error.message}`);
      throw new Error(`Combined search failed: ${error.message}`);
    }
  }

  async performBraveSearch(query, focusArea) {
    const BRAVE_API_KEY = 'BSAETbHcrj5O1Kju1aSWt-_BdhltP1x';
    const BRAVE_API_URL = 'https://api.search.brave.com/res/v1/web/search';

    // Enhance query based on focus area
    let enhancedQuery = query;
    const focusTerms = {
      'technical': ' documentation API reference',
      'tutorials': ' tutorial guide how-to',
      'downloads': ' download install setup',
      'documentation': ' docs documentation manual',
      'general': ''
    };

    if (focusTerms[focusArea]) {
      enhancedQuery += focusTerms[focusArea];
    }

    const searchParams = new URLSearchParams({
      q: enhancedQuery,
      count: '12',
      offset: '0',
      mkt: 'en-US',
      safesearch: 'moderate',
      search_lang: 'en',
      country: 'US',
      spellcheck: '1',
      result_filter: 'web',
      units: 'metric',
      extra_snippets: '1',
      summary: '1'
    });

    const response = await fetch(`${BRAVE_API_URL}?${searchParams}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': BRAVE_API_KEY,
        'User-Agent': 'DEMONCORE-QUANTUM-SYSTEM/1.0'
      }
    });

    if (!response.ok) {
      throw new Error(`Brave API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.web?.results || [];
  }

  async performContext7Search(query, focusArea) {
    console.log(`📚 Context7 Search: ${query} (${focusArea}) - Mock implementation`);

    // Enhanced mock responses based on focus area
    const focusResults = {
      'technical': [
        {
          title: `Technical Documentation: ${query}`,
          content: `Comprehensive technical documentation for "${query}" including API references, implementation details, and code examples.`,
          url: `https://docs.example.com/technical/${encodeURIComponent(query)}`,
          source: 'Technical Docs',
          relevance: 9,
          tags: ['technical', 'api', 'documentation']
        },
        {
          title: `Developer Reference: ${query}`,
          content: `Developer-focused reference materials for "${query}" with integration guides and best practices.`,
          url: `https://dev.example.com/reference/${encodeURIComponent(query)}`,
          source: 'Dev Reference',
          relevance: 8,
          tags: ['developer', 'reference', 'integration']
        }
      ],
      'tutorials': [
        {
          title: `Tutorial: Getting Started with ${query}`,
          content: `Step-by-step tutorial for "${query}" covering basic setup, configuration, and common use cases.`,
          url: `https://learn.example.com/tutorials/${encodeURIComponent(query)}`,
          source: 'Learning Center',
          relevance: 9,
          tags: ['tutorial', 'beginner', 'guide']
        },
        {
          title: `Advanced Guide: ${query}`,
          content: `Advanced techniques and best practices for "${query}" with real-world examples and optimization tips.`,
          url: `https://learn.example.com/advanced/${encodeURIComponent(query)}`,
          source: 'Advanced Guides',
          relevance: 8,
          tags: ['advanced', 'best-practices', 'optimization']
        }
      ],
      'downloads': [
        {
          title: `Download: ${query}`,
          content: `Official download page for "${query}" with latest versions, installation instructions, and system requirements.`,
          url: `https://downloads.example.com/${encodeURIComponent(query)}`,
          source: 'Downloads',
          relevance: 10,
          tags: ['download', 'installation', 'official'],
          directDownload: `https://cdn.example.com/downloads/${query}-latest.zip`
        }
      ],
      'documentation': [
        {
          title: `Documentation: ${query}`,
          content: `Complete documentation for "${query}" including user guides, API documentation, and troubleshooting.`,
          url: `https://docs.example.com/${encodeURIComponent(query)}`,
          source: 'Official Docs',
          relevance: 9,
          tags: ['documentation', 'official', 'comprehensive']
        }
      ],
      'general': [
        {
          title: `Overview: ${query}`,
          content: `General information and overview of "${query}" with key features and use cases.`,
          url: `https://info.example.com/${encodeURIComponent(query)}`,
          source: 'General Info',
          relevance: 7,
          tags: ['overview', 'general', 'introduction']
        }
      ]
    };

    return focusResults[focusArea] || focusResults['general'];
  }

  formatWebResults(webResults, focusArea) {
    return webResults.map(result => {
      const url = result.url?.toLowerCase() || '';
      const title = result.title?.toLowerCase() || '';
      const snippet = result.snippet?.toLowerCase() || '';
      const combined = `${title} ${snippet} ${url}`;

      // Calculate relevance based on focus area
      let relevance = 5; // Base relevance

      const focusKeywords = {
        'technical': ['api', 'documentation', 'reference', 'sdk', 'library'],
        'tutorials': ['tutorial', 'guide', 'how-to', 'step-by-step', 'learn'],
        'downloads': ['download', 'install', 'setup', 'binary', 'release'],
        'documentation': ['docs', 'manual', 'guide', 'documentation', 'help'],
        'general': ['overview', 'about', 'introduction', 'what-is']
      };

      const keywords = focusKeywords[focusArea] || [];
      keywords.forEach(keyword => {
        if (combined.includes(keyword)) relevance += 1;
      });

      // Boost known good sources
      if (url.includes('github.com') || url.includes('docs.') || url.includes('developer.')) {
        relevance += 1;
      }

      // Detect tags
      const tags = [];
      if (combined.includes('tutorial') || combined.includes('guide')) tags.push('tutorial');
      if (combined.includes('download') || combined.includes('install')) tags.push('download');
      if (combined.includes('api') || combined.includes('reference')) tags.push('technical');
      if (combined.includes('docs') || combined.includes('documentation')) tags.push('documentation');

      return {
        title: result.title || 'No title',
        snippet: result.snippet || result.description || 'No description',
        url: result.url || '',
        source: 'Web Search',
        relevance: Math.min(10, relevance),
        tags,
        age: result.age || 'Unknown',
        directDownload: this.extractDirectDownload(result.url)
      };
    }).filter(result => result.relevance >= 5); // Filter low-relevance results
  }

  combineSearchResults(webResults, docResults, focusArea) {
    const allResults = [...webResults, ...docResults];

    // Remove duplicates based on URL similarity
    const uniqueResults = [];
    const seenUrls = new Set();

    allResults.forEach(result => {
      if (result.error) return; // Skip error results

      const urlKey = this.normalizeUrl(result.url);
      if (!seenUrls.has(urlKey)) {
        seenUrls.add(urlKey);
        uniqueResults.push(result);
      }
    });

    // Sort by relevance and source preference
    return uniqueResults
      .sort((a, b) => {
        // Prioritize by relevance first
        if (b.relevance !== a.relevance) {
          return b.relevance - a.relevance;
        }
        // Then by source preference
        const sourceOrder = { 'Official Docs': 4, 'Technical Docs': 3, 'Downloads': 2, 'Web Search': 1 };
        return (sourceOrder[b.source] || 0) - (sourceOrder[a.source] || 0);
      })
      .slice(0, 15); // Top 15 results
  }

  normalizeUrl(url) {
    try {
      const parsed = new URL(url);
      return `${parsed.hostname}${parsed.pathname}`.toLowerCase();
    } catch {
      return url.toLowerCase();
    }
  }

  extractDirectDownload(url) {
    if (!url) return null;

    const downloadPatterns = [
      '/releases/download/',
      '/resolve/main/',
      '/archive/',
      '.zip',
      '.tar.gz',
      '.exe',
      '.msi',
      '.deb',
      '.rpm'
    ];

    return downloadPatterns.some(pattern => url.includes(pattern)) ? url : null;
  }

  getSearchSuggestions(query, focusArea, resultCount) {
    if (resultCount > 5) return '';

    let suggestions = '\n💡 Search Suggestions:\n';

    if (focusArea === 'general') {
      suggestions += '- Try a more specific focus area (technical, tutorials, downloads, documentation)\n';
    }

    suggestions += '- Add version numbers or specific terms\n';
    suggestions += '- Try alternative keywords or synonyms\n';
    suggestions += '- Use quotes for exact phrases\n';

    const focusAlternatives = {
      'technical': 'Try "tutorials" or "downloads" focus',
      'tutorials': 'Try "technical" or "documentation" focus',
      'downloads': 'Try "technical" or "general" focus',
      'documentation': 'Try "tutorials" or "technical" focus',
      'general': 'Try "technical", "tutorials", or "downloads" focus'
    };

    if (focusAlternatives[focusArea]) {
      suggestions += `- ${focusAlternatives[focusArea]}\n`;
    }

    return suggestions;
  }

  setupErrorHandling() {
    // Handle server errors
    this.server.onerror = (error) => {
      console.error('[MCP Server] Error:', error);
    };

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      console.error('[MCP Server] Uncaught Exception:', error);
      process.exit(1);
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      console.error('[MCP Server] Unhandled Rejection at:', promise, 'reason:', reason);
      process.exit(1);
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('[MCP Server] Custom MCP Server running on stdio');
  }

}
// Start the server
const server = new CustomMCPServer();
server.run().catch((error) => {
  console.error('[MCP Server] Failed to start:', error);
  process.exit(1);
});

