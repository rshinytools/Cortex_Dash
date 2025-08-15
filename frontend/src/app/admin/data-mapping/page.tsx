// ABOUTME: Data Mapping Engine page for semantic field mapping
// ABOUTME: Maps EDC data to widget requirements using intelligent mapping

'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { UserMenu } from '@/components/user-menu';
import { 
  GitBranch,
  Database,
  FileUp,
  Link2,
  Cpu,
  CheckCircle,
  AlertCircle,
  ArrowRight
} from 'lucide-react';

export default function DataMappingPage() {
  const router = useRouter();

  return (
    <div className="container mx-auto py-6">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Data Mapping Engine</h1>
            <p className="text-muted-foreground">
              Intelligent semantic mapping between EDC data and widget requirements
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
              <CardTitle className="text-sm font-medium">Active Mappings</CardTitle>
              <GitBranch className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">Study data mappings</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Datasets</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">Connected sources</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Templates</CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">Reusable mappings</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Validation</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">Active</div>
              <p className="text-xs text-muted-foreground">Schema validation</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Mapping Process</CardTitle>
            <CardDescription>
              How data flows from EDC sources to dashboard widgets
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between space-x-4">
              <div className="flex-1 text-center">
                <div className="mx-auto mb-2 h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <FileUp className="h-6 w-6 text-primary" />
                </div>
                <p className="text-sm font-medium">Data Upload</p>
                <p className="text-xs text-muted-foreground">
                  CSV, Excel, SAS7BDAT
                </p>
              </div>
              
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
              
              <div className="flex-1 text-center">
                <div className="mx-auto mb-2 h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <Database className="h-6 w-6 text-primary" />
                </div>
                <p className="text-sm font-medium">Metadata Extraction</p>
                <p className="text-xs text-muted-foreground">
                  Column analysis & types
                </p>
              </div>
              
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
              
              <div className="flex-1 text-center">
                <div className="mx-auto mb-2 h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <Link2 className="h-6 w-6 text-primary" />
                </div>
                <p className="text-sm font-medium">Semantic Mapping</p>
                <p className="text-xs text-muted-foreground">
                  Field connections
                </p>
              </div>
              
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
              
              <div className="flex-1 text-center">
                <div className="mx-auto mb-2 h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <CheckCircle className="h-6 w-6 text-primary" />
                </div>
                <p className="text-sm font-medium">Validation</p>
                <p className="text-xs text-muted-foreground">
                  Type & quality checks
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Supported Data Sources</CardTitle>
              <CardDescription>
                File formats and API integrations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold mb-2">File Formats</h4>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">CSV</Badge>
                    <Badge variant="secondary">Excel (XLSX)</Badge>
                    <Badge variant="secondary">SAS7BDAT</Badge>
                    <Badge variant="secondary">Parquet</Badge>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-semibold mb-2">API Integrations</h4>
                  <div className="flex flex-wrap gap-2">
                    <Badge>Medidata Rave</Badge>
                    <Badge>Veeva Vault</Badge>
                    <Badge>RESTful APIs</Badge>
                    <Badge>SFTP Sources</Badge>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-semibold mb-2">Clinical Standards</h4>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">CDISC SDTM</Badge>
                    <Badge variant="outline">ADaM</Badge>
                    <Badge variant="outline">SEND</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Mapping Features</CardTitle>
              <CardDescription>
                Advanced capabilities for data transformation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                  <span>Visual drag-and-drop field mapping interface</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                  <span>Automatic pattern recognition for common fields</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                  <span>Multi-dataset JOIN support with key matching</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                  <span>Calculated fields with expression builder</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                  <span>Data quality validation and fix suggestions</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                  <span>Reusable mapping templates across studies</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                  <span>Real-time preview with sample data</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Query Generation Engine</CardTitle>
            <CardDescription>
              Automatic SQL generation from mappings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <h4 className="text-sm font-semibold mb-2">SQL Components</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• SELECT clause generation</li>
                  <li>• JOIN logic for datasets</li>
                  <li>• WHERE clause filters</li>
                  <li>• GROUP BY aggregations</li>
                  <li>• Subquery support</li>
                </ul>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold mb-2">Optimization</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Query plan analysis</li>
                  <li>• Index recommendations</li>
                  <li>• Batch processing</li>
                  <li>• Parallel execution</li>
                  <li>• Result caching</li>
                </ul>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold mb-2">Validation</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Type compatibility</li>
                  <li>• Required field checks</li>
                  <li>• Relationship validation</li>
                  <li>• Data quality rules</li>
                  <li>• Custom validators</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}