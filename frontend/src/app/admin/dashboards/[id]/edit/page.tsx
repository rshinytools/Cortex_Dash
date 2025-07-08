// ABOUTME: Edit existing dashboard template page
// ABOUTME: Loads dashboard configuration and allows editing using the designer

"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Save, Loader2, Settings, Menu } from "lucide-react"
import { DashboardDesigner } from "@/components/admin/dashboard-designer"
import { useDashboards } from "@/hooks/use-dashboards"
import { useToast } from "@/hooks/use-toast"
import { menusApi } from "@/lib/api/menus"

export default function EditDashboardPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  const { getDashboard, updateDashboard } = useDashboards()
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [layoutConfig, setLayoutConfig] = useState<any[]>([])
  const [selectedMenuItem, setSelectedMenuItem] = useState<string>("")
  const [menuLayouts, setMenuLayouts] = useState<Record<string, any[]>>({})
  
  const [metadata, setMetadata] = useState({
    name: "",
    description: "",
    category: "general",
    menuTemplateId: "none",
  })
  const [menuTemplates, setMenuTemplates] = useState<any[]>([])
  const [loadingMenus, setLoadingMenus] = useState(false)
  const [selectedMenuTemplate, setSelectedMenuTemplate] = useState<any>(null)

  useEffect(() => {
    loadDashboard()
    loadMenuTemplates()
  }, [params.id])

  useEffect(() => {
    if (metadata.menuTemplateId && metadata.menuTemplateId !== "none") {
      loadSelectedMenuTemplate(metadata.menuTemplateId)
    } else {
      setSelectedMenuTemplate(null)
      setSelectedMenuItem("")
    }
  }, [metadata.menuTemplateId])

  const loadMenuTemplates = async () => {
    setLoadingMenus(true)
    try {
      const response = await menusApi.getMenuTemplates({ size: 100 })
      setMenuTemplates(response.items || [])
    } catch (error) {
      console.error("Failed to load menu templates:", error)
    } finally {
      setLoadingMenus(false)
    }
  }

  const loadSelectedMenuTemplate = async (templateId: string) => {
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
        category: dashboard.category || "general",
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

  const handleLayoutChange = (newLayout: any[]) => {
    if (selectedMenuItem) {
      // Save layout for the current menu item
      setMenuLayouts(prev => ({
        ...prev,
        [selectedMenuItem]: newLayout
      }))
    } else {
      // No menu selected, use default layout
      setLayoutConfig(newLayout)
    }
  }

  const getCurrentLayout = () => {
    if (selectedMenuItem && menuLayouts[selectedMenuItem]) {
      return menuLayouts[selectedMenuItem]
    }
    return layoutConfig
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      // Get the current layout based on whether we're in menu mode or not
      const currentLayout = getCurrentLayout()
      
      const dashboardData = {
        ...metadata,
        layout: currentLayout,
        menuLayouts: selectedMenuTemplate ? menuLayouts : undefined,
        widgets: currentLayout.map(item => ({
          id: item.i,
          type: item.type,
          config: item.config || {},
          position: { x: item.x, y: item.y, w: item.w, h: item.h }
        }))
      }
      
      await updateDashboard(params.id as string, dashboardData)
      
      toast({
        title: "Dashboard updated",
        description: "Your dashboard template has been updated successfully."
      })
      
      if (showSettings) {
        setShowSettings(false)
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update dashboard. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (showSettings) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <div className="flex items-center mb-6">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setShowSettings(false)}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Designer
          </Button>
        </div>

        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Dashboard Settings</h1>
            <p className="text-muted-foreground mt-2">
              Update dashboard information and configuration
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Dashboard Information</CardTitle>
              <CardDescription>
                Update basic information about your dashboard template
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="name">Dashboard Name</Label>
                <Input
                  id="name"
                  value={metadata.name}
                  onChange={(e) => setMetadata({ ...metadata, name: e.target.value })}
                  placeholder="e.g., Safety Monitoring Dashboard"
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={metadata.description}
                  onChange={(e) => setMetadata({ ...metadata, description: e.target.value })}
                  placeholder="Describe the purpose and contents of this dashboard..."
                  className="mt-1"
                  rows={3}
                />
              </div>

              <div>
                <Label htmlFor="category">Category</Label>
                <Select
                  value={metadata.category}
                  onValueChange={(value) => setMetadata({ ...metadata, category: value })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General</SelectItem>
                    <SelectItem value="safety">Safety</SelectItem>
                    <SelectItem value="efficacy">Efficacy</SelectItem>
                    <SelectItem value="enrollment">Enrollment</SelectItem>
                    <SelectItem value="operations">Operations</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="menuTemplate">Menu Template</Label>
                <Select
                  value={metadata.menuTemplateId}
                  onValueChange={(value) => {
                    setMetadata({ ...metadata, menuTemplateId: value })
                    // Clear menu layouts when changing menu template
                    setMenuLayouts({})
                    setSelectedMenuItem("")
                  }}
                  disabled={loadingMenus}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder={loadingMenus ? "Loading..." : "Select a menu template"} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No menu template</SelectItem>
                    {menuTemplates.map((menu) => (
                      <SelectItem key={menu.id} value={menu.id}>
                        <div className="flex items-center gap-2">
                          <Menu className="h-4 w-4" />
                          {menu.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground mt-1">
                  Select a menu template to define the navigation structure for this dashboard
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end space-x-4">
            <Button variant="outline" onClick={() => setShowSettings(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col">
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
            <p className="text-sm text-muted-foreground">{metadata.description}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowSettings(true)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
      <div className="flex-1 flex overflow-hidden">
        {metadata.menuTemplateId !== "none" && !selectedMenuTemplate && (
          <div className="w-64 border-r bg-muted/10 p-4 flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}
        {selectedMenuTemplate && (
          <div className="w-64 border-r bg-muted/10 p-4 overflow-y-auto">
            <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
              <Menu className="h-4 w-4" />
              {selectedMenuTemplate.name}
            </h3>
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
            {selectedMenuItem && (
              <div className="mt-6 p-3 bg-muted rounded-md">
                <p className="text-xs font-medium text-muted-foreground">Currently designing:</p>
                <p className="text-sm font-medium mt-1">
                  {selectedMenuTemplate.items?.find((item: any) => 
                    item.id === selectedMenuItem || 
                    item.children?.some((child: any) => child.id === selectedMenuItem)
                  )?.label || 
                  selectedMenuTemplate.items?.find((item: any) => 
                    item.children?.some((child: any) => child.id === selectedMenuItem)
                  )?.children?.find((child: any) => child.id === selectedMenuItem)?.label}
                </p>
              </div>
            )}
          </div>
        )}
        <div className="flex-1 overflow-hidden">
          <DashboardDesigner
            key={selectedMenuItem || 'default'}
            initialLayout={getCurrentLayout()}
            onChange={handleLayoutChange}
            mode="design"
          />
        </div>
      </div>
    </div>
  )
}