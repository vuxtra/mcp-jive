// Jive MCP API Client

import {
  JiveApiConfig,
  ApiResponse,
  WorkItem,
  CreateWorkItemRequest,
  UpdateWorkItemRequest,
  SearchWorkItemsRequest,
  SearchWorkItemsResponse,
  ApiError,
} from './types';

class JiveApiClient {
  private config: JiveApiConfig;
  private abortController: AbortController | null = null;

  constructor(config: JiveApiConfig) {
    this.config = config;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    this.abortController = new AbortController();
    
    const url = `${this.config.baseUrl}${endpoint}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

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
      
      if (error.name === 'AbortError') {
        throw new ApiError('Request timeout', 408);
      }
      
      throw new ApiError(
        `Network error: ${error.message}`,
        0,
        error
      );
    }
  }

  private async retryRequest<T>(
    requestFn: () => Promise<ApiResponse<T>>,
    attempts: number = this.config.retryAttempts
  ): Promise<ApiResponse<T>> {
    let lastError: ApiError;
    
    for (let i = 0; i <= attempts; i++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error instanceof ApiError ? error : new ApiError(error.message);
        
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
      this.makeRequest<any>('/api/mcp/jive_manage_work_item', {
        method: 'POST',
        body: JSON.stringify({
          tool_name: 'jive_manage_work_item',
          parameters: {
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
        }),
      })
    );
    
    // Handle ToolCallResponse structure and extract work item data
    return this.extractWorkItemFromResponse(response);
  }

  async getWorkItem(workItemId: string): Promise<ApiResponse<WorkItem>> {
    const response = await this.retryRequest(() =>
      this.makeRequest<any>('/api/mcp/jive_get_work_item', {
        method: 'POST',
        body: JSON.stringify({
          tool_name: 'jive_get_work_item',
          parameters: {
            work_item_id: workItemId,
            include_children: false,
            include_metadata: true,
            format: 'detailed',
          },
        }),
      })
    );
    
    // Handle ToolCallResponse structure and extract work item data
    return this.extractWorkItemFromResponse(response);
  }

  async updateWorkItem(request: UpdateWorkItemRequest): Promise<ApiResponse<WorkItem>> {
    const response = await this.retryRequest(() =>
      this.makeRequest<any>('/api/mcp/jive_manage_work_item', {
        method: 'POST',
        body: JSON.stringify({
          tool_name: 'jive_manage_work_item',
          parameters: {
            action: 'update',
            work_item_id: request.work_item_id,
            title: request.title,
            description: request.description,
            status: request.status,
            priority: request.priority,
            notes: request.notes,
            acceptance_criteria: request.acceptance_criteria,
          },
        }),
      })
    );
    
    // Handle ToolCallResponse structure and extract work item data
    return this.extractWorkItemFromResponse(response);
  }

  async deleteWorkItem(workItemId: string): Promise<ApiResponse<void>> {
    return this.retryRequest(() =>
      this.makeRequest<void>('/api/mcp/jive_manage_work_item', {
        method: 'POST',
        body: JSON.stringify({
          tool_name: 'jive_manage_work_item',
          parameters: {
            action: 'delete',
            work_item_id: workItemId,
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
    const response = await this.retryRequest(() =>
      this.makeRequest<SearchWorkItemsResponse>('/api/mcp/jive_search_content', {
        method: 'POST',
        body: JSON.stringify({
          tool_name: 'jive_search_content',
          parameters: {
            query: request.query,
            search_type: request.search_type || 'keyword',
            filters: request.filters,
            limit: request.limit || 10,
            format: request.format || 'summary',
          },
        }),
      })
    );
    
    // Handle ToolCallResponse format
    if (response && typeof response === 'object' && 'success' in response) {
      if (response.success && response.result) {
        const result = response.result;
        // Transform work items in the results
        if (result.results && Array.isArray(result.results)) {
          result.results = this.transformWorkItems(result.results);
        }
        return result;
      } else {
        throw new Error(response.error || 'Search failed');
      }
    }
    
    // Fallback: return the response as-is with transformation
    const result = response.data || response;
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
      this.makeRequest('/api/mcp/jive_get_hierarchy', {
        method: 'POST',
        body: JSON.stringify({
          tool_name: 'jive_get_hierarchy',
          parameters: {
            work_item_id: workItemId,
            relationship_type: relationshipType,
            action: 'get',
            max_depth: 5,
            include_completed: true,
            include_cancelled: false,
            include_metadata: true,
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
      this.makeRequest('/api/mcp/jive_track_progress', {
        method: 'POST',
        body: JSON.stringify({
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
        }),
      })
    );
  }

  // Utility methods
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