// React Hook for Jive MCP API Integration

import { useState, useEffect, useCallback, useRef } from 'react';
import { JiveApiClient } from '../lib/api/client';
import { JiveWebSocketClient } from '../lib/api/websocket';
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
  
  // WebSocket Client
  wsClient: JiveWebSocketClient | null;
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
  
  // WebSocket Methods
  connectWebSocket: () => Promise<void>;
  disconnectWebSocket: () => void;
  sendMessage: (message: Omit<WebSocketMessage, 'timestamp'>) => void;
  subscribeToEvents: (eventType: string, handler: (message: WebSocketMessage) => void) => () => void;
  
  // Utility Methods
  clearError: () => void;
  reconnect: () => Promise<void>;
}

const DEFAULT_CONFIG: JiveApiConfig = {
  baseUrl: process.env.NEXT_PUBLIC_JIVE_API_URL || 'http://localhost:3454',
  wsUrl: process.env.NEXT_PUBLIC_JIVE_WS_URL || 'ws://localhost:3454/ws',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
};

// Load settings from localStorage
function loadSettingsFromStorage(): Partial<JiveApiConfig> {
  try {
    // Check if we're in a browser environment
    if (typeof window !== 'undefined' && window.localStorage) {
      const savedSettings = localStorage.getItem('jive-app-settings');
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        return {
          timeout: settings.apiTimeout || DEFAULT_CONFIG.timeout,
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

  // Initialize config with defaults and user config (localStorage will be loaded in useEffect)
  const [config, setConfig] = useState({ ...DEFAULT_CONFIG, ...userConfig });

  // Load settings from localStorage on client side only
  useEffect(() => {
    const storageConfig = loadSettingsFromStorage();
    setConfig({ ...DEFAULT_CONFIG, ...storageConfig, ...userConfig });
  }, [JSON.stringify(userConfig)]);

  // State
  const [client, setClient] = useState<JiveApiClient | null>(null);
  const [wsClient, setWsClient] = useState<JiveWebSocketClient | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    isConnected: false,
    isConnecting: false,
    reconnectAttempts: 0,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Refs to prevent stale closures
  const clientRef = useRef<JiveApiClient | null>(null);
  const wsClientRef = useRef<JiveWebSocketClient | null>(null);

  // Initialize clients
  useEffect(() => {
    const initializeClients = async () => {
      try {
        setIsInitializing(true);
        setError(null);

        // Initialize HTTP client
        const httpClient = new JiveApiClient(config);
        setClient(httpClient);
        clientRef.current = httpClient;

        // Initialize WebSocket client if enabled
        if (enableWebSocket) {
          const websocketClient = new JiveWebSocketClient(config);
          setWsClient(websocketClient);
          wsClientRef.current = websocketClient;

          // Subscribe to connection state changes
          websocketClient.onConnection((state) => {
            setConnectionState(state);
          });

          // Auto-connect if enabled
          if (autoConnect) {
            await websocketClient.connect();
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to initialize Jive API');
      } finally {
        setIsInitializing(false);
      }
    };

    initializeClients();

    // Cleanup on unmount
    return () => {
      if (wsClientRef.current) {
        wsClientRef.current.disconnect();
      }
    };
  }, [JSON.stringify(config), autoConnect, enableWebSocket]);

  // API Methods with error handling
  const createWorkItem = useCallback(async (data: CreateWorkItemRequest): Promise<WorkItem> => {
    if (!clientRef.current) throw new Error('API client not initialized');
    
    setIsLoading(true);
    setError(null);
    
    try {
      return await clientRef.current.createWorkItem(data);
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
      return await clientRef.current.getWorkItem(id);
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
      return await clientRef.current.updateWorkItem(id, data);
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

  // WebSocket Methods
  const connectWebSocket = useCallback(async (): Promise<void> => {
    if (!wsClientRef.current) throw new Error('WebSocket client not initialized');
    
    setError(null);
    
    try {
      await wsClientRef.current.connect();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect WebSocket';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const disconnectWebSocket = useCallback((): void => {
    if (wsClientRef.current) {
      wsClientRef.current.disconnect();
    }
  }, []);

  const sendMessage = useCallback((message: Omit<WebSocketMessage, 'timestamp'>): void => {
    if (!wsClientRef.current) {
      throw new Error('WebSocket client not initialized');
    }
    
    wsClientRef.current.send(message);
  }, []);

  const subscribeToEvents = useCallback((eventType: string, handler: (message: WebSocketMessage) => void): () => void => {
    if (!wsClientRef.current) {
      throw new Error('WebSocket client not initialized');
    }
    
    return wsClientRef.current.on(eventType, handler);
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
    if (wsClientRef.current) {
      wsClientRef.current.disconnect();
      await wsClientRef.current.connect();
    }
  }, []);

  return {
    // Clients
    client,
    wsClient,
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