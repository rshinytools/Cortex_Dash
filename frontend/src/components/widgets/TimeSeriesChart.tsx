// ABOUTME: Time Series Chart widget renderer component
// ABOUTME: Displays temporal data with line/area charts, multiple series, and trends

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Line, Area } from 'recharts';
import {
  LineChart,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { format } from 'date-fns';

interface TimeSeriesChartProps {
  data: {
    widget_type: string;
    chart_type?: 'line' | 'area' | 'step';
    data: {
      labels: string[];
      datasets: Array<{
        label: string;
        data: number[];
        periods?: string[];
        error_bars?: number[];
        moving_average?: number[];
        is_forecast?: boolean[];
        type?: string;
        borderDash?: number[];
      }>;
    };
    summary?: {
      min: number;
      max: number;
      avg: number;
      total: number;
      data_points: number;
    };
    metadata?: {
      last_updated: string;
      time_granularity: string;
      aggregation_type: string;
      is_cumulative: boolean;
    };
  };
  config?: {
    title?: string;
    description?: string;
    height?: number;
    showLegend?: boolean;
    showGrid?: boolean;
    showTooltip?: boolean;
    colors?: string[];
    stacked?: boolean;
    showMovingAverage?: boolean;
    showForecast?: boolean;
    dateFormat?: string;
  };
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({ data, config = {} }) => {
  const {
    title = 'Time Series',
    description,
    height = 300,
    showLegend = true,
    showGrid = true,
    showTooltip = true,
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
    stacked = false,
    showMovingAverage = true,
    showForecast = true,
    dateFormat = 'MMM dd',
  } = config;

  // Transform data for Recharts
  const chartData = data.data.labels.map((label, index) => {
    const point: any = { name: label };
    
    data.data.datasets.forEach((dataset) => {
      const key = dataset.label.replace(/\s+/g, '_');
      point[key] = dataset.data[index];
      
      if (dataset.error_bars && dataset.error_bars[index] !== undefined) {
        point[`${key}_error`] = [
          dataset.data[index] - dataset.error_bars[index],
          dataset.data[index] + dataset.error_bars[index],
        ];
      }
      
      if (dataset.moving_average && showMovingAverage) {
        point[`${key}_ma`] = dataset.moving_average[index];
      }
      
      if (dataset.is_forecast) {
        point[`${key}_forecast`] = dataset.is_forecast[index];
      }
    });
    
    return point;
  });

  const formatXAxisTick = (tickItem: string) => {
    try {
      const date = new Date(tickItem);
      if (!isNaN(date.getTime())) {
        return format(date, dateFormat);
      }
    } catch {
      // Not a date, return as is
    }
    return tickItem;
  };

  const formatTooltipLabel = (value: any) => {
    if (typeof value === 'number') {
      return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    return value;
  };

  const ChartComponent = data.chart_type === 'area' ? AreaChart : LineChart;
  const DataComponent: any = data.chart_type === 'area' ? Area : Line;

  const renderChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <ChartComponent data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
        <XAxis 
          dataKey="name"
          tickFormatter={formatXAxisTick}
          className="text-xs"
        />
        <YAxis 
          className="text-xs"
          tickFormatter={(value) => value.toLocaleString()}
        />
        {showTooltip && (
          <Tooltip
            formatter={formatTooltipLabel}
            labelFormatter={(label) => formatXAxisTick(label)}
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
            }}
          />
        )}
        {showLegend && <Legend />}
        
        {/* Reference lines for average */}
        {data.summary && (
          <ReferenceLine
            y={data.summary.avg}
            stroke="#9ca3af"
            strokeDasharray="5 5"
            label={{ value: `Avg: ${data.summary.avg.toFixed(1)}`, position: 'right' }}
          />
        )}
        
        {/* Main data series */}
        {data.data.datasets.map((dataset, index) => {
          const key = dataset.label.replace(/\s+/g, '_');
          const color = colors[index % colors.length];
          
          return (
            <React.Fragment key={key}>
              <DataComponent
                type="monotone"
                dataKey={key}
                stroke={color}
                fill={color}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
                name={dataset.label}
                stackId={stacked ? 'stack' : undefined}
                strokeDasharray={dataset.borderDash ? dataset.borderDash.join(' ') : undefined}
                fillOpacity={data.chart_type === 'area' ? 0.3 : 0}
              />
              
              {/* Moving average line */}
              {showMovingAverage && dataset.moving_average && (
                <Line
                  type="monotone"
                  dataKey={`${key}_ma`}
                  stroke={color}
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name={`${dataset.label} (MA)`}
                  opacity={0.7}
                />
              )}
            </React.Fragment>
          );
        })}
      </ChartComponent>
    </ResponsiveContainer>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
        {data.metadata && (
          <div className="flex gap-4 text-xs text-muted-foreground mt-2">
            <span>Granularity: {data.metadata.time_granularity}</span>
            <span>Aggregation: {data.metadata.aggregation_type}</span>
            {data.metadata.is_cumulative && <span>Cumulative</span>}
          </div>
        )}
      </CardHeader>
      <CardContent>
        {renderChart()}
        
        {data.summary && (
          <div className="mt-4 pt-4 border-t grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">Min</div>
              <div className="font-medium">{data.summary.min.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Max</div>
              <div className="font-medium">{data.summary.max.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Average</div>
              <div className="font-medium">{data.summary.avg.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Total</div>
              <div className="font-medium">{data.summary.total.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Points</div>
              <div className="font-medium">{data.summary.data_points}</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};