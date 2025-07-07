// ABOUTME: Create new dashboard page with template selection
// ABOUTME: Allows creating new dashboard templates using the dashboard designer

"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
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
import { ArrowLeft, Save, Loader2 } from "lucide-react"
import { DashboardDesigner } from "@/components/admin/dashboard-designer"
import { useDashboards } from "@/hooks/use-dashboards"
import { useToast } from "@/hooks/use-toast"

interface DashboardMetadata {
  name: string
  description: string
  category: string
  template: string
}

export default function NewDashboardPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { createDashboard } = useDashboards()
  const [isSaving, setIsSaving] = useState(false)
  const [showDesigner, setShowDesigner] = useState(false)
  const [layoutConfig, setLayoutConfig] = useState<any[]>([])
  
  const [metadata, setMetadata] = useState<DashboardMetadata>({
    name: "",
    description: "",
    category: "general",
    template: "blank"
  })

  const handleNext = () => {
    if (!metadata.name) {
      toast({
        title: "Name required",
        description: "Please provide a name for your dashboard",
        variant: "destructive"
      })
      return
    }
    setShowDesigner(true)
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const dashboardData = {
        ...metadata,
        layout: layoutConfig,
        widgets: layoutConfig.map(item => ({
          id: item.i,
          type: item.type,
          config: item.config || {},
          position: { x: item.x, y: item.y, w: item.w, h: item.h }
        }))
      }
      
      await createDashboard(dashboardData)
      
      toast({
        title: "Dashboard created",
        description: "Your dashboard template has been created successfully."
      })
      
      router.push("/admin/dashboards")
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create dashboard. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsSaving(false)
    }
  }

  if (showDesigner) {
    return (
      <div className="h-screen flex flex-col">
        <div className="border-b px-6 py-4 flex items-center justify-between bg-background">
          <div className="flex items-center space-x-4">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setShowDesigner(false)}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h2 className="text-lg font-semibold">{metadata.name}</h2>
              <p className="text-sm text-muted-foreground">{metadata.description}</p>
            </div>
          </div>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Dashboard
              </>
            )}
          </Button>
        </div>
        <div className="flex-1 overflow-hidden">
          <DashboardDesigner
            initialLayout={layoutConfig}
            onChange={setLayoutConfig}
            mode="design"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="flex items-center mb-6">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => router.back()}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      </div>

      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Create Dashboard Template</h1>
          <p className="text-muted-foreground mt-2">
            Design a reusable dashboard template for your studies
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Dashboard Information</CardTitle>
            <CardDescription>
              Provide basic information about your dashboard template
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
              <Label htmlFor="template">Starting Template</Label>
              <Select
                value={metadata.template}
                onValueChange={(value) => setMetadata({ ...metadata, template: value })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="blank">Blank Dashboard</SelectItem>
                  <SelectItem value="safety">Safety Template</SelectItem>
                  <SelectItem value="enrollment">Enrollment Template</SelectItem>
                  <SelectItem value="overview">Study Overview Template</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground mt-1">
                Choose a template to start with or begin from scratch
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button onClick={handleNext} size="lg">
            Next: Design Dashboard
          </Button>
        </div>
      </div>
    </div>
  )
}