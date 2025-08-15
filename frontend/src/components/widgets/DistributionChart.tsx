// ABOUTME: Distribution Chart widget renderer component
// ABOUTME: Supports bar, pie, histogram, box plot, and other distribution visualizations

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Line,
  LabelList,
} from 'recharts';

interface DistributionChartProps {
  data: {
    widget_type: string;
    chart_subtype: string;
    data: {
      labels: string[];
      datasets: Array<{
        label?: string;
        data: number[];
        percentages?: number[];
        type?: string;
        stack?: string;
        yAxisID?: string;
        orientation?: string;
      }>;
    };
    summary?: {
      total: number;
      categories: number;
      max_value: number;
      min_value: number;
      avg_value: number;
      pareto_point?: {
        index: number;
        percentage_items: number;
        percentage_value: number;
      };
    };
    metadata?: {
      last_updated: string;
      aggregation_type: string;
      show_percentage: boolean;
      sorted_by: string;
      sort_order: string;
    };
  };
  config?: {
    title?: string;
    description?: string;
    height?: number;
    showLegend?: boolean;
    showGrid?: boolean;
    showTooltip?: boolean;
    showValues?: boolean;
    showPercentages?: boolean;
    colors?: string[];
    orientation?: 'vertical' | 'horizontal';
  };
}

export const DistributionChart: React.FC<DistributionChartProps> = ({ data, config = {} }) => {
  const {
    title = 'Distribution',
    description,
    height = 300,
    showLegend = true,
    showGrid = true,
    showTooltip = true,
    showValues = false,
    showPercentages = false,
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'],
    orientation = 'vertical',
  } = config;

  // Prepare chart data
  const prepareChartData = () => {
    if (data.chart_subtype === 'pie' || data.chart_subtype === 'donut') {
      // Pie chart data format
      return data.data.labels.map((label, index) => ({
        name: label,
        value: data.data.datasets[0].data[index],
        percentage: data.data.datasets[0].percentages?.[index],
      }));
    } else {
      // Bar chart data format
      const chartData = data.data.labels.map((label, index) => {
        const point: any = { name: label };
        
        data.data.datasets.forEach((dataset) => {
          const key = dataset.label || 'value';
          point[key] = dataset.data[index];
          if (dataset.percentages) {
            point[`${key}_percentage`] = dataset.percentages[index];
          }
        });
        
        return point;
      });
      
      return chartData;
    }
  };

  const chartData = prepareChartData();

  const renderBarChart = () => {
    const isHorizontal = orientation === 'horizontal' || data.chart_subtype === 'horizontal_bar';
    const isStacked = data.chart_subtype === 'stacked_bar';
    const isGrouped = data.chart_subtype === 'grouped_bar';
    
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          layout={isHorizontal ? 'horizontal' : 'vertical'}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
          {isHorizontal ? (
            <>
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={100} />
            </>
          ) : (
            <>
              <XAxis dataKey="name" />
              <YAxis />
            </>
          )}
          {showTooltip && <Tooltip />}
          {showLegend && data.data.datasets.length > 1 && <Legend />}
          
          {data.data.datasets.map((dataset, index) => {
            const key = dataset.label || 'value';
            const color = colors[index % colors.length];
            
            return (
              <Bar
                key={key}
                dataKey={key}
                fill={color}
                stackId={isStacked ? 'stack' : undefined}
                name={dataset.label}
              >
                {showValues && <LabelList dataKey={key} position="top" />}
              </Bar>
            );
          })}
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderPieChart = () => {
    const isDonut = data.chart_subtype === 'donut';
    const radius = isDonut ? { innerRadius: 60, outerRadius: 80 } : { outerRadius: 80 };
    
    return (
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={showValues ? (entry: any) => `${entry.name}: ${entry.value}` : false}
            {...radius}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          {showTooltip && <Tooltip />}
          {showLegend && <Legend />}
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderParetoChart = () => {
    // Pareto chart with bar and line
    return (
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
          <XAxis dataKey="name" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          {showTooltip && <Tooltip />}
          {showLegend && <Legend />}
          
          <Bar yAxisId="left" dataKey="value" fill={colors[0]} name="Value" />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="cumulative_percentage"
            stroke={colors[1]}
            strokeWidth={2}
            dot={{ r: 4 }}
            name="Cumulative %"
          />
        </ComposedChart>
      </ResponsiveContainer>
    );
  };

  const renderHistogram = () => {
    return renderBarChart(); // Histogram uses bar chart with different data
  };

  const renderChart = () => {
    switch (data.chart_subtype) {
      case 'pie':
      case 'donut':
        return renderPieChart();
      case 'pareto':
        return renderParetoChart();
      case 'histogram':
        return renderHistogram();
      default:
        return renderBarChart();
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
        {data.metadata && (
          <div className="flex gap-4 text-xs text-muted-foreground mt-2">
            <span>Type: {data.chart_subtype}</span>
            <span>Aggregation: {data.metadata.aggregation_type}</span>
            {data.metadata.sorted_by && (
              <span>Sorted by: {data.metadata.sorted_by} ({data.metadata.sort_order})</span>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent>
        {renderChart()}
        
        {data.summary && (
          <div className="mt-4 pt-4 border-t">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">Total</div>
                <div className="font-medium">{data.summary.total.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Categories</div>
                <div className="font-medium">{data.summary.categories}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Max</div>
                <div className="font-medium">{data.summary.max_value.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Min</div>
                <div className="font-medium">{data.summary.min_value.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Average</div>
                <div className="font-medium">{data.summary.avg_value.toLocaleString()}</div>
              </div>
            </div>
            
            {data.summary.pareto_point && (
              <div className="mt-3 p-3 bg-muted/50 rounded-lg">
                <div className="text-sm">
                  <span className="font-medium">Pareto Analysis:</span>
                  <span className="ml-2">
                    {data.summary.pareto_point.percentage_items.toFixed(1)}% of items account for{' '}
                    {data.summary.pareto_point.percentage_value.toFixed(1)}% of the value
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};