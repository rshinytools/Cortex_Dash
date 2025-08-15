// ABOUTME: Pipeline Configuration page for data transformation workflows
// ABOUTME: Manages ETL pipelines, SDTM/ADaM mapping, and validation rules

'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { UserMenu } from '@/components/user-menu';
import { 
  Database,
  GitBranch,
  PlayCircle,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  FileCode,
  Activity
} from 'lucide-react';

export default function PipelineConfigPage() {
  const router = useRouter();

  return (
    <div className="container mx-auto py-6">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Pipeline Configuration</h1>
            <p className="text-muted-foreground">
              Data transformation workflows with flexible mapping and validation
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <UserMenu />
            <Button onClick={() => router.push('/admin')}>
              Back to Admin
            </Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Pipelines</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">Running workflows</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Transformations</CardTitle>
              <GitBranch className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">Configured rules</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Last Run</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">Never</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">No data</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Data Source Mapping</CardTitle>
              <CardDescription>
                Map source data fields to target schema
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Mapping Coverage</span>
                  <span className="text-muted-foreground">0%</span>
                </div>
                <Progress value={0} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Data Categories</h4>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">Demographics</Badge>
                  <Badge variant="outline">Clinical Events</Badge>
                  <Badge variant="outline">Laboratory Results</Badge>
                  <Badge variant="outline">Medications</Badge>
                  <Badge variant="outline">Vital Signs</Badge>
                  <Badge variant="outline">Custom Fields</Badge>
                </div>
              </div>
              
              <Button variant="outline" className="w-full">
                <FileCode className="h-4 w-4 mr-2" />
                Configure Field Mapping
              </Button>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Analysis Datasets</CardTitle>
              <CardDescription>
                Create derived datasets for analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Dataset Creation</span>
                  <span className="text-muted-foreground">0%</span>
                </div>
                <Progress value={0} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Dataset Types</h4>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">Subject Level</Badge>
                  <Badge variant="outline">Event Level</Badge>
                  <Badge variant="outline">Visit Level</Badge>
                  <Badge variant="outline">Time Series</Badge>
                  <Badge variant="outline">Aggregated</Badge>
                </div>
              </div>
              
              <Button variant="outline" className="w-full">
                <Database className="h-4 w-4 mr-2" />
                Configure Datasets
              </Button>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Pipeline Stages</CardTitle>
            <CardDescription>
              Data transformation workflow stages
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <FileCode className="h-5 w-5 text-primary" />
                  </div>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold">1. Data Ingestion</h4>
                  <p className="text-sm text-muted-foreground">
                    Load raw data from various sources (CSV, Excel, SAS, APIs)
                  </p>
                </div>
                <Badge variant="secondary">Configured</Badge>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <AlertCircle className="h-5 w-5 text-primary" />
                  </div>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold">2. Data Validation</h4>
                  <p className="text-sm text-muted-foreground">
                    Quality checks, completeness validation, and anomaly detection
                  </p>
                </div>
                <Badge variant="secondary">Configured</Badge>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <GitBranch className="h-5 w-5 text-primary" />
                  </div>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold">3. Transformation</h4>
                  <p className="text-sm text-muted-foreground">
                    Apply mapping rules, calculate derived variables, normalize formats
                  </p>
                </div>
                <Badge variant="secondary">Configured</Badge>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <Database className="h-5 w-5 text-primary" />
                  </div>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold">4. Output Generation</h4>
                  <p className="text-sm text-muted-foreground">
                    Create structured datasets and custom outputs based on study requirements
                  </p>
                </div>
                <Badge variant="secondary">Configured</Badge>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <CheckCircle className="h-5 w-5 text-primary" />
                  </div>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold">5. Quality Control</h4>
                  <p className="text-sm text-muted-foreground">
                    Final validation, compliance checks, and audit trail generation
                  </p>
                </div>
                <Badge variant="secondary">Configured</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Validation Rules</CardTitle>
              <CardDescription>
                Data quality and compliance checks
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>Required field validation</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>Data type consistency checks</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>Range and boundary validation</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>Cross-domain relationship checks</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>Data standard compliance (configurable)</span>
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>Custom business rules</span>
                </li>
              </ul>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>
                Pipeline execution statistics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Average Processing Time</span>
                  <Badge variant="outline">- min</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Records Processed</span>
                  <Badge variant="outline">-</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Error Rate</span>
                  <Badge variant="outline">-%</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Cache Hit Rate</span>
                  <Badge variant="outline">-%</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Parallel Execution</span>
                  <Badge variant="secondary">Enabled</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}