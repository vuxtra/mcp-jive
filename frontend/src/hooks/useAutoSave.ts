'use client';

import { useEffect, useRef, useCallback } from 'react';

interface UseAutoSaveOptions {
  data: any;
  onSave: (data: any) => Promise<void>;
  delay?: number; // Delay in milliseconds before auto-save triggers
  enabled?: boolean; // Whether auto-save is enabled
  dependencies?: any[]; // Additional dependencies to watch
}

interface UseAutoSaveReturn {
  isAutoSaving: boolean;
  lastAutoSaveTime: Date | null;
  triggerAutoSave: () => void;
}

/**
 * Custom hook for auto-save functionality
 * Automatically saves data after a specified delay when data changes
 */
export function useAutoSave({
  data,
  onSave,
  delay = 2000, // Default 2 seconds
  enabled = true,
  dependencies = [],
}: UseAutoSaveOptions): UseAutoSaveReturn {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isAutoSavingRef = useRef(false);
  const lastAutoSaveTimeRef = useRef<Date | null>(null);
  const previousDataRef = useRef<any>(null);
  const isMountedRef = useRef(true);

  // Load auto-save settings from localStorage
  const loadAutoSaveSettings = useCallback(() => {
    try {
      // Check if we're in a browser environment
      if (typeof window !== 'undefined' && window.localStorage) {
        const settings = localStorage.getItem('jive-app-settings');
        if (settings) {
          const parsedSettings = JSON.parse(settings);
          return {
            enabled: parsedSettings.autoSave ?? true,
            delay: (parsedSettings.autoSaveDelay ?? 3) * 1000, // Convert seconds to milliseconds
          };
        }
      }
    } catch (error) {
      console.warn('Failed to load auto-save settings:', error);
    }
    return { enabled: true, delay: 3000 };
  }, []);

  // Check if data has meaningful changes
  const hasDataChanged = useCallback((newData: any, oldData: any) => {
    if (!oldData) return false;
    
    // Deep comparison for objects
    if (typeof newData === 'object' && typeof oldData === 'object') {
      const newDataStr = JSON.stringify(newData);
      const oldDataStr = JSON.stringify(oldData);
      return newDataStr !== oldDataStr;
    }
    
    return newData !== oldData;
  }, []);

  // Trigger auto-save manually
  const triggerAutoSave = useCallback(async () => {
    if (!enabled || isAutoSavingRef.current || !data) return;

    const settings = loadAutoSaveSettings();
    if (!settings.enabled) return;

    try {
      isAutoSavingRef.current = true;
      await onSave(data);
      lastAutoSaveTimeRef.current = new Date();
    } catch (error) {
      console.error('Auto-save failed:', error);
    } finally {
      if (isMountedRef.current) {
        isAutoSavingRef.current = false;
      }
    }
  }, [data, onSave, enabled, loadAutoSaveSettings]);

  // Auto-save effect
  useEffect(() => {
    if (!enabled || !data) return;

    const settings = loadAutoSaveSettings();
    if (!settings.enabled) return;

    // Check if data has actually changed
    if (!hasDataChanged(data, previousDataRef.current)) {
      previousDataRef.current = data;
      return;
    }

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout for auto-save
    timeoutRef.current = setTimeout(() => {
      if (isMountedRef.current && !isAutoSavingRef.current) {
        triggerAutoSave();
      }
    }, settings.delay);

    // Update previous data reference
    previousDataRef.current = data;

    // Cleanup function
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [data, enabled, triggerAutoSave, hasDataChanged, loadAutoSaveSettings, ...dependencies]);

  // Listen for localStorage changes to update settings
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'jive-app-settings') {
        // Reset timeout with new delay if auto-save is active
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [loadAutoSaveSettings]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    isAutoSaving: isAutoSavingRef.current,
    lastAutoSaveTime: lastAutoSaveTimeRef.current,
    triggerAutoSave,
  };
}

export default useAutoSave;