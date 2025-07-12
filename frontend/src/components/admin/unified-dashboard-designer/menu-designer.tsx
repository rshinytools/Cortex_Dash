// ABOUTME: Menu designer component for creating and editing menu structures
// ABOUTME: Provides tree view with drag-and-drop functionality for menu items

"use client";

import { useState } from "react";
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
  DragOverEvent,
  UniqueIdentifier,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import {
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { 
  ChevronRight, ChevronDown, Grip, Edit2, Trash2, Plus, Layout, 
  FolderOpen, Minus, ExternalLink, Home, BarChart3, Users, 
  FileText, Settings, Shield, Activity, Calendar, Package,
  Database, Globe, Heart, TrendingUp, AlertCircle, CheckCircle,
  Info, HelpCircle, Mail, Phone, Search, Filter, Download,
  Upload, RefreshCw, Save, Copy, Printer, Share2, Lock,
  Unlock, Eye, EyeOff, Star, Bookmark, Flag, Tag,
  Clock, MapPin, Navigation, Zap, Coffee, Moon, Sun
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import type { MenuItem } from "@/types/menu";
import { MenuItemType } from "@/types/menu";

// Available icons for menu items
const MENU_ICONS = [
  { value: "Home", label: "Home", icon: Home },
  { value: "BarChart3", label: "Bar Chart", icon: BarChart3 },
  { value: "Users", label: "Users", icon: Users },
  { value: "FileText", label: "File Text", icon: FileText },
  { value: "Settings", label: "Settings", icon: Settings },
  { value: "Shield", label: "Shield", icon: Shield },
  { value: "Activity", label: "Activity", icon: Activity },
  { value: "Calendar", label: "Calendar", icon: Calendar },
  { value: "Package", label: "Package", icon: Package },
  { value: "Database", label: "Database", icon: Database },
  { value: "Globe", label: "Globe", icon: Globe },
  { value: "Heart", label: "Heart", icon: Heart },
  { value: "TrendingUp", label: "Trending Up", icon: TrendingUp },
  { value: "AlertCircle", label: "Alert Circle", icon: AlertCircle },
  { value: "CheckCircle", label: "Check Circle", icon: CheckCircle },
  { value: "Info", label: "Info", icon: Info },
  { value: "HelpCircle", label: "Help Circle", icon: HelpCircle },
  { value: "Layout", label: "Layout", icon: Layout },
  { value: "FolderOpen", label: "Folder Open", icon: FolderOpen },
  { value: "ExternalLink", label: "External Link", icon: ExternalLink },
  { value: "Download", label: "Download", icon: Download },
  { value: "Upload", label: "Upload", icon: Upload },
  { value: "RefreshCw", label: "Refresh", icon: RefreshCw },
  { value: "Save", label: "Save", icon: Save },
  { value: "Copy", label: "Copy", icon: Copy },
  { value: "Share2", label: "Share", icon: Share2 },
  { value: "Lock", label: "Lock", icon: Lock },
  { value: "Eye", label: "Eye", icon: Eye },
  { value: "Star", label: "Star", icon: Star },
  { value: "Bookmark", label: "Bookmark", icon: Bookmark },
  { value: "Flag", label: "Flag", icon: Flag },
  { value: "Tag", label: "Tag", icon: Tag },
  { value: "Clock", label: "Clock", icon: Clock },
  { value: "MapPin", label: "Map Pin", icon: MapPin },
  { value: "Zap", label: "Zap", icon: Zap },
];

interface MenuDesignerProps {
  items: MenuItem[];
  selectedItemId: string | null;
  onSelectItem: (itemId: string) => void;
  onUpdateItem: (itemId: string, updates: Partial<MenuItem>) => void;
  onDeleteItem: (itemId: string) => void;
  onAddItem: (parentId?: string) => void;
  onReorderItems: (items: MenuItem[]) => void;
}

interface MenuItemProps {
  item: MenuItem;
  level: number;
  selected: boolean;
  onSelect: () => void;
  onUpdate: (updates: Partial<MenuItem>) => void;
  onDelete: () => void;
  onAddChild: () => void;
  // Props to pass through to children
  selectedItemId: string | null;
  onSelectItem: (itemId: string) => void;
  onUpdateItem: (itemId: string, updates: Partial<MenuItem>) => void;
  onDeleteItem: (itemId: string) => void;
  onAddItem: (parentId?: string) => void;
}

function MenuItemComponent({
  item,
  level,
  selected,
  onSelect,
  onUpdate,
  onDelete,
  onAddChild,
  selectedItemId,
  onSelectItem,
  onUpdateItem,
  onDeleteItem,
  onAddItem,
}: MenuItemProps) {
  const [expanded, setExpanded] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editLabel, setEditLabel] = useState(item.label);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
    isOver,
  } = useSortable({ id: item.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleSaveLabel = () => {
    if (editLabel.trim()) {
      onUpdate({ label: editLabel.trim() });
    }
    setEditing(false);
  };

  const hasChildren = item.children && item.children.length > 0;

  return (
    <div ref={setNodeRef} style={style} role="treeitem" aria-selected={selected}>
      <div
        className={cn(
          "group flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted/50 transition-all relative",
          selected && "bg-primary/10 text-primary",
          isDragging && "cursor-grabbing opacity-50",
          isOver && item.type === MenuItemType.GROUP && "bg-primary/10"
        )}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
        onClick={onSelect}
      >
        {/* Expand/collapse button */}
        <button
          className="p-0.5"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
        >
          {hasChildren ? (
            expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )
          ) : (
            <div className="h-4 w-4" />
          )}
        </button>

        {/* Drag handle */}
        <div
          {...attributes}
          {...listeners}
          className="touch-none"
          data-testid="drag-handle"
        >
          <Grip className="h-4 w-4 cursor-move text-muted-foreground hover:text-foreground transition-colors" />
        </div>

        {/* Icon - show custom icon if set, otherwise show type icon */}
        {(() => {
          if (item.icon && item.icon !== "none") {
            const iconData = MENU_ICONS.find(i => i.value === item.icon);
            const IconComponent = iconData?.icon || Layout;
            return <IconComponent className="h-4 w-4 text-primary" />;
          }
          
          // Default type icons
          switch (item.type) {
            case "dashboard_page":
              return <Layout className="h-4 w-4 text-primary" />;
            case "group":
              return <FolderOpen className="h-4 w-4 text-muted-foreground" />;
            case "divider":
              return <Minus className="h-4 w-4 text-muted-foreground" />;
            case "external":
              return <ExternalLink className="h-4 w-4 text-muted-foreground" />;
            default:
              return <Layout className="h-4 w-4 text-muted-foreground" />;
          }
        })()}

        {/* Label */}
        {editing ? (
          <Input
            value={editLabel}
            onChange={(e) => setEditLabel(e.target.value)}
            onBlur={handleSaveLabel}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSaveLabel();
              if (e.key === "Escape") {
                setEditLabel(item.label);
                setEditing(false);
              }
            }}
            className="h-6 flex-1"
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span className="flex-1 text-sm">{item.label}</span>
        )}

        {/* Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={(e) => {
              e.stopPropagation();
              setEditing(true);
            }}
          >
            <Edit2 className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={(e) => {
              e.stopPropagation();
              onAddChild();
            }}
          >
            <Plus className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Drop indicator for groups */}
      {item.type === MenuItemType.GROUP && isOver && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="h-full w-full rounded-md bg-primary/10 ring-2 ring-primary ring-inset" />
        </div>
      )}

      {/* Children */}
      {hasChildren && expanded && (
        <SortableContext
          items={item.children!.map(child => child.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="ml-2 border-l-2 border-muted">
            {item.children!.map((child) => (
              <ConnectedMenuItem
                key={child.id}
                item={child}
                level={level + 1}
                selectedItemId={selectedItemId}
                onSelectItem={onSelectItem}
                onUpdateItem={onUpdateItem}
                onDeleteItem={onDeleteItem}
                onAddItem={onAddItem}
              />
            ))}
          </div>
        </SortableContext>
      )}
    </div>
  );
}

