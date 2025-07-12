// ABOUTME: Legacy dashboard page - redirects to unified dashboard templates
// ABOUTME: This page is deprecated in favor of the unified dashboard template system

"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"

export default function DashboardsPage() {
  const router = useRouter()
  
  useEffect(() => {
    // Redirect to the new unified dashboard templates page
    router.replace('/admin/dashboard-templates')
  }, [router])
  
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