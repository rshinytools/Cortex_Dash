// ABOUTME: Base widget interface and types for all dashboard widgets
// ABOUTME: Defines common props, data loading interface, and export functionality

import { ReactNode } from 'react';
import { DataContract } from '@/types/widget';

export interface BaseWidgetData {
  lastUpdated?: Date;
  error?: string;
  loading?: boolean;
}

export interface BaseWidgetProps {
  id: string;
  title: string;
  description?: string;
  configuration: Record<string, any>;
  data?: any;
  loading?: boolean;
  error?: string;
  onRefresh?: () => void;
  onExport?: (format: 'png' | 'csv' | 'json') => void;
  className?: string;
  height?: number;
  width?: number;
}

export interface WidgetComponent {
  (props: BaseWidgetProps): ReactNode;
  displayName: string;
  defaultHeight?: number;
  defaultWidth?: number;
  supportedExportFormats?: Array<'png' | 'csv' | 'json'>;
  dataContract?: DataContract;
  validateConfiguration?: (config: Record<string, any>) => boolean;
}

export interface WidgetRegistration {
  type: string;
  component: WidgetComponent;
  name: string;
  description: string;
  icon?: ReactNode;
  category?: string;
  configSchema?: Record<string, any>;
}

export interface WidgetInstance {
  id: string;
  type: string;
  title: string;
  description?: string;
  configuration: Record<string, any>;
  layout: {
    x: number;
    y: number;
    w: number;
    h: number;
    minW?: number;
    minH?: number;
    maxW?: number;
    maxH?: number;
  };
  dataSource?: {
    endpoint?: string;
    query?: string;
    refreshInterval?: number;
  };
}

export interface DashboardConfiguration {
  id: string;
  name: string;
  description?: string;
  widgets: WidgetInstance[];
  layout: {
    cols: number;
    rowHeight: number;
    breakpoints?: Record<string, number>;
    layouts?: Record<string, Array<{
      i: string;
      x: number;
      y: number;
      w: number;
      h: number;
    }>>;
  };
  theme?: {
    primaryColor?: string;
    backgroundColor?: string;
    textColor?: string;
  };
}

// Utility function to export widget as image
export async function exportWidgetAsImage(elementId: string, filename: string): Promise<void> {
  try {
    // Dynamic import to avoid loading html2canvas in SSR
    const html2canvas = (await import('html2canvas')).default;
    
    const element = document.getElementById(elementId);
    if (!element) {
      console.error(`Element with id ${elementId} not found`);
      return;
    }

    const canvas = await html2canvas(element, {
      backgroundColor: '#ffffff',
      scale: 2,
      logging: false,
    });

    // Create download link
    const link = document.createElement('a');
    link.download = filename;
    link.href = canvas.toDataURL('image/png');
    link.click();
  } catch (error) {
    console.error('Error exporting widget as image:', error);
    // Fallback - just log for now
    console.log(`Exporting widget ${elementId} as ${filename} (fallback)`);
  }
}

// Utility function to export widget data as CSV
export function exportWidgetDataAsCSV(data: any[], filename: string): void {
  // Convert data to CSV format
  if (!data || data.length === 0) {
    console.warn('No data to export');
    return;
  }

  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        // Escape values containing commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    )
  ].join('\n');

  // Create and download file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Utility function to export widget data as JSON
export function exportWidgetDataAsJSON(data: any, filename: string): void {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}