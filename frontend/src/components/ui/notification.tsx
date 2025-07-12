// ABOUTME: Notification component for displaying save status and feedback
// ABOUTME: Provides toast-like notifications with loading states and autosave indicators

"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Loader2, Save } from "lucide-react";
import { cn } from "@/lib/utils";

export interface NotificationProps {
  show: boolean;
  type: "success" | "error" | "loading" | "info";
  message: string;
  detail?: string;
  duration?: number;
  onClose?: () => void;
}

export function Notification({
  show,
  type,
  message,
  detail,
  duration = 4000,
  onClose,
}: NotificationProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      if (type !== "loading" && duration > 0) {
        const timer = setTimeout(() => {
          setIsVisible(false);
          onClose?.();
        }, duration);
        return () => clearTimeout(timer);
      }
    } else {
      setIsVisible(false);
    }
  }, [show, type, duration, onClose]);

  const icons = {
    success: <CheckCircle className="h-5 w-5 text-green-600" />,
    error: <XCircle className="h-5 w-5 text-red-600" />,
    loading: <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />,
    info: <Save className="h-5 w-5 text-blue-600" />,
  };

  const backgrounds = {
    success: "bg-green-50 border-green-200",
    error: "bg-red-50 border-red-200",
    loading: "bg-blue-50 border-blue-200",
    info: "bg-blue-50 border-blue-200",
  };

  if (!isVisible) return null;

  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 z-50 flex items-start gap-3 rounded-lg border p-4 shadow-lg transition-all duration-300",
        backgrounds[type],
        isVisible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
      )}
      role="alert"
    >
      <div className="flex-shrink-0">{icons[type]}</div>
      <div className="flex-1 space-y-1">
        <p className="text-sm font-medium text-gray-900">{message}</p>
        {detail && <p className="text-sm text-gray-600">{detail}</p>}
      </div>
    </div>
  );
}

export interface AutosaveIndicatorProps {
  lastSaved: Date | null;
  isUnsaved: boolean;
  isSaving: boolean;
}

export function AutosaveIndicator({
  lastSaved,
  isUnsaved,
  isSaving,
}: AutosaveIndicatorProps) {
  const [timeAgo, setTimeAgo] = useState("");

  useEffect(() => {
    if (!lastSaved) return;

    const updateTimeAgo = () => {
      const seconds = Math.floor((Date.now() - lastSaved.getTime()) / 1000);
      if (seconds < 60) {
        setTimeAgo("just now");
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        setTimeAgo(`${minutes} minute${minutes > 1 ? "s" : ""} ago`);
      } else {
        const hours = Math.floor(seconds / 3600);
        setTimeAgo(`${hours} hour${hours > 1 ? "s" : ""} ago`);
      }
    };

    updateTimeAgo();
    const interval = setInterval(updateTimeAgo, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, [lastSaved]);

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      {isSaving ? (
        <>
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>Saving...</span>
        </>
      ) : isUnsaved ? (
        <>
          <div className="h-2 w-2 rounded-full bg-orange-500" />
          <span>Unsaved changes</span>
        </>
      ) : lastSaved ? (
        <>
          <CheckCircle className="h-3 w-3 text-green-600" />
          <span>Saved {timeAgo}</span>
        </>
      ) : null}
    </div>
  );
}