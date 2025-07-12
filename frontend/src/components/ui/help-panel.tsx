// ABOUTME: Help panel component for contextual help and tooltips
// ABOUTME: Provides a collapsible help panel with section-specific guidance

"use client";

import { useState } from "react";
import { HelpCircle, X, ChevronRight, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export interface HelpSection {
  id: string;
  title: string;
  content: string;
  subsections?: {
    title: string;
    content: string;
  }[];
}

export interface HelpPanelProps {
  sections: HelpSection[];
  currentSection?: string;
}

export function HelpPanel({ sections, currentSection }: HelpPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(currentSection ? [currentSection] : [])
  );

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) {
        next.delete(sectionId);
      } else {
        next.add(sectionId);
      }
      return next;
    });
  };

  return (
    <>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(true)}
              className="fixed bottom-4 left-4 z-40 h-12 w-12 rounded-full shadow-lg"
            >
              <HelpCircle className="h-6 w-6" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Help & Documentation</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent side="left" className="w-96 overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Help & Documentation</SheetTitle>
          </SheetHeader>

          <div className="mt-6 space-y-4">
            {sections.map((section) => (
              <div key={section.id} className="border rounded-lg">
                <button
                  onClick={() => toggleSection(section.id)}
                  className={cn(
                    "flex w-full items-center justify-between p-4 text-left hover:bg-muted/50",
                    currentSection === section.id && "bg-muted/50"
                  )}
                >
                  <h3 className="font-medium">{section.title}</h3>
                  {expandedSections.has(section.id) ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </button>

                {expandedSections.has(section.id) && (
                  <div className="border-t p-4">
                    <p className="text-sm text-muted-foreground whitespace-pre-line">
                      {section.content}
                    </p>

                    {section.subsections && (
                      <div className="mt-4 space-y-3">
                        {section.subsections.map((subsection, idx) => (
                          <div key={idx}>
                            <h4 className="text-sm font-medium mb-1">
                              {subsection.title}
                            </h4>
                            <p className="text-sm text-muted-foreground whitespace-pre-line">
                              {subsection.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}

export interface HelpIconProps {
  content: string;
  side?: "top" | "right" | "bottom" | "left";
}

export function HelpIcon({ content, side = "top" }: HelpIconProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
        </TooltipTrigger>
        <TooltipContent side={side} className="max-w-sm">
          <p className="text-sm">{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}