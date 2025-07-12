// ABOUTME: Redirect page for old dashboard creation flow
// ABOUTME: Redirects to the new unified dashboard template designer

"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"

export default function NewDashboardPage() {
  const router = useRouter()
  
  // Redirect to the new unified dashboard template creation
  useEffect(() => {
    router.replace('/admin/dashboard-templates/new')
  }, [router])
  
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
        <p>Redirecting to unified dashboard designer...</p>
      </div>
    </div>
  )
}