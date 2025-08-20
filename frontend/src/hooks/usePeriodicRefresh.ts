import { useEffect, useRef, useCallback } from 'react';

interface UsePeriodicRefreshOptions {
  refreshFunction: () => Promise<void> | void;
  intervalMs?: number;
  enabled?: boolean;
  dependencies?: any[];
}

interface UsePeriodicRefreshReturn {
  startRefresh: () => void;
  stopRefresh: () => void;
  isRefreshing: boolean;
  manualRefresh: () => Promise<void>;
}

/**
 * Custom hook for periodic refresh functionality
 * Loads refresh interval from localStorage settings and manages periodic execution
 */
export function usePeriodicRefresh({
  refreshFunction,
  intervalMs,
  enabled = true,
  dependencies = []
}: UsePeriodicRefreshOptions): UsePeriodicRefreshReturn {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isRefreshingRef = useRef(false);
  const refreshFunctionRef = useRef(refreshFunction);

  // Update the refresh function ref when it changes
  useEffect(() => {
    refreshFunctionRef.current = refreshFunction;
  }, [refreshFunction]);

  // Load refresh interval from localStorage
  const getRefreshInterval = useCallback((): number => {
    try {
      // Check if we're in a browser environment
      if (typeof window !== 'undefined' && window.localStorage) {
        const settings = localStorage.getItem('jive-app-settings');
        if (settings) {
          const parsedSettings = JSON.parse(settings);
          const refreshInterval = parsedSettings.refreshInterval;
          
          // Convert to milliseconds and validate
          if (typeof refreshInterval === 'number' && refreshInterval > 0) {
            return refreshInterval * 1000; // Convert seconds to milliseconds
          }
        }
      }
    } catch (error) {
      console.warn('Failed to load refresh interval from settings:', error);
    }
    
    // Return provided intervalMs or default to 30 seconds
    return intervalMs || 30000;
  }, [intervalMs]);

  const stopRefresh = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const startRefresh = useCallback(() => {
    stopRefresh(); // Clear any existing interval
    
    if (!enabled) return;
    
    const interval = getRefreshInterval();
    
    // Only start if interval is greater than 0 (0 means disabled)
    if (interval > 0) {
      intervalRef.current = setInterval(async () => {
        if (!isRefreshingRef.current) {
          isRefreshingRef.current = true;
          try {
            await refreshFunctionRef.current();
          } catch (error) {
            console.error('Periodic refresh failed:', error);
          } finally {
            isRefreshingRef.current = false;
          }
        }
      }, interval);
    }
  }, [enabled, getRefreshInterval, stopRefresh]);

  const manualRefresh = useCallback(async () => {
    if (!isRefreshingRef.current) {
      isRefreshingRef.current = true;
      try {
        await refreshFunctionRef.current();
      } catch (error) {
        console.error('Manual refresh failed:', error);
        throw error;
      } finally {
        isRefreshingRef.current = false;
      }
    }
  }, []);

  // Start/restart refresh when dependencies change
  useEffect(() => {
    startRefresh();
    return stopRefresh;
  }, [startRefresh, stopRefresh, ...dependencies]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRefresh();
    };
  }, [stopRefresh]);

  // Listen for settings changes in localStorage
  useEffect(() => {
    // Check if we're in a browser environment
    if (typeof window === 'undefined') return;
    
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === 'jive-app-settings') {
        // Restart refresh with new interval
        startRefresh();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [startRefresh]);

  return {
    startRefresh,
    stopRefresh,
    isRefreshing: isRefreshingRef.current,
    manualRefresh
  };
}