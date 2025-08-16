// WebSocket Client for Jive MCP Real-time Communication

import {
  WebSocketMessage,
  ConnectionState,
  JiveApiConfig,
} from './types';

type WebSocketEventHandler = (message: WebSocketMessage) => void;
type ConnectionEventHandler = (state: ConnectionState) => void;

class JiveWebSocketClient {
  private ws: WebSocket | null = null;
  private config: JiveApiConfig;
  private connectionState: ConnectionState;
  private eventHandlers: Map<string, WebSocketEventHandler[]> = new Map();
  private connectionHandlers: ConnectionEventHandler[] = [];
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private heartbeatIntervalId: NodeJS.Timeout | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private maxQueueSize = 100;

  constructor(config: JiveApiConfig) {
    this.config = config;
    this.connectionState = {
      isConnected: false,
      isConnecting: false,
      reconnectAttempts: 0,
    };
  }

  // Connection Management
  async connect(): Promise<void> {
    if (this.connectionState.isConnected || this.connectionState.isConnecting) {
      return;
    }

    this.updateConnectionState({
      isConnecting: true,
      error: undefined,
    });

    try {
      this.ws = new WebSocket(this.config.wsUrl);
      this.setupWebSocketEventHandlers();
      
      // Wait for connection to be established
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'));
        }, this.config.timeout);

        this.ws!.onopen = () => {
          clearTimeout(timeout);
          resolve();
        };

        this.ws!.onerror = (error) => {
          clearTimeout(timeout);
          reject(new Error('WebSocket connection failed'));
        };
      });
    } catch (error) {
      this.updateConnectionState({
        isConnecting: false,
        error: error.message,
      });
      throw error;
    }
  }

  disconnect(): void {
    this.clearReconnectTimeout();
    this.clearHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.updateConnectionState({
      isConnected: false,
      isConnecting: false,
      reconnectAttempts: 0,
    });
  }

  private setupWebSocketEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.updateConnectionState({
        isConnected: true,
        isConnecting: false,
        lastConnected: new Date(),
        reconnectAttempts: 0,
        error: undefined,
      });

      this.startHeartbeat();
      this.processMessageQueue();
    };

    this.ws.onclose = (event) => {
      this.updateConnectionState({
        isConnected: false,
        isConnecting: false,
      });

      this.clearHeartbeat();

      // Attempt reconnection if not a clean close
      if (event.code !== 1000 && this.connectionState.reconnectAttempts < this.config.retryAttempts) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.updateConnectionState({
        error: 'WebSocket connection error',
      });
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimeout();
    
    const delay = this.config.retryDelay * Math.pow(2, this.connectionState.reconnectAttempts);
    
    this.reconnectTimeoutId = setTimeout(() => {
      this.updateConnectionState({
        reconnectAttempts: this.connectionState.reconnectAttempts + 1,
      });
      
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  private clearReconnectTimeout(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    
    this.heartbeatIntervalId = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
      }
    }, 30000); // Send ping every 30 seconds
  }

  private clearHeartbeat(): void {
    if (this.heartbeatIntervalId) {
      clearInterval(this.heartbeatIntervalId);
      this.heartbeatIntervalId = null;
    }
  }

  private updateConnectionState(updates: Partial<ConnectionState>): void {
    this.connectionState = { ...this.connectionState, ...updates };
    this.connectionHandlers.forEach(handler => handler(this.connectionState));
  }

  private handleMessage(message: WebSocketMessage): void {
    // Handle pong responses
    if (message.type === 'pong') {
      return;
    }

    // Emit to registered handlers
    const handlers = this.eventHandlers.get(message.type) || [];
    const allHandlers = this.eventHandlers.get('*') || [];
    
    [...handlers, ...allHandlers].forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in WebSocket message handler:', error);
      }
    });
  }

  // Message Sending
  send(message: Omit<WebSocketMessage, 'timestamp'>): void {
    const fullMessage: WebSocketMessage = {
      ...message,
      timestamp: new Date().toISOString(),
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(fullMessage));
    } else {
      // Queue message for later sending
      this.queueMessage(fullMessage);
    }
  }

  private queueMessage(message: WebSocketMessage): void {
    if (this.messageQueue.length >= this.maxQueueSize) {
      this.messageQueue.shift(); // Remove oldest message
    }
    this.messageQueue.push(message);
  }

  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()!;
      this.ws.send(JSON.stringify(message));
    }
  }

  // Event Handling
  on(eventType: string, handler: WebSocketEventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    
    this.eventHandlers.get(eventType)!.push(handler);
    
    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }

  onConnection(handler: ConnectionEventHandler): () => void {
    this.connectionHandlers.push(handler);
    
    // Immediately call with current state
    handler(this.connectionState);
    
    // Return unsubscribe function
    return () => {
      const index = this.connectionHandlers.indexOf(handler);
      if (index > -1) {
        this.connectionHandlers.splice(index, 1);
      }
    };
  }

  off(eventType: string, handler?: WebSocketEventHandler): void {
    if (!handler) {
      this.eventHandlers.delete(eventType);
      return;
    }
    
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  // Getters
  get isConnected(): boolean {
    return this.connectionState.isConnected;
  }

  get isConnecting(): boolean {
    return this.connectionState.isConnecting;
  }

  get connectionInfo(): ConnectionState {
    return { ...this.connectionState };
  }

  // Configuration
  updateConfig(newConfig: Partial<JiveApiConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

export { JiveWebSocketClient };
export type { WebSocketEventHandler, ConnectionEventHandler };