// ABOUTME: Patient timeline widget for visualizing clinical events over time
// ABOUTME: Displays visits, treatments, adverse events, and other milestones chronologically

'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2, Calendar, Pill, Heart, Activity, FileText, AlertTriangle } from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { format, parseISO } from 'date-fns';

interface PatientTimelineConfig {
  dateField: string;
  eventTypeField: string;
  eventDescriptionField?: string;
  patientIdField?: string;
  severityField?: string;
  categoryField?: string;
  displayType?: 'vertical' | 'horizontal' | 'gantt';
  groupByPatient?: boolean;
  eventTypes?: {
    [key: string]: {
      label: string;
      color: string;
      icon?: 'calendar' | 'pill' | 'heart' | 'activity' | 'file' | 'alert';
    };
  };
  dateFormat?: string;
  showEventDetails?: boolean;
  showLegend?: boolean;
  maxEventsPerPatient?: number;
  sortOrder?: 'asc' | 'desc';
  highlightSevere?: boolean;
  severityThreshold?: string | number;
  compactMode?: boolean;
}

const defaultEventTypes = {
  visit: { label: 'Visit', color: '#3b82f6', icon: 'calendar' as const },
  treatment: { label: 'Treatment', color: '#10b981', icon: 'pill' as const },
  ae: { label: 'Adverse Event', color: '#f59e0b', icon: 'alert' as const },
  lab: { label: 'Lab Test', color: '#8b5cf6', icon: 'activity' as const },
  assessment: { label: 'Assessment', color: '#ec4899', icon: 'file' as const },
  vital: { label: 'Vital Signs', color: '#14b8a6', icon: 'heart' as const },
};

const getEventIcon = (iconType?: string) => {
  switch (iconType) {
    case 'calendar':
      return Calendar;
    case 'pill':
      return Pill;
    case 'heart':
      return Heart;
    case 'activity':
      return Activity;
    case 'file':
      return FileText;
    case 'alert':
      return AlertTriangle;
    default:
      return Calendar;
  }
};

