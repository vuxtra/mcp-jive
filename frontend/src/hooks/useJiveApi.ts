// React Hook for Jive MCP API Integration

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { JiveApiClient } from '../lib/api/client';
import { useNamespace } from '../contexts/NamespaceContext';
import {
  JiveApiConfig,
  WorkItem,
  CreateWorkItemRequest,
  UpdateWorkItemRequest,
  SearchWorkItemsRequest,
  SearchWorkItemsResponse,
  ConnectionState,
  WebSocketMessage,
} from '../types';

interface UseJiveApiOptions {
  config?: Partial<JiveApiConfig>;
  autoConnect?: boolean;
  enableWebSocket?: boolean;
}

interface UseJiveApiReturn {
  // API Client
  client: JiveApiClient | null;
  
  // WebSocket State
  connectionState: ConnectionState;
  
  // Loading States
  isLoading: boolean;
  isInitializing: boolean;
  
  // Error State
  error: string | null;
  
  // API Methods
  createWorkItem: (data: CreateWorkItemRequest) => Promise<WorkItem>;
  getWorkItem: (id: string) => Promise<WorkItem>;
  updateWorkItem: (id: string, data: UpdateWorkItemRequest) => Promise<WorkItem>;
  deleteWorkItem: (id: string) => Promise<void>;
  searchWorkItems: (params: SearchWorkItemsRequest) => Promise<SearchWorkItemsResponse>;
  getWorkItemHierarchy: (id: string, options?: any) => Promise<any>;
  trackProgress: (id: string, data: any) => Promise<any>;
  reorderWorkItems: (workItemIds: string[], parentId?: string) => Promise<any>;
  
  // WebSocket Methods
  connectWebSocket: () => Promise<void>;
  disconnectWebSocket: () => void;
  sendMessage: (message: Omit<WebSocketMessage, 'timestamp'>) => void;
  subscribeToEvents: (eventType: string, handler: (message: WebSocketMessage) => void) => () => void;
  
  // Utility Methods
  clearError: () => void;
  reconnect: () => Promise<void>;
}

// Create default config function to avoid SSR issues with process.env
function createDefaultConfig(): JiveApiConfig {
  // Only access process.env in browser context or provide fallbacks
  // Empty baseUrl means use relative URLs for Next.js API routes
  const baseUrl = (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_JIVE_API_URL) 
    ? process.env.NEXT_PUBLIC_JIVE_API_URL 
    : '';
  
  const wsUrl = (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_JIVE_WS_URL) 
    ? process.env.NEXT_PUBLIC_JIVE_WS_URL 
    : 'ws://localhost:3454/ws';

  const config = {
    baseUrl,
    wsUrl,
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000,
  };

  // Debug logging only in browser context
  if (typeof window !== 'undefined') {
    console.log('[DEBUG] Environment variables:', {
      NEXT_PUBLIC_JIVE_API_URL: process.env.NEXT_PUBLIC_JIVE_API_URL,
      NEXT_PUBLIC_JIVE_WS_URL: process.env.NEXT_PUBLIC_JIVE_WS_URL,
      config: config
    });
  }

  return config;
}

// Load settings from localStorage
function loadSettingsFromStorage(): Partial<JiveApiConfig> {
  try {
    // Check if we're in a browser environment
    if (typeof window !== 'undefined' && window.localStorage) {
      const savedSettings = localStorage.getItem('jive-app-settings');
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        return {
          timeout: settings.apiTimeout || 30000,
        };
      }
    }
  } catch (error) {
    console.warn('Failed to load settings from localStorage:', error);
  }
  return {};
}

