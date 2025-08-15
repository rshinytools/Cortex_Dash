// ABOUTME: Component for displaying and managing mapping templates
// ABOUTME: Shows list of reusable templates with CRUD operations

import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
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
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  Plus, 
  Search, 
  MoreVertical, 
  Edit, 
  Copy, 
  Trash, 
  FileJson,
  Filter,
  Download,
  Upload
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

interface MappingTemplate {
  id: string;
  name: string;
  description: string;
  widget_type: string;
  category: string;
  tags: string[];
  configuration: any;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
  usage_count: number;
}

export function MappingTemplateList() {
  const [templates, setTemplates] = useState<MappingTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterCategory, setFilterCategory] = useState('all');
  const [selectedTemplate, setSelectedTemplate] = useState<MappingTemplate | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/mapping-templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch templates',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (template: MappingTemplate) => {
    try {
      const response = await fetch(`/api/v1/mapping-templates/${template.id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Template deleted successfully',
        });
        fetchTemplates();
        setShowDeleteDialog(false);
        setSelectedTemplate(null);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete template',
        variant: 'destructive',
      });
    }
  };

  const handleDuplicate = async (template: MappingTemplate) => {
    try {
      const response = await fetch(`/api/v1/mapping-templates/${template.id}/duplicate`, {
        method: 'POST',
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Template duplicated successfully',
        });
        fetchTemplates();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to duplicate template',
        variant: 'destructive',
      });
    }
  };

  const handleExport = async (template: MappingTemplate) => {
    const dataStr = JSON.stringify(template.configuration, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `${template.name}_template.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || template.widget_type === filterType;
    const matchesCategory = filterCategory === 'all' || template.category === filterCategory;
    
    return matchesSearch && matchesType && matchesCategory;
  });

  const getWidgetTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'kpi_metric': 'bg-blue-100 text-blue-800',
      'time_series': 'bg-green-100 text-green-800',
      'distribution': 'bg-purple-100 text-purple-800',
      'data_table': 'bg-orange-100 text-orange-800',
      'subject_timeline': 'bg-pink-100 text-pink-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Mapping Templates</h2>
          <p className="text-muted-foreground">
            Reusable widget configuration templates
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Upload className="mr-2 h-4 w-4" />
            Import
          </Button>
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            New Template
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search templates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>
        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-[180px]">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Widget Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="kpi_metric">KPI Metric</SelectItem>
            <SelectItem value="time_series">Time Series</SelectItem>
            <SelectItem value="distribution">Distribution</SelectItem>
            <SelectItem value="data_table">Data Table</SelectItem>
            <SelectItem value="subject_timeline">Timeline</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="clinical">Clinical</SelectItem>
            <SelectItem value="operational">Operational</SelectItem>
            <SelectItem value="safety">Safety</SelectItem>
            <SelectItem value="quality">Quality</SelectItem>
            <SelectItem value="custom">Custom</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Templates Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>Usage</TableHead>
              <TableHead>Version</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Updated</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8">
                  Loading templates...
                </TableCell>
              </TableRow>
            ) : filteredTemplates.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8">
                  No templates found
                </TableCell>
              </TableRow>
            ) : (
              filteredTemplates.map((template) => (
                <TableRow key={template.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{template.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {template.description}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant="secondary"
                      className={getWidgetTypeColor(template.widget_type)}
                    >
                      {template.widget_type.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {template.category}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">
                      {template.tags.slice(0, 2).map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      {template.tags.length > 2 && (
                        <Badge variant="secondary" className="text-xs">
                          +{template.tags.length - 2}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {template.usage_count} uses
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      v{template.version}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={template.is_active ? 'default' : 'secondary'}>
                      {template.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm text-muted-foreground">
                      {new Date(template.updated_at).toLocaleDateString()}
                    </div>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedTemplate(template);
                            setShowEditDialog(true);
                          }}
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDuplicate(template)}
                        >
                          <Copy className="mr-2 h-4 w-4" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleExport(template)}
                        >
                          <Download className="mr-2 h-4 w-4" />
                          Export
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => {
                            setSelectedTemplate(template);
                            setShowDeleteDialog(true);
                          }}
                        >
                          <Trash className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Template</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedTemplate?.name}"? 
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => selectedTemplate && handleDelete(selectedTemplate)}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}