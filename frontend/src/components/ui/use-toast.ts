// ABOUTME: Toast notification hook for displaying user feedback
// ABOUTME: Provides programmatic interface to show success/error messages

import { toast } from "sonner"

type ToastProps = {
  title?: string
  description?: string
  variant?: "default" | "destructive"
}

export const useToast = () => {
  const showToast = ({ title, description, variant = "default" }: ToastProps) => {
    if (variant === "destructive") {
      toast.error(title || "Error", {
        description,
      })
    } else {
      toast.success(title || "Success", {
        description,
      })
    }
  }

  return {
    toast: showToast,
  }
}

export { toast }