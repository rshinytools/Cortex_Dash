// ABOUTME: Admin page for managing widget definitions
// ABOUTME: Lists all widgets with filtering, search, and CRUD operations

'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useWidgets, useDeleteWidget, useToggleWidgetStatus } from '@/hooks/use-widgets'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Plus, 
  Search, 
  MoreHorizontal, 
  Edit, 
  Trash2, 
  Copy,
  Power,
  PowerOff,
  Filter,
  Code2,
  Layers,
  Grid3X3,
  ArrowLeft
} from 'lucide-react'
import { WidgetCategory, WidgetType } from '@/types/widget'

// Component for toggle status menu item to handle hook properly
function ToggleStatusMenuItem({ widgetId, isActive }: { widgetId: string; isActive: boolean }) {
  const toggleStatus = useToggleWidgetStatus(widgetId)
  
  return (
    <DropdownMenuItem
      onClick={() => toggleStatus.mutate(!isActive)}
    >
      {isActive ? (
        <>
          <PowerOff className="mr-2 h-4 w-4" />
          Deactivate
        </>
      ) : (
        <>
          <Power className="mr-2 h-4 w-4" />
          Activate
        </>
      )}
    </DropdownMenuItem>
  )
}

export default function WidgetsPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [deleteWidgetId, setDeleteWidgetId] = useState<string | null>(null)

  // Query parameters
  const queryParams = useMemo(() => {
    const params: any = {
      page: 1,
      size: 20,
    }
    
    if (search) {
      params.search = search
    }
    
    if (categoryFilter !== 'all') {
      params.category = categoryFilter
    }
    
    if (typeFilter !== 'all') {
      params.type = typeFilter
    }
    
    return params
  }, [search, categoryFilter, typeFilter])

  // Fetch widgets
  const { data: widgetsData, isLoading } = useWidgets(queryParams)
  const deleteWidget = useDeleteWidget()

  // Handle delete
  const handleDelete = async () => {
    if (deleteWidgetId) {
      await deleteWidget.mutateAsync(deleteWidgetId)
      setDeleteWidgetId(null)
    }
  }

  // Category badge color
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      [WidgetCategory.METRICS]: 'default',
      [WidgetCategory.CHARTS]: 'secondary',
      [WidgetCategory.TABLES]: 'outline',
      [WidgetCategory.MAPS]: 'destructive',
      [WidgetCategory.SPECIALIZED]: 'default',
    }
    return colors[category] || 'default'
  }

  // Type icon
  const getTypeIcon = (type: string) => {
    switch (type) {
      case WidgetType.METRIC:
        return <Grid3X3 className="h-4 w-4" />
      case WidgetType.CHART:
        return <Layers className="h-4 w-4" />
      case WidgetType.TABLE:
        return <Code2 className="h-4 w-4" />
      default:
        return <Code2 className="h-4 w-4" />
    }
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
        <span className="text-foreground">Widget Library</span>
      </div>

      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/admin')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Admin
        </Button>
        <div className="flex-1">
          <h2 className="text-3xl font-bold tracking-tight">Widget Library</h2>
          <p className="text-muted-foreground">
            Manage reusable widget templates for dashboards
          </p>
        </div>
        <Button onClick={() => router.push('/admin/widgets/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Create Widget
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Search and filter widgets</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search widgets..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8"
              />
            </div>

            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All categories</SelectItem>
                {Object.entries(WidgetCategory).map(([key, value]) => (
                  <SelectItem key={value} value={value}>
                    {key.charAt(0) + key.slice(1).toLowerCase().replace('_', ' ')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types</SelectItem>
                {Object.entries(WidgetType).map(([key, value]) => (
                  <SelectItem key={value} value={value}>
                    {key.charAt(0) + key.slice(1).toLowerCase().replace('_', ' ')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Widgets</CardTitle>
          <CardDescription>
            {widgetsData ? `${widgetsData.total} widgets available` : 'Loading widgets...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : widgetsData && widgetsData.items.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {widgetsData.items.map((widget) => (
                  <TableRow key={widget.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{widget.name}</div>
                        {widget.description && (
                          <div className="text-sm text-muted-foreground line-clamp-1">
                            {widget.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getCategoryColor(widget.category) as any}>
                        {widget.category ? widget.category.replace('_', ' ') : 'Unknown'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getTypeIcon(widget.type || '')}
                        <span className="capitalize">{widget.type ? widget.type.replace('_', ' ') : 'Unknown'}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{widget.version}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={(widget.is_active ?? widget.isActive) ? 'default' : 'secondary'}>
                        {(widget.is_active ?? widget.isActive) ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {widget.updated_at || widget.updatedAt ? 
                        new Date(widget.updated_at || widget.updatedAt || '').toLocaleDateString() : 
                        'N/A'}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <span className="sr-only">Open menu</span>
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem
                            onClick={() => router.push(`/admin/widgets/${widget.id}/edit`)}
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => {
                              // TODO: Implement duplicate functionality
                              console.log('Duplicate', widget.id)
                            }}
                          >
                            <Copy className="mr-2 h-4 w-4" />
                            Duplicate
                          </DropdownMenuItem>
                          <ToggleStatusMenuItem
                            widgetId={widget.id}
                            isActive={(widget.is_active ?? widget.isActive) || false}
                          />
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteWidgetId(widget.id)}
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
          ) : (
            <div className="text-center py-12">
              <div className="text-muted-foreground mb-4">
                {search || categoryFilter !== 'all' || typeFilter !== 'all'
                  ? 'No widgets found matching your filters'
                  : 'No widgets have been created yet'}
              </div>
              {(!search && categoryFilter === 'all' && typeFilter === 'all') && (
                <Button onClick={() => router.push('/admin/widgets/new')}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create your first widget
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={!!deleteWidgetId} onOpenChange={() => setDeleteWidgetId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the widget
              definition and remove it from all dashboards.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}