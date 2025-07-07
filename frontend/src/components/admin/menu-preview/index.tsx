// ABOUTME: Menu preview component for displaying menu structure
// ABOUTME: Shows hierarchical menu items in a visual tree format

"use client";

import { ChevronRight, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MenuItem } from "@/types/menu";

interface MenuPreviewProps {
  items: MenuItem[];
  className?: string;
}

function MenuItemPreview({ item, level = 0 }: { item: MenuItem; level?: number }) {
  const hasChildren = item.children && item.children.length > 0;

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 rounded px-2 py-1 text-sm",
          level === 0 && "font-medium"
        )}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
      >
        {hasChildren ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <div className="h-3 w-3" />
        )}
        {item.icon && <span className="text-xs text-muted-foreground">[{item.icon}]</span>}
        <span>{item.label}</span>
        {!item.isVisible && (
          <span className="text-xs text-muted-foreground">(hidden)</span>
        )}
      </div>
      {hasChildren && (
        <div>
          {item.children!.map((child) => (
            <MenuItemPreview key={child.id} item={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function MenuPreview({ items, className }: MenuPreviewProps) {
  return (
    <div className={cn("space-y-1", className)}>
      {items.map((item) => (
        <MenuItemPreview key={item.id} item={item} />
      ))}
    </div>
  );
}