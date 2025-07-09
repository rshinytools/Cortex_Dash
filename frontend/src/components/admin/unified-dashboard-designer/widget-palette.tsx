// ABOUTME: Widget palette component for displaying available widgets
// ABOUTME: Allows dragging widgets to add them to the dashboard

"use client";

import { useState } from "react";
import { useDrag } from "react-dnd";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { cn } from "@/lib/utils";
import type { WidgetDefinition } from "@/types/widget";
import { WidgetCategory } from "@/types/widget";

interface WidgetPaletteProps {
  widgetDefinitions: WidgetDefinition[];
  onAddWidget: (widgetDefId: string) => void;
}

interface WidgetItemProps {
  widget: WidgetDefinition;
  onAdd: () => void;
}

function WidgetItem({ widget, onAdd }: WidgetItemProps) {
  const [{ isDragging }, drag] = useDrag({
    type: "widget",
    item: { widgetDefId: widget.id },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  });

  return (
    <div
      ref={drag as any}
      className={cn(
        "cursor-move rounded-lg border p-3 transition-all hover:border-primary hover:shadow-sm",
        isDragging && "opacity-50"
      )}
      onClick={onAdd}
    >
      <div className="mb-2 flex items-start justify-between">
        <h4 className="text-sm font-medium">{widget.name}</h4>
        <Badge variant="secondary" className="text-xs">
          {widget.type}
        </Badge>
      </div>
      {widget.description && (
        <p className="mb-2 text-xs text-muted-foreground line-clamp-2">
          {widget.description}
        </p>
      )}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>
          {widget.size.defaultWidth}x{widget.size.defaultHeight}
        </span>
        {widget.tags && widget.tags.length > 0 && (
          <>
            <span>•</span>
            <span>{widget.tags.slice(0, 2).join(", ")}</span>
          </>
        )}
      </div>
    </div>
  );
}

export function WidgetPalette({ widgetDefinitions, onAddWidget }: WidgetPaletteProps) {
  const [search, setSearch] = useState("");

  // Filter widgets based on search
  const filteredWidgets = widgetDefinitions.filter(
    (widget) =>
      widget.name.toLowerCase().includes(search.toLowerCase()) ||
      widget.description?.toLowerCase().includes(search.toLowerCase()) ||
      widget.tags?.some((tag) => tag.toLowerCase().includes(search.toLowerCase()))
  );

  // Group widgets by category
  const widgetsByCategory = filteredWidgets.reduce((acc, widget) => {
    const category = widget.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(widget);
    return acc;
  }, {} as Record<WidgetCategory, WidgetDefinition[]>);

  const categoryLabels: Record<WidgetCategory, string> = {
    [WidgetCategory.SAFETY]: "Safety",
    [WidgetCategory.EFFICACY]: "Efficacy",
    [WidgetCategory.ENROLLMENT]: "Enrollment",
    [WidgetCategory.OPERATIONS]: "Operations",
    [WidgetCategory.QUALITY]: "Quality",
    [WidgetCategory.FINANCE]: "Finance",
    [WidgetCategory.CUSTOM]: "Custom",
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b p-4">
        <h3 className="mb-3 font-semibold">Widget Palette</h3>
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search widgets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4">
          {Object.keys(widgetsByCategory).length === 0 ? (
            <p className="text-center text-sm text-muted-foreground">
              No widgets found
            </p>
          ) : (
            <Accordion
              type="multiple"
              defaultValue={Object.keys(widgetsByCategory)}
              className="space-y-2"
            >
              {Object.entries(widgetsByCategory).map(([category, widgets]) => (
                <AccordionItem key={category} value={category} className="border-none">
                  <AccordionTrigger className="rounded-lg bg-muted/50 px-3 py-2 hover:bg-muted">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">
                        {categoryLabels[category as WidgetCategory]}
                      </span>
                      <Badge variant="outline" className="ml-2">
                        {widgets.length}
                      </Badge>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-2 pt-2">
                    {widgets.map((widget) => (
                      <WidgetItem
                        key={widget.id}
                        widget={widget}
                        onAdd={() => onAddWidget(widget.id)}
                      />
                    ))}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          )}
        </div>
      </ScrollArea>

      <div className="border-t p-4 text-xs text-muted-foreground">
        Drag widgets to the dashboard or click to add
      </div>
    </div>
  );
}