// ABOUTME: Admin page for listing and managing menu templates
// ABOUTME: Provides CRUD operations for menu configurations used by studies

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/use-toast'
import { Breadcrumbs, BreadcrumbItem } from '@/components/ui/breadcrumbs'
import { Loader2, MoreHorizontal, Plus, Search, Menu, Eye, Edit, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import { menusApi } from '@/lib/api/menus'

interface MenuItem {
  id: string
  label: string
  icon?: string
  path?: string
  children?: MenuItem[]
  permissions?: string[]
}

interface MenuTemplate {
  id: string
  name: string
  description?: string
  items: MenuItem[]
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
  studies_count: number
}

export default function MenuTemplatesPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [templates, setTemplates] = useState<MenuTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [templateToDelete, setTemplateToDelete] = useState<MenuTemplate | null>(null)

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      const response = await menusApi.getMenuTemplates()
      setTemplates(response.items || [])
    } catch (error) {
      console.error('Error fetching menu templates:', error)
      toast({
        title: 'Error',
        description: 'Failed to load menu templates',
        variant: 'destructive',
      })
      setTemplates([])
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!templateToDelete) return

    try {
      await menusApi.deleteMenuTemplate(templateToDelete.id)

      toast({
        title: 'Success',
        description: 'Menu template deleted successfully',
      })

      fetchTemplates()
    } catch (error) {
      console.error('Error deleting menu template:', error)
      toast({
        title: 'Error',
        description: 'Failed to delete menu template',
        variant: 'destructive',
      })
    } finally {
      setDeleteDialogOpen(false)
      setTemplateToDelete(null)
    }
  }

  const filteredTemplates = (templates || []).filter(template =>
    template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const countMenuItems = (items: MenuItem[]): number => {
    return items.reduce((count, item) => {
      return count + 1 + (item.children ? countMenuItems(item.children) : 0)
    }, 0)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const breadcrumbItems: BreadcrumbItem[] = [
    { label: 'Menu Templates', icon: <Menu className="h-4 w-4" /> }
  ]

  return (
    <div className="space-y-6">
      <Breadcrumbs items={breadcrumbItems} />
      
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Menu Templates</h1>
          <p className="text-muted-foreground">
            Create and manage navigation menu templates for studies
          </p>
        </div>
        <Button asChild>
          <Link href="/admin/menus/new">
            <Plus className="mr-2 h-4 w-4" />
            New Template
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Templates</CardTitle>
              <CardDescription>
                {(templates || []).length} menu template{(templates || []).length !== 1 ? 's' : ''} available
              </CardDescription>
            </div>
            <div className="relative w-64">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search templates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredTemplates.length === 0 ? (
            <div className="text-center py-12">
              <Menu className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold">No menu templates found</h3>
              <p className="text-muted-foreground mt-2">
                {searchTerm ? 'Try a different search term' : 'Create your first menu template to get started'}
              </p>
              {!searchTerm && (
                <Button asChild className="mt-4">
                  <Link href="/admin/menus/new">
                    <Plus className="mr-2 h-4 w-4" />
                    Create Template
                  </Link>
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Menu Items</TableHead>
                  <TableHead>Studies</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTemplates.map((template) => (
                  <TableRow key={template.id}>
                    <TableCell className="font-medium">{template.name}</TableCell>
                    <TableCell>
                      <span className="text-muted-foreground text-sm">
                        {template.description || 'No description'}
                      </span>
                    </TableCell>
                    <TableCell>{countMenuItems(template.items)}</TableCell>
                    <TableCell>{template.studies_count}</TableCell>
                    <TableCell>
                      <Badge variant={template.is_active ? 'default' : 'secondary'}>
                        {template.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {format(new Date(template.updated_at), 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                            <span className="sr-only">Open menu</span>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem asChild>
                            <Link href={`/admin/menus/${template.id}/preview`}>
                              <Eye className="mr-2 h-4 w-4" />
                              Preview
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link href={`/admin/menus/${template.id}/edit`}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive"
                            disabled={template.studies_count > 0}
                            onClick={() => {
                              setTemplateToDelete(template)
                              setDeleteDialogOpen(true)
                            }}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the menu template "{templateToDelete?.name}".
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}