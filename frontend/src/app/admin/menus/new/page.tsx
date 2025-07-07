// ABOUTME: Page for creating new menu templates using the menu designer
// ABOUTME: Provides form inputs for template metadata and menu structure design

'use client'

import { useState } from 'react'
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
import { ArrowLeft, Save } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { menusApi } from '@/lib/api/menus'

export default function NewMenuTemplatePage() {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewItems, setPreviewItems] = useState<MenuItem[]>([])
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_active: true,
  })

  const [menuItems, setMenuItems] = useState<MenuItem[]>([])

  const handleSave = async (items: MenuItem[]) => {
    if (!formData.name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Please provide a name for the menu template',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      await menusApi.createMenuTemplate({
        ...formData,
        items: items,
      })

      toast({
        title: 'Success',
        description: 'Menu template created successfully',
      })

      router.push('/admin/menus')
    } catch (error) {
      console.error('Error creating menu template:', error)
      toast({
        title: 'Error',
        description: 'Failed to create menu template',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
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

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/admin/menus">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Create Menu Template</h1>
          <p className="text-muted-foreground">
            Design a new navigation menu template for studies
          </p>
        </div>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Template Details</CardTitle>
            <CardDescription>
              This template will define the sidebar navigation for study dashboards
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
          initialItems={menuItems}
          onSave={handleSave}
          onPreview={handlePreview}
          isLoading={loading}
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