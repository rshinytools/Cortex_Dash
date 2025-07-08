// ABOUTME: Dashboard preview page showing how the dashboard will look in production
// ABOUTME: Displays dashboard in read-only mode with actual widget rendering

"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Edit, Maximize2, Minimize2 } from "lucide-react"
import { DashboardDesigner } from "@/components/admin/dashboard-designer"
import { useDashboards } from "@/hooks/use-dashboards"
import { useToast } from "@/hooks/use-toast"
import { Loader2 } from "lucide-react"
import { menusApi } from "@/lib/api/menus"

export default function PreviewDashboardPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  const { getDashboard } = useDashboards()
  const [isLoading, setIsLoading] = useState(true)
  const [fullscreen, setFullscreen] = useState(false)
  const [layoutConfig, setLayoutConfig] = useState<any[]>([])
  const [selectedMenuItem, setSelectedMenuItem] = useState<string>("")
  const [menuLayouts, setMenuLayouts] = useState<Record<string, any[]>>({})
  const [selectedMenuTemplate, setSelectedMenuTemplate] = useState<any>(null)
  
  const [metadata, setMetadata] = useState({
    name: "",
    description: "",
    menuTemplateId: "none",
  })

  useEffect(() => {
    loadDashboard()
  }, [params.id])

  useEffect(() => {
    if (metadata.menuTemplateId && metadata.menuTemplateId !== "none") {
      loadMenuTemplate(metadata.menuTemplateId)
    }
  }, [metadata.menuTemplateId])

  const loadMenuTemplate = async (templateId: string) => {
    try {
      const template = await menusApi.getMenuTemplate(templateId)
      setSelectedMenuTemplate(template)
      // Select the first menu item by default
      if (template.items && template.items.length > 0) {
        const firstDashboardItem = template.items.find((item: any) => item.type === 'dashboard')
        if (firstDashboardItem) {
          setSelectedMenuItem(firstDashboardItem.id)
        }
      }
    } catch (error) {
      console.error("Failed to load menu template:", error)
    }
  }

  const loadDashboard = async () => {
    try {
      const dashboard = await getDashboard(params.id as string)
      setMetadata({
        name: dashboard.name,
        description: dashboard.description || "",
        menuTemplateId: dashboard.menuTemplateId || "none",
      })
      setLayoutConfig(dashboard.layout || [])
      // Load menu layouts if available
      if (dashboard.menuLayouts) {
        setMenuLayouts(dashboard.menuLayouts)
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load dashboard. Please try again.",
        variant: "destructive"
      })
      router.push("/admin/dashboards")
    } finally {
      setIsLoading(false)
    }
  }

  const getCurrentLayout = () => {
    if (selectedMenuItem && menuLayouts[selectedMenuItem]) {
      return menuLayouts[selectedMenuItem]
    }
    return layoutConfig
  }

  const toggleFullscreen = () => {
    if (!fullscreen) {
      document.documentElement.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
    setFullscreen(!fullscreen)
  }

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {!fullscreen && (
        <div className="border-b px-6 py-4 flex items-center justify-between bg-background">
          <div className="flex items-center space-x-4">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => router.push("/admin/dashboards")}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h2 className="text-lg font-semibold">{metadata.name}</h2>
              <p className="text-sm text-muted-foreground">Preview Mode</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={toggleFullscreen}
            >
              {fullscreen ? (
                <Minimize2 className="h-4 w-4 mr-2" />
              ) : (
                <Maximize2 className="h-4 w-4 mr-2" />
              )}
              {fullscreen ? "Exit Fullscreen" : "Fullscreen"}
            </Button>
            <Button 
              size="sm"
              onClick={() => router.push(`/admin/dashboards/${params.id}/edit`)}
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit Dashboard
            </Button>
          </div>
        </div>
      )}
      
      <div className="flex-1 flex overflow-hidden">
        {selectedMenuTemplate && (
          <div className="w-64 border-r bg-muted/10 p-4 overflow-y-auto">
            <h3 className="font-semibold text-sm mb-3">Navigation</h3>
            <div className="space-y-1">
              {selectedMenuTemplate.items?.map((item: any) => {
                if (item.type === 'group') {
                  return (
                    <div key={item.id} className="mt-3">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                        {item.label}
                      </p>
                      <div className="space-y-1 ml-2">
                        {item.children?.map((child: any) => (
                          <Button
                            key={child.id}
                            variant={selectedMenuItem === child.id ? "secondary" : "ghost"}
                            size="sm"
                            className="w-full justify-start"
                            onClick={() => setSelectedMenuItem(child.id)}
                          >
                            {child.label}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )
                } else if (item.type === 'dashboard') {
                  return (
                    <Button
                      key={item.id}
                      variant={selectedMenuItem === item.id ? "secondary" : "ghost"}
                      size="sm"
                      className="w-full justify-start"
                      onClick={() => setSelectedMenuItem(item.id)}
                    >
                      {item.label}
                    </Button>
                  )
                }
                return null
              })}
            </div>
          </div>
        )}
        
        <div className="flex-1 overflow-hidden bg-muted/5">
          <DashboardDesigner
            key={selectedMenuItem || 'default'}
            initialLayout={getCurrentLayout()}
            mode="preview"
          />
        </div>
      </div>
    </div>
  )
}