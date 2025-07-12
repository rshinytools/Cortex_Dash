// ABOUTME: Theme editor component for customizing dashboard appearance
// ABOUTME: Allows users to select and customize themes with live preview

"use client";

import { useState } from "react";
import { Palette, Sun, Moon, Settings2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { HelpIcon } from "@/components/ui/help-panel";
import { cn } from "@/lib/utils";

export interface DashboardTheme {
  id: string;
  name: string;
  mode: "light" | "dark" | "auto";
  colors: {
    primary: string;
    secondary: string;
    background: string;
    foreground: string;
    card: string;
    cardForeground: string;
    muted: string;
    mutedForeground: string;
    accent: string;
    accentForeground: string;
    border: string;
  };
  typography: {
    fontFamily: string;
    baseFontSize: number;
    headingFontFamily?: string;
    lineHeight: number;
  };
  spacing: {
    baseUnit: number;
    containerPadding: number;
    widgetGap: number;
  };
  borderRadius: number;
}

export const defaultThemes: DashboardTheme[] = [
  {
    id: "light",
    name: "Light",
    mode: "light",
    colors: {
      primary: "#3b82f6",
      secondary: "#6366f1",
      background: "#ffffff",
      foreground: "#09090b",
      card: "#ffffff",
      cardForeground: "#09090b",
      muted: "#f4f4f5",
      mutedForeground: "#71717a",
      accent: "#f4f4f5",
      accentForeground: "#18181b",
      border: "#e4e4e7",
    },
    typography: {
      fontFamily: "Inter, sans-serif",
      baseFontSize: 14,
      lineHeight: 1.5,
    },
    spacing: {
      baseUnit: 4,
      containerPadding: 24,
      widgetGap: 16,
    },
    borderRadius: 8,
  },
  {
    id: "dark",
    name: "Dark",
    mode: "dark",
    colors: {
      primary: "#3b82f6",
      secondary: "#6366f1",
      background: "#09090b",
      foreground: "#fafafa",
      card: "#09090b",
      cardForeground: "#fafafa",
      muted: "#27272a",
      mutedForeground: "#a1a1aa",
      accent: "#27272a",
      accentForeground: "#fafafa",
      border: "#27272a",
    },
    typography: {
      fontFamily: "Inter, sans-serif",
      baseFontSize: 14,
      lineHeight: 1.5,
    },
    spacing: {
      baseUnit: 4,
      containerPadding: 24,
      widgetGap: 16,
    },
    borderRadius: 8,
  },
  {
    id: "clinical",
    name: "Clinical",
    mode: "light",
    colors: {
      primary: "#0ea5e9",
      secondary: "#06b6d4",
      background: "#f8fafc",
      foreground: "#0f172a",
      card: "#ffffff",
      cardForeground: "#0f172a",
      muted: "#f1f5f9",
      mutedForeground: "#64748b",
      accent: "#e0f2fe",
      accentForeground: "#0c4a6e",
      border: "#e2e8f0",
    },
    typography: {
      fontFamily: "Inter, sans-serif",
      baseFontSize: 14,
      headingFontFamily: "Inter, sans-serif",
      lineHeight: 1.6,
    },
    spacing: {
      baseUnit: 4,
      containerPadding: 32,
      widgetGap: 20,
    },
    borderRadius: 6,
  },
];

export interface ThemeEditorProps {
  theme: DashboardTheme;
  onChange: (theme: DashboardTheme) => void;
  onPreview?: (theme: DashboardTheme) => void;
}

export function ThemeEditor({ theme, onChange, onPreview }: ThemeEditorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [customColors, setCustomColors] = useState(theme.colors);

  const handlePresetChange = (themeId: string) => {
    const preset = defaultThemes.find((t) => t.id === themeId);
    if (preset) {
      onChange(preset);
      setCustomColors(preset.colors);
    }
  };

  const handleColorChange = (colorKey: keyof typeof theme.colors, value: string) => {
    const newColors = { ...customColors, [colorKey]: value };
    setCustomColors(newColors);
    onChange({ ...theme, colors: newColors });
  };

  const handleTypographyChange = (key: keyof typeof theme.typography, value: any) => {
    onChange({
      ...theme,
      typography: { ...theme.typography, [key]: value },
    });
  };

  const handleSpacingChange = (key: keyof typeof theme.spacing, value: number) => {
    onChange({
      ...theme,
      spacing: { ...theme.spacing, [key]: value },
    });
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm">
          <Palette className="mr-2 h-4 w-4" />
          Theme
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Dashboard Theme</h3>
            <HelpIcon content="Customize the appearance of your dashboard including colors, typography, and spacing." />
          </div>

          <Tabs defaultValue="presets" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="presets">Presets</TabsTrigger>
              <TabsTrigger value="colors">Colors</TabsTrigger>
              <TabsTrigger value="style">Style</TabsTrigger>
            </TabsList>

            <TabsContent value="presets" className="space-y-4">
              <div className="space-y-2">
                <Label>Theme Preset</Label>
                <Select value={theme.id} onValueChange={handlePresetChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {defaultThemes.map((preset) => (
                      <SelectItem key={preset.id} value={preset.id}>
                        <div className="flex items-center gap-2">
                          {preset.mode === "dark" ? (
                            <Moon className="h-4 w-4" />
                          ) : (
                            <Sun className="h-4 w-4" />
                          )}
                          {preset.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-3 gap-2">
                {defaultThemes.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => handlePresetChange(preset.id)}
                    className={cn(
                      "relative h-20 rounded-lg border-2 p-2 transition-all",
                      theme.id === preset.id
                        ? "border-primary"
                        : "border-border hover:border-muted-foreground"
                    )}
                    style={{ backgroundColor: preset.colors.background }}
                  >
                    <div className="absolute inset-2 flex flex-col gap-1">
                      <div
                        className="h-2 rounded"
                        style={{ backgroundColor: preset.colors.primary }}
                      />
                      <div
                        className="h-4 rounded"
                        style={{ backgroundColor: preset.colors.card }}
                      />
                      <div
                        className="h-1 rounded"
                        style={{ backgroundColor: preset.colors.muted }}
                      />
                    </div>
                    <span
                      className="absolute bottom-1 left-2 text-xs font-medium"
                      style={{ color: preset.colors.foreground }}
                    >
                      {preset.name}
                    </span>
                  </button>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="colors" className="space-y-4">
              <div className="grid gap-3">
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs">Primary</Label>
                    <div className="flex gap-2">
                      <Input
                        type="color"
                        value={customColors.primary}
                        onChange={(e) => handleColorChange("primary", e.target.value)}
                        className="h-8 w-16 p-1"
                      />
                      <Input
                        type="text"
                        value={customColors.primary}
                        onChange={(e) => handleColorChange("primary", e.target.value)}
                        className="h-8 flex-1"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label className="text-xs">Secondary</Label>
                    <div className="flex gap-2">
                      <Input
                        type="color"
                        value={customColors.secondary}
                        onChange={(e) => handleColorChange("secondary", e.target.value)}
                        className="h-8 w-16 p-1"
                      />
                      <Input
                        type="text"
                        value={customColors.secondary}
                        onChange={(e) => handleColorChange("secondary", e.target.value)}
                        className="h-8 flex-1"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label className="text-xs">Background</Label>
                    <div className="flex gap-2">
                      <Input
                        type="color"
                        value={customColors.background}
                        onChange={(e) => handleColorChange("background", e.target.value)}
                        className="h-8 w-16 p-1"
                      />
                      <Input
                        type="text"
                        value={customColors.background}
                        onChange={(e) => handleColorChange("background", e.target.value)}
                        className="h-8 flex-1"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label className="text-xs">Card</Label>
                    <div className="flex gap-2">
                      <Input
                        type="color"
                        value={customColors.card}
                        onChange={(e) => handleColorChange("card", e.target.value)}
                        className="h-8 w-16 p-1"
                      />
                      <Input
                        type="text"
                        value={customColors.card}
                        onChange={(e) => handleColorChange("card", e.target.value)}
                        className="h-8 flex-1"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="style" className="space-y-4">
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label className="text-xs">Font Family</Label>
                  <Select
                    value={theme.typography.fontFamily}
                    onValueChange={(value) => handleTypographyChange("fontFamily", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Inter, sans-serif">Inter</SelectItem>
                      <SelectItem value="Roboto, sans-serif">Roboto</SelectItem>
                      <SelectItem value="Open Sans, sans-serif">Open Sans</SelectItem>
                      <SelectItem value="Lato, sans-serif">Lato</SelectItem>
                      <SelectItem value="Poppins, sans-serif">Poppins</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">Base Font Size</Label>
                    <span className="text-xs text-muted-foreground">
                      {theme.typography.baseFontSize}px
                    </span>
                  </div>
                  <Slider
                    value={[theme.typography.baseFontSize]}
                    onValueChange={([value]) => handleTypographyChange("baseFontSize", value)}
                    min={12}
                    max={18}
                    step={1}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">Border Radius</Label>
                    <span className="text-xs text-muted-foreground">
                      {theme.borderRadius}px
                    </span>
                  </div>
                  <Slider
                    value={[theme.borderRadius]}
                    onValueChange={([value]) => onChange({ ...theme, borderRadius: value })}
                    min={0}
                    max={16}
                    step={2}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">Widget Gap</Label>
                    <span className="text-xs text-muted-foreground">
                      {theme.spacing.widgetGap}px
                    </span>
                  </div>
                  <Slider
                    value={[theme.spacing.widgetGap]}
                    onValueChange={([value]) => handleSpacingChange("widgetGap", value)}
                    min={8}
                    max={32}
                    step={4}
                  />
                </div>
              </div>
            </TabsContent>
          </Tabs>

          {onPreview && (
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => onPreview(theme)}
            >
              <Settings2 className="mr-2 h-4 w-4" />
              Preview Theme
            </Button>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}