// ABOUTME: Widget selection component for dashboard template designer
// ABOUTME: Allows users to browse and select widgets from the library to add to their dashboard

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Search, Plus, Info } from 'lucide-react';
import { widgetsApi } from '@/lib/api/widgets';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';

interface WidgetSelectorProps {
  open: boolean;
  onClose: () => void;
  onSelect: (widget: any) => void;
}

export function WidgetSelector({ open, onClose, onSelect }: WidgetSelectorProps) {
  const [categories, setCategories] = useState<any[]>([]);
  const [widgets, setWidgets] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (open) {
      loadCategories();
      loadWidgets();
    }
  }, [open]);

  useEffect(() => {
    if (open) {
      loadWidgets();
    }
  }, [selectedCategory]);

  const loadCategories = async () => {
    try {
      const data = await widgetsApi.getCategories();
      setCategories(data);
    } catch (error) {
      console.error('Failed to load categories:', error);
      toast({
        title: 'Error',
        description: 'Failed to load widget categories',
        variant: 'destructive',
      });
    }
  };

  const loadWidgets = async () => {
    setLoading(true);
    try {
      const params = selectedCategory !== 'all' 
        ? { category_id: parseInt(selectedCategory) }
        : undefined;
      
      const data = await widgetsApi.getLibrary(params);
      setWidgets(data);
    } catch (error) {
      console.error('Failed to load widgets:', error);
      toast({
        title: 'Error',
        description: 'Failed to load widgets',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredWidgets = widgets.filter(widget =>
    widget.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    widget.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectWidget = (widget: any) => {
    onSelect(widget);
    onClose();
  };

  const getSizeDisplay = (constraints: any) => {
    if (!constraints) return '';
    return `${constraints.defaultWidth}x${constraints.defaultHeight}`;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Add Widget</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search widgets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Category Tabs */}
          <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
            <TabsList className="grid grid-cols-6 w-full">
              <TabsTrigger value="all">All</TabsTrigger>
              {categories.map((category) => (
                <TabsTrigger key={category.id} value={category.id.toString()}>
                  {category.display_name}
                  <Badge variant="secondary" className="ml-2">
                    {category.widget_count}
                  </Badge>
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value={selectedCategory} className="mt-4">
              <ScrollArea className="h-[400px] pr-4">
                {loading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-4">
                    {filteredWidgets.map((widget) => (
                      <Card
                        key={widget.id}
                        className={cn(
                          "cursor-pointer transition-all hover:shadow-md",
                          "hover:border-primary"
                        )}
                        onClick={() => handleSelectWidget(widget)}
                      >
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div>
                              <CardTitle className="text-base">{widget.name}</CardTitle>
                              <CardDescription className="mt-1">
                                {widget.description}
                              </CardDescription>
                            </div>
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-8 w-8"
                              onClick={(e) => {
                                e.stopPropagation();
                                // TODO: Show widget details
                              }}
                            >
                              <Info className="h-4 w-4" />
                            </Button>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="flex items-center justify-between text-sm text-muted-foreground">
                            <div className="flex items-center gap-4">
                              <span>Size: {getSizeDisplay(widget.size_constraints)}</span>
                              <Badge variant="outline">{widget.category.display_name}</Badge>
                            </div>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSelectWidget(widget);
                              }}
                            >
                              <Plus className="h-4 w-4 mr-1" />
                              Add
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}

                {!loading && filteredWidgets.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                    <p>No widgets found</p>
                    {searchQuery && (
                      <p className="text-sm mt-1">Try adjusting your search</p>
                    )}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
}