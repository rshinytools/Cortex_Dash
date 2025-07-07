// ABOUTME: Real-time cursors component for showing live user activity on dashboards
// ABOUTME: Displays user cursors, selections, and active areas with smooth animations

'use client';

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface UserCursor {
  user_id: string;
  user_name: string;
  user_avatar?: string;
  user_color: string;
  position: {
    x: number;
    y: number;
  };
  last_seen: Date;
  active: boolean;
  selection?: {
    element_id?: string;
    start_x: number;
    start_y: number;
    end_x: number;
    end_y: number;
  };
  activity?: {
    type: 'viewing' | 'editing' | 'commenting' | 'filtering';
    target?: string;
    description?: string;
  };
}

export interface UserPresence {
  user_id: string;
  user_name: string;
  user_avatar?: string;
  user_color: string;
  status: 'online' | 'away' | 'offline';
  last_activity: Date;
  current_widget?: string;
  current_action?: string;
}

interface CursorProps {
  cursor: UserCursor;
  currentUserId: string;
  className?: string;
}

function Cursor({ cursor, currentUserId, className }: CursorProps) {
  const [isVisible, setIsVisible] = useState(true);
  const lastPosition = useRef(cursor.position);

  // Hide cursor if it hasn't moved in a while
  useEffect(() => {
    const timeSinceLastSeen = Date.now() - cursor.last_seen.getTime();
    if (timeSinceLastSeen > 5000) { // 5 seconds
      setIsVisible(false);
    } else {
      setIsVisible(true);
    }
  }, [cursor.last_seen]);

  // Smooth cursor movement
  useEffect(() => {
    lastPosition.current = cursor.position;
  }, [cursor.position]);

  // Don't show our own cursor
  if (cursor.user_id === currentUserId || !isVisible || !cursor.active) {
    return null;
  }

  return (
    <div
      className={cn(
        "fixed pointer-events-none z-50 transition-all duration-100 ease-out",
        className
      )}
      style={{
        left: cursor.position.x,
        top: cursor.position.y,
        transform: 'translate(-2px, -2px)',
      }}
    >
      {/* Cursor pointer */}
      <div className="relative">
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          className="drop-shadow-lg"
        >
          <path
            d="M0 0L8 16L11 11L16 8L0 0Z"
            fill={cursor.user_color}
            stroke="white"
            strokeWidth="1"
          />
        </svg>
        
        {/* User name label */}
        <div
          className="absolute top-4 left-4 px-2 py-1 rounded text-xs text-white font-medium whitespace-nowrap"
          style={{ backgroundColor: cursor.user_color }}
        >
          {cursor.user_name}
        </div>
      </div>

      {/* Selection area */}
      {cursor.selection && (
        <div
          className="absolute border-2 rounded opacity-30"
          style={{
            borderColor: cursor.user_color,
            backgroundColor: cursor.user_color,
            left: Math.min(cursor.selection.start_x, cursor.selection.end_x) - cursor.position.x,
            top: Math.min(cursor.selection.start_y, cursor.selection.end_y) - cursor.position.y,
            width: Math.abs(cursor.selection.end_x - cursor.selection.start_x),
            height: Math.abs(cursor.selection.end_y - cursor.selection.start_y),
          }}
        />
      )}
    </div>
  );
}

interface PresenceAvatarProps {
  presence: UserPresence;
  currentUserId: string;
  onClick?: () => void;
  className?: string;
}

