// ABOUTME: Permission context for managing user permissions in the frontend
// ABOUTME: Provides hooks and components for checking permissions

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useAuth } from '@/lib/auth-context';

interface PermissionContextType {
  permissions: Set<string>;
  roles: string[];
  isSystemAdmin: boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (...permissions: string[]) => boolean;
  hasAllPermissions: (...permissions: string[]) => boolean;
  hasRole: (role: string) => boolean;
  loading: boolean;
  refreshPermissions: () => Promise<void>;
}

const PermissionContext = createContext<PermissionContextType | undefined>(undefined);

export function PermissionProvider({ children }: { children: ReactNode }) {
  const { user, isAuthenticated } = useAuth();
  const [permissions, setPermissions] = useState<Set<string>>(new Set());
  const [roles, setRoles] = useState<string[]>([]);
  const [isSystemAdmin, setIsSystemAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchPermissions = async () => {
    if (!isAuthenticated || !user) {
      setPermissions(new Set());
      setRoles([]);
      setIsSystemAdmin(false);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      
      // Fetch user permissions
      const permResponse = await fetch('/api/v1/rbac/my-permissions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (permResponse.ok) {
        const permData = await permResponse.json();
        setPermissions(new Set(permData.permissions));
        setIsSystemAdmin(permData.is_system_admin);
      }
      
      // Fetch user roles
      const roleResponse = await fetch('/api/v1/rbac/my-roles', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (roleResponse.ok) {
        const roleData = await roleResponse.json();
        setRoles(roleData.map((r: any) => r.role_name));
      }
    } catch (error) {
      console.error('Failed to fetch permissions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPermissions();
  }, [isAuthenticated, user]);

  const hasPermission = (permission: string): boolean => {
    if (isSystemAdmin) return true; // System admin has all permissions
    return permissions.has(permission);
  };

  const hasAnyPermission = (...perms: string[]): boolean => {
    if (isSystemAdmin) return true;
    return perms.some(p => permissions.has(p));
  };

  const hasAllPermissions = (...perms: string[]): boolean => {
    if (isSystemAdmin) return true;
    return perms.every(p => permissions.has(p));
  };

  const hasRole = (role: string): boolean => {
    if (role === 'system_admin' && isSystemAdmin) return true;
    return roles.includes(role);
  };

  const value: PermissionContextType = {
    permissions,
    roles,
    isSystemAdmin,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    loading,
    refreshPermissions: fetchPermissions
  };

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
}

export function usePermissions() {
  const context = useContext(PermissionContext);
  if (context === undefined) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
}