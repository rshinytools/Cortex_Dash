// ABOUTME: Page for creating new widget definitions
// ABOUTME: Provides form interface for defining widget properties and configuration schema

'use client'

import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useCreateWidget } from '@/hooks/use-widgets'
import { WidgetForm } from '@/components/admin/widget-form'
import { CreateWidgetRequest } from '@/lib/api/widgets'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'

export default function NewWidgetPage() {
  const router = useRouter()
  const createWidget = useCreateWidget()

  const handleSubmit = async (data: CreateWidgetRequest) => {
    try {
      const widget = await createWidget.mutateAsync(data)
      router.push('/admin/widgets')
    } catch (error) {
      // Error is handled by the mutation hook
    }
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
          <h2 className="text-3xl font-bold tracking-tight">Create Widget</h2>
          <p className="text-muted-foreground">
            Define a new reusable widget template
          </p>
        </div>
      </div>

      <WidgetForm
        onSubmit={handleSubmit as any}
        isLoading={createWidget.isPending}
      />
    </div>
  )
}