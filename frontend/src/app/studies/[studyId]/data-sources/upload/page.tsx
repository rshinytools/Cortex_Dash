// ABOUTME: Data upload management page using the new parquet-based system
// ABOUTME: Displays upload history and allows new uploads with conversion tracking

'use client';

import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DataSourceManager } from '@/components/data-sources/DataSourceManager';

export default function DataUploadPage() {
  const router = useRouter();
  const params = useParams();
  const studyId = params.studyId as string;

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push(`/studies/${studyId}/data-sources`)}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Data Sources
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Data Upload Management</h1>
          <p className="text-muted-foreground mt-1">
            Upload and manage clinical data files for processing
          </p>
        </div>
      </div>

      <DataSourceManager studyId={studyId} />
    </div>
  );
}