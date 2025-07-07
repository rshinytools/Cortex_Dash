// ABOUTME: Page for editing existing menu templates using the menu designer
// ABOUTME: Loads template data and allows modification of menu structure and metadata

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { MenuDesigner, MenuItem } from '@/components/admin/menu-designer'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { ArrowLeft, Save, Loader2, Menu } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { menusApi } from '@/lib/api/menus'

interface MenuTemplate {
  id: string
  name: string
  description?: string
  items: MenuItem[]
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
}

export default function EditMenuTemplatePage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewItems, setPreviewItems] = useState<MenuItem[]>([])
  
  const [template, setTemplate] = useState<MenuTemplate | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_active: true,
  })

  useEffect(() => {
    fetchTemplate()
  }, [params.id])

  const fetchTemplate = async () => {
    try {
      const data = await menusApi.getMenuTemplate(params.id)
      setTemplate(data)
      setFormData({
        name: data.name,
        description: data.description || '',
        is_active: data.is_active,
      })
    } catch (error) {
      console.error('Error fetching menu template:', error)
      toast({
        title: 'Error',
        description: 'Failed to load menu template',
        variant: 'destructive',
      })
      router.push('/admin/menus')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (items: MenuItem[]) => {
    if (!formData.name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Please provide a name for the menu template',
        variant: 'destructive',
      })
      return
    }

    setSaving(true)
    try {
      await menusApi.updateMenuTemplate(params.id, {
        ...formData,
        items: items,
      })

      toast({
        title: 'Success',
        description: 'Menu template updated successfully',
      })

      router.push('/admin/menus')
    } catch (error) {
      console.error('Error updating menu template:', error)
      toast({
        title: 'Error',
        description: 'Failed to update menu template',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const handlePreview = (items: MenuItem[]) => {
    setPreviewItems(items)
    setPreviewOpen(true)
  }

  const renderPreviewItem = (item: MenuItem, depth: number = 0) => {
    return (
      <div key={item.id} style={{ paddingLeft: `${depth * 20}px` }} className="py-1">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">•</span>
          <span>{item.label}</span>
          {item.path && (
            <span className="text-xs text-muted-foreground">({item.path})</span>
          )}
        </div>
        {item.children && item.children.map((child) => renderPreviewItem(child, depth + 1))}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!template) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-semibold">Menu template not found</h3>
        <Button asChild className="mt-4">
          <Link href="/admin/menus">Back to Menu Templates</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
        <Button
          variant="link"
          className="p-0 h-auto font-normal"
          onClick={() => router.push('/admin')}
        >
          Admin
        </Button>
        <span>/</span>
        <Button
          variant="link"
          className="p-0 h-auto font-normal"
          onClick={() => router.push('/admin/menus')}
        >
          Menu Templates
        </Button>
        <span>/</span>
        <span className="text-foreground">{template.name}</span>
      </div>

      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/admin/menus')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Menu Templates
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">Edit Menu Template</h1>
          <p className="text-muted-foreground">
            Modify the navigation menu template
          </p>
        </div>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Template Details</CardTitle>
            <CardDescription>
              Basic information about the menu template
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Template Name</Label>
              <Input
                id="name"
                placeholder="e.g., Clinical Trial Navigation"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe the purpose of this menu template..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
              <Label htmlFor="is_active" className="cursor-pointer">
                Active (Available for use in studies)
              </Label>
            </div>
          </CardContent>
        </Card>

        <MenuDesigner
          initialItems={template.items}
          onSave={handleSave}
          onPreview={handlePreview}
          isLoading={saving}
        />
      </div>

      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>Menu Preview</DialogTitle>
            <DialogDescription>
              This is how the menu will appear in the navigation sidebar
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[400px] w-full rounded-md border p-4">
            {previewItems.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No menu items to preview
              </p>
            ) : (
              <div className="space-y-1">
                {previewItems.map((item) => renderPreviewItem(item))}
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  )
}