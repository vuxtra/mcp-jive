'use client';

// React Context Provider for Jive MCP API Integration

import React, { createContext, useContext, ReactNode } from 'react';
import { useJiveApi, UseJiveApiReturn, UseJiveApiOptions } from '../../hooks/useJiveApi';
import {
  JiveApiConfig,
  WorkItem,
  CreateWorkItemRequest,
  UpdateWorkItemRequest,
  SearchWorkItemsRequest,
  SearchWorkItemsResponse,
  ConnectionState,
  WebSocketMessage,
} from '../../types';

// Context type
type JiveApiContextType = UseJiveApiReturn | null;

// Create context
const JiveApiContext = createContext<JiveApiContextType>(null);

// Provider props
interface JiveApiProviderProps {
  children: ReactNode;
  config?: Partial<JiveApiConfig>;
  autoConnect?: boolean;
  enableWebSocket?: boolean;
}

// Provider component
export function JiveApiProvider({
  children,
  config,
  autoConnect = true,
  enableWebSocket = true,
}: JiveApiProviderProps) {
  const jiveApi = useJiveApi({
    config,
    autoConnect,
    enableWebSocket,
  });

  return (
    <JiveApiContext.Provider value={jiveApi}>
      {children}
    </JiveApiContext.Provider>
  );
}

// Hook to use the context
export function useJiveApiContext(): UseJiveApiReturn {
  const context = useContext(JiveApiContext);
  
  if (!context) {
    throw new Error('useJiveApiContext must be used within a JiveApiProvider');
  }
  
  return context;
}

// Convenience hooks for specific functionality
export function useWorkItems() {
  const {
    createWorkItem,
    getWorkItem,
    updateWorkItem,
    deleteWorkItem,
    searchWorkItems,
    getWorkItemHierarchy,
    trackProgress,
    isLoading,
    error,
    clearError,
  } = useJiveApiContext();

  return {
    createWorkItem,
    getWorkItem,
    updateWorkItem,
    deleteWorkItem,
    searchWorkItems,
    getWorkItemHierarchy,
    trackProgress,
    isLoading,
    error,
    clearError,
  };
}

export function useWebSocketConnection() {
  const {
    connectionState,
    connectWebSocket,
    disconnectWebSocket,
    sendMessage,
    subscribeToEvents,
    reconnect,
    error,
    clearError,
  } = useJiveApiContext();

  return {
    connectionState,
    connectWebSocket,
    disconnectWebSocket,
    sendMessage,
    subscribeToEvents,
    reconnect,
    error,
    clearError,
  };
}

// Connection status component
export function ConnectionStatus() {
  const { connectionState, reconnect, error } = useWebSocketConnection();

  if (!connectionState.isConnected && !connectionState.isConnecting) {
    return (
      <div className="flex items-center gap-2 px-3 py-1 bg-red-50 border border-red-200 rounded-md">
        <div className="w-2 h-2 bg-red-500 rounded-full" />
        <span className="text-sm text-red-700">Disconnected</span>
        <button
          onClick={reconnect}
          className="text-xs text-red-600 hover:text-red-800 underline"
        >
          Reconnect
        </button>
      </div>
    );
  }

  if (connectionState.isConnecting) {
    return (
      <div className="flex items-center gap-2 px-3 py-1 bg-yellow-50 border border-yellow-200 rounded-md">
        <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
        <span className="text-sm text-yellow-700">Connecting...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 px-3 py-1 bg-green-50 border border-green-200 rounded-md">
      <div className="w-2 h-2 bg-green-500 rounded-full" />
      <span className="text-sm text-green-700">Connected</span>
      {connectionState.lastConnected && (
        <span className="text-xs text-green-600">
          {new Date(connectionState.lastConnected).toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}

// Error boundary for API errors
interface ApiErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: string) => ReactNode;
}

export function ApiErrorBoundary({ children, fallback }: ApiErrorBoundaryProps) {
  const { error, clearError } = useJiveApiContext();

  if (error) {
    if (fallback) {
      return <>{fallback(error)}</>;
    }

    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-md">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-sm font-medium text-red-800">API Error</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
          </div>
          <button
            onClick={clearError}
            className="text-red-400 hover:text-red-600"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

// Loading wrapper component
interface LoadingWrapperProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function LoadingWrapper({ children, fallback }: LoadingWrapperProps) {
  const { isLoading, isInitializing } = useJiveApiContext();

  if (isInitializing) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-gray-600">Initializing Jive API...</span>
        </div>
      </div>
    );
  }

  if (isLoading && fallback) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

// Export types
export type {
  JiveApiProviderProps,
  ApiErrorBoundaryProps,
  LoadingWrapperProps,
};