// Jive MCP API Client

import {
  JiveApiConfig,
  ApiResponse,
  WorkItem as ApiWorkItem,
  CreateWorkItemRequest,
  UpdateWorkItemRequest,
  SearchWorkItemsRequest,
  SearchWorkItemsResponse as ApiSearchWorkItemsResponse,
} from './types';
import type { WorkItem, SearchWorkItemsResponse } from '../../types';

class JiveApiClient {
  private config: JiveApiConfig;
  private abortController: AbortController | null = null;
  private currentNamespace: string | null = null;

  constructor(config: JiveApiConfig) {
    this.config = config;
  }

  setNamespace(namespace: string | null): void {
    this.currentNamespace = namespace;
  }

  getCurrentNamespace(): string | null {
    return this.currentNamespace;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    this.abortController = new AbortController();
    
    const url = `${this.config.baseUrl}${endpoint}`;
    console.log('Making request to URL:', url);
    console.log('Base URL:', this.config.baseUrl);
    console.log('Endpoint:', endpoint);
    console.log('Current namespace:', this.currentNamespace);
    
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    // Add namespace header if set
    if (this.currentNamespace) {
      defaultHeaders['X-Namespace'] = this.currentNamespace;
    }
    
    console.log('Request headers:', defaultHeaders);

    const requestOptions: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
      signal: this.abortController.signal,
    };

    // Add timeout
    const timeoutId = setTimeout(() => {
      if (this.abortController) {
        this.abortController.abort();
      }
    }, this.config.timeout);

    try {
      const response = await fetch(url, requestOptions);
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new ApiError(
          `HTTP ${response.status}: ${errorText}`,
          response.status,
          errorText
        );
      }

