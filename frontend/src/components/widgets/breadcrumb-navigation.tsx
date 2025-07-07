// ABOUTME: Breadcrumb navigation component for drill-down paths in dashboard widgets
// ABOUTME: Provides visual navigation history and quick access to previous drill-down levels

'use client';

import React, { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  ChevronRight, 
  Home, 
  ArrowLeft, 
  X,
  MoreHorizontal 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDrillDownManager, DrillDownLevel } from './drill-down-manager';

interface BreadcrumbNavigationProps {
  pathId?: string;
  className?: string;
  variant?: 'full' | 'compact' | 'minimal';
  showHomeButton?: boolean;
  showBackButton?: boolean;
  showClearButton?: boolean;
  maxItems?: number;
}

export function BreadcrumbNavigation({
  pathId,
  className,
  variant = 'full',
  showHomeButton = true,
  showBackButton = true,
  showClearButton = true,
  maxItems = 5,
}: BreadcrumbNavigationProps) {
  const {
    getBreadcrumbs,
    navigateToLevel,
    goBack,
    clearDrillDown,
    getActivePath,
  } = useDrillDownManager();

  const activePath = getActivePath();
  const breadcrumbs = getBreadcrumbs(pathId);

  // Handle navigation to specific level
  const handleNavigateToLevel = useCallback((level: number) => {
    const targetPathId = pathId || activePath?.id;
    if (targetPathId) {
      navigateToLevel(targetPathId, level);
    }
  }, [pathId, activePath, navigateToLevel]);

  // Handle back navigation
  const handleGoBack = useCallback(() => {
    goBack(pathId);
  }, [pathId, goBack]);

  // Handle clear drill-down
  const handleClear = useCallback(() => {
    clearDrillDown(pathId);
  }, [pathId, clearDrillDown]);

  // Don't render if no breadcrumbs
  if (breadcrumbs.length === 0) {
    return null;
  }

  // Minimal variant - just current level
  if (variant === 'minimal') {
    const currentLevel = breadcrumbs[breadcrumbs.length - 1];
    return (
      <div className={cn("flex items-center gap-2", className)}>
        {showBackButton && breadcrumbs.length > 1 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleGoBack}
            className="h-6 px-2"
          >
            <ArrowLeft className="h-3 w-3" />
          </Button>
        )}
        <Badge variant="secondary" className="text-xs">
          {currentLevel.title}
        </Badge>
        {showClearButton && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            className="h-6 w-6 p-0"
          >
            <X className="h-3 w-3" />
          </Button>
        )}
      </div>
    );
  }

  // Prepare breadcrumb items with truncation
  let visibleBreadcrumbs = breadcrumbs;
  let hasHiddenItems = false;

  if (variant === 'compact' && breadcrumbs.length > maxItems) {
    hasHiddenItems = true;
    // Keep first item, last few items, and show ellipsis
    const keepFirst = 1;
    const keepLast = maxItems - 2; // Account for ellipsis
    visibleBreadcrumbs = [
      ...breadcrumbs.slice(0, keepFirst),
      ...breadcrumbs.slice(-keepLast),
    ];
  }

  return (
    <div className={cn(
      "flex items-center gap-1 text-sm",
      variant === 'compact' && "max-w-md",
      className
    )}>
      {/* Home button */}
      {showHomeButton && (
        <>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleNavigateToLevel(0)}
            className="h-6 px-2 text-muted-foreground hover:text-foreground"
            disabled={breadcrumbs.length <= 1}
          >
            <Home className="h-3 w-3" />
            {variant === 'full' && <span className="ml-1">Dashboard</span>}
          </Button>
          {breadcrumbs.length > 0 && (
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
          )}
        </>
      )}

      {/* Back button */}
      {showBackButton && breadcrumbs.length > 1 && variant !== 'minimal' && (
        <>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleGoBack}
            className="h-6 px-2"
          >
            <ArrowLeft className="h-3 w-3" />
            {variant === 'full' && <span className="ml-1">Back</span>}
          </Button>
          <ChevronRight className="h-3 w-3 text-muted-foreground" />
        </>
      )}

      {/* Breadcrumb items */}
      {visibleBreadcrumbs.map((level, index) => {
        const isLast = index === breadcrumbs.length - 1;
        const isClickable = !isLast && index < breadcrumbs.length - 1;
        const actualIndex = hasHiddenItems && index === 1 
          ? breadcrumbs.length - (visibleBreadcrumbs.length - 1) + index - 1
          : index;

        return (
          <React.Fragment key={level.id}>
            {/* Show ellipsis for hidden items */}
            {hasHiddenItems && index === 1 && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 text-muted-foreground"
                  disabled
                >
                  <MoreHorizontal className="h-3 w-3" />
                </Button>
                <ChevronRight className="h-3 w-3 text-muted-foreground" />
              </>
            )}

            {/* Breadcrumb item */}
            {isClickable ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleNavigateToLevel(actualIndex)}
                className="h-6 px-2 text-muted-foreground hover:text-foreground"
              >
                <span className="truncate max-w-32">
                  {level.title}
                </span>
              </Button>
            ) : (
              <Badge 
                variant={isLast ? "default" : "secondary"}
                className="text-xs max-w-32 truncate"
              >
                {level.title}
              </Badge>
            )}

            {/* Separator */}
            {!isLast && (
              <ChevronRight className="h-3 w-3 text-muted-foreground" />
            )}
          </React.Fragment>
        );
      })}

      {/* Clear button */}
      {showClearButton && (
        <>
          <div className="mx-1 border-l border-border h-4" />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            className="h-6 px-2 text-muted-foreground hover:text-destructive"
            title="Clear drill-down"
          >
            <X className="h-3 w-3" />
            {variant === 'full' && <span className="ml-1">Clear</span>}
          </Button>
        </>
      )}
    </div>
  );
}

// Compact breadcrumb for use in widget headers
export function CompactBreadcrumb({ 
  pathId, 
  className 
}: { 
  pathId?: string; 
  className?: string; 
}) {
  return (
    <BreadcrumbNavigation
      pathId={pathId}
      variant="compact"
      showHomeButton={false}
      showBackButton={false}
      maxItems={3}
      className={className}
    />
  );
}

// Minimal breadcrumb for constrained spaces
export function MinimalBreadcrumb({ 
  pathId, 
  className 
}: { 
  pathId?: string; 
  className?: string; 
}) {
  return (
    <BreadcrumbNavigation
      pathId={pathId}
      variant="minimal"
      showHomeButton={false}
      className={className}
    />
  );
}

// Navigation toolbar with breadcrumbs and controls
interface NavigationToolbarProps {
  pathId?: string;
  className?: string;
  showStats?: boolean;
}

export function NavigationToolbar({
  pathId,
  className,
  showStats = true,
}: NavigationToolbarProps) {
  const { getActivePath } = useDrillDownManager();
  
  const activePath = getActivePath();
  const path = pathId ? null : activePath; // Use provided pathId or active path

  if (!path && !pathId) {
    return null;
  }

  return (
    <div className={cn(
      "flex items-center justify-between gap-4 p-2 border-b bg-muted/30",
      className
    )}>
      {/* Breadcrumb navigation */}
      <div className="flex-1 min-w-0">
        <BreadcrumbNavigation
          pathId={pathId}
          variant="full"
          maxItems={4}
        />
      </div>

      {/* Stats */}
      {showStats && path && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>
            Level {path.current_level + 1} of {path.levels.length}
          </span>
          <span>
            Max depth: {path.max_depth}
          </span>
        </div>
      )}
    </div>
  );
}