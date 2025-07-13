// ABOUTME: Component for comparing two template versions side by side
// ABOUTME: Shows differences between versions with change highlighting

import React, { useEffect, useState } from 'react';
import {
  GitCompare,
  Plus,
  Minus,
  Edit,
  AlertTriangle,
  ChevronRight,
  Loader2,
  X,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { dashboardTemplateApi } from '@/lib/api/dashboard-templates';
import { VersionComparison as VersionComparisonType, ChangeDetail, ChangeCategory } from '@/types/template-version';
import { format } from 'date-fns';

interface VersionComparisonProps {
  templateId: string;
  version1Id: string;
  version2Id: string;
  onClose?: () => void;
  className?: string;
}

export function VersionComparison({
  templateId,
  version1Id,
  version2Id,
  onClose,
  className,
}: VersionComparisonProps) {
  const [comparison, setComparison] = useState<VersionComparisonType | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<ChangeCategory | 'all'>('all');

  useEffect(() => {
    fetchComparison();
  }, [templateId, version1Id, version2Id]);

  const fetchComparison = async () => {
    try {
      setLoading(true);
      const data = await dashboardTemplateApi.compareVersions(templateId, version1Id, version2Id);
      setComparison(data);
    } catch (error) {
      console.error('Failed to compare versions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getChangeIcon = (change: ChangeDetail) => {
    switch (change.type) {
      case 'addition':
        return <Plus className="h-4 w-4 text-green-500" />;
      case 'removal':
        return <Minus className="h-4 w-4 text-red-500" />;
      case 'type_change':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case 'value_change':
        return <Edit className="h-4 w-4 text-blue-500" />;
      default:
        return null;
    }
  };

  const getChangeBadgeVariant = (changeType: string) => {
    switch (changeType) {
      case 'major':
        return 'destructive';
      case 'minor':
        return 'default';
      case 'patch':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getCategoryBadgeVariant = (category: ChangeCategory) => {
    switch (category) {
      case 'structure':
      case 'menu':
        return 'destructive';
      case 'widget':
      case 'data_source':
        return 'default';
      case 'styling':
      case 'metadata':
        return 'secondary';
      case 'permission':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const filterChanges = (changes: ChangeDetail[]) => {
    if (selectedCategory === 'all') return changes;
    return changes.filter(change => change.category === selectedCategory);
  };

  const groupChangesByCategory = (changes: ChangeDetail[]) => {
    return changes.reduce((groups, change) => {
      const category = change.category;
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(change);
      return groups;
    }, {} as Record<ChangeCategory, ChangeDetail[]>);
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (!comparison) {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <p className="text-muted-foreground">Failed to load comparison</p>
        </CardContent>
      </Card>
    );
  }

  const filteredChanges = filterChanges(comparison.changes);
  const groupedChanges = groupChangesByCategory(comparison.changes);
  const categories = Object.keys(groupedChanges) as ChangeCategory[];

  return (
    <Card className={cn('max-w-6xl', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <GitCompare className="h-5 w-5" />
              Version Comparison
            </CardTitle>
            <CardDescription>
              Comparing changes between versions
            </CardDescription>
          </div>
          {onClose && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Version Info */}
        <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
          <div className="flex-1">
            <div className="font-medium">v{comparison.version1.version}</div>
            <div className="text-sm text-muted-foreground">
              {format(new Date(comparison.version1.created_at), 'PPp')}
            </div>
          </div>
          <ChevronRight className="h-5 w-5 mx-4" />
          <div className="flex-1 text-right">
            <div className="font-medium">v{comparison.version2.version}</div>
            <div className="text-sm text-muted-foreground">
              {format(new Date(comparison.version2.created_at), 'PPp')}
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Overall Change:</span>
            <Badge variant={getChangeBadgeVariant(comparison.change_type)}>
              {comparison.change_type.toUpperCase()}
            </Badge>
            {comparison.has_breaking_changes && (
              <Badge variant="destructive">Breaking Changes</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{comparison.summary}</p>
        </div>

        <Separator />

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant={selectedCategory === 'all' ? 'default' : 'outline'}
            onClick={() => setSelectedCategory('all')}
          >
            All ({comparison.changes.length})
          </Button>
          {categories.map(category => (
            <Button
              key={category}
              size="sm"
              variant={selectedCategory === category ? 'default' : 'outline'}
              onClick={() => setSelectedCategory(category)}
            >
              <Badge
                variant={getCategoryBadgeVariant(category)}
                className="mr-1"
              >
                {category.replace('_', ' ')}
              </Badge>
              ({groupedChanges[category].length})
            </Button>
          ))}
        </div>

        {/* Changes List */}
        <ScrollArea className="h-[400px]">
          <div className="space-y-3">
            {filteredChanges.length === 0 ? (
              <p className="text-center py-8 text-muted-foreground">
                No changes in this category
              </p>
            ) : (
              filteredChanges.map((change, index) => (
                <div
                  key={index}
                  className={cn(
                    'p-4 rounded-lg border',
                    change.breaking && 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950'
                  )}
                >
                  <div className="flex items-start gap-3">
                    {getChangeIcon(change)}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">
                          {change.description}
                        </span>
                        <Badge
                          variant={getCategoryBadgeVariant(change.category)}
                          className="text-xs"
                        >
                          {change.category.replace('_', ' ')}
                        </Badge>
                        {change.breaking && (
                          <Badge variant="destructive" className="text-xs">
                            Breaking
                          </Badge>
                        )}
                      </div>
                      
                      <div className="text-xs text-muted-foreground font-mono">
                        {change.path}
                      </div>

                      {/* Show value changes */}
                      {change.type === 'value_change' && (
                        <div className="grid grid-cols-2 gap-4 mt-2">
                          <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded text-xs">
                            <div className="font-medium text-red-700 dark:text-red-400 mb-1">
                              Old Value
                            </div>
                            <code className="text-red-600 dark:text-red-300">
                              {change.old_value || 'null'}
                            </code>
                          </div>
                          <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded text-xs">
                            <div className="font-medium text-green-700 dark:text-green-400 mb-1">
                              New Value
                            </div>
                            <code className="text-green-600 dark:text-green-300">
                              {change.new_value || 'null'}
                            </code>
                          </div>
                        </div>
                      )}

                      {/* Show type changes */}
                      {change.type === 'type_change' && (
                        <div className="flex items-center gap-2 mt-2 text-xs">
                          <Badge variant="outline" className="text-red-600">
                            {change.old_type}
                          </Badge>
                          <ChevronRight className="h-3 w-3" />
                          <Badge variant="outline" className="text-green-600">
                            {change.new_type}
                          </Badge>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}