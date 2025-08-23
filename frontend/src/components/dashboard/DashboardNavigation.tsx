// ABOUTME: Dashboard navigation component with support for hierarchical menu structure
// ABOUTME: Handles dashboard page navigation with expandable groups and external links

"use client";

import { useState } from "react";
import { ChevronRight, ChevronDown, Layout, ExternalLink, Minus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { MenuItem } from "@/types/menu";
import { MenuItemType } from "@/types/menu";

interface DashboardNavigationProps {
  items: MenuItem[];
  selectedItemId: string | null;
  onSelectItem: (itemId: string) => void;
  className?: string;
}

interface NavItemProps {
  item: MenuItem;
  level: number;
  selectedItemId: string | null;
  onSelectItem: (itemId: string) => void;
  expandedGroups: Set<string>;
  onToggleGroup: (groupId: string) => void;
}

function NavItem({
  item,
  level,
  selectedItemId,
  onSelectItem,
  expandedGroups,
  onToggleGroup,
}: NavItemProps) {
  const isSelected = item.id === selectedItemId;
  const isGroup = item.type === MenuItemType.GROUP;
  const isDashboardPage = item.type === MenuItemType.DASHBOARD_PAGE;
  const isExpanded = expandedGroups.has(item.id);
  const hasChildren = item.children && item.children.length > 0;

  if (item.type === MenuItemType.DIVIDER) {
    return (
      <div
        className="my-2 border-t border-border"
        style={{ marginLeft: `${level * 12}px` }}
      />
    );
  }

  const handleClick = () => {
    if (isGroup && hasChildren) {
      onToggleGroup(item.id);
    } else if (isDashboardPage) {
      onSelectItem(item.id);
    } else if (item.type === MenuItemType.EXTERNAL && item.url) {
      // Security: Validate URL to prevent javascript: and data: protocol attacks
      const url = item.url;
      const isValidUrl = /^https?:\/\//i.test(url);
      
      if (!isValidUrl) {
        console.warn('Blocked potentially dangerous URL:', url);
        return;
      }
      
      // Security: Add noopener,noreferrer to prevent tab-nabbing attacks
      window.open(url, item.target || "_blank", 'noopener,noreferrer');
    }
  };

  return (
    <div>
      <Button
        variant={isSelected ? "secondary" : "ghost"}
        size="sm"
        className={cn(
          "w-full justify-start gap-2 px-2 py-1.5 h-auto font-normal",
          isSelected && "bg-primary/10 text-primary hover:bg-primary/15",
          !item.isEnabled && "opacity-50 cursor-not-allowed"
        )}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
        onClick={handleClick}
        disabled={!item.isEnabled}
      >
        {/* Expand/collapse icon for groups */}
        {isGroup && hasChildren ? (
          isExpanded ? (
            <ChevronDown className="h-4 w-4 shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0" />
          )
        ) : (
          <div className="h-4 w-4 shrink-0" />
        )}

        {/* Item type icon */}
        {isDashboardPage && <Layout className="h-4 w-4 shrink-0 text-primary" />}
        {item.type === MenuItemType.EXTERNAL && (
          <ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}

        {/* Label */}
        <span className="flex-1 text-left">{item.label}</span>

        {/* Badge */}
        {item.badge && (
          <span className="ml-auto">
            {item.badge.count !== undefined ? (
              <span className="inline-flex items-center justify-center rounded-full bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary">
                {item.badge.count}
              </span>
            ) : item.badge.text ? (
              <span className="text-xs text-muted-foreground">{item.badge.text}</span>
            ) : null}
          </span>
        )}
      </Button>

      {/* Render children if expanded */}
      {isGroup && hasChildren && isExpanded && (
        <div className="mt-0.5">
          {item.children!.map((child) => (
            <NavItem
              key={child.id}
              item={child}
              level={level + 1}
              selectedItemId={selectedItemId}
              onSelectItem={onSelectItem}
              expandedGroups={expandedGroups}
              onToggleGroup={onToggleGroup}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function DashboardNavigation({
  items,
  selectedItemId,
  onSelectItem,
  className,
}: DashboardNavigationProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(() => {
    // Auto-expand groups that contain the selected item
    const expanded = new Set<string>();
    
    const findParentGroups = (menuItems: MenuItem[], targetId: string, parents: string[] = []): string[] => {
      for (const item of menuItems) {
        if (item.id === targetId) {
          return parents;
        }
        if (item.children && item.children.length > 0) {
          const found = findParentGroups(item.children, targetId, [...parents, item.id]);
          if (found.length > parents.length) {
            return found;
          }
        }
      }
      return parents;
    };

    if (selectedItemId) {
      const parentGroups = findParentGroups(items, selectedItemId);
      parentGroups.forEach(id => expanded.add(id));
    }

    return expanded;
  });

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  if (!items || items.length === 0) {
    return (
      <div className={cn("p-4 text-center text-muted-foreground", className)}>
        No menu items configured
      </div>
    );
  }

  return (
    <nav className={cn("space-y-0.5", className)}>
      {items.map((item) => (
        <NavItem
          key={item.id}
          item={item}
          level={0}
          selectedItemId={selectedItemId}
          onSelectItem={onSelectItem}
          expandedGroups={expandedGroups}
          onToggleGroup={toggleGroup}
        />
      ))}
    </nav>
  );
}