const TimelineEvent: React.FC<{
  event: any;
  config: PatientTimelineConfig;
  isLast: boolean;
}> = ({ event, config, isLast }) => {
  const eventType = event[config.eventTypeField];
  const eventConfig = config.eventTypes?.[eventType] || defaultEventTypes[eventType] || {
    label: eventType,
    color: '#666',
    icon: 'calendar'
  };
  
  const Icon = getEventIcon(eventConfig.icon);
  const isSevere = config.highlightSevere && config.severityField && 
    event[config.severityField] >= (config.severityThreshold || 3);
  
  const eventDate = parseISO(event[config.dateField]);
  const formattedDate = format(eventDate, config.dateFormat || 'MMM dd, yyyy');
  
  return (
    <div className="flex gap-4 pb-8 relative">
      {/* Timeline line */}
      {!isLast && (
        <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-border" />
      )}
      
      {/* Event icon */}
      <div 
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center z-10",
          isSevere ? "bg-red-100 ring-2 ring-red-500" : "bg-background ring-2 ring-border"
        )}
        style={{ 
          backgroundColor: isSevere ? undefined : `${eventConfig.color}20`,
          borderColor: eventConfig.color 
        }}
      >
        <Icon 
          className="h-4 w-4" 
          style={{ color: isSevere ? '#ef4444' : eventConfig.color }}
        />
      </div>
      
      {/* Event content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span 
                className="text-sm font-medium"
                style={{ color: isSevere ? '#ef4444' : eventConfig.color }}
              >
                {eventConfig.label}
              </span>
              {isSevere && (
                <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                  Severe
                </span>
              )}
            </div>
            {config.showEventDetails !== false && event[config.eventDescriptionField || 'description'] && (
              <p className="text-sm text-muted-foreground mt-1">
                {event[config.eventDescriptionField || 'description']}
              </p>
            )}
            {config.categoryField && event[config.categoryField] && (
              <p className="text-xs text-muted-foreground mt-1">
                Category: {event[config.categoryField]}
              </p>
            )}
          </div>
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {formattedDate}
          </span>
        </div>
      </div>
    </div>
  );
};

const CompactTimelineEvent: React.FC<{
  event: any;
  config: PatientTimelineConfig;
}> = ({ event, config }) => {
  const eventType = event[config.eventTypeField];
  const eventConfig = config.eventTypes?.[eventType] || defaultEventTypes[eventType] || {
    label: eventType,
    color: '#666',
    icon: 'calendar'
  };
  
  const Icon = getEventIcon(eventConfig.icon);
  const eventDate = parseISO(event[config.dateField]);
  const formattedDate = format(eventDate, 'MMM dd');
  
  return (
    <div className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-muted/50 transition-colors">
      <Icon 
        className="h-3 w-3 flex-shrink-0" 
        style={{ color: eventConfig.color }}
      />
      <span className="text-xs font-medium flex-shrink-0" style={{ color: eventConfig.color }}>
        {eventConfig.label}
      </span>
      <span className="text-xs text-muted-foreground truncate flex-1">
        {event[config.eventDescriptionField || 'description'] || ''}
      </span>
      <span className="text-xs text-muted-foreground flex-shrink-0">
        {formattedDate}
      </span>
    </div>
  );
};

const HorizontalTimeline: React.FC<{
  events: any[];
  config: PatientTimelineConfig;
}> = ({ events, config }) => {
  // Group events by date for horizontal display
  const eventsByDate = useMemo(() => {
    const grouped = new Map<string, any[]>();
    events.forEach(event => {
      const date = format(parseISO(event[config.dateField]), 'yyyy-MM-dd');
      if (!grouped.has(date)) {
        grouped.set(date, []);
      }
      grouped.get(date)!.push(event);
    });
    return Array.from(grouped.entries()).sort(([a], [b]) => 
      config.sortOrder === 'desc' ? b.localeCompare(a) : a.localeCompare(b)
    );
  }, [events, config]);
  
  return (
    <div className="overflow-x-auto">
      <div className="min-w-[600px]">
        {/* Timeline header */}
        <div className="flex border-b pb-2 mb-4">
          {eventsByDate.map(([date, _], index) => (
            <div key={date} className="flex-1 text-center">
              <span className="text-xs text-muted-foreground">
                {format(parseISO(date), 'MMM dd')}
              </span>
            </div>
          ))}
        </div>
        
        {/* Timeline events */}
        <div className="relative">
          {/* Horizontal line */}
          <div className="absolute top-4 left-0 right-0 h-0.5 bg-border" />
          
          {/* Events */}
          <div className="flex">
            {eventsByDate.map(([date, dateEvents], index) => (
              <div key={date} className="flex-1 flex flex-col items-center">
                <div className="w-2 h-2 bg-border rounded-full mb-4" />
                <div className="space-y-1">
                  {dateEvents.map((event, eventIndex) => {
                    const eventType = event[config.eventTypeField];
                    const eventConfig = config.eventTypes?.[eventType] || 
                      defaultEventTypes[eventType] || {
                        label: eventType,
                        color: '#666',
                        icon: 'calendar'
                      };
                    const Icon = getEventIcon(eventConfig.icon);
                    
                    return (
                      <div
                        key={eventIndex}
                        className="flex items-center gap-1 px-2 py-1 bg-background border rounded text-xs"
                        style={{ borderColor: eventConfig.color }}
                      >
                        <Icon className="h-3 w-3" style={{ color: eventConfig.color }} />
                        <span>{eventConfig.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export const PatientTimeline: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as PatientTimelineConfig;

  const processedData = useMemo(() => {
    if (!data) return { events: [], patients: [] };
    
    const records = Array.isArray(data) ? data : data?.records || [];
    
    // Filter and sort events
    let events = records.filter(r => r[config.dateField] && r[config.eventTypeField]);
    
    // Sort by date
    events.sort((a, b) => {
      const dateA = new Date(a[config.dateField]).getTime();
      const dateB = new Date(b[config.dateField]).getTime();
      return config.sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
    });
    
    // Group by patient if requested
    let patients: string[] = [];
    if (config.groupByPatient && config.patientIdField) {
      patients = [...new Set(events.map(e => e[config.patientIdField!]))];
      
      // Limit events per patient if specified
      if (config.maxEventsPerPatient) {
        const eventsByPatient = new Map<string, any[]>();
        events.forEach(event => {
          const patientId = event[config.patientIdField!];
          if (!eventsByPatient.has(patientId)) {
            eventsByPatient.set(patientId, []);
          }
          const patientEvents = eventsByPatient.get(patientId)!;
          if (patientEvents.length < config.maxEventsPerPatient) {
            patientEvents.push(event);
          }
        });
        events = Array.from(eventsByPatient.values()).flat();
      }
    }
    
    return { events, patients };
  }, [data, config]);

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

  const { events, patients } = processedData;

  if (!events || events.length === 0) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No events available</p>
        </CardContent>
      </Card>
    );
  }

  const displayType = config.displayType || 'vertical';

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="pb-2 flex-shrink-0">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 overflow-auto">
        {/* Legend */}
        {config.showLegend !== false && (
          <div className="flex flex-wrap gap-4 mb-4 pb-4 border-b">
            {Object.entries(config.eventTypes || defaultEventTypes).map(([key, eventType]) => {
              const Icon = getEventIcon(eventType.icon);
              return (
                <div key={key} className="flex items-center gap-2">
                  <Icon className="h-4 w-4" style={{ color: eventType.color }} />
                  <span className="text-xs text-muted-foreground">{eventType.label}</span>
                </div>
              );
            })}
          </div>
        )}

        {/* Timeline display */}
        {displayType === 'vertical' && !config.groupByPatient && (
          <div className="space-y-0">
            {config.compactMode ? (
              <div className="space-y-0.5">
                {events.map((event, index) => (
                  <CompactTimelineEvent
                    key={index}
                    event={event}
                    config={config}
                  />
                ))}
              </div>
            ) : (
              events.map((event, index) => (
                <TimelineEvent
                  key={index}
                  event={event}
                  config={config}
                  isLast={index === events.length - 1}
                />
              ))
            )}
          </div>
        )}

        {displayType === 'vertical' && config.groupByPatient && (
          <div className="space-y-6">
            {patients.map(patientId => {
              const patientEvents = events.filter(e => e[config.patientIdField!] === patientId);
              return (
                <div key={patientId} className="space-y-0">
                  <h4 className="font-medium text-sm mb-4">Patient: {patientId}</h4>
                  {patientEvents.map((event, index) => (
                    <TimelineEvent
                      key={index}
                      event={event}
                      config={config}
                      isLast={index === patientEvents.length - 1}
                    />
                  ))}
                </div>
              );
            })}
          </div>
        )}

        {displayType === 'horizontal' && (
          <HorizontalTimeline events={events} config={config} />
        )}
      </CardContent>
    </Card>
  );
};

PatientTimeline.displayName = 'PatientTimeline';
PatientTimeline.defaultHeight = 6;
PatientTimeline.defaultWidth = 8;
PatientTimeline.supportedExportFormats = ['png', 'json', 'csv'];
PatientTimeline.validateConfiguration = (config: Record<string, any>) => {
  return config.dateField && config.eventTypeField;
};