// ABOUTME: Layout wrapper for study-specific pages with dynamic sidebar navigation
// ABOUTME: Replaces static navigation with menu template-based dynamic navigation

'use client'

import { DynamicSidebar } from '@/components/layout/dynamic-sidebar'
import { Breadcrumbs } from '@/components/layout/breadcrumbs'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Menu, X } from 'lucide-react'
import { Sheet, SheetContent } from '@/components/ui/sheet'

interface StudyLayoutProps {
  children: React.ReactNode
  params: {
    studyId: string
  }
}

export default function StudyLayout({ children, params }: StudyLayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <DynamicSidebar 
          studyId={params.studyId} 
          className="w-64 border-r bg-background"
        />
      </div>

      {/* Mobile Menu Sheet */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent side="left" className="p-0 w-64">
          <DynamicSidebar 
            studyId={params.studyId}
            onNavigate={() => setMobileMenuOpen(false)}
          />
        </SheetContent>
      </Sheet>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="border-b bg-background">
          <div className="flex items-center gap-4 px-4 py-3">
            {/* Mobile Menu Toggle */}
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>

            {/* Breadcrumbs */}
            <Breadcrumbs studyId={params.studyId} homeLabel="Studies" homeHref="/studies" />
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-muted/40 p-4 md:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  )
}