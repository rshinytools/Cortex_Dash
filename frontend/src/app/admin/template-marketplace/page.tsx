// ABOUTME: Template marketplace main page for browsing, searching, and filtering dashboard templates
// ABOUTME: Currently disabled - redirects to disabled page

'use client';

import MarketplaceDisabled from './disabled';

export default function TemplateMarketplacePage() {
  return <MarketplaceDisabled />;
}

/* Original implementation preserved below for future use
import { useState, useEffect } from 'react';
import { Search, Filter, Star, Download, Eye, Grid, List, ArrowUpDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';

interface TemplateMarketplaceItem {
  id: string;
  code: string;
  name: string;
  description: string;
  category: 'overview' | 'safety' | 'efficacy' | 'operational' | 'quality' | 'custom';
  version_string: string;
  screenshot_urls: string[];
  tags: string[];
  average_rating: number;
  total_ratings: number;
  download_count: number;
  creator_name: string;
  created_at: string;
  is_verified: boolean;
}

interface TemplateFilters {
  category: string;
  rating: string;
  sortBy: string;
  searchTerm: string;
}

const CATEGORIES = [
  { value: 'all', label: 'All Categories' },
  { value: 'overview', label: 'Overview' },
  { value: 'safety', label: 'Safety' },
  { value: 'efficacy', label: 'Efficacy' },
  { value: 'operational', label: 'Operational' },
  { value: 'quality', label: 'Quality' },
  { value: 'custom', label: 'Custom' },
];

const SORT_OPTIONS = [
  { value: 'popular', label: 'Most Popular' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'recent', label: 'Most Recent' },
  { value: 'downloads', label: 'Most Downloaded' },
  { value: 'name', label: 'Name A-Z' },
];

export default function TemplateMarketplacePage() {
  const [templates, setTemplates] = useState<TemplateMarketplaceItem[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<TemplateMarketplaceItem[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateMarketplaceItem | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const { toast } = useToast();

  const [filters, setFilters] = useState<TemplateFilters>({
    category: 'all',
    rating: 'all',
    sortBy: 'popular',
    searchTerm: '',
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [templates, filters]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      
      // Mock data for now - replace with actual API call
      const mockTemplates: TemplateMarketplaceItem[] = [
        {
          id: '1',
          code: 'clinical-overview-v2',
          name: 'Clinical Overview Dashboard',
          description: 'Comprehensive overview dashboard with enrollment metrics, safety signals, and study progress tracking.',
          category: 'overview',
          version_string: '2.1.0',
          screenshot_urls: ['/api/placeholder/400/300', '/api/placeholder/400/300'],
          tags: ['enrollment', 'safety', 'overview', 'metrics'],
          average_rating: 4.8,
          total_ratings: 124,
          download_count: 1250,
          creator_name: 'Sagarmatha AI',
          created_at: '2024-01-15T10:00:00Z',
          is_verified: true,
        },
        {
          id: '2',
          code: 'safety-monitoring',
          name: 'Safety Monitoring Dashboard',
          description: 'Specialized dashboard for adverse event monitoring and safety signal detection.',
          category: 'safety',
          version_string: '1.5.2',
          screenshot_urls: ['/api/placeholder/400/300'],
          tags: ['safety', 'adverse-events', 'monitoring', 'signals'],
          average_rating: 4.6,
          total_ratings: 89,
          download_count: 756,
          creator_name: 'SafetyFirst Analytics',
          created_at: '2024-02-20T14:30:00Z',
          is_verified: false,
        },
        {
          id: '3',
          code: 'efficacy-analysis',
          name: 'Efficacy Analysis Suite',
          description: 'Advanced efficacy analysis with endpoint tracking and statistical visualizations.',
          category: 'efficacy',
          version_string: '3.0.1',
          screenshot_urls: ['/api/placeholder/400/300', '/api/placeholder/400/300', '/api/placeholder/400/300'],
          tags: ['efficacy', 'endpoints', 'statistics', 'analysis'],
          average_rating: 4.9,
          total_ratings: 156,
          download_count: 1580,
          creator_name: 'Clinical Stats Pro',
          created_at: '2024-03-10T09:15:00Z',
          is_verified: true,
        },
      ];

      setTemplates(mockTemplates);
    } catch (error) {
      console.error('Error fetching templates:', error);
      toast({
        title: 'Error',
        description: 'Failed to load templates from marketplace',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...templates];

    // Apply search filter
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase();
      filtered = filtered.filter(
        (template) =>
          template.name.toLowerCase().includes(searchLower) ||
          template.description.toLowerCase().includes(searchLower) ||
          template.tags.some(tag => tag.toLowerCase().includes(searchLower))
      );
    }

    // Apply category filter
    if (filters.category !== 'all') {
      filtered = filtered.filter((template) => template.category === filters.category);
    }

    // Apply rating filter
    if (filters.rating !== 'all') {
      const minRating = parseFloat(filters.rating);
      filtered = filtered.filter((template) => template.average_rating >= minRating);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (filters.sortBy) {
        case 'rating':
          return b.average_rating - a.average_rating;
        case 'recent':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'downloads':
          return b.download_count - a.download_count;
        case 'name':
          return a.name.localeCompare(b.name);
        case 'popular':
        default:
          return (b.download_count * 0.7 + b.total_ratings * 0.3) - (a.download_count * 0.7 + a.total_ratings * 0.3);
      }
    });

    setFilteredTemplates(filtered);
  };

  const handleDownloadTemplate = async (template: TemplateMarketplaceItem) => {
    try {
      // API call to download template
      toast({
        title: 'Success',
        description: `Template "${template.name}" has been added to your templates`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download template',
        variant: 'destructive',
      });
    }
  };

  const handlePreviewTemplate = (template: TemplateMarketplaceItem) => {
    setSelectedTemplate(template);
    setPreviewOpen(true);
  };

  const renderStars = (rating: number) => {
    return [...Array(5)].map((_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < Math.floor(rating) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
      />
    ));
  };

  const renderTemplateCard = (template: TemplateMarketplaceItem) => (
    <Card key={template.id} className="group hover:shadow-lg transition-shadow">
      <CardHeader className="relative">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <CardTitle className="text-lg">{template.name}</CardTitle>
              {template.is_verified && (
                <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700">
                  Verified
                </Badge>
              )}
            </div>
            <Badge variant="outline" className="capitalize mb-2">
              {template.category}
            </Badge>
            <CardDescription className="text-sm">{template.description}</CardDescription>
          </div>
        </div>
        
        {template.screenshot_urls.length > 0 && (
          <div className="mt-4 relative overflow-hidden rounded-md">
            <img 
              src={template.screenshot_urls[0]} 
              alt={`${template.name} preview`}
              className="w-full h-32 object-cover group-hover:scale-105 transition-transform"
            />
            {template.screenshot_urls.length > 1 && (
              <Badge className="absolute bottom-2 right-2 bg-black/50 text-white">
                +{template.screenshot_urls.length - 1} more
              </Badge>
            )}
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        <div className="flex flex-wrap gap-1 mb-4">
          {template.tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
          {template.tags.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{template.tags.length - 3}
            </Badge>
          )}
        </div>
        
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-1">
            {renderStars(template.average_rating)}
            <span className="text-sm text-gray-600 ml-1">
              {template.average_rating.toFixed(1)} ({template.total_ratings})
            </span>
          </div>
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <Download className="w-4 h-4" />
            {template.download_count.toLocaleString()}
          </div>
        </div>
        
        <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
          <span>v{template.version_string}</span>
          <span>by {template.creator_name}</span>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => handlePreviewTemplate(template)}
          >
            <Eye className="w-4 h-4 mr-1" />
            Preview
          </Button>
          <Button
            size="sm"
            className="flex-1"
            onClick={() => handleDownloadTemplate(template)}
          >
            <Download className="w-4 h-4 mr-1" />
            Download
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const renderTemplateList = (template: TemplateMarketplaceItem) => (
    <Card key={template.id} className="mb-4">
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          {template.screenshot_urls.length > 0 && (
            <img 
              src={template.screenshot_urls[0]} 
              alt={`${template.name} preview`}
              className="w-24 h-24 object-cover rounded-md flex-shrink-0"
            />
          )}
          
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-lg font-semibold">{template.name}</h3>
                  {template.is_verified && (
                    <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700">
                      Verified
                    </Badge>
                  )}
                  <Badge variant="outline" className="capitalize">
                    {template.category}
                  </Badge>
                </div>
                <p className="text-gray-600 text-sm mb-2">{template.description}</p>
                
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <div className="flex items-center gap-1">
                    {renderStars(template.average_rating)}
                    <span className="ml-1">
                      {template.average_rating.toFixed(1)} ({template.total_ratings})
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Download className="w-4 h-4" />
                    {template.download_count.toLocaleString()}
                  </div>
                  <span>v{template.version_string}</span>
                  <span>by {template.creator_name}</span>
                </div>
              </div>
              
              <div className="flex gap-2 ml-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePreviewTemplate(template)}
                >
                  <Eye className="w-4 h-4 mr-1" />
                  Preview
                </Button>
                <Button
                  size="sm"
                  onClick={() => handleDownloadTemplate(template)}
                >
                  <Download className="w-4 h-4 mr-1" />
                  Download
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading templates...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Template Marketplace</h1>
        <p className="text-gray-600">
          Discover and download dashboard templates from the community
        </p>
      </div>

      {/* Filters */}
      <div className="mb-8 space-y-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search templates..."
                value={filters.searchTerm}
                onChange={(e) => setFilters({ ...filters, searchTerm: e.target.value })}
                className="pl-10"
              />
            </div>
          </div>
          
          <div className="flex gap-2">
            <Select
              value={filters.category}
              onValueChange={(value) => setFilters({ ...filters, category: value })}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((category) => (
                  <SelectItem key={category.value} value={category.value}>
                    {category.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={filters.rating}
              onValueChange={(value) => setFilters({ ...filters, rating: value })}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Rating" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Ratings</SelectItem>
                <SelectItem value="4.5">4.5+ Stars</SelectItem>
                <SelectItem value="4.0">4.0+ Stars</SelectItem>
                <SelectItem value="3.5">3.5+ Stars</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.sortBy}
              onValueChange={(value) => setFilters({ ...filters, sortBy: value })}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <div className="flex border rounded-md">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('grid')}
                className="rounded-r-none"
              >
                <Grid className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('list')}
                className="rounded-l-none"
              >
                <List className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="mb-4 flex items-center justify-between">
        <span className="text-sm text-gray-600">
          {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} found
        </span>
      </div>

      {/* Templates Grid/List */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map(renderTemplateCard)}
        </div>
      ) : (
        <div>
          {filteredTemplates.map(renderTemplateList)}
        </div>
      )}

      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No templates found matching your filters.</p>
        </div>
      )}

      {/* Template Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {selectedTemplate && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {selectedTemplate.name}
                  {selectedTemplate.is_verified && (
                    <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                      Verified
                    </Badge>
                  )}
                </DialogTitle>
                <DialogDescription>
                  {selectedTemplate.description}
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-6">
                {/* Screenshots */}
                {selectedTemplate.screenshot_urls.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3">Preview Images</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {selectedTemplate.screenshot_urls.map((url, index) => (
                        <img
                          key={index}
                          src={url}
                          alt={`Preview ${index + 1}`}
                          className="w-full h-48 object-cover rounded-md border"
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Details */}
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold mb-3">Details</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Category:</span>
                        <Badge variant="outline" className="capitalize">
                          {selectedTemplate.category}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Version:</span>
                        <span>{selectedTemplate.version_string}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Creator:</span>
                        <span>{selectedTemplate.creator_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Downloads:</span>
                        <span>{selectedTemplate.download_count.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-3">Ratings & Reviews</h3>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        {renderStars(selectedTemplate.average_rating)}
                        <span className="text-sm">
                          {selectedTemplate.average_rating.toFixed(1)} out of 5
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">
                        Based on {selectedTemplate.total_ratings} review{selectedTemplate.total_ratings !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Tags */}
                <div>
                  <h3 className="font-semibold mb-3">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedTemplate.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-4 border-t">
                  <Button
                    onClick={() => handleDownloadTemplate(selectedTemplate)}
                    className="flex-1"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download Template
                  </Button>
                  <Button variant="outline" onClick={() => setPreviewOpen(false)}>
                    Close
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
*/