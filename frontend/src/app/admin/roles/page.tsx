// ABOUTME: Role management page - displays all available roles and their permissions
// ABOUTME: Read-only view showing role definitions and associated permissions

'use client';

import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Shield,
  Users,
  FileText,
  Settings,
  Eye,
  Edit,
  Trash2,
  Plus,
  Lock,
  Unlock,
  ArrowLeft
} from 'lucide-react';
import { UserRole } from '@/types';
import { UserMenu } from '@/components/user-menu';

interface RolePermission {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  description: string;
}

interface RoleDefinition {
  role: UserRole;
  label: string;
  description: string;
  variant: "default" | "secondary" | "destructive" | "outline";
  permissions: RolePermission[];
}

const roleDefinitions: RoleDefinition[] = [
  {
    role: UserRole.SYSTEM_ADMIN,
    label: 'System Admin',
    description: 'Complete system access and control',
    variant: 'destructive',
    permissions: [
      { icon: Shield, label: 'Full System Access', description: 'Access to all system features' },
      { icon: Users, label: 'Manage Organizations', description: 'Create and manage all organizations' },
      { icon: Settings, label: 'System Configuration', description: 'Configure system-wide settings' },
      { icon: FileText, label: 'All Studies Access', description: 'Access to all studies across organizations' },
    ],
  },
  {
    role: UserRole.ORG_ADMIN,
    label: 'Organization Admin',
    description: 'Manage users within organization',
    variant: 'default',
    permissions: [
      { icon: Users, label: 'Manage Organization Users', description: 'Create and manage users in organization' },
      { icon: Eye, label: 'View Studies', description: 'View all studies in organization' },
      { icon: FileText, label: 'View Reports', description: 'Access to organization reports' },
      { icon: Shield, label: 'View Activity Logs', description: 'Monitor organization activities' },
    ],
  },
  {
    role: UserRole.STUDY_MANAGER,
    label: 'Study Manager',
    description: 'Manage specific studies and their configurations',
    variant: 'secondary',
    permissions: [
      { icon: Edit, label: 'Configure Studies', description: 'Manage study settings and pipelines' },
      { icon: Users, label: 'Assign Study Users', description: 'Manage study team members' },
      { icon: FileText, label: 'Full Study Access', description: 'Complete access to assigned studies' },
      { icon: Settings, label: 'Study Configuration', description: 'Configure dashboards and widgets' },
    ],
  },
  {
    role: UserRole.DATA_ANALYST,
    label: 'Data Analyst',
    description: 'Analyze study data and create reports',
    variant: 'secondary',
    permissions: [
      { icon: Eye, label: 'View Study Data', description: 'Access to study data and dashboards' },
      { icon: FileText, label: 'Create Reports', description: 'Generate and export reports' },
      { icon: Settings, label: 'Configure Widgets', description: 'Customize dashboard widgets' },
      { icon: Eye, label: 'View Pipelines', description: 'Monitor data pipeline status' },
    ],
  },
  {
    role: UserRole.VIEWER,
    label: 'Viewer',
    description: 'Read-only access to assigned studies',
    variant: 'outline',
    permissions: [
      { icon: Eye, label: 'View Dashboards', description: 'View study dashboards' },
      { icon: Eye, label: 'View Reports', description: 'Access generated reports' },
      { icon: Lock, label: 'Read-Only Access', description: 'Cannot modify any data' },
    ],
  },
];

export default function RolesPage() {
  const { user } = useAuth();
  const router = useRouter();

  // Check if user has permission
  const canAccessPage = user?.role && 
    [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN].includes(user.role as UserRole);

  if (!canAccessPage) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="py-6">
            <p className="text-center text-muted-foreground">
              You don't have permission to access this page.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
        <Button
          variant="link"
          className="p-0 h-auto font-normal"
          onClick={() => router.push('/dashboard')}
        >
          Dashboard
        </Button>
        <span>/</span>
        <Button
          variant="link"
          className="p-0 h-auto font-normal"
          onClick={() => router.push('/admin')}
        >
          Admin
        </Button>
        <span>/</span>
        <span className="text-foreground">Roles & Permissions</span>
      </div>

      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/admin')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Admin
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Roles & Permissions</h1>
          <p className="text-muted-foreground mt-1">
            Overview of system roles and their associated permissions
          </p>
        </div>
        <UserMenu />
      </div>

      <div className="grid gap-6">
        {roleDefinitions.map((roledef) => (
          <Card key={roledef.role}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Shield className="h-6 w-6 text-muted-foreground" />
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {roledef.label}
                      <Badge variant={roledef.variant}>
                        {roledef.role}
                      </Badge>
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {roledef.description}
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {roledef.permissions.map((permission, index) => {
                  const Icon = permission.icon;
                  return (
                    <div key={index} className="flex items-start gap-3">
                      <div className="mt-0.5">
                        <Icon className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-sm">{permission.label}</p>
                        <p className="text-sm text-muted-foreground">
                          {permission.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        ))}

        <Card className="bg-muted/50">
          <CardContent className="py-6">
            <div className="flex items-center gap-3">
              <Lock className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="font-medium">Role Assignment</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Roles can only be assigned by System Administrators or Organization Administrators
                  (for their organization). Users inherit all permissions associated with their role.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}