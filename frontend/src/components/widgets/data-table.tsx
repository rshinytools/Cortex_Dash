// ABOUTME: Data table widget for displaying tabular data with sorting and filtering
// ABOUTME: Uses tanstack table with pagination and export functionality

'use client';

import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AlertCircle, Loader2, ChevronLeft, ChevronRight, Search, Download } from 'lucide-react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  useReactTable,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { tableDataContract } from './data-contracts';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface DataTableConfig {
  columns: Array<{
    field: string;
    header: string;
    type?: 'text' | 'number' | 'date' | 'boolean';
    format?: string;
    width?: number;
    align?: 'left' | 'center' | 'right';
    sortable?: boolean;
    filterable?: boolean;
  }>;
  pageSize?: number;
  showPagination?: boolean;
  showSearch?: boolean;
  showExport?: boolean;
  striped?: boolean;
  compact?: boolean;
  maxHeight?: number;
}

const formatCellValue = (value: any, type?: string, format?: string): string => {
  if (value === null || value === undefined) return '-';

  switch (type) {
    case 'number':
      if (format === 'percentage') {
        return `${(value * 100).toFixed(2)}%`;
      }
      if (format === 'currency') {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(value);
      }
      return new Intl.NumberFormat('en-US').format(value);
    
    case 'date':
      const date = new Date(value);
      if (isNaN(date.getTime())) return value;
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    
    case 'boolean':
      return value ? 'Yes' : 'No';
    
    default:
      return String(value);
  }
};

export const DataTable: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  onExport,
  className
}) => {
  const config = configuration as DataTableConfig;
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const tableData = useMemo(() => {
    if (Array.isArray(data)) return data;
    if (data?.records && Array.isArray(data.records)) return data.records;
    return [];
  }, [data]);

  const columns = useMemo<ColumnDef<any>[]>(() => {
    return config.columns.map(col => ({
      id: col.field,
      accessorKey: col.field,
      header: col.header,
      size: col.width,
      enableSorting: col.sortable !== false,
      enableColumnFilter: col.filterable !== false,
      cell: ({ getValue }) => {
        const value = getValue();
        return (
          <div className={cn('text-sm', {
            'text-left': col.align === 'left' || !col.align,
            'text-center': col.align === 'center',
            'text-right': col.align === 'right',
          })}>
            {formatCellValue(value, col.type, col.format)}
          </div>
        );
      },
    }));
  }, [config.columns]);

  const table = useReactTable({
    data: tableData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: config.showPagination !== false ? getPaginationRowModel() : undefined,
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: 'includesString',
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    initialState: {
      pagination: {
        pageSize: config.pageSize || 10,
      },
    },
  });

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

  if (!tableData || tableData.length === 0) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-base">{title}</CardTitle>
            {description && (
              <CardDescription className="text-xs mt-1">{description}</CardDescription>
            )}
          </div>
          {config.showExport !== false && onExport && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onExport('csv')}
              className="ml-2"
            >
              <Download className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-0">
        {config.showSearch !== false && (
          <div className="px-6 pb-3">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search..."
                value={globalFilter}
                onChange={(e) => setGlobalFilter(e.target.value)}
                className="pl-8 h-9"
              />
            </div>
          </div>
        )}

        <div className={cn("flex-1 overflow-auto px-6", {
          [`max-h-[${config.maxHeight}px]`]: config.maxHeight,
        })}>
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead
                      key={header.id}
                      className={cn("text-xs font-medium", {
                        'cursor-pointer select-none': header.column.getCanSort(),
                      })}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center gap-1">
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                        {header.column.getCanSort() && (
                          <span className="text-muted-foreground">
                            {{
                              asc: ' ↑',
                              desc: ' ↓',
                            }[header.column.getIsSorted() as string] ?? ''}
                          </span>
                        )}
                      </div>
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.map((row, index) => (
                <TableRow
                  key={row.id}
                  className={cn({
                    'bg-muted/50': config.striped && index % 2 === 1,
                  })}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell
                      key={cell.id}
                      className={cn('text-sm', {
                        'py-2': config.compact,
                        'py-3': !config.compact,
                      })}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {config.showPagination !== false && (
          <div className="flex items-center justify-between px-6 py-3 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
              {Math.min(
                (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                tableData.length
              )}{' '}
              of {tableData.length} entries
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

DataTable.displayName = 'DataTable';
DataTable.defaultHeight = 6;
DataTable.defaultWidth = 8;
DataTable.supportedExportFormats = ['csv', 'json'];
DataTable.dataContract = tableDataContract;
DataTable.validateConfiguration = (config: Record<string, any>) => {
  return config.columns?.length > 0;
};