// ABOUTME: Legacy dashboard edit page - redirects to unified dashboard templates
// ABOUTME: This page is deprecated in favor of the unified dashboard template system

"use client"

import { useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { Loader2 } from "lucide-react"

export default function EditDashboardPage() {
  const router = useRouter()
  const params = useParams()
  
  useEffect(() => {
    // Redirect to the new unified dashboard templates edit page
    router.replace(`/admin/dashboard-templates/${params.id}/edit`)
  }, [router, params.id])
  
  // Show loading state while redirecting
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
        <p>Redirecting to dashboard template editor...</p>
      </div>
    </div>
  )
}