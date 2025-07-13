// ABOUTME: Individual template details page for viewing template information, reviews, and downloading
// ABOUTME: Currently disabled - redirects to disabled page

'use client';

import MarketplaceDisabled from '../disabled';

export default function TemplateDetailPage() {
  return <MarketplaceDisabled />;
}

/* Original implementation preserved below for future use
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Download, Star, Calendar, User, Shield, Tag, Github, ExternalLink, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';

interface TemplateDetails {
  id: string;
  code: string;
  name: string;
  description: string;
  category: string;
  version_string: string;
  screenshot_urls: string[];
  tags: string[];
  average_rating: number;
  total_ratings: number;
  download_count: number;
  creator_name: string;
  creator_avatar?: string;
  created_at: string;
  updated_at: string;
  is_verified: boolean;
  documentation_url?: string;
  source_url?: string;
  license: string;
  version_history: VersionHistory[];
  reviews: TemplateReview[];
  related_templates: RelatedTemplate[];
  compatibility: string[];
  requirements: string[];
}

interface VersionHistory {
  version: string;
  release_date: string;
  changes: string[];
  breaking_changes: boolean;
}

interface TemplateReview {
  id: string;
  user_name: string;
  user_avatar?: string;
  rating: number;
  review_text: string;
  created_at: string;
  is_verified: boolean;
}

interface RelatedTemplate {
  id: string;
  name: string;
  category: string;
  rating: number;
  downloads: number;
}

export default function TemplateDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const [template, setTemplate] = useState<TemplateDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeImageIndex, setActiveImageIndex] = useState(0);

  useEffect(() => {
    if (params.id) {
      fetchTemplateDetails(params.id as string);
    }
  }, [params.id]);

  const fetchTemplateDetails = async (id: string) => {
    try {
      setLoading(true);
      
      // Mock data - replace with actual API call
      const mockTemplate: TemplateDetails = {
        id,
        code: 'clinical-overview-v2',
        name: 'Clinical Overview Dashboard',
        description: 'A comprehensive overview dashboard designed for clinical trial monitoring. This template provides essential metrics including enrollment tracking, safety signals, efficacy endpoints, and operational KPIs. Perfect for study teams who need a unified view of their clinical trial progress.',
        category: 'overview',
        version_string: '2.1.0',
        screenshot_urls: [
          '/api/placeholder/800/600',
          '/api/placeholder/800/600',
          '/api/placeholder/800/600',
        ],
        tags: ['enrollment', 'safety', 'overview', 'metrics', 'clinical-trial', 'monitoring'],
        average_rating: 4.8,
        total_ratings: 124,
        download_count: 1250,
        creator_name: 'Sagarmatha AI',
        creator_avatar: '/api/placeholder/40/40',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-03-20T15:30:00Z',
        is_verified: true,
        documentation_url: 'https://docs.example.com/templates/clinical-overview',
        source_url: 'https://github.com/example/clinical-overview-template',
        license: 'MIT',
        compatibility: ['CDISC SDTM', 'CDISC ADaM', 'Custom Data'],
        requirements: ['ADSL Dataset', 'ADAE Dataset', 'Study Metadata'],
        version_history: [
          {
            version: '2.1.0',
            release_date: '2024-03-20',
            changes: [
              'Added responsive layout support',
              'Improved safety signal detection',
              'Enhanced data quality indicators',
              'Fixed enrollment chart pagination'
            ],
            breaking_changes: false,
          },
          {
            version: '2.0.0',
            release_date: '2024-02-15',
            changes: [
              'Complete redesign with new layout system',
              'Added theme customization',
              'New widget positioning system',
              'Breaking: Changed data requirements format'
            ],
            breaking_changes: true,
          },
          {
            version: '1.5.0',
            release_date: '2024-01-15',
            changes: [
              'Initial marketplace release',
              'Core overview widgets',
              'Basic enrollment tracking'
            ],
            breaking_changes: false,
          },
        ],
        reviews: [
          {
            id: '1',
            user_name: 'Dr. Sarah Chen',
            user_avatar: '/api/placeholder/32/32',
            rating: 5,
            review_text: 'Excellent template! Saved us weeks of development time. The enrollment metrics are exactly what we needed for our oncology study.',
            created_at: '2024-03-10T14:20:00Z',
            is_verified: true,
          },
          {
            id: '2',
            user_name: 'Mike Rodriguez',
            user_avatar: '/api/placeholder/32/32',
            rating: 4,
            review_text: 'Very good template with comprehensive metrics. Would love to see more customization options for the safety widgets.',
            created_at: '2024-03-05T09:15:00Z',
            is_verified: false,
          },
          {
            id: '3',
            user_name: 'Clinical Data Manager',
            rating: 5,
            review_text: 'Perfect for our Phase III study. The data quality indicators helped us catch several issues early.',
            created_at: '2024-02-28T16:45:00Z',
            is_verified: true,
          },
        ],
        related_templates: [
          {
            id: '2',
            name: 'Safety Monitoring Dashboard',
            category: 'safety',
            rating: 4.6,
            downloads: 756,
          },
          {
            id: '3',
            name: 'Efficacy Analysis Suite',
            category: 'efficacy',
            rating: 4.9,
            downloads: 1580,
          },
        ],
      };

      setTemplate(mockTemplate);
    } catch (error) {
      console.error('Error fetching template details:', error);
      toast({
        title: 'Error',
        description: 'Failed to load template details',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!template) return;

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

  const renderStars = (rating: number) => {
    return [...Array(5)].map((_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < Math.floor(rating) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
      />
    ));
  };

  const getRatingDistribution = () => {
    if (!template?.reviews) return [];
    
    const distribution = [0, 0, 0, 0, 0];
    template.reviews.forEach(review => {
      distribution[review.rating - 1]++;
    });
    
    return distribution.map((count, index) => ({
      stars: index + 1,
      count,
      percentage: template.reviews.length > 0 ? (count / template.reviews.length) * 100 : 0
    })).reverse();
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading template details...</div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Template Not Found</h1>
          <Button onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header *//*}
      <div className="mb-8">
        <Button 
          variant="ghost" 
          onClick={() => router.back()}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Marketplace
        </Button>

        <div className="flex flex-col lg:flex-row gap-8">
          // Template Info
          <div className="flex-1">
            <div className="flex items-start gap-4 mb-6">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h1 className="text-3xl font-bold">{template.name}</h1>
                  {template.is_verified && (
                    <Badge className="bg-blue-100 text-blue-700">
                      <Shield className="w-3 h-3 mr-1" />
                      Verified
                    </Badge>
                  )}
                </div>
                
                <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                  <div className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    {template.creator_name}
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Updated {new Date(template.updated_at).toLocaleDateString()}
                  </div>
                  <Badge variant="outline" className="capitalize">
                    {template.category}
                  </Badge>
                </div>

                <p className="text-gray-700 mb-4">{template.description}</p>

                <div className="flex items-center gap-6 mb-4">
                  <div className="flex items-center gap-2">
                    {renderStars(template.average_rating)}
                    <span className="font-medium">{template.average_rating.toFixed(1)}</span>
                    <span className="text-gray-600">({template.total_ratings} reviews)</span>
                  </div>
                  <div className="flex items-center gap-1 text-gray-600">
                    <Download className="w-4 h-4" />
                    {template.download_count.toLocaleString()} downloads
                  </div>
                  <span className="text-gray-600">v{template.version_string}</span>
                </div>

                <div className="flex flex-wrap gap-2 mb-6">
                  {template.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      <Tag className="w-3 h-3 mr-1" />
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            // Action Buttons
            <div className="flex gap-3 mb-8">
              <Button onClick={handleDownload} size="lg" className="flex-1 lg:flex-none">
                <Download className="w-4 h-4 mr-2" />
                Download Template
              </Button>
              {template.documentation_url && (
                <Button variant="outline" size="lg" asChild>
                  <a href={template.documentation_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Documentation
                  </a>
                </Button>
              )}
              {template.source_url && (
                <Button variant="outline" size="lg" asChild>
                  <a href={template.source_url} target="_blank" rel="noopener noreferrer">
                    <Github className="w-4 h-4 mr-2" />
                    Source
                  </a>
                </Button>
              )}
            </div>
          </div>

          // Screenshots
          <div className="lg:w-96">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Preview</CardTitle>
              </CardHeader>
              <CardContent>
                {template.screenshot_urls.length > 0 && (
                  <div className="space-y-4">
                    <div className="relative">
                      <img
                        src={template.screenshot_urls[activeImageIndex]}
                        alt={`Preview ${activeImageIndex + 1}`}
                        className="w-full h-48 object-cover rounded-lg border"
                      />
                    </div>
                    {template.screenshot_urls.length > 1 && (
                      <div className="flex gap-2 overflow-x-auto">
                        {template.screenshot_urls.map((url, index) => (
                          <button
                            key={index}
                            onClick={() => setActiveImageIndex(index)}
                            className={`flex-shrink-0 w-16 h-12 rounded border-2 overflow-hidden ${
                              index === activeImageIndex ? 'border-blue-500' : 'border-gray-200'
                            }`}
                          >
                            <img
                              src={url}
                              alt={`Thumbnail ${index + 1}`}
                              className="w-full h-full object-cover"
                            />
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      // Tabs
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="reviews">Reviews</TabsTrigger>
          <TabsTrigger value="versions">Version History</TabsTrigger>
          <TabsTrigger value="related">Related Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            // Requirements
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Requirements</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {template.requirements.map((req) => (
                    <li key={req} className="flex items-center gap-2 text-sm">
                      <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0" />
                      {req}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            // Compatibility
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Compatibility</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {template.compatibility.map((comp) => (
                    <li key={comp} className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0" />
                      {comp}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            // Template Info
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Template Info</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">License:</span>
                  <span>{template.license}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Template ID:</span>
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded">{template.code}</code>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Created:</span>
                  <span>{new Date(template.created_at).toLocaleDateString()}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="reviews" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            // Rating Summary
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Rating Breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-3xl font-bold">{template.average_rating.toFixed(1)}</div>
                  <div className="flex items-center justify-center gap-1 mb-1">
                    {renderStars(template.average_rating)}
                  </div>
                  <div className="text-sm text-gray-600">
                    {template.total_ratings} review{template.total_ratings !== 1 ? 's' : ''}
                  </div>
                </div>
                
                <Separator />
                
                <div className="space-y-2">
                  {getRatingDistribution().map((rating) => (
                    <div key={rating.stars} className="flex items-center gap-2 text-sm">
                      <span className="w-8">{rating.stars}★</span>
                      <Progress value={rating.percentage} className="flex-1" />
                      <span className="w-8 text-right">{rating.count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            // Reviews
            <div className="lg:col-span-2 space-y-4">
              {template.reviews.map((review) => (
                <Card key={review.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <Avatar>
                        {review.user_avatar ? (
                          <img src={review.user_avatar} alt={review.user_name} />
                        ) : (
                          <AvatarFallback>
                            {review.user_name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        )}
                      </Avatar>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium">{review.user_name}</span>
                          {review.is_verified && (
                            <Badge variant="secondary" className="text-xs">
                              Verified
                            </Badge>
                          )}
                          <span className="text-sm text-gray-500">
                            {new Date(review.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-2 mb-3">
                          {renderStars(review.rating)}
                        </div>
                        
                        <p className="text-gray-700">{review.review_text}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="versions" className="space-y-4">
          {template.version_history.map((version) => (
            <Card key={version.version}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Version {version.version}</CardTitle>
                  <div className="flex items-center gap-2">
                    {version.breaking_changes && (
                      <Badge variant="destructive">Breaking Changes</Badge>
                    )}
                    <span className="text-sm text-gray-500">
                      {new Date(version.release_date).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {version.changes.map((change, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 flex-shrink-0" />
                      {change}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="related" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {template.related_templates.map((related) => (
              <Card key={related.id} className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="p-4">
                  <h3 className="font-medium mb-2">{related.name}</h3>
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <Badge variant="outline" className="capitalize">
                      {related.category}
                    </Badge>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                        {related.rating.toFixed(1)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Download className="w-3 h-3" />
                        {related.downloads}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
*/