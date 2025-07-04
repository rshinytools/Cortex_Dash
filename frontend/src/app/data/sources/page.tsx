// ABOUTME: Data sources management page for configuring study data connections
// ABOUTME: Allows users to add, edit, and monitor data source configurations

'use client';

import { MainLayout } from '@/components/layout/main-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Database, Cloud, FolderSync, Server, MoreHorizontal } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export default function DataSourcesPage() {
  const dataSources = [
    {
      id: '1',
      name: 'Medidata Rave',
      type: 'api',
      status: 'active',
      lastSync: '2024-03-04 10:30 AM',
      icon: Cloud,
    },
    {
      id: '2',
      name: 'SFTP Server - Lab Data',
      type: 'sftp',
      status: 'active',
      lastSync: '2024-03-04 09:15 AM',
      icon: Server,
    },
    {
      id: '3',
      name: 'Shared Folder - SAS Datasets',
      type: 'folder',
      status: 'inactive',
      lastSync: '2024-03-03 11:45 PM',
      icon: FolderSync,
    },
  ];

  const getStatusColor = (status: string) => {
    return status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Data Sources</h1>
            <p className="text-muted-foreground">
              Configure and manage data connections for your studies
            </p>
          </div>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Data Source
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Configured Data Sources</CardTitle>
            <CardDescription>
              All data sources configured for your organization
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Sync</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dataSources.map((source) => {
                  const Icon = source.icon;
                  return (
                    <TableRow key={source.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center space-x-2">
                          <Icon className="h-4 w-4 text-muted-foreground" />
                          <span>{source.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="capitalize">{source.type}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className={getStatusColor(source.status)}>
                          {source.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{source.lastSync}</TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>Edit</DropdownMenuItem>
                            <DropdownMenuItem>Test Connection</DropdownMenuItem>
                            <DropdownMenuItem>Sync Now</DropdownMenuItem>
                            <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}