// ABOUTME: Page for editing existing widget definitions
// ABOUTME: Loads widget data and provides form interface for updates with version management

'use client'

import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useWidget, useUpdateWidget } from '@/hooks/use-widgets'
import { WidgetForm } from '@/components/admin/widget-form'
import { UpdateWidgetRequest } from '@/lib/api/widgets'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ArrowLeft, AlertCircle } from 'lucide-react'

interface EditWidgetPageProps {
  params: {
    id: string
  }
}

export default function EditWidgetPage({ params }: EditWidgetPageProps) {
  const router = useRouter()
  const { id } = params

  // Fetch widget data
  const { data: widget, isLoading, error } = useWidget(id)
  const updateWidget = useUpdateWidget(id)

  const handleSubmit = async (data: UpdateWidgetRequest) => {
    try {
      await updateWidget.mutateAsync(data)
      router.push('/admin/widgets')
    } catch (error) {
      // Error is handled by the mutation hook
    }
  }

  if (isLoading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-96" />
          </div>
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !widget) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center gap-4">
          <Link href="/admin/widgets">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex-1">
            <h2 className="text-3xl font-bold tracking-tight">Edit Widget</h2>
          </div>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error ? 'Failed to load widget. Please try again.' : 'Widget not found.'}
          </AlertDescription>
        </Alert>
        <div className="flex justify-center">
          <Link href="/admin/widgets">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Widgets
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center gap-4">
        <Link href="/admin/widgets">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h2 className="text-3xl font-bold tracking-tight">Edit Widget</h2>
          <p className="text-muted-foreground">
            Update the widget definition for "{widget.name}"
          </p>
        </div>
      </div>

      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Modifying the configuration schema will increment the widget version.
          Existing instances will continue to use the previous version until updated.
        </AlertDescription>
      </Alert>

      <WidgetForm
        widget={widget}
        onSubmit={handleSubmit}
        isLoading={updateWidget.isPending}
      />
    </div>
  )
}