// ABOUTME: Widget Engines page showing the actual widget implementation we built
// ABOUTME: Based on WIDGET_ARCHITECTURE_IMPLEMENTATION.md with 5 core widget types

'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { UserMenu } from '@/components/user-menu';
import { motion } from 'framer-motion';
import { 
  BarChart3,
  LineChart,
  PieChart,
  Table2,
  Clock,
  Cpu,
  Database,
  GitBranch,
  Zap,
  Settings,
  CheckCircle,
  ArrowRight,
  Layers,
  Activity
} from 'lucide-react';

const widgetEngines = [
  {
    name: 'KPI Metric Card',
    type: 'kpi_card',
    description: 'Display key performance indicators with comparisons and trends',
    features: [
      'Aggregation logic',
      'Comparison calculations',
      'Trend indicators',
      'Configurable thresholds'
    ],
    icon: BarChart3,
    status: 'active',
    color: 'from-blue-500 to-cyan-500',
    dataContract: {
      required: ['value_field'],
      optional: ['comparison_field', 'target_field'],
      aggregations: ['SUM', 'AVG', 'COUNT', 'MIN', 'MAX']
    }
  },
  {
    name: 'Time Series Chart',
    type: 'time_series',
    description: 'Visualize data trends over time with flexible time ranges',
    features: [
      'Multi-series support',
      'Date range filtering',
      'Real-time updates',
      'Customizable axes'
    ],
    icon: LineChart,
    status: 'active',
    color: 'from-purple-500 to-pink-500',
    dataContract: {
      required: ['date_field', 'value_field'],
      optional: ['series_field', 'filter_field'],
      aggregations: ['SUM', 'AVG', 'COUNT']
    }
  },
  {
    name: 'Distribution Chart',
    type: 'distribution',
    description: 'Show data distribution with pie, donut, or bar charts',
    features: [
      'Multiple chart types',
      'Dynamic legends',
      'Percentage calculations',
      'Color customization'
    ],
    icon: PieChart,
    status: 'active',
    color: 'from-green-500 to-emerald-500',
    dataContract: {
      required: ['category_field', 'value_field'],
      optional: ['filter_field'],
      aggregations: ['COUNT', 'SUM', 'DISTINCT']
    }
  },
  {
    name: 'Data Table',
    type: 'data_table',
    description: 'Tabular display with sorting, filtering, and pagination',
    features: [
      'Column sorting',
      'Advanced filtering',
      'Pagination support',
      'Export capabilities'
    ],
    icon: Table2,
    status: 'active',
    color: 'from-orange-500 to-red-500',
    dataContract: {
      required: ['display_fields'],
      optional: ['sort_field', 'filter_fields'],
      aggregations: ['NONE', 'GROUP_BY']
    }
  },
  {
    name: 'Real-time Metric',
    type: 'realtime_metric',
    description: 'Live updating metrics with WebSocket support',
    features: [
      'WebSocket connection',
      'Auto-refresh',
      'Alert thresholds',
      'Historical comparison'
    ],
    icon: Activity,
    status: 'beta',
    color: 'from-indigo-500 to-purple-500',
    dataContract: {
      required: ['metric_field', 'websocket_endpoint'],
      optional: ['alert_threshold', 'comparison_period'],
      aggregations: ['LATEST', 'AVG', 'MAX']
    }
  }
];

