// ABOUTME: Component to show that template marketplace is disabled
// ABOUTME: Redirects users back to admin page with a message

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function MarketplaceDisabled() {
  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    toast({
      title: 'Feature Disabled',
      description: 'The template marketplace is not available in this version.',
      variant: 'default',
    });
    
    // Redirect after 3 seconds
    const timer = setTimeout(() => {
      router.push('/admin');
    }, 3000);

    return () => clearTimeout(timer);
  }, [router, toast]);

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <AlertCircle className="h-6 w-6" />
          </div>
          <CardTitle>Template Marketplace Disabled</CardTitle>
          <CardDescription>
            This feature is not available. Redirecting you back to the admin panel...
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <Button 
            onClick={() => router.push('/admin')}
            variant="default"
          >
            Return to Admin Panel
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}