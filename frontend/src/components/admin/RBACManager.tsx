// ABOUTME: RBAC management interface for System Administrators
// ABOUTME: Allows dynamic permission assignment and role management

import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  Shield, 
  Users, 
  Key, 
  Settings, 
  Save,
  RefreshCw,
  UserPlus,
  Lock,
  Unlock,
  AlertCircle
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';

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
  permission_count: number;
}

interface PermissionMatrix {
  roles: string[];
  permissions: string[];
  matrix: Record<string, Record<string, boolean>>;
}

export function RBACManager() {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [matrix, setMatrix] = useState<PermissionMatrix | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [modifiedPermissions, setModifiedPermissions] = useState<Record<string, Set<string>>>({});
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch permissions
      const permRes = await fetch('/api/v1/rbac/permissions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (permRes.ok) {
        const permData = await permRes.json();
        setPermissions(permData);
      }
      
      // Fetch roles
      const roleRes = await fetch('/api/v1/rbac/roles', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (roleRes.ok) {
        const roleData = await roleRes.json();
        setRoles(roleData);
        if (roleData.length > 0 && !selectedRole) {
          setSelectedRole(roleData[0].name);
        }
      }
      
      // Fetch permission matrix
      const matrixRes = await fetch('/api/v1/rbac/permission-matrix', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (matrixRes.ok) {
        const matrixData = await matrixRes.json();
        setMatrix(matrixData);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch RBAC data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePermissionToggle = (role: string, permission: string, checked: boolean) => {
    const roleModifications = modifiedPermissions[role] || new Set();
    
    if (checked) {
      roleModifications.add(permission);
    } else {
      roleModifications.delete(permission);
    }
    
    setModifiedPermissions({
      ...modifiedPermissions,
      [role]: roleModifications
    });
    
    // Update local matrix
    if (matrix) {
      const newMatrix = { ...matrix };
      newMatrix.matrix[role][permission] = checked;
      setMatrix(newMatrix);
    }
  };

  const savePermissions = async () => {
    try {
      setSaving(true);
      
      for (const [roleName, permissions] of Object.entries(modifiedPermissions)) {
        if (permissions.size === 0) continue;
        
        const role = roles.find(r => r.name === roleName);
        if (!role) continue;
        
        // Get all permissions for this role from matrix
        const allPermissions = matrix?.permissions.filter(
          p => matrix.matrix[roleName][p]
        ) || [];
        
        const response = await fetch(`/api/v1/rbac/roles/${role.id}/permissions`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            permissions: allPermissions
          })
        });
        
        if (!response.ok) {
          throw new Error('Failed to update permissions');
        }
      }
      
      toast({
        title: 'Success',
        description: 'Permissions updated successfully',
      });
      
      setModifiedPermissions({});
      fetchData(); // Refresh data
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save permissions',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const initializeDefaults = async () => {
    try {
      const response = await fetch('/api/v1/rbac/initialize-defaults', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Default permissions initialized',
        });
        fetchData();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to initialize defaults',
        variant: 'destructive',
      });
    }
  };

  // Group permissions by resource
  const groupedPermissions = permissions.reduce((acc, perm) => {
    if (!acc[perm.resource]) {
      acc[perm.resource] = [];
    }
    acc[perm.resource].push(perm);
    return acc;
  }, {} as Record<string, Permission[]>);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">RBAC Management</h1>
          <p className="text-muted-foreground">
            Manage roles and permissions dynamically
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={initializeDefaults}>
            <Settings className="mr-2 h-4 w-4" />
            Initialize Defaults
          </Button>
          <Button variant="outline" onClick={fetchData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button 
            onClick={savePermissions} 
            disabled={Object.keys(modifiedPermissions).length === 0 || saving}
          >
            <Save className="mr-2 h-4 w-4" />
            Save Changes
          </Button>
        </div>
      </div>

      {Object.keys(modifiedPermissions).length > 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You have unsaved changes. Click "Save Changes" to apply them.
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="matrix" className="space-y-4">
        <TabsList>
          <TabsTrigger value="matrix">Permission Matrix</TabsTrigger>
          <TabsTrigger value="roles">Roles</TabsTrigger>
          <TabsTrigger value="permissions">Permissions</TabsTrigger>
        </TabsList>

        <TabsContent value="matrix" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Permission Matrix</CardTitle>
              <CardDescription>
                Configure which permissions each role has access to
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : matrix ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="sticky left-0 bg-background">Resource</TableHead>
                        <TableHead className="sticky left-0 bg-background">Permission</TableHead>
                        {roles.map(role => (
                          <TableHead key={role.name} className="text-center">
                            <div className="flex flex-col items-center">
                              <span className="font-medium">{role.display_name}</span>
                              <Badge variant="outline" className="mt-1 text-xs">
                                {role.name}
                              </Badge>
                            </div>
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {Object.entries(groupedPermissions).map(([resource, perms]) => (
                        <React.Fragment key={resource}>
                          {perms.map((permission, index) => (
                            <TableRow key={permission.name}>
                              {index === 0 && (
                                <TableCell 
                                  rowSpan={perms.length} 
                                  className="font-medium border-r"
                                >
                                  <Badge variant="secondary">
                                    {resource}
                                  </Badge>
                                </TableCell>
                              )}
                              <TableCell>
                                <div>
                                  <div className="font-mono text-sm">{permission.name}</div>
                                  <div className="text-xs text-muted-foreground">
                                    {permission.description}
                                  </div>
                                </div>
                              </TableCell>
                              {roles.map(role => (
                                <TableCell key={`${role.name}-${permission.name}`} className="text-center">
                                  <Checkbox
                                    checked={matrix.matrix[role.name]?.[permission.name] || false}
                                    onCheckedChange={(checked) => 
                                      handlePermissionToggle(role.name, permission.name, checked as boolean)
                                    }
                                    disabled={role.name === 'system_admin'} // System admin always has all
                                  />
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </React.Fragment>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div>No data available</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="roles" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Roles</CardTitle>
              <CardDescription>
                System roles and their descriptions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role</TableHead>
                    <TableHead>Display Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Permissions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {roles.map(role => (
                    <TableRow key={role.id}>
                      <TableCell>
                        <code className="text-sm">{role.name}</code>
                      </TableCell>
                      <TableCell className="font-medium">
                        {role.display_name}
                      </TableCell>
                      <TableCell className="text-sm">
                        {role.description}
                      </TableCell>
                      <TableCell>
                        <Badge variant={role.is_system ? 'default' : 'secondary'}>
                          {role.is_system ? 'System' : 'Custom'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {role.permission_count} permissions
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="permissions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Available Permissions</CardTitle>
              <CardDescription>
                All permissions available in the system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Permission</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Type</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {permissions.map(permission => (
                    <TableRow key={permission.id}>
                      <TableCell>
                        <code className="text-sm">{permission.name}</code>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {permission.resource}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {permission.action}
                      </TableCell>
                      <TableCell className="text-sm">
                        {permission.description}
                      </TableCell>
                      <TableCell>
                        {permission.is_system ? (
                          <Lock className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Unlock className="h-4 w-4 text-muted-foreground" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}