      const data = await response.json();
      return data as ApiResponse<T>;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError('Request timeout', 408);
      }
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new ApiError(
        `Network error: ${errorMessage}`,
        0,
        error
      );
    }
  }

  private async retryRequest<T>(
    requestFn: () => Promise<ApiResponse<T>>,
    attempts: number = this.config.retryAttempts
  ): Promise<ApiResponse<T>> {
    let lastError: ApiError = new ApiError('Request failed after all retry attempts');
    
    for (let i = 0; i <= attempts; i++) {
      try {
        return await requestFn();
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        lastError = error instanceof ApiError ? error : new ApiError(errorMessage);
        
        // Don't retry on client errors (4xx)
        if (lastError.status && lastError.status >= 400 && lastError.status < 500) {
          throw lastError;
        }
        
        if (i < attempts) {
          await new Promise(resolve => 
            setTimeout(resolve, this.config.retryDelay * Math.pow(2, i))
          );
        }
      }
    }
    
    throw lastError;
  }

  // Work Item Management Methods - Integrated with Jive MCP API
  async createWorkItem(request: CreateWorkItemRequest): Promise<ApiResponse<WorkItem>> {
    const response = await this.retryRequest(() =>
      this.makeRequest<any>('/mcp', {
        method: 'POST',
        body: JSON.stringify({
          method: 'tools/call',
          params: {
            name: 'jive_manage_work_item',
            arguments: {
              action: 'create',
              type: request.type,
              title: request.title,
              description: request.description,
              status: request.status || 'not_started',
              priority: request.priority || 'medium',
              parent_id: request.parent_id,
              context_tags: request.context_tags || [],
              complexity: request.complexity || 'moderate',
              notes: request.notes,
              acceptance_criteria: request.acceptance_criteria || [],
            },
          },
        }),
      })
    );
    
    // Handle ToolCallResponse structure and extract work item data
    return this.extractWorkItemFromResponse(response);
  }

  async getWorkItem(workItemId: string): Promise<ApiResponse<WorkItem>> {
    const response = await this.retryRequest(() =>
      this.makeRequest<any>('/mcp', {
        method: 'POST',
        body: JSON.stringify({
          method: 'tools/call',
          params: {
            name: 'jive_get_work_item',
            arguments: {
              work_item_id: workItemId,
              include_children: false,
              include_metadata: true,
              format: 'detailed',
            },
          },
        }),
      })
    );
    
    // Handle ToolCallResponse structure and extract work item data
    return this.extractWorkItemFromResponse(response);
  }

  async updateWorkItem(request: UpdateWorkItemRequest): Promise<ApiResponse<WorkItem>> {
    const response = await this.retryRequest(() =>
      this.makeRequest<any>('/mcp', {
        method: 'POST',
        body: JSON.stringify({
          method: 'tools/call',
          params: {
            name: 'jive_manage_work_item',
            arguments: {
              action: 'update',
              work_item_id: request.work_item_id,
              title: request.title,
              description: request.description,
              status: request.status,
              priority: request.priority,
              notes: request.notes,
              acceptance_criteria: request.acceptance_criteria,
            },
          },
        }),
      })
    );
    
    // Handle ToolCallResponse structure and extract work item data
    return this.extractWorkItemFromResponse(response);
  }

  async deleteWorkItem(workItemId: string): Promise<ApiResponse<void>> {
    return this.retryRequest(() =>
      this.makeRequest<void>('/mcp', {
        method: 'POST',
        body: JSON.stringify({
          method: 'tools/call',
          params: {
            name: 'jive_manage_work_item',
            arguments: {
              action: 'delete',
              work_item_id: workItemId,
            },
          },
        }),
      })
    );
  }

  // Transform API WorkItem to frontend WorkItem (map item_type to type and progress_percentage to progress)
  private extractWorkItemFromResponse(response: any): ApiResponse<WorkItem> {
    // Handle ToolCallResponse structure: { success: boolean, result: { data: WorkItem, message: string, metadata: any } }
    if (response && typeof response === 'object' && 'success' in response) {
      if (response.success && response.result) {
        const workItemData = response.result.data || response.result;
        return {
          success: true,
          data: this.transformWorkItem(workItemData)
        };
      } else {
        return {
          success: false,
          error: response.error || 'Operation failed'
        };
      }
    }
    
    // Fallback: handle direct response
    if (response && response.data) {
      return {
        success: true,
        data: this.transformWorkItem(response.data)
      };
    }
    
    return {
      success: false,
      error: 'Invalid response format'
    };
  }

  private transformWorkItem(apiWorkItem: any): WorkItem {
    if (!apiWorkItem) return apiWorkItem;
    
    const transformed = {
      ...apiWorkItem,
      type: apiWorkItem.item_type, // Map item_type to type for frontend compatibility
    };
    
    // Convert progress_percentage (0-100) to progress (0.0-1.0) if present
    if (typeof apiWorkItem.progress_percentage === 'number') {
      transformed.progress = apiWorkItem.progress_percentage / 100;
    } else if (typeof apiWorkItem.progress === 'undefined') {
      // Default progress to 0.0 if not present
      transformed.progress = 0.0;
    }
    
    return transformed;
  }

  // Transform array of work items
  private transformWorkItems(workItems: any[]): WorkItem[] {
    if (!Array.isArray(workItems)) return workItems;
    return workItems.map(item => this.transformWorkItem(item));
  }

  async searchWorkItems(request: SearchWorkItemsRequest): Promise<SearchWorkItemsResponse> {
    // Use hybrid search for empty queries to enable loading all items
    const searchType = request.search_type || (request.query.trim() === '' ? 'hybrid' : 'keyword');
    
    console.log('🔍 searchWorkItems called - namespace:', this.currentNamespace, 'query:', request.query);
    
    const requestBody = {
      method: 'tools/call',
      params: {
        name: 'jive_search_content',
        arguments: {
          query: request.query,
          search_type: searchType,
          filters: request.filters,
          limit: request.limit || 10,
          format: request.format || 'summary',
        },
      },
    };
    
    const response = await this.retryRequest(() =>
      this.makeRequest<ApiSearchWorkItemsResponse>('/mcp', {
        method: 'POST',
        body: JSON.stringify(requestBody),
      })
    );
    
    console.log('Raw API response:', response);
    console.log('Response type:', typeof response);
    console.log('Response keys:', Object.keys(response || {}));
    
    // Handle MCP JSON-RPC response format
    if (response && typeof response === 'object' && 'result' in response) {
      const mcpResponse = response as any;
      console.log('MCP response detected, result:', mcpResponse.result);
      
      if (mcpResponse.result && mcpResponse.result.content && Array.isArray(mcpResponse.result.content)) {
        const content = mcpResponse.result.content[0];
        if (content && content.type === 'text' && content.text) {
          try {
            let textContent = content.text;
            
            // Handle Python TextContent object format: [TextContent(type='text', text='...')]
            if (textContent.startsWith('[TextContent(')) {
              // Find the start and end of the JSON content
              const startMarker = "text='";
              const endMarker = "', annotations=";
              const startIndex = textContent.indexOf(startMarker);
              const endIndex = textContent.indexOf(endMarker);
              
              if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
                textContent = textContent.substring(startIndex + startMarker.length, endIndex);
                // Handle double-escaped JSON - unescape the escaped characters
                textContent = textContent.replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\');
                console.log('Extracted and unescaped JSON from TextContent:', textContent.substring(0, 200) + '...');
              } else {
                console.error('Could not extract JSON from TextContent format');
                throw new Error('Invalid TextContent format');
              }
            }
            
            const parsedResult = JSON.parse(textContent);
            console.log('Parsed MCP result:', parsedResult);
            
            if (parsedResult.results && Array.isArray(parsedResult.results)) {
              parsedResult.results = this.transformWorkItems(parsedResult.results);
            }
            return parsedResult as SearchWorkItemsResponse;
          } catch (parseError) {
            console.error('Failed to parse MCP response text:', parseError);
            console.error('Raw text content:', content.text);
            throw new Error('Invalid JSON in MCP response');
          }
        }
      }
    }
    
    // Handle ToolCallResponse format (legacy)
    if (response && typeof response === 'object' && 'success' in response) {
      const backendResponse = response as any;
      console.log('Has success property, backendResponse:', backendResponse);
      console.log('backendResponse.success:', backendResponse.success);
      console.log('backendResponse.result:', backendResponse.result);
      
      if (backendResponse.success && backendResponse.result) {
        // MCP tool response format: result is an array with text field containing JSON
        if (Array.isArray(backendResponse.result) && backendResponse.result.length > 0) {
          const textResult = backendResponse.result[0];
          
          if (textResult.type === 'text' && textResult.text) {
            try {
              const parsedResult = JSON.parse(textResult.text);
              
              if (parsedResult.results && Array.isArray(parsedResult.results)) {
                parsedResult.results = this.transformWorkItems(parsedResult.results);
              }
              return parsedResult as SearchWorkItemsResponse;
            } catch (parseError) {
              console.error('Failed to parse MCP tool response:', parseError);
              throw new Error('Invalid response format from MCP tool');
            }
          }
        }
        
        // Fallback: direct result object (current format)
        const result = backendResponse.result;
        console.log('Fallback: direct result object, result:', result);
        console.log('result.results:', result.results);
        console.log('result.results is array:', Array.isArray(result.results));
        if (result.results && Array.isArray(result.results)) {
          console.log('Using direct result.results, count:', result.results.length);
          result.results = this.transformWorkItems(result.results);
          return result as SearchWorkItemsResponse;
        }
        
        // Handle case where result is the search response directly
        if (result && Array.isArray(result)) {
          return {
            success: true,
            results: this.transformWorkItems(result),
            total_found: result.length
          } as SearchWorkItemsResponse;
        }
      } else {
        throw new Error(backendResponse.error || 'Search failed');
      }
    }
    
    // Fallback: return the response as-is with transformation
    const result = (response as any).data || response;
    if (result.results && Array.isArray(result.results)) {
      result.results = this.transformWorkItems(result.results);
    }
    return result;
  }

  async getWorkItemHierarchy(
    workItemId: string,
    relationshipType: string = 'children'
  ): Promise<ApiResponse<any>> {
    return this.retryRequest(() =>
      this.makeRequest('/mcp', {
        method: 'POST',
        body: JSON.stringify({
          method: 'tools/call',
          params: {
            name: 'jive_get_hierarchy',
            arguments: {
              work_item_id: workItemId,
              relationship_type: relationshipType,
              action: 'get',
              max_depth: 5,
              include_completed: true,
              include_cancelled: false,
              include_metadata: true,
            },
          },
        }),
      })
    );
  }



  async trackProgress(
    workItemId: string,
    progressData: any
  ): Promise<ApiResponse<any>> {
    return this.retryRequest(() =>
      this.makeRequest('/mcp', {
        method: 'POST',
        body: JSON.stringify({
          method: 'tools/call',
          params: {
            name: 'jive_track_progress',
            arguments: {
              action: 'track',
              work_item_id: workItemId,
              progress_data: {
                progress_percentage: progressData.progress_percentage,
                status: progressData.status,
                notes: progressData.notes,
                estimated_completion: progressData.estimated_completion,
                blockers: progressData.blockers || [],
                auto_calculate_status: true,
              },
            },
          },
        }),
      })
    );
  }

  async reorderWorkItems(
    workItemIds: string[],
    parentId?: string
  ): Promise<ApiResponse<any>> {
    return this.retryRequest(() =>
      this.makeRequest('/mcp', {
        method: 'POST',
        body: JSON.stringify({
          method: 'tools/call',
          params: {
            name: 'jive_reorder_work_items',
            arguments: {
              action: 'reorder',
              work_item_ids: workItemIds,
              parent_id: parentId || null,
            },
          },
        }),
      })
    );
  }

  // Utility methods
  async healthCheck(): Promise<boolean> {
    try {
      // Use a lightweight search request as health check
      const response = await this.makeRequest('/search', {
        method: 'POST',
        body: JSON.stringify({
          query: '',
          limit: 1
        })
      });
      return response.success;
    } catch (error) {
      return false;
    }
  }

  cancelCurrentRequest(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  updateConfig(newConfig: Partial<JiveApiConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

// Custom API Error class
class ApiError extends Error {
  public status?: number;
  public details?: any;

  constructor(message: string, status?: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export { JiveApiClient, ApiError };
export type { JiveApiConfig };