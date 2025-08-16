// API Types for Jive MCP Integration

export interface JiveApiConfig {
  baseUrl: string;
  wsUrl: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  error_code?: string;
}

export interface WorkItem {
  id: string;
  item_id: string;
  title: string;
  description: string;
  item_type: 'initiative' | 'epic' | 'feature' | 'story' | 'task';
  status: 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignee?: string;
  tags: string[];
  estimated_hours?: number;
  actual_hours?: number;
  progress: number;
  parent_id?: string;
  dependencies: string[];
  context_tags: string[];
  complexity: 'simple' | 'moderate' | 'complex';
  notes?: string;
  acceptance_criteria: string[];
  executable: boolean;
  execution_instructions?: string;
  created_at: string;
  updated_at: string;
  metadata: string;
}

export interface CreateWorkItemRequest {
  type: WorkItem['item_type'];
  title: string;
  description: string;
  status?: WorkItem['status'];
  priority?: WorkItem['priority'];
  parent_id?: string;
  context_tags?: string[];
  complexity?: WorkItem['complexity'];
  notes?: string;
  acceptance_criteria?: string[];
}

export interface UpdateWorkItemRequest {
  work_item_id: string;
  title?: string;
  description?: string;
  status?: WorkItem['status'];
  priority?: WorkItem['priority'];
  notes?: string;
  acceptance_criteria?: string[];
}

export interface SearchWorkItemsRequest {
  query: string;
  search_type?: 'semantic' | 'keyword' | 'hybrid';
  filters?: {
    type?: string[];
    status?: string[];
    priority?: string[];
  };
  limit?: number;
  format?: 'detailed' | 'summary' | 'minimal';
}

export interface SearchWorkItemsResponse {
  success: boolean;
  query: string;
  search_type: string;
  content_types: string[];
  results: WorkItem[];
  total_found: number;
  filters_applied: any;
}

export interface WebSocketMessage {
  type: 'work_item_update' | 'progress_update' | 'execution_update' | 'error';
  data: any;
  timestamp: string;
}

export interface ConnectionState {
  isConnected: boolean;
  isConnecting: boolean;
  lastConnected?: Date;
  reconnectAttempts: number;
  error?: string;
}

export interface ApiError extends Error {
  code?: string;
  status?: number;
  details?: any;
}