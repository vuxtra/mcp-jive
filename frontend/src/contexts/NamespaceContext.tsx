'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useJiveApiContext } from '../components/providers/JiveApiProvider';

interface NamespaceContextType {
  currentNamespace: string;
  availableNamespaces: string[];
  setNamespace: (namespace: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

const NamespaceContext = createContext<NamespaceContextType | undefined>(undefined);

interface NamespaceProviderProps {
  children: ReactNode;
}

export const NamespaceProvider: React.FC<NamespaceProviderProps> = ({ children }) => {
  // Initialize with null to prevent hydration mismatch, will be set in useEffect
  const [currentNamespace, setCurrentNamespace] = useState<string>('default');
  const [availableNamespaces, setAvailableNamespaces] = useState<string[]>(['default']);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isHydrated, setIsHydrated] = useState<boolean>(false);
  
  const { connectionState, sendMessage, setNamespace: setApiNamespace } = useJiveApiContext();

  // Handle hydration and localStorage loading
  useEffect(() => {
    setIsHydrated(true);
    const savedNamespace = localStorage.getItem('mcp-jive-namespace');
    if (savedNamespace) {
      setCurrentNamespace(savedNamespace);
    }
  }, []);

  // Update current namespace when available namespaces change
  useEffect(() => {
    if (isHydrated && availableNamespaces.length > 0) {
      const savedNamespace = localStorage.getItem('mcp-jive-namespace');
      if (savedNamespace && availableNamespaces.includes(savedNamespace)) {
        if (savedNamespace !== currentNamespace) {
          setCurrentNamespace(savedNamespace);
        }
      } else if (!availableNamespaces.includes(currentNamespace)) {
        // If current namespace is not in available list, default to 'default' or first available
        const defaultNamespace = availableNamespaces.includes('default') ? 'default' : availableNamespaces[0];
        if (defaultNamespace !== currentNamespace) {
          setCurrentNamespace(defaultNamespace);
        }
      }
    }
  }, [availableNamespaces, isHydrated]);

  // Save namespace to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('mcp-jive-namespace', currentNamespace);
  }, [currentNamespace]);

  // Sync namespace with API client whenever it changes
  useEffect(() => {
    if (setApiNamespace && typeof setApiNamespace === 'function' && isHydrated) {
      // Always send the namespace, including 'default', for proper backend isolation
      console.log('🔄 NamespaceContext: Setting API namespace to:', currentNamespace);
      setApiNamespace(currentNamespace);
    }
  }, [currentNamespace, setApiNamespace, isHydrated]);

  const setNamespace = async (namespace: string): Promise<void> => {
    if (namespace === currentNamespace) return;

    setIsLoading(true);
    setError(null);

    try {
      // If connected to server, send namespace change request
      if (connectionState?.isConnected && sendMessage) {
        try {
          sendMessage({
            type: 'work_item_update',
            data: {
              action: 'set_namespace_context',
              namespace: namespace === 'default' ? null : namespace
            }
          });
        } catch (err) {
          console.error('Error sending namespace change message:', err);
          // Continue with local state update even if message fails
        }
      }

      // Update local state
      setCurrentNamespace(namespace);

      // Trigger a refresh of work items or other data that depends on namespace
      window.dispatchEvent(new CustomEvent('namespace-changed', {
        detail: { namespace }
      }));

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to change namespace';
      setError(errorMessage);
      console.error('Error changing namespace:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch available namespaces from server REST API
  useEffect(() => {
    const fetchNamespaces = async () => {
      try {
        const response = await fetch('/api/namespaces');
        if (response.ok) {
          const data = await response.json();
          if (data.namespaces && Array.isArray(data.namespaces)) {
            // Ensure 'default' is always included and comes first
            const namespaces = [...data.namespaces];
            if (!namespaces.includes('default')) {
              namespaces.unshift('default');
            } else {
              // Move 'default' to the front if it exists
              const defaultIndex = namespaces.indexOf('default');
              if (defaultIndex > 0) {
                namespaces.splice(defaultIndex, 1);
                namespaces.unshift('default');
              }
            }
            setAvailableNamespaces(namespaces);
          }
        } else {
          console.error('Failed to fetch namespaces:', response.statusText);
          setAvailableNamespaces(['default']);
        }
      } catch (err) {
        console.error('Error fetching namespaces:', err);
        // Keep default namespace if fetch fails
        setAvailableNamespaces(['default']);
      }
    };

    fetchNamespaces();
  }, []);

  const value: NamespaceContextType = {
    currentNamespace,
    availableNamespaces,
    setNamespace,
    isLoading,
    error,
  };

  return (
    <NamespaceContext.Provider value={value}>
      {children}
    </NamespaceContext.Provider>
  );
};

export const useNamespace = (): NamespaceContextType => {
  const context = useContext(NamespaceContext);
  if (context === undefined) {
    throw new Error('useNamespace must be used within a NamespaceProvider');
  }
  return context;
};

export default NamespaceContext;