// ABOUTME: Enrollment map widget for visualizing geographic distribution of study participants
// ABOUTME: Uses simple SVG-based visualization as a placeholder for geographic data

'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2, MapPin } from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { scaleLinear } from 'd3-scale';
import { enrollmentMapDataContract } from './data-contracts';

interface EnrollmentMapConfig {
  mapType: 'world' | 'usa' | 'europe';
  dataField: string;
  locationField: string; // country code or state code
  showMarkers?: boolean;
  showLabels?: boolean;
  colorScale?: {
    min: string;
    max: string;
  };
  markerScale?: number;
  projection?: string;
}

interface MapData {
  [location: string]: {
    value: number;
    label?: string;
    coordinates?: [number, number];
  };
}

export const EnrollmentMap: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as EnrollmentMapConfig;

  const processedData = useMemo(() => {
    if (!data) return {};
    
    const mapData: MapData = {};
    const records = Array.isArray(data) ? data : data?.records || [];
    
    records.forEach((record: any) => {
      const location = record[config.locationField];
      const value = record[config.dataField] || 0;
      
      if (location) {
        mapData[location] = {
          value: typeof value === 'number' ? value : parseInt(value) || 0,
          label: record.label || location,
          coordinates: record.coordinates,
        };
      }
    });
    
    return mapData;
  }, [data, config]);

  const colorScale = useMemo(() => {
    const values = Object.values(processedData).map(d => d.value);
    const minValue = Math.min(...values, 0);
    const maxValue = Math.max(...values, 1);
    
    return scaleLinear<string>()
      .domain([minValue, maxValue])
      .range([config.colorScale?.min || '#e0f2fe', config.colorScale?.max || '#0369a1']);
  }, [processedData, config.colorScale]);

  if (loading) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex flex-col items-center justify-center h-full">
          <AlertCircle className="h-8 w-8 text-destructive mb-2" />
          <p className="text-sm text-muted-foreground text-center">{error}</p>
        </CardContent>
      </Card>
    );
  }

  // TODO: Implement a proper geographic visualization library that supports React 19
  // Options to consider:
  // 1. Leaflet with react-leaflet (interactive maps)
  // 2. D3.js with custom React wrapper (full control)
  // 3. Mapbox GL JS with react-map-gl (advanced features)
  // 4. Wait for react-simple-maps to support React 19
  
  // For now, showing a simple data visualization placeholder
  const sortedData = Object.entries(processedData)
    .sort(([, a], [, b]) => b.value - a.value)
    .slice(0, 10); // Show top 10 locations

  const maxValue = Math.max(...Object.values(processedData).map(d => d.value), 1);

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="pb-2 flex-shrink-0">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 p-4">
        <div className="h-full flex flex-col">
          {/* Placeholder Map Visualization */}
          <div className="flex-1 bg-muted/20 rounded-lg border border-border p-4 flex flex-col items-center justify-center">
            <MapPin className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-sm text-muted-foreground text-center mb-4">
              Geographic visualization temporarily unavailable
            </p>
            
            {/* Show data as a simple bar chart instead */}
            {sortedData.length > 0 && (
              <div className="w-full max-w-md">
                <h4 className="text-sm font-medium mb-2">Top Locations by {config.dataField}</h4>
                <div className="space-y-2">
                  {sortedData.map(([location, data]) => {
                    const percentage = (data.value / maxValue) * 100;
                    return (
                      <div key={location} className="flex items-center gap-2">
                        <span className="text-xs font-medium w-16 text-right">
                          {data.label || location}
                        </span>
                        <div className="flex-1 bg-muted rounded-full h-4 relative overflow-hidden">
                          <div
                            className="absolute inset-y-0 left-0 bg-primary transition-all duration-300"
                            style={{
                              width: `${percentage}%`,
                              backgroundColor: colorScale(data.value),
                            }}
                          />
                        </div>
                        <span className="text-xs font-medium w-12 text-left">
                          {data.value}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
          
          {/* Legend */}
          <div className="mt-4 flex items-center justify-center gap-4">
            <div className="flex items-center gap-2 text-xs">
              <div 
                className="w-4 h-4 rounded"
                style={{ backgroundColor: config.colorScale?.min || '#e0f2fe' }}
              />
              <span>Low</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div 
                className="w-4 h-4 rounded"
                style={{ backgroundColor: config.colorScale?.max || '#0369a1' }}
              />
              <span>High</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

EnrollmentMap.displayName = 'EnrollmentMap';
EnrollmentMap.defaultHeight = 5;
EnrollmentMap.defaultWidth = 8;
EnrollmentMap.supportedExportFormats = ['png', 'json'];
EnrollmentMap.dataContract = enrollmentMapDataContract;
EnrollmentMap.validateConfiguration = (config: Record<string, any>) => {
  return config.mapType && config.dataField && config.locationField;
};