// Connected menu item that passes through props
function ConnectedMenuItem({
  item,
  level,
  selectedItemId,
  onSelectItem,
  onUpdateItem,
  onDeleteItem,
  onAddItem,
}: {
  item: MenuItem;
  level: number;
  selectedItemId: string | null;
  onSelectItem: (itemId: string) => void;
  onUpdateItem: (itemId: string, updates: Partial<MenuItem>) => void;
  onDeleteItem: (itemId: string) => void;
  onAddItem: (parentId?: string) => void;
}) {
  return (
    <MenuItemComponent
      item={item}
      level={level}
      selected={item.id === selectedItemId}
      onSelect={() => onSelectItem(item.id)}
      onUpdate={(updates) => onUpdateItem(item.id, updates)}
      onDelete={() => onDeleteItem(item.id)}
      onAddChild={() => onAddItem(item.id)}
      selectedItemId={selectedItemId}
      onSelectItem={onSelectItem}
      onUpdateItem={onUpdateItem}
      onDeleteItem={onDeleteItem}
      onAddItem={onAddItem}
    />
  );
}

export function MenuDesigner({
  items,
  selectedItemId,
  onSelectItem,
  onUpdateItem,
  onDeleteItem,
  onAddItem,
  onReorderItems,
}: MenuDesignerProps) {
  const [showItemSettings, setShowItemSettings] = useState(false);
  const [activeId, setActiveId] = useState<UniqueIdentifier | null>(null);
  const [overId, setOverId] = useState<UniqueIdentifier | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const selectedItem = selectedItemId
    ? findMenuItem(items, selectedItemId)
    : null;

  const activeItem = activeId
    ? findMenuItem(items, activeId as string)
    : null;

  function findMenuItem(items: MenuItem[], id: string): MenuItem | null {
    for (const item of items) {
      if (item.id === id) return item;
      if (item.children) {
        const found = findMenuItem(item.children, id);
        if (found) return found;
      }
    }
    return null;
  }

  function findParent(items: MenuItem[], childId: string, parent: MenuItem | null = null): MenuItem | null {
    for (const item of items) {
      if (item.children) {
        if (item.children.some(child => child.id === childId)) {
          return item;
        }
        const found = findParent(item.children, childId, item);
        if (found) return found;
      }
    }
    return parent;
  }

  function removeItem(items: MenuItem[], id: string): MenuItem[] {
    return items.reduce((acc, item) => {
      if (item.id === id) {
        return acc;
      }
      if (item.children) {
        return [...acc, { ...item, children: removeItem(item.children, id) }];
      }
      return [...acc, item];
    }, [] as MenuItem[]);
  }

  function insertItem(items: MenuItem[], item: MenuItem, parentId: string | null, targetIndex: number): MenuItem[] {
    if (!parentId) {
      // Insert at root level
      const newItems = [...items];
      newItems.splice(targetIndex, 0, item);
      return newItems.map((item, index) => ({ ...item, order: index }));
    }

    // Insert as child of parent
    return items.map(parent => {
      if (parent.id === parentId) {
        const children = parent.children || [];
        const newChildren = [...children];
        newChildren.splice(targetIndex, 0, item);
        return {
          ...parent,
          children: newChildren.map((child, index) => ({ ...child, order: index }))
        };
      }
      if (parent.children) {
        return {
          ...parent,
          children: insertItem(parent.children, item, parentId, targetIndex)
        };
      }
      return parent;
    });
  }

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id);
  };

  const handleDragOver = (event: DragOverEvent) => {
    setOverId(event.over?.id || null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    setOverId(null);

    if (!over || active.id === over.id) {
      return;
    }

    const activeItem = findMenuItem(items, active.id as string);
    const overItem = findMenuItem(items, over.id as string);

    if (!activeItem) return;

    let newItems = removeItem(items, active.id as string);

    if (overItem) {
      const overParent = findParent(items, over.id as string);
      const activeParent = findParent(items, active.id as string);

      if (overItem.type === 'group' && overItem.id !== activeParent?.id) {
        // Drop into a group
        const childCount = overItem.children?.length || 0;
        newItems = insertItem(newItems, activeItem, overItem.id, childCount);
      } else {
        // Drop beside an item
        const parentId = overParent?.id || null;
        const siblings = parentId && overParent ? overParent.children || [] : items;
        const overIndex = siblings.findIndex(item => item.id === over.id);
        newItems = insertItem(newItems, activeItem, parentId, overIndex);
      }
    } else {
      // Drop at root level
      newItems = insertItem(newItems, activeItem, null, items.length);
    }

    onReorderItems(newItems);
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="space-y-4">
        {/* Menu tree */}
        <SortableContext
          items={items.map(item => item.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-1">
            {items.map((item) => (
              <ConnectedMenuItem
                key={item.id}
                item={item}
                level={0}
                selectedItemId={selectedItemId}
                onSelectItem={onSelectItem}
                onUpdateItem={onUpdateItem}
                onDeleteItem={onDeleteItem}
                onAddItem={onAddItem}
              />
            ))}
          </div>
        </SortableContext>

      {/* Item settings */}
      {selectedItem && (
        <div className="space-y-4 rounded-lg border p-4">
          <h4 className="font-medium">Item Settings</h4>
          
          <div className="space-y-2">
            <Label htmlFor="item-type">Type</Label>
            <Select
              value={selectedItem.type}
              onValueChange={(value) =>
                onUpdateItem(selectedItem.id, { type: value as MenuItemType })
              }
            >
              <SelectTrigger id="item-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="dashboard_page">Dashboard Page</SelectItem>
                <SelectItem value="group">Group (has submenus)</SelectItem>
                <SelectItem value="divider">Divider</SelectItem>
                <SelectItem value="external">External</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {selectedItem.type === "external" && (
            <div className="space-y-2">
              <Label htmlFor="item-url">External URL</Label>
              <Input
                id="item-url"
                value={selectedItem.url || ""}
                onChange={(e) => onUpdateItem(selectedItem.id, { url: e.target.value })}
                placeholder="https://example.com"
              />
            </div>
          )}

          {selectedItem.type === "dashboard_page" && (
            <div className="p-3 bg-muted rounded-md">
              <p className="text-sm text-muted-foreground">
                This menu item will have its own canvas in the dashboard designer where you can add widgets.
              </p>
            </div>
          )}

          {selectedItem.type === "group" && (
            <div className="p-3 bg-muted rounded-md">
              <p className="text-sm text-muted-foreground">
                This is a placeholder for submenus. Add Dashboard Page items as children to create navigable pages.
              </p>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="item-icon">Icon</Label>
            <Select
              value={selectedItem.icon || "none"}
              onValueChange={(value) => onUpdateItem(selectedItem.id, { icon: value === "none" ? undefined : value })}
            >
              <SelectTrigger id="item-icon">
                <SelectValue placeholder="Select an icon">
                  {selectedItem.icon && selectedItem.icon !== "none" && (
                    <div className="flex items-center gap-2">
                      {(() => {
                        const iconData = MENU_ICONS.find(i => i.value === selectedItem.icon);
                        const IconComponent = iconData?.icon || Layout;
                        return (
                          <>
                            <IconComponent className="h-4 w-4" />
                            <span>{iconData?.label || selectedItem.icon}</span>
                          </>
                        );
                      })()}
                    </div>
                  )}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No icon</SelectItem>
                {MENU_ICONS.map((iconOption) => {
                  const IconComponent = iconOption.icon;
                  return (
                    <SelectItem key={iconOption.value} value={iconOption.value}>
                      <div className="flex items-center gap-2">
                        <IconComponent className="h-4 w-4" />
                        <span>{iconOption.label}</span>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selectedItem.isVisible}
                onChange={(e) =>
                  onUpdateItem(selectedItem.id, { isVisible: e.target.checked })
                }
              />
              <span className="text-sm">Visible</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selectedItem.isEnabled}
                onChange={(e) =>
                  onUpdateItem(selectedItem.id, { isEnabled: e.target.checked })
                }
              />
              <span className="text-sm">Enabled</span>
            </label>
          </div>
        </div>
      )}
      </div>

      {/* Drag overlay */}
      <DragOverlay>
        {activeItem ? (
          <div className="opacity-80">
            <div
              className="group flex items-center gap-2 rounded-md px-2 py-1.5 bg-background border-2 border-primary shadow-2xl"
              style={{ paddingLeft: "8px", minWidth: "200px" }}
            >
              {/* Icon */}
              {(() => {
                if (activeItem.icon && activeItem.icon !== "none") {
                  const iconData = MENU_ICONS.find(i => i.value === activeItem.icon);
                  const IconComponent = iconData?.icon || Layout;
                  return <IconComponent className="h-4 w-4 text-primary" />;
                }
                
                // Default type icons
                switch (activeItem.type) {
                  case "dashboard_page":
                    return <Layout className="h-4 w-4 text-primary" />;
                  case "group":
                    return <FolderOpen className="h-4 w-4 text-muted-foreground" />;
                  case "divider":
                    return <Minus className="h-4 w-4 text-muted-foreground" />;
                  case "external":
                    return <ExternalLink className="h-4 w-4 text-muted-foreground" />;
                  default:
                    return <Layout className="h-4 w-4 text-muted-foreground" />;
                }
              })()}
              <span className="text-sm">{activeItem.label}</span>
            </div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}