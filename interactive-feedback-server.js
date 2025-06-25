#!/usr/bin/env node

/**
 * 🎯 ENHANCED INTERACTIVE FEEDBACK MCP SERVER
 * Custom server for Ultra-Advanced Inpainting System
 * Provides interactive feedback, session management, user preferences, and web utilities
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs/promises';
import path from 'path';

// Add fetch for web capabilities
async function fetchWithTimeout(url, options = {}, timeout = 10000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

class InteractiveFeedbackServer {
  constructor() {
    this.server = new Server(
      {
        name: 'interactive-feedback-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.feedbackStore = new Map();
    this.sessionData = new Map();
    this.userPreferences = new Map();
    this.setupHandlers();
  }

  setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'store_feedback',
            description: 'Store user feedback about inpainting results',
            inputSchema: {
              type: 'object',
              properties: {
                session_id: {
                  type: 'string',
                  description: 'Unique session identifier',
                },
                algorithm: {
                  type: 'string',
                  description: 'Algorithm used (lama, edge_connect, etc.)',
                },
                rating: {
                  type: 'number',
                  description: 'User rating 1-5',
                  minimum: 1,
                  maximum: 5,
                },
                feedback: {
                  type: 'string',
                  description: 'User feedback text',
                },
                parameters: {
                  type: 'object',
                  description: 'Parameters used for inpainting',
                },
                result_quality: {
                  type: 'string',
                  enum: ['excellent', 'good', 'fair', 'poor'],
                  description: 'Quality assessment',
                },
              },
              required: ['session_id', 'algorithm', 'rating'],
            },
          },
          {
            name: 'get_feedback_analytics',
            description: 'Get analytics about user feedback and preferences',
            inputSchema: {
              type: 'object',
              properties: {
                timeframe: {
                  type: 'string',
                  enum: ['day', 'week', 'month', 'all'],
                  description: 'Timeframe for analytics',
                },
                algorithm: {
                  type: 'string',
                  description: 'Filter by specific algorithm',
                },
              },
            },
          },
          {
            name: 'store_user_preference',
            description: 'Store user preferences for inpainting',
            inputSchema: {
              type: 'object',
              properties: {
                user_id: {
                  type: 'string',
                  description: 'User identifier',
                },
                preference_type: {
                  type: 'string',
                  enum: ['algorithm', 'parameters', 'ui_theme', 'workflow'],
                  description: 'Type of preference',
                },
                preference_value: {
                  type: 'object',
                  description: 'Preference data',
                },
              },
              required: ['user_id', 'preference_type', 'preference_value'],
            },
          },
          {
            name: 'get_user_preferences',
            description: 'Retrieve user preferences',
            inputSchema: {
              type: 'object',
              properties: {
                user_id: {
                  type: 'string',
                  description: 'User identifier',
                },
                preference_type: {
                  type: 'string',
                  description: 'Specific preference type to retrieve',
                },
              },
              required: ['user_id'],
            },
          },
          {
            name: 'suggest_optimal_settings',
            description: 'Suggest optimal settings based on image analysis and user history',
            inputSchema: {
              type: 'object',
              properties: {
                image_properties: {
                  type: 'object',
                  description: 'Properties of the input image',
                  properties: {
                    width: { type: 'number' },
                    height: { type: 'number' },
                    has_faces: { type: 'boolean' },
                    complexity: { type: 'string', enum: ['low', 'medium', 'high'] },
                    dominant_colors: { type: 'array', items: { type: 'string' } },
                  },
                },
                mask_properties: {
                  type: 'object',
                  description: 'Properties of the mask',
                  properties: {
                    area_percentage: { type: 'number' },
                    shape_complexity: { type: 'string', enum: ['simple', 'complex'] },
                    edge_sharpness: { type: 'string', enum: ['soft', 'sharp'] },
                  },
                },
                user_id: {
                  type: 'string',
                  description: 'User ID for personalized suggestions',
                },
              },
              required: ['image_properties'],
            },
          },
          {
            name: 'track_session_metrics',
            description: 'Track session metrics and performance',
            inputSchema: {
              type: 'object',
              properties: {
                session_id: {
                  type: 'string',
                  description: 'Session identifier',
                },
                action: {
                  type: 'string',
                  enum: ['start', 'inpaint', 'download', 'error', 'complete'],
                  description: 'Action type',
                },
                metadata: {
                  type: 'object',
                  description: 'Additional metadata',
                },
              },
              required: ['session_id', 'action'],
            },
          },
          {
            name: 'generate_improvement_suggestions',            description: 'Generate suggestions for improving inpainting results',
            inputSchema: {
              type: 'object',
              properties: {
                current_result: {
                  type: 'object',
                  description: 'Current inpainting result metadata',
                },
                user_feedback: {
                  type: 'string',
                  description: 'User feedback about current result',
                },
                algorithm_used: {
                  type: 'string',
                  description: 'Algorithm that was used',
                },
              },
              required: ['current_result', 'algorithm_used'],
            },
          },
          {
            name: 'fetch_url',
            description: 'Fetch content from a URL (for model downloads, documentation, etc.)',
            inputSchema: {
              type: 'object',
              properties: {
                url: {
                  type: 'string',
                  description: 'URL to fetch',
                },
                method: {
                  type: 'string',
                  enum: ['GET', 'POST', 'PUT', 'DELETE'],
                  description: 'HTTP method',
                  default: 'GET',
                },
                headers: {
                  type: 'object',
                  description: 'HTTP headers',
                },
                body: {
                  type: 'string',
                  description: 'Request body for POST/PUT requests',
                },
                timeout: {
                  type: 'number',
                  description: 'Timeout in milliseconds',
                  default: 10000,
                },
              },
              required: ['url'],
            },
          },
          {
            name: 'download_file',
            description: 'Download a file from URL to local storage (for model downloads)',
            inputSchema: {
              type: 'object',
              properties: {
                url: {
                  type: 'string',
                  description: 'URL to download from',
                },
                filename: {
                  type: 'string',
                  description: 'Local filename to save as',
                },
                directory: {
                  type: 'string',
                  description: 'Directory to save in (relative to project)',
                  default: 'models',
                },
              },
              required: ['url', 'filename'],
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'store_feedback':
            return await this.storeFeedback(args);
          case 'get_feedback_analytics':
            return await this.getFeedbackAnalytics(args);
          case 'store_user_preference':
            return await this.storeUserPreference(args);
          case 'get_user_preferences':
            return await this.getUserPreferences(args);
          case 'suggest_optimal_settings':
            return await this.suggestOptimalSettings(args);
          case 'track_session_metrics':
            return await this.trackSessionMetrics(args);          case 'generate_improvement_suggestions':
            return await this.generateImprovementSuggestions(args);
          case 'fetch_url':
            return await this.fetchUrl(args);
          case 'download_file':
            return await this.downloadFile(args);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        throw new McpError(ErrorCode.InternalError, error.message);
      }
    });
  }

  async storeFeedback(args) {
    const { session_id, algorithm, rating, feedback, parameters, result_quality } = args;
    
    const feedbackEntry = {
      timestamp: new Date().toISOString(),
      session_id,
      algorithm,
      rating,
      feedback,
      parameters,
      result_quality,
    };

    this.feedbackStore.set(`${session_id}_${Date.now()}`, feedbackEntry);
    
    // Persist to file
    await this.persistFeedback(feedbackEntry);

    return {
      content: [
        {
          type: 'text',
          text: `✅ Feedback stored successfully for session ${session_id}. Rating: ${rating}/5, Algorithm: ${algorithm}`,
        },
      ],
    };
  }

  async getFeedbackAnalytics(args) {
    const { timeframe = 'all', algorithm } = args;
    
    const analytics = {
      total_sessions: this.feedbackStore.size,
      average_rating: 0,
      algorithm_ratings: {},
      quality_distribution: {},
      top_issues: [],
      recommendations: [],
    };

    const entries = Array.from(this.feedbackStore.values());
    
    // Filter by timeframe and algorithm
    const filteredEntries = entries.filter(entry => {
      if (algorithm && entry.algorithm !== algorithm) return false;
      
      if (timeframe !== 'all') {
        const entryDate = new Date(entry.timestamp);
        const now = new Date();
        const daysDiff = (now - entryDate) / (1000 * 60 * 60 * 24);
        
        switch (timeframe) {
          case 'day': return daysDiff <= 1;
          case 'week': return daysDiff <= 7;
          case 'month': return daysDiff <= 30;
        }
      }
      
      return true;
    });

    if (filteredEntries.length > 0) {
      analytics.average_rating = filteredEntries.reduce((sum, entry) => sum + entry.rating, 0) / filteredEntries.length;
      
      // Algorithm ratings
      filteredEntries.forEach(entry => {
        if (!analytics.algorithm_ratings[entry.algorithm]) {
          analytics.algorithm_ratings[entry.algorithm] = { count: 0, total: 0, average: 0 };
        }
        analytics.algorithm_ratings[entry.algorithm].count++;
        analytics.algorithm_ratings[entry.algorithm].total += entry.rating;
      });
      
      Object.keys(analytics.algorithm_ratings).forEach(alg => {
        const data = analytics.algorithm_ratings[alg];
        data.average = data.total / data.count;
      });
      
      // Quality distribution
      filteredEntries.forEach(entry => {
        if (entry.result_quality) {
          analytics.quality_distribution[entry.result_quality] = 
            (analytics.quality_distribution[entry.result_quality] || 0) + 1;
        }
      });
    }

    return {
      content: [
        {
          type: 'text',
          text: `📊 Feedback Analytics (${timeframe}):\n${JSON.stringify(analytics, null, 2)}`,
        },
      ],
    };
  }

  async storeUserPreference(args) {
    const { user_id, preference_type, preference_value } = args;
    
    if (!this.userPreferences.has(user_id)) {
      this.userPreferences.set(user_id, {});
    }
    
    this.userPreferences.get(user_id)[preference_type] = {
      value: preference_value,
      updated: new Date().toISOString(),
    };

    return {
      content: [
        {
          type: 'text',
          text: `✅ User preference stored: ${preference_type} for user ${user_id}`,
        },
      ],
    };
  }

  async getUserPreferences(args) {
    const { user_id, preference_type } = args;
    
    const userPrefs = this.userPreferences.get(user_id) || {};
    
    if (preference_type) {
      const pref = userPrefs[preference_type];
      return {
        content: [
          {
            type: 'text',
            text: pref ? JSON.stringify(pref, null, 2) : `No preference found for ${preference_type}`,
          },
        ],
      };
    }

    return {
      content: [
        {
          type: 'text',
          text: `👤 User Preferences for ${user_id}:\n${JSON.stringify(userPrefs, null, 2)}`,
        },
      ],
    };
  }

  async suggestOptimalSettings(args) {
    const { image_properties, mask_properties, user_id } = args;
    
    const suggestions = {
      recommended_algorithm: 'lama',
      strength: 0.8,
      guidance_scale: 7.5,
      reasoning: [],
    };

    // Algorithm selection logic
    if (image_properties.has_faces) {
      suggestions.recommended_algorithm = 'sd_inpainting';
      suggestions.reasoning.push('Detected faces - using SD for better face preservation');
    } else if (mask_properties?.area_percentage > 0.3) {
      suggestions.recommended_algorithm = 'mat';
      suggestions.reasoning.push('Large mask area - MAT excels at filling large regions');
    } else if (image_properties.complexity === 'high') {
      suggestions.recommended_algorithm = 'edge_connect';
      suggestions.reasoning.push('High complexity image - EdgeConnect preserves fine details');
    }

    // Parameter adjustments
    if (mask_properties?.edge_sharpness === 'sharp') {
      suggestions.strength = 0.9;
      suggestions.reasoning.push('Sharp mask edges - increased strength for better blending');
    }

    // User preference integration
    if (user_id) {
      const userPrefs = this.userPreferences.get(user_id);
      if (userPrefs?.algorithm?.value) {
        suggestions.user_preferred_algorithm = userPrefs.algorithm.value;
        suggestions.reasoning.push(`User previously preferred: ${userPrefs.algorithm.value}`);
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: `🎯 Optimal Settings Suggestions:\n${JSON.stringify(suggestions, null, 2)}`,
        },
      ],
    };
  }

  async trackSessionMetrics(args) {
    const { session_id, action, metadata } = args;
    
    if (!this.sessionData.has(session_id)) {
      this.sessionData.set(session_id, {
        start_time: new Date().toISOString(),
        actions: [],
      });
    }
    
    this.sessionData.get(session_id).actions.push({
      action,
      timestamp: new Date().toISOString(),
      metadata,
    });

    return {
      content: [
        {
          type: 'text',
          text: `📊 Session metric tracked: ${action} for session ${session_id}`,
        },
      ],
    };
  }

  async generateImprovementSuggestions(args) {
    const { current_result, user_feedback, algorithm_used } = args;
    
    const suggestions = [];
    
    if (user_feedback?.includes('blurry') || user_feedback?.includes('blur')) {
      suggestions.push({
        issue: 'Blurry result',
        suggestion: 'Try increasing strength to 0.9 or switch to MAT algorithm',
        priority: 'high',
      });
    }
    
    if (user_feedback?.includes('color') || user_feedback?.includes('colour')) {
      suggestions.push({
        issue: 'Color mismatch',
        suggestion: 'Use EdgeConnect for better color consistency, or adjust guidance scale',
        priority: 'medium',
      });
    }
    
    if (algorithm_used === 'lama' && user_feedback?.includes('detail')) {
      suggestions.push({
        issue: 'Lack of detail',
        suggestion: 'Switch to SD inpainting with detailed prompt for better texture generation',
        priority: 'high',
      });
    }

    return {
      content: [
        {
          type: 'text',
          text: `💡 Improvement Suggestions:\n${JSON.stringify(suggestions, null, 2)}`,
        },
      ],
    };
  }

  async persistFeedback(feedbackEntry) {
    try {
      const feedbackFile = path.join(process.cwd(), 'feedback_data.json');
      let existingData = [];
      
      try {
        const data = await fs.readFile(feedbackFile, 'utf8');
        existingData = JSON.parse(data);
      } catch (error) {
        // File doesn't exist yet, start with empty array
      }
      
      existingData.push(feedbackEntry);
      await fs.writeFile(feedbackFile, JSON.stringify(existingData, null, 2));
    } catch (error) {
      console.error('Failed to persist feedback:', error);
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('🎯 Interactive Feedback MCP Server running...');
  }
}

const server = new InteractiveFeedbackServer();
server.run().catch(console.error);