export function useJiveApi(options: UseJiveApiOptions = {}): UseJiveApiReturn {
  const {
    config: userConfig = {},
    autoConnect = true,
    enableWebSocket = true, // Re-enabled after fixing server WebSocket endpoint
  } = options;

  // Get current namespace from context
  const { currentNamespace } = useNamespace();

  // Memoize the user config to prevent unnecessary re-renders
  const memoizedUserConfig = useMemo(() => userConfig, [JSON.stringify(userConfig)]);

  // Memoize the final config to prevent unnecessary re-renders
  const [storageConfig, setStorageConfig] = useState(() => loadSettingsFromStorage());
  const config = useMemo(() => ({
    ...createDefaultConfig(),
    ...storageConfig,
    ...memoizedUserConfig
  }), [storageConfig, memoizedUserConfig]);

  // Load settings from localStorage on client side only
  useEffect(() => {
    const newStorageConfig = loadSettingsFromStorage();
    setStorageConfig(newStorageConfig);
  }, [memoizedUserConfig]);

  // State
  const [client, setClient] = useState<JiveApiClient | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    isConnected: false,
    isConnecting: false,
    reconnectAttempts: 0,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const eventHandlersRef = useRef<Map<string, ((message: WebSocketMessage) => void)[]>>(new Map());

  // Refs to prevent stale closures
  const clientRef = useRef<JiveApiClient | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // WebSocket connection using react-use-websocket
  const {
    sendMessage: sendWebSocketMessage,
    lastMessage,
    readyState,
    getWebSocket
  } = useWebSocket(
    enableWebSocket && typeof window !== 'undefined' ? config.wsUrl : null,
    {
      shouldReconnect: () => true,
      reconnectAttempts: 10,
      reconnectInterval: (attemptNumber) => Math.min(Math.pow(2, attemptNumber) * 1000, 30000),
      onOpen: () => {
        reconnectAttemptsRef.current = 0;
        setConnectionState({
          isConnected: true,
          isConnecting: false,
          reconnectAttempts: 0,
          lastConnected: new Date()
        });
      },
      onClose: () => {
        setConnectionState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false
        }));
      },
      onError: (event) => {
        console.error('[WebSocket] Connection error:', event);
        setError('WebSocket connection failed');
      },
      onReconnectStop: (numAttempts) => {
        console.error('[WebSocket] Reconnection stopped after', numAttempts, 'attempts');
        setError('Failed to reconnect to WebSocket after multiple attempts');
        setConnectionState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          reconnectAttempts: numAttempts
        }));
      }
    }
  );

  // Update connection state based on readyState
  useEffect(() => {
    const isConnecting = readyState === ReadyState.CONNECTING;
    const isConnected = readyState === ReadyState.OPEN;
    
    setConnectionState(prev => ({
      ...prev,
      isConnected,
      isConnecting
    }));
  }, [readyState]);

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data);
        
        // Create WebSocket message with timestamp
        const message: WebSocketMessage = {
          ...data,
          timestamp: new Date().toISOString()
        };
        
        // Emit to all registered handlers
        eventHandlersRef.current.forEach((handlers, eventType) => {
          if (eventType === 'message' || data.type === eventType) {
            handlers.forEach(handler => {
              try {
                handler(message);
              } catch (error) {
                console.error('[WebSocket] Error in event handler:', error);
              }
            });
          }
        });
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error);
      }
    }
  }, [lastMessage]);

  // Initialize HTTP client
  useEffect(() => {
    let isMounted = true;
    
    const initializeClient = async () => {
      try {
        setIsInitializing(true);
        setError(null);

        // Initialize HTTP client
        const httpClient = new JiveApiClient(config);
        
        if (!isMounted) {
          return;
        }
        
        setClient(httpClient);
        clientRef.current = httpClient;
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to initialize Jive API');
        }
      } finally {
        if (isMounted) {
          setIsInitializing(false);
        }
      }
    };

    initializeClient();

    // Cleanup on unmount
    return () => {
      isMounted = false;
      if (clientRef.current) {
        clientRef.current = null;
      }
    };
  }, [config]);

  // Update client namespace when context changes
  useEffect(() => {
    if (clientRef.current) {
      // Convert 'default' to null for the API client
      const namespace = currentNamespace === 'default' ? null : currentNamespace;
      clientRef.current.setNamespace(namespace);
    }
  }, [currentNamespace]);

  // API Methods with error handling
  const createWorkItem = useCallback(async (data: CreateWorkItemRequest): Promise<WorkItem> => {
    if (!clientRef.current) throw new Error('API client not initialized');
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await clientRef.current.createWorkItem(data);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to create work item');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create work item';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getWorkItem = useCallback(async (id: string): Promise<WorkItem> => {
    if (!clientRef.current) throw new Error('API client not initialized');
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await clientRef.current.getWorkItem(id);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to get work item');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get work item';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateWorkItem = useCallback(async (id: string, data: UpdateWorkItemRequest): Promise<WorkItem> => {
    if (!clientRef.current) throw new Error('API client not initialized');
    
    setIsLoading(true);
    setError(null);
    
    try {
      const request = { ...data, work_item_id: id };
      const response = await clientRef.current.updateWorkItem(request);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to update work item');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update work item';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteWorkItem = useCallback(async (id: string): Promise<void> => {
    if (!clientRef.current) throw new Error('API client not initialized');
    
    setIsLoading(true);
    setError(null);
    
    try {
      await clientRef.current.deleteWorkItem(id);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete work item';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const searchWorkItems = useCallback(async (params: SearchWorkItemsRequest): Promise<SearchWorkItemsResponse> => {
    if (!clientRef.current) throw new Error('API client not initialized');
    
    setIsLoading(true);
    setError(null);
    
    try {
      return await clientRef.current.searchWorkItems(params);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to search work items';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getWorkItemHierarchy = useCallback(async (id: string, options?: any): Promise<any> => {
    if (!clientRef.current) throw new Error('API client not initialized');
    
    setIsLoading(true);
    setError(null);
    
    try {
      return await clientRef.current.getWorkItemHierarchy(id, options);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get work item hierarchy';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);



  const trackProgress = useCallback(async (id: string, data: any): Promise<any> => {
    if (!clientRef.current) throw new Error('API client not initialized');
    
    setIsLoading(true);
    setError(null);
    
    try {
      return await clientRef.current.trackProgress(id, data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to track progress';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reorderWorkItems = useCallback(async (workItemIds: string[], parentId?: string): Promise<any> => {
    if (!clientRef.current) throw new Error('API client not initialized');
    
    setIsLoading(true);
    setError(null);
    
    try {
      return await clientRef.current.reorderWorkItems(workItemIds, parentId);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reorder work items';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // WebSocket Methods
  const connectWebSocket = useCallback(async (): Promise<void> => {
    if (readyState === ReadyState.CLOSED || readyState === ReadyState.UNINSTANTIATED) {
      // react-use-websocket will automatically connect when the URL is provided
    }
  }, [readyState]);

  const disconnectWebSocket = useCallback((): void => {
    // Use react-use-websocket's disconnect method
    if (readyState === ReadyState.OPEN || readyState === ReadyState.CONNECTING) {
      // The disconnect will be handled by react-use-websocket
    }
  }, [readyState]);

  const sendMessage = useCallback((message: Omit<WebSocketMessage, 'timestamp'>): void => {
    if (readyState !== ReadyState.OPEN) {
      throw new Error('WebSocket is not connected');
    }
    
    const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
    sendWebSocketMessage(messageStr);
  }, [readyState, sendWebSocketMessage]);

  const subscribeToEvents = useCallback((eventType: string, handler: (message: WebSocketMessage) => void): () => void => {
    // Add handler to event handlers map
    const handlers = eventHandlersRef.current.get(eventType) || [];
    handlers.push(handler);
    eventHandlersRef.current.set(eventType, handlers);
    
    // Return unsubscribe function
    return () => {
      const currentHandlers = eventHandlersRef.current.get(eventType);
      if (currentHandlers) {
        const filteredHandlers = currentHandlers.filter(h => h !== handler);
        if (filteredHandlers.length === 0) {
          eventHandlersRef.current.delete(eventType);
        } else {
          eventHandlersRef.current.set(eventType, filteredHandlers);
        }
      }
    };
  }, []);

  // Health check method
  const checkHealth = useCallback(async (): Promise<boolean> => {
    if (!clientRef.current) return false;
    
    try {
      return await clientRef.current.healthCheck();
    } catch (error) {
      return false;
    }
  }, []);

  // Remove periodic health checks - rely on WebSocket events for real-time connection status
  // The WebSocket client already handles connection state management and reconnection
  // No need for polling when we have real-time WebSocket events

  // Utility Methods
  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  const reconnect = useCallback(async (): Promise<void> => {
    // react-use-websocket handles reconnection automatically
  }, []);

  return {
    // Client
    client,
    connectionState,
    
    // Loading States
    isLoading,
    isInitializing,
    
    // Error State
    error,
    
    // API Methods
    createWorkItem,
    getWorkItem,
    updateWorkItem,
    deleteWorkItem,
    searchWorkItems,
    getWorkItemHierarchy,
    trackProgress,
    reorderWorkItems,
    
    // WebSocket Methods
    connectWebSocket,
    disconnectWebSocket,
    sendMessage,
    subscribeToEvents,
    
    // Utility Methods
    clearError,
    reconnect,
  };
}

export type { UseJiveApiReturn, UseJiveApiOptions };