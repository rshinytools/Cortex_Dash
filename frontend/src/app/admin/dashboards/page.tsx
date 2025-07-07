// ABOUTME: Dashboard template list page for admin panel
// ABOUTME: Displays all dashboard templates with create/edit/delete actions

"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { 
  Search, 
  Plus, 
  MoreHorizontal, 
  Edit, 
  Eye, 
  Trash2,
  LayoutDashboard 
} from "lucide-react"
import { useDashboards } from "@/hooks/use-dashboards"
import { useToast } from "@/hooks/use-toast"

export default function DashboardsPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [searchQuery, setSearchQuery] = useState("")
  const [deleteId, setDeleteId] = useState<string | null>(null)
  
  const { 
    dashboards, 
    isLoading, 
    deleteDashboard 
  } = useDashboards()

  const filteredDashboards = dashboards?.filter(dashboard => 
    dashboard.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    dashboard.category?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const handleDelete = async () => {
    if (!deleteId) return
    
    try {
      await deleteDashboard(deleteId)
      toast({
        title: "Dashboard deleted",
        description: "The dashboard template has been deleted successfully."
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete dashboard. Please try again.",
        variant: "destructive"
      })
    } finally {
      setDeleteId(null)
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Templates</h1>
          <p className="text-muted-foreground mt-2">
            Create and manage dashboard templates for your studies
          </p>
        </div>
        <Button onClick={() => router.push("/admin/dashboards/new")}>
          <Plus className="h-4 w-4 mr-2" />
          Create Dashboard
        </Button>
      </div>

      <Card className="p-4">
        <div className="flex items-center space-x-4 mb-6">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search dashboards..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-8">Loading dashboards...</div>
        ) : filteredDashboards.length === 0 ? (
          <div className="text-center py-12">
            <LayoutDashboard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-4">
              {searchQuery ? "No dashboards found matching your search" : "No dashboard templates yet"}
            </p>
            {!searchQuery && (
              <Button onClick={() => router.push("/admin/dashboards/new")}>
                Create Your First Dashboard
              </Button>
            )}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Studies</TableHead>
                <TableHead>Widgets</TableHead>
                <TableHead>Last Modified</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[100px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDashboards.map((dashboard) => (
                <TableRow key={dashboard.id}>
                  <TableCell className="font-medium">{dashboard.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{dashboard.category || "General"}</Badge>
                  </TableCell>
                  <TableCell>{dashboard.studyCount || 0}</TableCell>
                  <TableCell>{dashboard.widgetCount || 0}</TableCell>
                  <TableCell>
                    {new Date(dashboard.updatedAt).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Badge variant={dashboard.status === "active" ? "success" : "secondary"}>
                      {dashboard.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem 
                          onClick={() => router.push(`/admin/dashboards/${dashboard.id}/preview`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          Preview
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => router.push(`/admin/dashboards/${dashboard.id}/edit`)}
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => setDeleteId(dashboard.id)}
                          className="text-destructive"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Dashboard Template</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this dashboard template? This action cannot be undone.
              All studies using this template will need to select a new dashboard.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}