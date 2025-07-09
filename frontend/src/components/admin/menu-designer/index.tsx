// ABOUTME: Interactive menu designer component with drag-and-drop functionality
// ABOUTME: Allows creation of hierarchical menu structures with role-based visibility

'use client'

import { useState, useEffect } from 'react'
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from '@dnd-kit/core'
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { SortableItem } from './sortable-item'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Plus, Save, Eye, Trash2, GripVertical, ChevronRight, ChevronDown, Folder, FileText, BarChart2, Settings, Users, Database, Activity, Shield, Menu, Info } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'

export interface MenuItem {
  id: string
  label: string
  icon?: string
  path?: string
  children?: MenuItem[]
  permissions?: string[]
  isExpanded?: boolean
  type?: string
  order?: number
  dashboard_code?: string
  url?: string
}

interface MenuDesignerProps {
  initialItems?: MenuItem[]
  onSave?: (items: MenuItem[]) => void
  onPreview?: (items: MenuItem[]) => void
  isLoading?: boolean
}

const AVAILABLE_ICONS = [
  { value: 'folder', label: 'Folder', icon: Folder },
  { value: 'file-text', label: 'Document', icon: FileText },
  { value: 'bar-chart-2', label: 'Chart', icon: BarChart2 },
  { value: 'settings', label: 'Settings', icon: Settings },
  { value: 'users', label: 'Users', icon: Users },
  { value: 'database', label: 'Database', icon: Database },
  { value: 'activity', label: 'Activity', icon: Activity },
  { value: 'shield', label: 'Security', icon: Shield },
  { value: 'menu', label: 'Menu', icon: Menu },
]

// Use actual user roles for menu visibility
const AVAILABLE_ROLES = [
  'system_admin',
  'org_admin',
  'study_manager',
  'data_analyst',
  'viewer',
  'auditor',
]

