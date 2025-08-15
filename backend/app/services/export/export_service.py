# ABOUTME: Export service for generating various report formats
# ABOUTME: Supports Excel, PDF, CSV exports with formatting and templates

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import io
import pandas as pd
from enum import Enum

from app.core.logging import logger

class ExportFormat(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"
    HTML = "html"

class ExportService:
    """Service for exporting dashboard and widget data"""
    
    def __init__(self):
        self.export_path = Path("exports")
        self.export_path.mkdir(exist_ok=True)
    
    async def export_dashboard(
        self,
        dashboard_id: str,
        format: ExportFormat,
        include_filters: bool = True,
        include_metadata: bool = True
    ) -> bytes:
        """Export complete dashboard to specified format"""
        
        try:
            # Get dashboard data
            dashboard_data = await self._get_dashboard_data(dashboard_id)
            
            if format == ExportFormat.EXCEL:
                return self._export_to_excel(dashboard_data, include_metadata)
            elif format == ExportFormat.CSV:
                return self._export_to_csv(dashboard_data)
            elif format == ExportFormat.PDF:
                return await self._export_to_pdf(dashboard_data, include_metadata)
            elif format == ExportFormat.JSON:
                return self._export_to_json(dashboard_data)
            elif format == ExportFormat.HTML:
                return self._export_to_html(dashboard_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise e
    
    def _export_to_excel(self, data: Dict[str, Any], include_metadata: bool) -> bytes:
        """Export data to Excel format with multiple sheets"""
        
        import xlsxwriter
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        number_format = workbook.add_format({'num_format': '#,##0.00'})
        
        # Add metadata sheet
        if include_metadata:
            metadata_sheet = workbook.add_worksheet('Metadata')
            metadata_sheet.write(0, 0, 'Export Date', header_format)
            metadata_sheet.write(0, 1, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            metadata_sheet.write(1, 0, 'Dashboard', header_format)
            metadata_sheet.write(1, 1, data.get('dashboard_name', ''))
            metadata_sheet.write(2, 0, 'Study', header_format)
            metadata_sheet.write(2, 1, data.get('study_name', ''))
            metadata_sheet.write(3, 0, 'User', header_format)
            metadata_sheet.write(3, 1, data.get('exported_by', ''))
        
        # Add data sheets for each widget
        for widget in data.get('widgets', []):
            sheet_name = widget['name'][:31]  # Excel limit
            worksheet = workbook.add_worksheet(sheet_name)
            
            if 'dataframe' in widget:
                df = widget['dataframe']
                
                # Write headers
                for col_num, column in enumerate(df.columns):
                    worksheet.write(0, col_num, column, header_format)
                
                # Write data
                for row_num, row_data in enumerate(df.values, 1):
                    for col_num, cell_value in enumerate(row_data):
                        if pd.isna(cell_value):
                            worksheet.write(row_num, col_num, '')
                        elif isinstance(cell_value, (int, float)):
                            worksheet.write_number(row_num, col_num, cell_value, number_format)
                        elif isinstance(cell_value, datetime):
                            worksheet.write_datetime(row_num, col_num, cell_value, date_format)
                        else:
                            worksheet.write(row_num, col_num, str(cell_value))
                
                # Auto-fit columns
                for col_num, column in enumerate(df.columns):
                    max_length = max(
                        df[column].astype(str).str.len().max(),
                        len(column)
                    )
                    worksheet.set_column(col_num, col_num, max_length + 2)
        
        workbook.close()
        output.seek(0)
        
        return output.getvalue()
    
    def _export_to_csv(self, data: Dict[str, Any]) -> bytes:
        """Export data to CSV format"""
        
        output = io.StringIO()
        
        # Combine all widget data
        combined_data = []
        
        for widget in data.get('widgets', []):
            if 'dataframe' in widget:
                df = widget['dataframe']
                df['widget'] = widget['name']
                combined_data.append(df)
        
        if combined_data:
            combined_df = pd.concat(combined_data, ignore_index=True)
            combined_df.to_csv(output, index=False)
        
        return output.getvalue().encode('utf-8')
    
    async def _export_to_pdf(self, data: Dict[str, Any], include_metadata: bool) -> bytes:
        """Export data to PDF format with charts"""
        
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4472C4'),
            spaceAfter=30
        )
        
        elements.append(Paragraph(data.get('dashboard_name', 'Dashboard Export'), title_style))
        elements.append(Spacer(1, 12))
        
        # Metadata
        if include_metadata:
            metadata = [
                ['Export Date:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')],
                ['Study:', data.get('study_name', '')],
                ['Exported By:', data.get('exported_by', '')],
                ['Filter Applied:', 'Yes' if data.get('filters') else 'No']
            ]
            
            metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(metadata_table)
            elements.append(Spacer(1, 20))
        
        # Widget data
        for widget in data.get('widgets', []):
            # Widget title
            elements.append(Paragraph(widget['name'], styles['Heading2']))
            elements.append(Spacer(1, 12))
            
            if 'dataframe' in widget:
                df = widget['dataframe']
                
                # Convert DataFrame to table
                table_data = [df.columns.tolist()]
                for row in df.values:
                    table_data.append([str(cell) if not pd.isna(cell) else '' for cell in row])
                
                # Create table
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(table)
                elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        output.seek(0)
        
        return output.getvalue()
    
    def _export_to_json(self, data: Dict[str, Any]) -> bytes:
        """Export data to JSON format"""
        
        import json
        
        # Convert DataFrames to JSON
        export_data = {
            'metadata': {
                'export_date': datetime.utcnow().isoformat(),
                'dashboard_name': data.get('dashboard_name'),
                'study_name': data.get('study_name'),
                'exported_by': data.get('exported_by')
            },
            'widgets': []
        }
        
        for widget in data.get('widgets', []):
            widget_data = {
                'name': widget['name'],
                'type': widget.get('type'),
                'data': widget['dataframe'].to_dict('records') if 'dataframe' in widget else []
            }
            export_data['widgets'].append(widget_data)
        
        return json.dumps(export_data, indent=2, default=str).encode('utf-8')
    
    def _export_to_html(self, data: Dict[str, Any]) -> bytes:
        """Export data to HTML format"""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #4472C4; }}
                h2 {{ color: #666; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
                th {{ background-color: #4472C4; color: white; padding: 10px; text-align: left; }}
                td {{ border: 1px solid #ddd; padding: 8px; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .metadata {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="metadata">
                <p><strong>Export Date:</strong> {export_date}</p>
                <p><strong>Study:</strong> {study_name}</p>
                <p><strong>Exported By:</strong> {exported_by}</p>
            </div>
            {content}
        </body>
        </html>
        """
        
        content = []
        
        for widget in data.get('widgets', []):
            content.append(f"<h2>{widget['name']}</h2>")
            
            if 'dataframe' in widget:
                df = widget['dataframe']
                content.append(df.to_html(index=False, classes='data-table'))
        
        html = html_template.format(
            title=data.get('dashboard_name', 'Dashboard Export'),
            export_date=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            study_name=data.get('study_name', ''),
            exported_by=data.get('exported_by', ''),
            content='\n'.join(content)
        )
        
        return html.encode('utf-8')
    
    async def _get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard data for export"""
        
        # This would fetch actual dashboard data
        # For now, return example data
        return {
            'dashboard_name': 'Clinical Trial Dashboard',
            'study_name': 'STUDY-001',
            'exported_by': 'System Admin',
            'widgets': [
                {
                    'name': 'Subject Enrollment',
                    'type': 'metric',
                    'dataframe': pd.DataFrame({
                        'Site': ['Site A', 'Site B', 'Site C'],
                        'Enrolled': [25, 30, 20],
                        'Target': [30, 30, 30]
                    })
                },
                {
                    'name': 'Adverse Events',
                    'type': 'table',
                    'dataframe': pd.DataFrame({
                        'Subject': ['001', '002', '003'],
                        'Event': ['Headache', 'Nausea', 'Fatigue'],
                        'Severity': ['Mild', 'Moderate', 'Mild'],
                        'Date': [datetime.now(), datetime.now(), datetime.now()]
                    })
                }
            ]
        }