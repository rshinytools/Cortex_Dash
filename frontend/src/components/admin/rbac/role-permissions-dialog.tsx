// ABOUTME: Dialog component for configuring role permissions
// ABOUTME: Allows admins to grant/revoke permissions for a specific role

'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Search, Shield, AlertCircle } from 'lucide-react';
import { secureApiClient } from '@/lib/api/secure-client';
import { toast } from 'sonner';

interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
  description: string;
  is_system: boolean;
}

interface Role {
  id: string;
  name: string;
  display_name: string;
  description: string;
  is_system: boolean;
  is_active: boolean;
}

interface RolePermissionsDialogProps {
  role: Role | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

export function RolePermissionsDialog({
  role,
  isOpen,
  onClose,
  onUpdate,
}: RolePermissionsDialogProps) {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [rolePermissions, setRolePermissions] = useState<string[]>([]);
  const [selectedPermissions, setSelectedPermissions] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (role && isOpen) {
      fetchPermissions();
      fetchRolePermissions();
    }
  }, [role, isOpen]);

  const fetchPermissions = async () => {
    try {
      setLoading(true);
      const response = await secureApiClient.get('/rbac/permissions');
      setPermissions(response.data);
    } catch (error) {
      console.error('Failed to fetch permissions:', error);
      toast.error('Failed to load permissions');
    } finally {
      setLoading(false);
    }
  };

  const fetchRolePermissions = async () => {
    if (!role) return;
    
    try {
      const response = await secureApiClient.get(
        `/rbac/roles/${role.id}/permissions`
      );
      const permissionNames = response.data.map((p: Permission) => p.name);
      setRolePermissions(permissionNames);
      setSelectedPermissions(new Set(permissionNames));
    } catch (error) {
      console.error('Failed to fetch role permissions:', error);
      toast.error('Failed to load role permissions');
    }
  };

  const handlePermissionToggle = (permissionName: string) => {
    const newSelected = new Set(selectedPermissions);
    if (newSelected.has(permissionName)) {
      newSelected.delete(permissionName);
    } else {
      newSelected.add(permissionName);
    }
    setSelectedPermissions(newSelected);
  };

  const handleSave = async () => {
    if (!role) return;

    try {
      setSaving(true);
      
      await secureApiClient.put(
        `/rbac/roles/${role.id}/permissions`,
        {
          permissions: Array.from(selectedPermissions),
        }
      );

      toast.success('Permissions updated successfully');
      onUpdate();
      onClose();
    } catch (error) {
      console.error('Failed to update permissions:', error);
      toast.error('Failed to update permissions');
    } finally {
      setSaving(false);
    }
  };

  const groupedPermissions = permissions.reduce((acc, permission) => {
    if (!acc[permission.resource]) {
      acc[permission.resource] = [];
    }
    acc[permission.resource].push(permission);
    return acc;
  }, {} as Record<string, Permission[]>);

  const filteredGroups = Object.entries(groupedPermissions).reduce((acc, [resource, perms]) => {
    const filtered = perms.filter(
      (p) =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (filtered.length > 0) {
      acc[resource] = filtered;
    }
    return acc;
  }, {} as Record<string, Permission[]>);

  const hasChanges = () => {
    const current = new Set(rolePermissions);
    if (current.size !== selectedPermissions.size) return true;
    for (const perm of selectedPermissions) {
      if (!current.has(perm)) return true;
    }
    return false;
  };

  if (!role) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Configure Permissions: {role.display_name}
          </DialogTitle>
          <DialogDescription>
            Select which permissions to grant to the {role.display_name} role.
            {role.is_system && (
              <Alert className="mt-2">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  This is a system role. Changes may affect platform functionality.
                </AlertDescription>
              </Alert>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search permissions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <ScrollArea className="h-[400px] border rounded-md p-4">
              <div className="space-y-6">
                {Object.entries(filteredGroups).map(([resource, perms]) => (
                  <div key={resource} className="space-y-2">
                    <h4 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
                      {resource}
                    </h4>
                    <div className="space-y-2">
                      {perms.map((permission) => (
                        <div
                          key={permission.id}
                          className="flex items-start space-x-3 py-2 px-3 rounded-md hover:bg-muted/50 transition-colors"
                        >
                          <Checkbox
                            id={permission.id}
                            checked={selectedPermissions.has(permission.name)}
                            onCheckedChange={() => handlePermissionToggle(permission.name)}
                            disabled={role.name === 'system_admin'}
                          />
                          <div className="flex-1 space-y-1">
                            <label
                              htmlFor={permission.id}
                              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                            >
                              <div className="flex items-center gap-2">
                                <span>{permission.name}</span>
                                <Badge variant="outline" className="text-xs">
                                  {permission.action}
                                </Badge>
                                {permission.is_system && (
                                  <Badge variant="secondary" className="text-xs">
                                    System
                                  </Badge>
                                )}
                              </div>
                            </label>
                            {permission.description && (
                              <p className="text-xs text-muted-foreground">
                                {permission.description}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {selectedPermissions.size} of {permissions.length} permissions selected
            </span>
            {hasChanges() && (
              <Badge variant="outline" className="text-xs">
                Unsaved changes
              </Badge>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={saving || !hasChanges() || role.name === 'system_admin'}
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}