export default function WidgetEnginesPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-8"
        >
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
            <Button
              variant="link"
              className="p-0 h-auto font-normal"
              onClick={() => router.push('/admin')}
            >
              Admin
            </Button>
            <span>/</span>
            <span className="text-foreground">Widget Engines</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 dark:from-cyan-400 dark:to-blue-400 bg-clip-text text-transparent">
                Widget Engines
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Core widget types with data contracts and mapping capabilities
              </p>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <UserMenu />
            </div>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="grid gap-6 md:grid-cols-4 mb-8"
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Engines</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">5</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Core widget types</p>
                </div>
                <div className="h-12 w-12 bg-cyan-100 dark:bg-cyan-900/20 rounded-lg flex items-center justify-center">
                  <Cpu className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Data Contracts</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">Active</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Schema validation</p>
                </div>
                <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <Database className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Processing</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">Real-time</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Live transformation</p>
                </div>
                <div className="h-12 w-12 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg flex items-center justify-center">
                  <Zap className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Mapping Engine</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">Ready</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Semantic mapping</p>
                </div>
                <div className="h-12 w-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <GitBranch className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Widget Engines Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8"
        >
          {widgetEngines.map((engine, index) => {
            const Icon = engine.icon;
            return (
              <motion.div
                key={engine.type}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-all hover:scale-105">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`p-3 bg-gradient-to-br ${engine.color} rounded-lg shadow-lg`}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <Badge 
                        variant={engine.status === 'active' ? 'default' : 'secondary'}
                        className={engine.status === 'active' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
                          : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                        }
                      >
                        {engine.status}
                      </Badge>
                    </div>
                    <CardTitle className="text-lg text-gray-900 dark:text-gray-100">{engine.name}</CardTitle>
                    <CardDescription className="text-gray-600 dark:text-gray-400">
                      {engine.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold mb-2 text-gray-900 dark:text-gray-100">Features</h4>
                      <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                        {engine.features.slice(0, 3).map((feature, idx) => (
                          <li key={idx} className="flex items-center gap-2">
                            <CheckCircle className="h-3 w-3 text-green-500" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                      <div className="flex flex-wrap gap-1">
                        {engine.dataContract.aggregations.slice(0, 3).map((agg) => (
                          <Badge 
                            key={agg} 
                            variant="outline" 
                            className="text-xs bg-gray-50 dark:bg-gray-700/50 border-gray-300 dark:border-gray-600"
                          >
                            {agg}
                          </Badge>
                        ))}
                        {engine.dataContract.aggregations.length > 3 && (
                          <Badge 
                            variant="outline" 
                            className="text-xs bg-gray-50 dark:bg-gray-700/50 border-gray-300 dark:border-gray-600"
                          >
                            +{engine.dataContract.aggregations.length - 3}
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    <Button 
                      className="w-full bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white"
                      size="sm"
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      Configure
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Architecture Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
              <CardTitle className="text-xl text-gray-900 dark:text-gray-100">Widget Architecture Overview</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400">
                Based on WIDGET_ARCHITECTURE_IMPLEMENTATION.md
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid gap-6 md:grid-cols-3">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg">
                  <h3 className="font-semibold mb-3 text-blue-900 dark:text-blue-100 flex items-center gap-2">
                    <Layers className="h-4 w-4" />
                    Core Principles
                  </h3>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                      Data Source Agnostic
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                      Semantic Mapping
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                      Reusable Templates
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                      Smart Caching
                    </li>
                  </ul>
                </div>
                
                <div className="p-4 bg-purple-50 dark:bg-purple-900/10 rounded-lg">
                  <h3 className="font-semibold mb-3 text-purple-900 dark:text-purple-100 flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Implementation Status
                  </h3>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-3 w-3 text-green-500" />
                      Foundation Layer
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-3 w-3 text-green-500" />
                      Data Mapping Engine
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-3 w-3 text-green-500" />
                      Calculation Engine
                    </li>
                    <li className="flex items-center gap-2">
                      <Clock className="h-3 w-3 text-yellow-500" />
                      Performance Optimization
                    </li>
                  </ul>
                </div>

                <div className="p-4 bg-green-50 dark:bg-green-900/10 rounded-lg">
                  <h3 className="font-semibold mb-3 text-green-900 dark:text-green-100 flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    Data Flow Pipeline
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <ArrowRight className="h-3 w-3 text-green-500" />
                      EDC Data Input
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <ArrowRight className="h-3 w-3 text-green-500" />
                      Metadata Extraction
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <ArrowRight className="h-3 w-3 text-green-500" />
                      Semantic Mapping
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <ArrowRight className="h-3 w-3 text-green-500" />
                      Widget Rendering
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}