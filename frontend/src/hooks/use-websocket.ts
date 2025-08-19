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
        console.log('WebSocket connected');
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

      ws.onclose = () => {
        console.log('WebSocket disconnected');
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
          console.log(
            `Attempting to reconnect (${reconnectAttemptsRef.current}/${reconnectAttempts})...`
          );
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      toast({
        title: 'Connection Error',
        description: 'Failed to establish real-time connection',
        variant: 'destructive',
      });
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
      console.warn('WebSocket is not connected');
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