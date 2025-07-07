// ABOUTME: Menu designer component for creating and editing menu structures
// ABOUTME: Provides tree view with drag-and-drop functionality for menu items

"use client";

import { useState } from "react";
import { ChevronRight, ChevronDown, Grip, Edit2, Trash2, Plus } from "lucide-react";
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
import type { MenuItem, MenuItemType } from "@/types/menu";

interface MenuDesignerProps {
  items: MenuItem[];
  selectedItemId: string | null;
  onSelectItem: (itemId: string) => void;
  onUpdateItem: (itemId: string, updates: Partial<MenuItem>) => void;
  onDeleteItem: (itemId: string) => void;
  onAddItem: (parentId?: string) => void;
}

interface MenuItemProps {
  item: MenuItem;
  level: number;
  selected: boolean;
  onSelect: () => void;
  onUpdate: (updates: Partial<MenuItem>) => void;
  onDelete: () => void;
  onAddChild: () => void;
}

function MenuItemComponent({
  item,
  level,
  selected,
  onSelect,
  onUpdate,
  onDelete,
  onAddChild,
}: MenuItemProps) {
  const [expanded, setExpanded] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editLabel, setEditLabel] = useState(item.label);

  const handleSaveLabel = () => {
    if (editLabel.trim()) {
      onUpdate({ label: editLabel.trim() });
    }
    setEditing(false);
  };

  const hasChildren = item.children && item.children.length > 0;

  return (
    <div>
      <div
        className={cn(
          "group flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted/50",
          selected && "bg-primary/10 text-primary"
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
        <Grip className="h-4 w-4 cursor-move text-muted-foreground" />

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

      {/* Children */}
      {hasChildren && expanded && (
        <div>
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
}: MenuDesignerProps) {
  const [showItemSettings, setShowItemSettings] = useState(false);

  const selectedItem = selectedItemId
    ? findMenuItem(items, selectedItemId)
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

  return (
    <div className="space-y-4">
      {/* Menu tree */}
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
                <SelectItem value="link">Link</SelectItem>
                <SelectItem value="dropdown">Dropdown</SelectItem>
                <SelectItem value="divider">Divider</SelectItem>
                <SelectItem value="header">Header</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {selectedItem.type === "link" && (
            <div className="space-y-2">
              <Label htmlFor="item-url">URL</Label>
              <Input
                id="item-url"
                value={selectedItem.url || ""}
                onChange={(e) => onUpdateItem(selectedItem.id, { url: e.target.value })}
                placeholder="#"
              />
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="item-icon">Icon</Label>
            <Input
              id="item-icon"
              value={selectedItem.icon || ""}
              onChange={(e) => onUpdateItem(selectedItem.id, { icon: e.target.value })}
              placeholder="e.g., Home, BarChart, Settings"
            />
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
  );
}