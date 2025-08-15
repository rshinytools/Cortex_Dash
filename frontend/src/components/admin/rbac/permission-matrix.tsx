// ABOUTME: Permission matrix component showing role-permission relationships
// ABOUTME: Provides a visual grid view of which roles have which permissions

'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { 
  Shield, 
  Check, 
  X, 
  Search,
  Loader2,
  Download,
  Edit,
  Save,
  AlertCircle
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

interface PermissionMatrix {
  roles: string[];
  permissions: string[];
  matrix: Record<string, Record<string, boolean>>;
}

export function PermissionMatrix() {
  const [matrix, setMatrix] = useState<PermissionMatrix | null>(null);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [editedMatrix, setEditedMatrix] = useState<Record<string, Record<string, boolean>>>({});
  const [saving, setSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedResource, setSelectedResource] = useState<string>('all');

  useEffect(() => {
    fetchMatrix();
  }, []);

  const fetchMatrix = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      const response = await axios.get('http://localhost:8000/api/v1/rbac/permission-matrix', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMatrix(response.data);
      setEditedMatrix(response.data.matrix);
    } catch (error) {
      console.error('Failed to fetch permission matrix:', error);
      toast.error('Failed to load permission matrix');
    } finally {
      setLoading(false);
    }
  };

  const handlePermissionToggle = (role: string, permission: string) => {
    if (!editMode) return;
    
    const newMatrix = { ...editedMatrix };
    if (!newMatrix[role]) {
      newMatrix[role] = {};
    }
    newMatrix[role][permission] = !newMatrix[role][permission];
    setEditedMatrix(newMatrix);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('auth_token');
      
      // Calculate changes for each role
      const updates = [];
      for (const role of matrix?.roles || []) {
        const permissions = [];
        for (const permission of matrix?.permissions || []) {
          if (editedMatrix[role]?.[permission]) {
            permissions.push(permission);
          }
        }
        
        // Find role ID (we'll need to fetch this)
        const rolesResponse = await axios.get('http://localhost:8000/api/v1/rbac/roles', {
          headers: { Authorization: `Bearer ${token}` },
        });
        const roleData = rolesResponse.data.find((r: any) => r.name === role);
        
        if (roleData) {
          updates.push({
            roleId: roleData.id,
            permissions,
          });
        }
      }
      
      // Update each role's permissions
      for (const update of updates) {
        await axios.put(
          `http://localhost:8000/api/v1/rbac/roles/${update.roleId}/permissions`,
          { permissions: update.permissions },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
      
      toast.success('Permissions updated successfully');
      setEditMode(false);
      fetchMatrix(); // Refresh the matrix
    } catch (error) {
      console.error('Failed to save permissions:', error);
      toast.error('Failed to save permissions');
    } finally {
      setSaving(false);
    }
  };

  const exportMatrix = () => {
    if (!matrix) return;
    
    // Create CSV content
    const headers = ['Permission', ...matrix.roles];
    const rows = matrix.permissions.map(permission => {
      const row = [permission];
      for (const role of matrix.roles) {
        row.push(editedMatrix[role]?.[permission] ? 'Yes' : 'No');
      }
      return row;
    });
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'permission-matrix.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Extract resources from permissions
  const resources = matrix ? 
    [...new Set(matrix.permissions.map(p => p.split('.')[0]))] : [];
  
  // Filter permissions based on search and resource
  const filteredPermissions = matrix?.permissions.filter(permission => {
    const matchesSearch = permission.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesResource = selectedResource === 'all' || permission.startsWith(selectedResource + '.');
    return matchesSearch && matchesResource;
  }) || [];

  const hasChanges = () => {
    if (!matrix) return false;
    return JSON.stringify(matrix.matrix) !== JSON.stringify(editedMatrix);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (!matrix) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">
            Failed to load permission matrix
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Permission Matrix</CardTitle>
            <CardDescription>
              Visual representation of role and permission relationships
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={exportMatrix}
            >
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            {!editMode ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditMode(true)}
              >
                <Edit className="h-4 w-4 mr-2" />
                Edit Mode
              </Button>
            ) : (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setEditMode(false);
                    setEditedMatrix(matrix.matrix);
                  }}
                  disabled={saving}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={saving || !hasChanges()}
                >
                  {saving ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save Changes
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search permissions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={selectedResource}
              onChange={(e) => setSelectedResource(e.target.value)}
              className="px-3 py-2 border rounded-md"
            >
              <option value="all">All Resources</option>
              {resources.map(resource => (
                <option key={resource} value={resource}>
                  {resource.charAt(0).toUpperCase() + resource.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {editMode && (
            <div className="bg-amber-50 border border-amber-200 rounded-md p-3 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-600" />
              <p className="text-sm text-amber-800">
                You are in edit mode. Click on checkboxes to modify permissions. Remember to save your changes.
              </p>
            </div>
          )}

          {/* Matrix Grid */}
          <div className="border rounded-lg overflow-hidden">
            <ScrollArea className="w-full">
              <div className="min-w-[800px]">
                {/* Header */}
                <div className="grid grid-cols-[250px_repeat(auto-fit,minmax(120px,1fr))] bg-muted/50 border-b">
                  <div className="p-3 font-semibold text-sm flex items-center">
                    <Shield className="h-4 w-4 mr-2" />
                    Permission / Role
                  </div>
                  {matrix.roles.map(role => (
                    <div key={role} className="p-3 text-center border-l">
                      <Badge variant="outline" className="text-xs">
                        {role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Badge>
                    </div>
                  ))}
                </div>

                {/* Permission Rows */}
                {filteredPermissions.map((permission, idx) => (
                  <div
                    key={permission}
                    className={`grid grid-cols-[250px_repeat(auto-fit,minmax(120px,1fr))] ${
                      idx % 2 === 0 ? 'bg-background' : 'bg-muted/20'
                    } border-b last:border-b-0`}
                  >
                    <div className="p-3 text-sm">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger className="text-left">
                            <span className="font-medium">{permission}</span>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="max-w-xs">
                              {permission.replace('.', ': ').replace('_', ' ')}
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    {matrix.roles.map(role => (
                      <div key={`${role}-${permission}`} className="p-3 text-center border-l">
                        {editMode && role !== 'system_admin' ? (
                          <Checkbox
                            checked={editedMatrix[role]?.[permission] || false}
                            onCheckedChange={() => handlePermissionToggle(role, permission)}
                            className="mx-auto"
                          />
                        ) : (
                          <div className="flex justify-center">
                            {(editMode ? editedMatrix : matrix.matrix)[role]?.[permission] ? (
                              <Check className="h-4 w-4 text-green-600" />
                            ) : (
                              <X className="h-4 w-4 text-muted-foreground/50" />
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Check className="h-4 w-4 text-green-600" />
              <span>Permission Granted</span>
            </div>
            <div className="flex items-center gap-2">
              <X className="h-4 w-4 text-muted-foreground/50" />
              <span>Permission Not Granted</span>
            </div>
            {editMode && (
              <div className="flex items-center gap-2">
                <Checkbox className="h-4 w-4" />
                <span>Click to Toggle</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}