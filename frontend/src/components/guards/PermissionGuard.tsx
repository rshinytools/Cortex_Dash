// ABOUTME: Permission guard components for conditionally rendering based on permissions
// ABOUTME: Provides CanAccess component and permission-based routing

import React, { ReactNode } from 'react';
import { usePermissions } from '@/contexts/PermissionContext';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ShieldOff } from 'lucide-react';

interface CanAccessProps {
  permission?: string;
  permissions?: string[];
  requireAll?: boolean;
  role?: string;
  fallback?: ReactNode;
  children: ReactNode;
}

/**
 * Component that conditionally renders children based on permissions
 * 
 * Usage:
 * <CanAccess permission="study.create">
 *   <CreateStudyButton />
 * </CanAccess>
 * 
 * <CanAccess permissions={["study.edit", "study.delete"]} requireAll={false}>
 *   <StudyActions />
 * </CanAccess>
 * 
 * <CanAccess role="system_admin">
 *   <AdminPanel />
 * </CanAccess>
 */
export function CanAccess({
  permission,
  permissions,
  requireAll = false,
  role,
  fallback = null,
  children
}: CanAccessProps) {
  const { hasPermission, hasAnyPermission, hasAllPermissions, hasRole, loading } = usePermissions();

  if (loading) {
    return null; // Or a loading spinner
  }

  let hasAccess = false;

  if (role) {
    hasAccess = hasRole(role);
  } else if (permission) {
    hasAccess = hasPermission(permission);
  } else if (permissions) {
    hasAccess = requireAll 
      ? hasAllPermissions(...permissions)
      : hasAnyPermission(...permissions);
  }

  return hasAccess ? <>{children}</> : <>{fallback}</>;
}

interface PermissionDeniedProps {
  message?: string;
}

export function PermissionDenied({ 
  message = "You don't have permission to access this resource" 
}: PermissionDeniedProps) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Alert className="max-w-md">
        <ShieldOff className="h-4 w-4" />
        <AlertDescription>
          {message}
        </AlertDescription>
      </Alert>
    </div>
  );
}

interface RequirePermissionProps {
  permission?: string;
  permissions?: string[];
  requireAll?: boolean;
  role?: string;
  children: ReactNode;
}

/**
 * Component that shows permission denied message if user lacks permissions
 */
export function RequirePermission({
  permission,
  permissions,
  requireAll = false,
  role,
  children
}: RequirePermissionProps) {
  return (
    <CanAccess
      permission={permission}
      permissions={permissions}
      requireAll={requireAll}
      role={role}
      fallback={<PermissionDenied />}
    >
      {children}
    </CanAccess>
  );
}

/**
 * Hook for permission-based navigation
 */
export function usePermissionNavigation() {
  const { hasPermission, hasRole } = usePermissions();

  const canNavigateTo = (path: string): boolean => {
    // Define route permissions
    const routePermissions: Record<string, string | string[]> = {
      '/admin/studies/new': 'study.create',
      '/admin/dashboard-templates/new': 'template.create',
      '/admin/users': 'user.manage_system',
      '/admin/rbac': 'permission.manage',
      '/studies/[id]/data': 'data.upload',
      '/studies/[id]/team': 'team.manage',
    };

    const requiredPermission = routePermissions[path];
    
    if (!requiredPermission) return true; // No permission required
    
    if (Array.isArray(requiredPermission)) {
      return requiredPermission.some(p => hasPermission(p));
    }
    
    return hasPermission(requiredPermission);
  };

  return { canNavigateTo };
}