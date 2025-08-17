// Re-export API types with frontend-friendly interface
export type {
  JiveApiConfig,
  ApiResponse,
  CreateWorkItemRequest,
  UpdateWorkItemRequest,
  SearchWorkItemsRequest,
  SearchWorkItemsResponse,
  WebSocketMessage,
  ConnectionState,
  ApiError,
} from './lib/api/types';

// Import the API WorkItem type
import type { WorkItem as ApiWorkItem } from './lib/api/types';

// Frontend WorkItem interface that maps item_type to type for compatibility
export interface WorkItem extends Omit<ApiWorkItem, 'item_type'> {
  type: ApiWorkItem['item_type'];
  item_type: ApiWorkItem['item_type']; // Keep both for backward compatibility
  
  // Frontend-specific properties
  displaySequence?: string; // Generated sequence number for display (e.g., "1.1", "2.3")
  children?: WorkItem[]; // Hierarchical children for tree display
}

// Type aliases for convenience
export type WorkItemType = WorkItem['type'];
export type WorkItemStatus = WorkItem['status'];
export type WorkItemPriority = WorkItem['priority'];
export type WorkItemComplexity = WorkItem['complexity'];