export function MenuDesigner({ initialItems = [], onSave, onPreview, isLoading }: MenuDesignerProps) {
  const [items, setItems] = useState<MenuItem[]>(initialItems)
  const [selectedItem, setSelectedItem] = useState<MenuItem | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  useEffect(() => {
    setItems(initialItems)
  }, [initialItems])

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (active.id !== over?.id) {
      setItems((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id)
        const newIndex = items.findIndex((item) => item.id === over?.id)
        return arrayMove(items, oldIndex, newIndex)
      })
    }
  }

  const generateId = () => {
    return `menu-item-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  const addMenuItem = (parentId?: string) => {
    const newItem: MenuItem = {
      id: generateId(),
      label: 'New Menu Item',
      icon: 'folder',
      path: '',
      permissions: [...AVAILABLE_ROLES],  // Default to all roles
      children: [],
      type: 'dashboard' as any,
      order: items.length + 1
    }

    if (parentId) {
      setItems((prevItems) => {
        const updateItems = (items: MenuItem[]): MenuItem[] => {
          return items.map((item) => {
            if (item.id === parentId) {
              return {
                ...item,
                children: [...(item.children || []), newItem],
                isExpanded: true,
              }
            }
            if (item.children) {
              return {
                ...item,
                children: updateItems(item.children),
              }
            }
            return item
          })
        }
        return updateItems(prevItems)
      })
    } else {
      setItems([...items, newItem])
    }

    setEditingItem(newItem)
    setEditDialogOpen(true)
  }

  const updateMenuItem = (updatedItem: MenuItem) => {
    setItems((prevItems) => {
      const updateItems = (items: MenuItem[]): MenuItem[] => {
        return items.map((item) => {
          if (item.id === updatedItem.id) {
            return updatedItem
          }
          if (item.children) {
            return {
              ...item,
              children: updateItems(item.children),
            }
          }
          return item
        })
      }
      return updateItems(prevItems)
    })
  }

  const deleteMenuItem = (itemId: string) => {
    setItems((prevItems) => {
      const deleteFromItems = (items: MenuItem[]): MenuItem[] => {
        return items
          .filter((item) => item.id !== itemId)
          .map((item) => {
            if (item.children) {
              return {
                ...item,
                children: deleteFromItems(item.children),
              }
            }
            return item
          })
      }
      return deleteFromItems(prevItems)
    })
  }

  const toggleItemExpanded = (itemId: string) => {
    setItems((prevItems) => {
      const toggleExpanded = (items: MenuItem[]): MenuItem[] => {
        return items.map((item) => {
          if (item.id === itemId) {
            return {
              ...item,
              isExpanded: !item.isExpanded,
            }
          }
          if (item.children) {
            return {
              ...item,
              children: toggleExpanded(item.children),
            }
          }
          return item
        })
      }
      return toggleExpanded(prevItems)
    })
  }

  const renderMenuItem = (item: MenuItem, depth: number = 0) => {
    const IconComponent = AVAILABLE_ICONS.find((i) => i.value === item.icon)?.icon || Folder
    const hasChildren = item.children && item.children.length > 0

    return (
      <div key={item.id} className="w-full">
        <div
          className={`flex items-center gap-2 p-2 rounded-md hover:bg-accent cursor-pointer ${
            selectedItem?.id === item.id ? 'bg-accent' : ''
          }`}
          style={{ paddingLeft: `${depth * 24 + 8}px` }}
          onClick={() => setSelectedItem(item)}
        >
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={(e) => {
              e.stopPropagation()
              if (hasChildren) {
                toggleItemExpanded(item.id)
              }
            }}
          >
            {hasChildren ? (
              item.isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )
            ) : (
              <div className="w-4" />
            )}
          </Button>
          <GripVertical className="h-4 w-4 text-muted-foreground" />
          <IconComponent className="h-4 w-4" />
          <span className="flex-1 text-sm">{item.label}</span>
          {item.path && (
            <Badge variant="secondary" className="text-xs">
              {item.path}
            </Badge>
          )}
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={(e) => {
                e.stopPropagation()
                setEditingItem(item)
                setEditDialogOpen(true)
              }}
            >
              <Settings className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={(e) => {
                e.stopPropagation()
                addMenuItem(item.id)
              }}
            >
              <Plus className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={(e) => {
                e.stopPropagation()
                deleteMenuItem(item.id)
              }}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </div>
        {hasChildren && item.isExpanded && item.children && (
          <div>
            {item.children.map((child) => renderMenuItem(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex gap-2">
          <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <strong>How it works:</strong> Create reusable menu structures here (e.g., Overview, Safety, Laboratory). 
            These templates define navigation patterns that can be used across multiple studies. 
            During study setup, you'll select a menu template and assign dashboard templates to each menu item.
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
          <CardHeader>
            <CardTitle>Menu Structure</CardTitle>
            <CardDescription>
              Design the sidebar navigation for study dashboards. Each menu item will be linked to a dashboard template during study setup.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button
                onClick={() => addMenuItem()}
                variant="outline"
                className="w-full"
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Menu Item
              </Button>
              <Separator />
              <ScrollArea className="h-[500px] pr-4">
                {items.length === 0 ? (
                  <div className="text-center py-12">
                    <Menu className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">
                      No menu items yet. Click "Add Menu Item" to get started.
                    </p>
                  </div>
                ) : (
                  <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                  >
                    <SortableContext
                      items={items.map((item) => item.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      <div className="space-y-1">
                        {items.map((item) => renderMenuItem(item))}
                      </div>
                    </SortableContext>
                  </DndContext>
                )}
              </ScrollArea>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Selected Item</CardTitle>
            <CardDescription>
              {selectedItem ? selectedItem.label : 'Select a menu item to view details'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedItem ? (
              <div className="space-y-4">
                <div>
                  <Label>Label</Label>
                  <p className="text-sm text-muted-foreground">{selectedItem.label}</p>
                </div>
                <div>
                  <Label>Path</Label>
                  <p className="text-sm text-muted-foreground">
                    {selectedItem.path || 'No path specified'}
                  </p>
                </div>
                <div>
                  <Label>Icon</Label>
                  <p className="text-sm text-muted-foreground">{selectedItem.icon || 'folder'}</p>
                </div>
                <div>
                  <Label>Visible to Roles</Label>
                  {selectedItem.permissions && selectedItem.permissions.length > 0 ? (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedItem.permissions.map((role) => (
                        <Badge key={role} variant="secondary" className="text-xs">
                          {role.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No roles selected (invalid)</p>
                  )}
                </div>
                <Button
                  onClick={() => {
                    setEditingItem(selectedItem)
                    setEditDialogOpen(true)
                  }}
                  className="w-full"
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Edit Item
                </Button>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                No item selected
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {onPreview && (
              <Button
                onClick={() => onPreview(items)}
                variant="outline"
                className="w-full"
              >
                <Eye className="mr-2 h-4 w-4" />
                Preview Menu
              </Button>
            )}
            {onSave && (
              <Button
                onClick={() => onSave(items)}
                className="w-full"
                disabled={isLoading}
              >
                <Save className="mr-2 h-4 w-4" />
                Save Template
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>Edit Menu Item</DialogTitle>
            <DialogDescription>
              Configure the menu item properties
            </DialogDescription>
          </DialogHeader>
          {editingItem && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="label">Label</Label>
                <Input
                  id="label"
                  value={editingItem.label}
                  onChange={(e) =>
                    setEditingItem({ ...editingItem, label: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="path">Path (Optional)</Label>
                <p className="text-xs text-muted-foreground mb-1">
                  Leave empty - dashboards will be assigned during study setup
                </p>
                <Input
                  id="path"
                  placeholder="Auto-generated during study setup"
                  value={editingItem.path || ''}
                  onChange={(e) =>
                    setEditingItem({ ...editingItem, path: e.target.value })
                  }
                  disabled
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Menu Type</Label>
                <Select
                  value={editingItem.type || 'dashboard'}
                  onValueChange={(value) =>
                    setEditingItem({ ...editingItem, type: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dashboard">Dashboard Page</SelectItem>
                    <SelectItem value="group">Group (Has Submenus)</SelectItem>
                    <SelectItem value="divider">Divider</SelectItem>
                    <SelectItem value="external">External Link</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {/* Show URL field for external links */}
              {editingItem.type === 'external' && (
                <div className="space-y-2">
                  <Label htmlFor="url">External URL</Label>
                  <Input
                    id="url"
                    placeholder="https://example.com"
                    value={editingItem.url || ''}
                    onChange={(e) =>
                      setEditingItem({ ...editingItem, url: e.target.value })
                    }
                  />
                </div>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="icon">Icon</Label>
                <Select
                  value={editingItem.icon || 'folder'}
                  onValueChange={(value) =>
                    setEditingItem({ ...editingItem, icon: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {AVAILABLE_ICONS.map((icon) => {
                      const IconComponent = icon.icon
                      return (
                        <SelectItem key={icon.value} value={icon.value}>
                          <div className="flex items-center gap-2">
                            <IconComponent className="h-4 w-4" />
                            <span>{icon.label}</span>
                          </div>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Visible to Roles</Label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const allSelected = editingItem.permissions?.length === AVAILABLE_ROLES.length
                      setEditingItem({
                        ...editingItem,
                        permissions: allSelected ? [] : [...AVAILABLE_ROLES]
                      })
                    }}
                  >
                    {editingItem.permissions?.length === AVAILABLE_ROLES.length ? 'Uncheck All' : 'Check All'}
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground mb-2">
                  Select which user roles can see this menu item. At least one role must be selected.
                </p>
                <div className="space-y-2">
                  {AVAILABLE_ROLES.map((role) => (
                    <div key={role} className="flex items-center space-x-2">
                      <Checkbox
                        id={role}
                        checked={editingItem.permissions?.includes(role)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setEditingItem({
                              ...editingItem,
                              permissions: [...(editingItem.permissions || []), role],
                            })
                          } else {
                            setEditingItem({
                              ...editingItem,
                              permissions: editingItem.permissions?.filter(
                                (p) => p !== role
                              ),
                            })
                          }
                        }}
                      />
                      <Label
                        htmlFor={role}
                        className="text-sm font-normal cursor-pointer"
                      >
                        {role.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (editingItem) {
                  // Validate at least one role is selected
                  if (!editingItem.permissions || editingItem.permissions.length === 0) {
                    alert('Please select at least one role for menu visibility')
                    return
                  }
                  updateMenuItem(editingItem)
                  setEditDialogOpen(false)
                }
              }}
            >
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
    </div>
  )
}