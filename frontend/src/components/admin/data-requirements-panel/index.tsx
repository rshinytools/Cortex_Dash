// ABOUTME: Data requirements panel component for displaying required fields
// ABOUTME: Shows all data fields needed by widgets in the dashboard template

"use client";

import { AlertCircle, Database, FileText } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DataRequirement } from "@/lib/api/dashboard-templates";

interface DataRequirementsPanelProps {
  requirements: DataRequirement[];
}

export function DataRequirementsPanel({ requirements }: DataRequirementsPanelProps) {
  // Group requirements by data source
  const requirementsBySource = requirements.reduce((acc, req) => {
    if (!acc[req.dataSource]) {
      acc[req.dataSource] = [];
    }
    acc[req.dataSource].push(req);
    return acc;
  }, {} as Record<string, DataRequirement[]>);

  const totalRequired = requirements.filter((req) => req.required).length;
  const totalOptional = requirements.filter((req) => !req.required).length;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Total Fields</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{requirements.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Required Fields</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{totalRequired}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Optional Fields</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{totalOptional}</div>
          </CardContent>
        </Card>
      </div>

      {/* Alert if no requirements */}
      {requirements.length === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Flexible Data Configuration</AlertTitle>
          <AlertDescription className="space-y-2">
            <p>
              The widgets in this template use flexible data configuration that will be set up 
              when applying the template to a specific study.
            </p>
            <p>
              Each widget can be configured to use any available dataset and fields from your 
              study data, making the template highly adaptable to different data structures.
            </p>
          </AlertDescription>
        </Alert>
      )}

      {/* Requirements by data source */}
      {Object.entries(requirementsBySource).map(([source, reqs]) => (
        <Card key={source}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              {source === "unknown" ? "Unmapped Fields" : source}
            </CardTitle>
            <CardDescription>
              {reqs.length} fields from this data source
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Required</TableHead>
                  <TableHead>Used By</TableHead>
                  <TableHead>Description</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reqs.map((req) => (
                  <TableRow key={req.id}>
                    <TableCell className="font-medium">{req.fieldName}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{req.fieldType}</Badge>
                    </TableCell>
                    <TableCell>
                      {req.required ? (
                        <Badge variant="destructive">Required</Badge>
                      ) : (
                        <Badge variant="secondary">Optional</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{req.widgetIds.length} widgets</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {req.description || "-"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ))}

      {/* Instructions */}
      <Alert>
        <FileText className="h-4 w-4" />
        <AlertTitle>How Data Configuration Works</AlertTitle>
        <AlertDescription className="mt-2 space-y-2">
          <p>
            This template uses a flexible data mapping approach. When applying the template to a study:
          </p>
          <ul className="ml-4 list-disc space-y-1">
            <li>Each widget can be configured to use any dataset from your study</li>
            <li>You'll select which fields to aggregate, filter, or display</li>
            <li>The same template can work with different data structures</li>
            <li>No predefined field requirements - adapts to your data</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );
}