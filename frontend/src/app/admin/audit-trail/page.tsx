// ABOUTME: Audit Trail page for comprehensive logging and compliance tracking
// ABOUTME: Shows all system activities, user actions, and data changes

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { AuthGuard } from '@/components/auth-guard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { 
  Shield,
  FileText,
  User,
  Clock,
  Activity,
  Database,
  Lock,
  Download,
  ArrowLeft,
  Search,
  LogIn,
  LogOut,
  UserPlus,
  Edit,
  Trash,
  Key,
  FileUp,
  AlertCircle,
  TrendingUp
} from 'lucide-react';
import { format } from 'date-fns';
import { motion } from 'framer-motion';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { UserMenu } from '@/components/user-menu';
import { secureApiClient } from '@/lib/api/secure-client';

interface AuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  user_id: string;
  user_email?: string;
  details?: any;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

function AuditTrailContent() {
  console.log('AuditTrailContent component mounted');
  const router = useRouter();
  const { user } = useAuth();
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [stats, setStats] = useState({
    totalEvents: 0,
    activeUsers: 0,
    securityEvents: 0,
    todayEvents: 0
  });

  const fetchAuditLogs = async () => {
    try {
      console.log('Fetching audit logs...');
      
      const response = await secureApiClient.get('/audit-trail/', {
      });
      
      console.log('Audit logs response:', response.data);
      
      if (response.data && Array.isArray(response.data)) {
        console.log('Setting', response.data.length, 'audit logs');
        setAuditLogs(response.data);
        
        // Calculate stats
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayLogs = response.data.filter((log: AuditLog) => 
          new Date(log.created_at) >= today
        );
        
        const uniqueUsers = new Set(response.data.map((log: AuditLog) => log.user_id));
        const securityLogs = response.data.filter((log: AuditLog) => 
          ['LOGIN', 'LOGOUT', 'LOGIN_FAILED', 'PERMISSION_DENIED'].includes(log.action)
        );
        
        setStats({
          totalEvents: response.data.length,
          activeUsers: uniqueUsers.size,
          securityEvents: securityLogs.length,
          todayEvents: todayLogs.length
        });
      }
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('useEffect triggered, calling fetchAuditLogs');
    fetchAuditLogs();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchAuditLogs, 30000);
    return () => clearInterval(interval);
  }, []);

  const getActionIcon = (action: string) => {
    switch (action.toUpperCase()) {
      case 'LOGIN': return <LogIn className="h-4 w-4" />;
      case 'LOGOUT': return <LogOut className="h-4 w-4" />;
      case 'CREATE': 
      case 'CREATE_USER': return <UserPlus className="h-4 w-4" />;
      case 'UPDATE':
      case 'UPDATE_USER': return <Edit className="h-4 w-4" />;
      case 'DELETE': return <Trash className="h-4 w-4" />;
      case 'UPLOAD': return <FileUp className="h-4 w-4" />;
      case 'GRANT':
      case 'REVOKE': return <Key className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getActionBadgeVariant = (action: string) => {
    const upperAction = action.toUpperCase();
    if (['LOGIN', 'CREATE', 'GRANT'].includes(upperAction)) return 'default';
    if (['LOGOUT', 'UPDATE'].includes(upperAction)) return 'secondary';
    if (['DELETE', 'REVOKE', 'LOGIN_FAILED'].includes(upperAction)) return 'destructive';
    return 'outline';
  };

  const filteredLogs = auditLogs.filter(log => {
    const matchesSearch = !searchTerm || 
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.resource_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.user_email && log.user_email.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesAction = actionFilter === 'all' || log.action === actionFilter;
    
    return matchesSearch && matchesAction;
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-8"
        >
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
            <Button
              variant="link"
              className="p-0 h-auto font-normal"
              onClick={() => router.push('/admin')}
            >
              Admin
            </Button>
            <span>/</span>
            <span className="text-foreground">Audit Trail</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 dark:from-purple-400 dark:to-pink-400 bg-clip-text text-transparent">
                Audit Trail
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Comprehensive audit logging for 21 CFR Part 11 compliance and security monitoring
              </p>
            </div>
            <div className="flex gap-3">
              <ThemeToggle />
              <UserMenu />
              <Button 
                variant="outline" 
                onClick={() => {
                  const csv = ['Time,User,Action,Resource,Details'].concat(
                    filteredLogs.map(log => 
                      `"${format(new Date(log.created_at), 'yyyy-MM-dd HH:mm:ss')}","${log.user_email || 'System'}","${log.action}","${log.resource_type}","${JSON.stringify(log.details || {})}"`
                    )
                  ).join('\n');
                  const blob = new Blob([csv], { type: 'text/csv' });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `audit-trail-${format(new Date(), 'yyyy-MM-dd')}.csv`;
                  a.click();
                }}
                className="border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <Download className="h-4 w-4 mr-2" />
                Export Logs
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="grid gap-6 md:grid-cols-4 mb-8"
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Events</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {stats.totalEvents.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Last 30 days</p>
                </div>
                <div className="h-12 w-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <Activity className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Active Users</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {stats.activeUsers}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Unique users</p>
                </div>
                <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <User className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Security Events</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {stats.securityEvents}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Auth & access</p>
                </div>
                <div className="h-12 w-12 bg-red-100 dark:bg-red-900/20 rounded-lg flex items-center justify-center">
                  <Shield className="h-6 w-6 text-red-600 dark:text-red-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Today's Events</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {stats.todayEvents}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Since midnight</p>
                </div>
                <div className="h-12 w-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Audit Categories */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 mb-8">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
              <CardTitle className="text-xl text-gray-900 dark:text-gray-100">Audit Categories</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400">
                Types of events tracked in the audit system
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid gap-6 md:grid-cols-3">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg">
                  <h4 className="text-sm font-semibold flex items-center text-blue-900 dark:text-blue-100 mb-3">
                    <User className="h-4 w-4 mr-2" />
                    User Activities
                  </h4>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    <li>• Login/Logout events</li>
                    <li>• Password changes</li>
                    <li>• Role assignments</li>
                    <li>• Permission changes</li>
                    <li>• Profile updates</li>
                  </ul>
                </div>
              
                <div className="p-4 bg-purple-50 dark:bg-purple-900/10 rounded-lg">
                  <h4 className="text-sm font-semibold flex items-center text-purple-900 dark:text-purple-100 mb-3">
                    <Database className="h-4 w-4 mr-2" />
                    Data Operations
                  </h4>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    <li>• Data uploads</li>
                    <li>• Pipeline executions</li>
                    <li>• Widget configurations</li>
                    <li>• Dashboard changes</li>
                    <li>• Export operations</li>
                  </ul>
                </div>
              
                <div className="p-4 bg-red-50 dark:bg-red-900/10 rounded-lg">
                  <h4 className="text-sm font-semibold flex items-center text-red-900 dark:text-red-100 mb-3">
                    <Shield className="h-4 w-4 mr-2" />
                    Security Events
                  </h4>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    <li>• Failed login attempts</li>
                    <li>• Access denials</li>
                    <li>• API authentication</li>
                    <li>• Session management</li>
                    <li>• Security violations</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Recent Events Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 mb-8">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl text-gray-900 dark:text-gray-100">Recent Audit Events</CardTitle>
                  <CardDescription className="text-gray-600 dark:text-gray-400">
                    Latest system activities and user actions
                  </CardDescription>
                </div>
                <div className="flex gap-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <Input
                      placeholder="Search events..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 w-64 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600"
                    />
                  </div>
                  <Select value={actionFilter} onValueChange={setActionFilter}>
                    <SelectTrigger className="w-[180px] bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600">
                      <SelectValue placeholder="Filter by action" />
                    </SelectTrigger>
                    <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                      <SelectItem value="all">All Actions</SelectItem>
                      <SelectItem value="LOGIN">Login</SelectItem>
                      <SelectItem value="LOGOUT">Logout</SelectItem>
                      <SelectItem value="CREATE">Create</SelectItem>
                      <SelectItem value="UPDATE">Update</SelectItem>
                      <SelectItem value="DELETE">Delete</SelectItem>
                      <SelectItem value="GRANT">Grant Permission</SelectItem>
                      <SelectItem value="REVOKE">Revoke Permission</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
            
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                </div>
              ) : filteredLogs.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow className="border-b border-gray-200 dark:border-gray-700">
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Time</TableHead>
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">User</TableHead>
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Action</TableHead>
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Resource</TableHead>
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">IP Address</TableHead>
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredLogs.slice(0, 20).map((log, index) => (
                      <motion.tr
                        key={log.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.02 }}
                        className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                      >
                        <TableCell className="text-sm text-gray-600 dark:text-gray-400 py-3">
                          {format(new Date(log.created_at), 'MMM d, HH:mm:ss')}
                        </TableCell>
                        <TableCell>
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {log.user_email || 'System'}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {getActionIcon(log.action)}
                            <Badge 
                              variant={getActionBadgeVariant(log.action)}
                              className="font-medium"
                            >
                              {log.action.toLowerCase().replace('_', ' ')}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-gray-700 dark:text-gray-300">
                          {log.resource_type}
                        </TableCell>
                        <TableCell className="text-sm text-gray-500 dark:text-gray-400">
                          {log.ip_address || '-'}
                        </TableCell>
                        <TableCell>
                          {log.details && Object.keys(log.details).length > 0 ? (
                            <Badge variant="outline" className="text-xs font-normal">
                              {Object.keys(log.details).length} fields
                            </Badge>
                          ) : (
                            <span className="text-sm text-gray-400">-</span>
                          )}
                        </TableCell>
                      </motion.tr>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="flex flex-col items-center justify-center py-12">
                  <FileText className="h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400 text-lg">No audit events found</p>
                  <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">
                    {searchTerm || actionFilter !== 'all' 
                      ? 'Try adjusting your search or filters'
                      : 'Events will appear here once system activity begins'}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Compliance and Retention Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
          className="grid gap-6 md:grid-cols-2"
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-t-lg">
              <CardTitle className="text-xl text-gray-900 dark:text-gray-100">Compliance Features</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400">
                Regulatory compliance capabilities
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <ul className="space-y-3">
                <li className="flex items-start">
                  <Badge className="mr-3 mt-0.5 bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">21 CFR Part 11</Badge>
                  <span className="text-gray-700 dark:text-gray-300">Electronic signatures and records</span>
                </li>
                <li className="flex items-start">
                  <Badge className="mr-3 mt-0.5 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">HIPAA</Badge>
                  <span className="text-gray-700 dark:text-gray-300">Protected health information security</span>
                </li>
                <li className="flex items-start">
                  <Badge className="mr-3 mt-0.5 bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">GDPR</Badge>
                  <span className="text-gray-700 dark:text-gray-300">Data privacy and protection</span>
                </li>
                <li className="flex items-start">
                  <Badge className="mr-3 mt-0.5 bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400">GxP</Badge>
                  <span className="text-gray-700 dark:text-gray-300">Good clinical practice standards</span>
                </li>
              </ul>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-t-lg">
              <CardTitle className="text-xl text-gray-900 dark:text-gray-100">Audit Retention</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400">
                Data retention and archival policies
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">User Activity Logs</span>
                  <Badge variant="outline" className="bg-white dark:bg-gray-800">7 years</Badge>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Data Change Logs</span>
                  <Badge variant="outline" className="bg-white dark:bg-gray-800">10 years</Badge>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Security Events</span>
                  <Badge variant="outline" className="bg-white dark:bg-gray-800">5 years</Badge>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">System Logs</span>
                  <Badge variant="outline" className="bg-white dark:bg-gray-800">3 years</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}

export default function AuditTrailPage() {
  return (
    <AuthGuard requiredRoles={['system_admin', 'org_admin']}>
      <AuditTrailContent />
    </AuthGuard>
  );
}