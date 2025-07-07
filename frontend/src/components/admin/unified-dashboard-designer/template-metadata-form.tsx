// ABOUTME: Template metadata form component for editing template properties
// ABOUTME: Handles template name, description, tags, and category

"use client";

import { X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DashboardCategory } from "@/types/dashboard";

interface TemplateMetadataFormProps {
  name: string;
  description: string;
  tags: string[];
  category: string;
  onNameChange: (name: string) => void;
  onDescriptionChange: (description: string) => void;
  onTagsChange: (tags: string[]) => void;
  onCategoryChange: (category: string) => void;
}

export function TemplateMetadataForm({
  name,
  description,
  tags,
  category,
  onNameChange,
  onDescriptionChange,
  onTagsChange,
  onCategoryChange,
}: TemplateMetadataFormProps) {
  const handleAddTag = (tag: string) => {
    if (tag && !tags.includes(tag)) {
      onTagsChange([...tags, tag]);
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onTagsChange(tags.filter((tag) => tag !== tagToRemove));
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Input
            placeholder="Template Name"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            className="font-semibold"
          />
        </div>
        <div className="space-y-2">
          <Select value={category} onValueChange={onCategoryChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={DashboardCategory.EXECUTIVE}>Executive</SelectItem>
              <SelectItem value={DashboardCategory.OPERATIONAL}>Operational</SelectItem>
              <SelectItem value={DashboardCategory.SAFETY}>Safety</SelectItem>
              <SelectItem value={DashboardCategory.EFFICACY}>Efficacy</SelectItem>
              <SelectItem value={DashboardCategory.QUALITY}>Quality</SelectItem>
              <SelectItem value={DashboardCategory.REGULATORY}>Regulatory</SelectItem>
              <SelectItem value={DashboardCategory.CUSTOM}>Custom</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Textarea
          placeholder="Template Description"
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
          rows={2}
        />
      </div>

      <div className="space-y-2">
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <Badge key={tag} variant="secondary">
              {tag}
              <Button
                variant="ghost"
                size="icon"
                className="ml-1 h-3 w-3 p-0"
                onClick={() => handleRemoveTag(tag)}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          ))}
          <Input
            placeholder="Add tag..."
            className="h-6 w-24"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleAddTag(e.currentTarget.value);
                e.currentTarget.value = "";
              }
            }}
          />
        </div>
      </div>
    </div>
  );
}