function PresenceAvatar({ presence, currentUserId, onClick, className }: PresenceAvatarProps) {
  if (presence.user_id === currentUserId) {
    return null;
  }

  const getStatusColor = () => {
    switch (presence.status) {
      case 'online':
        return 'bg-green-500';
      case 'away':
        return 'bg-yellow-500';
      case 'offline':
        return 'bg-gray-400';
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div 
      className={cn("relative cursor-pointer", className)}
      onClick={onClick}
      title={`${presence.user_name} - ${presence.status}`}
    >
      <Avatar 
        className="h-8 w-8 border-2"
        style={{ borderColor: presence.user_color }}
      >
        <AvatarImage src={presence.user_avatar} />
        <AvatarFallback 
          className="text-xs"
          style={{ backgroundColor: presence.user_color, color: 'white' }}
        >
          {presence.user_name.charAt(0).toUpperCase()}
        </AvatarFallback>
      </Avatar>
      
      {/* Status indicator */}
      <div 
        className={cn(
          "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white",
          getStatusColor()
        )}
      />
      
      {/* Activity indicator */}
      {presence.current_action && presence.status === 'online' && (
        <div 
          className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-pulse"
          style={{ backgroundColor: presence.user_color }}
          title={presence.current_action}
        />
      )}
    </div>
  );
}

interface ActivityIndicatorProps {
  activity: UserCursor['activity'];
  userColor: string;
  userName: string;
  position: { x: number; y: number };
  className?: string;
}

function ActivityIndicator({ 
  activity, 
  userColor, 
  userName, 
  position, 
  className 
}: ActivityIndicatorProps) {
  if (!activity) return null;

  const getActivityIcon = () => {
    switch (activity.type) {
      case 'editing':
        return '✏️';
      case 'commenting':
        return '💬';
      case 'filtering':
        return '🔍';
      case 'viewing':
        return '👁️';
      default:
        return '🔵';
    }
  };

  const getActivityColor = () => {
    switch (activity.type) {
      case 'editing':
        return 'bg-orange-500';
      case 'commenting':
        return 'bg-blue-500';
      case 'filtering':
        return 'bg-purple-500';
      case 'viewing':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div
      className={cn(
        "fixed pointer-events-none z-40 transition-all duration-300",
        className
      )}
      style={{
        left: position.x + 25,
        top: position.y - 10,
      }}
    >
      <Card className="p-2 shadow-lg">
        <CardContent className="p-0">
          <div className="flex items-center gap-2">
            <div 
              className={cn("w-2 h-2 rounded-full animate-pulse", getActivityColor())}
            />
            <span className="text-xs font-medium">{userName}</span>
            <span className="text-xs">{getActivityIcon()}</span>
            <span className="text-xs text-muted-foreground">
              {activity.description || activity.type}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface PresenceListProps {
  presences: UserPresence[];
  currentUserId: string;
  onUserClick?: (userId: string) => void;
  className?: string;
}

function PresenceList({ presences, currentUserId, onUserClick, className }: PresenceListProps) {
  const onlineUsers = presences.filter(p => p.status === 'online' && p.user_id !== currentUserId);
  const awayUsers = presences.filter(p => p.status === 'away' && p.user_id !== currentUserId);

  if (onlineUsers.length === 0 && awayUsers.length === 0) {
    return null;
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="text-xs text-muted-foreground">
        {onlineUsers.length + awayUsers.length} user{onlineUsers.length + awayUsers.length !== 1 ? 's' : ''} online
      </span>
      
      <div className="flex items-center gap-1">
        {onlineUsers.slice(0, 5).map((presence) => (
          <PresenceAvatar
            key={presence.user_id}
            presence={presence}
            currentUserId={currentUserId}
            onClick={() => onUserClick?.(presence.user_id)}
          />
        ))}
        
        {awayUsers.slice(0, 3).map((presence) => (
          <PresenceAvatar
            key={presence.user_id}
            presence={presence}
            currentUserId={currentUserId}
            onClick={() => onUserClick?.(presence.user_id)}
            className="opacity-60"
          />
        ))}
        
        {(onlineUsers.length + awayUsers.length) > 8 && (
          <Badge variant="secondary" className="text-xs">
            +{(onlineUsers.length + awayUsers.length) - 8}
          </Badge>
        )}
      </div>
    </div>
  );
}

interface RealTimeCursorsProps {
  dashboardId: string;
  widgetId?: string;
  currentUserId: string;
  currentUserName: string;
  currentUserColor?: string;
  className?: string;
  showPresenceList?: boolean;
  onCursorUpdate?: (cursor: UserCursor) => void;
  onPresenceUpdate?: (presence: UserPresence) => void;
}

export function RealTimeCursors({
  dashboardId,
  widgetId,
  currentUserId,
  currentUserName,
  currentUserColor = '#3b82f6',
  className,
  showPresenceList = true,
  onCursorUpdate,
  onPresenceUpdate,
}: RealTimeCursorsProps) {
  const [cursors, setCursors] = useState<UserCursor[]>([]);
  const [presences, setPresences] = useState<UserPresence[]>([]);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const lastUpdateTime = useRef(Date.now());

  // Generate user colors
  const userColors = [
    '#ef4444', '#f97316', '#eab308', '#22c55e', 
    '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899'
  ];

  const getUserColor = useCallback((userId: string) => {
    const index = Math.abs(userId.split('').reduce((a, b) => a + b.charCodeAt(0), 0)) % userColors.length;
    return userColors[index];
  }, []);

  // Mock real-time data - in a real app, this would come from WebSocket
  useEffect(() => {
    const mockCursors: UserCursor[] = [
      {
        user_id: 'user-2',
        user_name: 'Jane Smith',
        user_color: getUserColor('user-2'),
        position: { x: 150, y: 200 },
        last_seen: new Date(),
        active: true,
        activity: {
          type: 'viewing',
          description: 'Viewing chart data'
        }
      },
      {
        user_id: 'user-3',
        user_name: 'Bob Johnson',
        user_color: getUserColor('user-3'),
        position: { x: 300, y: 150 },
        last_seen: new Date(Date.now() - 2000),
        active: true,
        activity: {
          type: 'filtering',
          description: 'Applying filters'
        }
      },
    ];

    const mockPresences: UserPresence[] = [
      {
        user_id: 'user-2',
        user_name: 'Jane Smith',
        user_color: getUserColor('user-2'),
        status: 'online',
        last_activity: new Date(),
        current_widget: widgetId,
        current_action: 'viewing data'
      },
      {
        user_id: 'user-3',
        user_name: 'Bob Johnson',
        user_color: getUserColor('user-3'),
        status: 'online',
        last_activity: new Date(),
        current_action: 'configuring filters'
      },
      {
        user_id: 'user-4',
        user_name: 'Alice Brown',
        user_color: getUserColor('user-4'),
        status: 'away',
        last_activity: new Date(Date.now() - 5 * 60 * 1000),
      },
    ];

    setCursors(mockCursors);
    setPresences(mockPresences);

    // Simulate cursor movement
    const interval = setInterval(() => {
      setCursors(prev => prev.map(cursor => ({
        ...cursor,
        position: {
          x: cursor.position.x + (Math.random() - 0.5) * 20,
          y: cursor.position.y + (Math.random() - 0.5) * 20,
        },
        last_seen: new Date(),
      })));
    }, 2000);

    return () => clearInterval(interval);
  }, [widgetId, getUserColor]);

  // Track mouse movement
  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      const now = Date.now();
      // Throttle updates to avoid overwhelming
      if (now - lastUpdateTime.current < 50) return;
      
      lastUpdateTime.current = now;
      
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const newPosition = {
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
        };
        setMousePosition(newPosition);

        // Emit cursor update
        const cursorUpdate: UserCursor = {
          user_id: currentUserId,
          user_name: currentUserName,
          user_color: currentUserColor,
          position: newPosition,
          last_seen: new Date(),
          active: true,
        };

        onCursorUpdate?.(cursorUpdate);
      }
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener('mousemove', handleMouseMove);
      return () => container.removeEventListener('mousemove', handleMouseMove);
    }
  }, [currentUserId, currentUserName, currentUserColor, onCursorUpdate]);

  // Handle user activity tracking
  const trackActivity = useCallback((
    type: UserCursor['activity']['type'],
    description?: string,
    target?: string
  ) => {
    const presenceUpdate: UserPresence = {
      user_id: currentUserId,
      user_name: currentUserName,
      user_color: currentUserColor,
      status: 'online',
      last_activity: new Date(),
      current_widget: widgetId,
      current_action: description,
    };

    onPresenceUpdate?.(presenceUpdate);
  }, [currentUserId, currentUserName, currentUserColor, widgetId, onPresenceUpdate]);

  // Handle user click for following
  const handleUserClick = useCallback((userId: string) => {
    const userCursor = cursors.find(c => c.user_id === userId);
    if (userCursor && containerRef.current) {
      // Smooth scroll to user's position
      const container = containerRef.current;
      const targetX = userCursor.position.x - container.clientWidth / 2;
      const targetY = userCursor.position.y - container.clientHeight / 2;
      
      container.scrollTo({
        left: Math.max(0, targetX),
        top: Math.max(0, targetY),
        behavior: 'smooth'
      });
    }
  }, [cursors]);

  // Calculate visible cursors
  const visibleCursors = useMemo(() => {
    return cursors.filter(cursor => {
      const timeSinceLastSeen = Date.now() - cursor.last_seen.getTime();
      return timeSinceLastSeen < 10000 && cursor.active; // 10 seconds
    });
  }, [cursors]);

  return (
    <div ref={containerRef} className={cn("relative h-full w-full", className)}>
      {/* Render other users' cursors */}
      {visibleCursors.map((cursor) => (
        <React.Fragment key={cursor.user_id}>
          <Cursor
            cursor={cursor}
            currentUserId={currentUserId}
          />
          <ActivityIndicator
            activity={cursor.activity}
            userColor={cursor.user_color}
            userName={cursor.user_name}
            position={cursor.position}
          />
        </React.Fragment>
      ))}

      {/* Presence list */}
      {showPresenceList && (
        <div className="absolute top-2 right-2 z-30">
          <PresenceList
            presences={presences}
            currentUserId={currentUserId}
            onUserClick={handleUserClick}
          />
        </div>
      )}
    </div>
  );
}

// Hook for tracking user activity
export function useUserActivity(
  dashboardId: string,
  widgetId: string,
  userId: string
) {
  const trackActivity = useCallback((
    type: 'viewing' | 'editing' | 'commenting' | 'filtering',
    description?: string
  ) => {
    // In a real app, this would send to WebSocket/API
    console.log('User activity:', {
      dashboardId,
      widgetId,
      userId,
      type,
      description,
      timestamp: new Date().toISOString(),
    });
  }, [dashboardId, widgetId, userId]);

  return { trackActivity };
}

// Hook for managing collaborative sessions
export function useCollaborativeSession(dashboardId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate connection
    setIsConnected(true);
    setConnectionError(null);

    // Simulate occasional connection issues
    const interval = setInterval(() => {
      if (Math.random() < 0.05) { // 5% chance of connection issue
        setIsConnected(false);
        setConnectionError('Connection lost. Attempting to reconnect...');
        
        setTimeout(() => {
          setIsConnected(true);
          setConnectionError(null);
        }, 2000);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [dashboardId]);

  return { isConnected, connectionError };
}