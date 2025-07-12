// ABOUTME: Legacy dashboard preview page - redirects to unified dashboard templates
// ABOUTME: This page is deprecated in favor of the unified dashboard template system

"use client"

import { useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { Loader2 } from "lucide-react"

export default function PreviewDashboardPage() {
  const router = useRouter()
  const params = useParams()
  
  useEffect(() => {
    // Redirect to the dashboard templates list page (preview is now a dialog)
    router.replace('/admin/dashboard-templates')
  }, [router, params.id])
  
  // Show loading state while redirecting
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
        <p>Redirecting to dashboard templates...</p>
      </div>
    </div>
  )
}