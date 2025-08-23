// ABOUTME: WebSocket hook for real-time connections
// ABOUTME: Handles study initialization progress and other real-time updates

import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from '@/lib/auth-context';
import { toast } from '@/hooks/use-toast';

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface WebSocketHookOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  reconnectAttempts?: number;
}

export function useWebSocket(
  url: string | null,
  options: WebSocketHookOptions = {}
) {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnect = true,
    reconnectInterval = 5000,
    reconnectAttempts = 5,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const { token } = useAuth();

  const connect = useCallback(() => {
    if (!url || !token) return;

    try {
      // Construct WebSocket URL to connect to backend directly on port 8000
      // WebSocket endpoints are under /api/v1 prefix
      const backendHost = 'localhost:8000';
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const fullUrl = `${wsProtocol}//${backendHost}/api/v1${url}`;
      
      // Add token as query parameter for WebSocket authentication
      const wsUrl = new URL(fullUrl);
      wsUrl.searchParams.set('token', token);

      const ws = new WebSocket(wsUrl.toString());
      wsRef.current = ws;

      ws.onopen = () => {
        if (process.env.NODE_ENV === 'development') {
          console.debug('WebSocket connected');
        }
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        if (process.env.NODE_ENV === 'development') {
          console.debug('WebSocket disconnected', { code: event.code, reason: event.reason });
        }
        setIsConnected(false);
        wsRef.current = null;
        onClose?.();

        // Attempt to reconnect if enabled
        if (
          reconnect &&
          reconnectAttemptsRef.current < reconnectAttempts &&
          !reconnectTimeoutRef.current
        ) {
          reconnectAttemptsRef.current++;
          if (process.env.NODE_ENV === 'development') {
            console.debug(
              `Attempting to reconnect (${reconnectAttemptsRef.current}/${reconnectAttempts})...`
            );
          }
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        // WebSocket errors don't provide much detail, just log a simple message
        // The actual error details will come through the onclose event
        if (process.env.NODE_ENV === 'development') {
          console.debug('WebSocket connection error detected');
        }
        onError?.(error);
      };
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.debug('Failed to create WebSocket:', error);
      }
      // Don't show toast for WebSocket failures as they're not critical
      // and will attempt to reconnect automatically
    }
  }, [url, token, onMessage, onOpen, onClose, onError, reconnect, reconnectInterval, reconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      if (process.env.NODE_ENV === 'development') {
        console.debug('WebSocket is not connected, message not sent');
      }
    }
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
}