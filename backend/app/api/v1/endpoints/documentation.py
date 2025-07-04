# ABOUTME: API endpoints for serving markdown documentation
# ABOUTME: Provides web access to API documentation files

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
import markdown
import os

router = APIRouter()

# Documentation base path
DOCS_BASE_PATH = Path(__file__).parent.parent.parent.parent.parent / "docs" / "api-documentation"

@router.get("/", response_class=HTMLResponse)
async def get_documentation_index():
    """
    Get documentation index page
    """
    index_path = DOCS_BASE_PATH / "README.md"
    
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Documentation index not found")
    
    # Read markdown content
    with open(index_path, 'r') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(md_content, extensions=['extra', 'toc', 'tables'])
    
    # Wrap in HTML template
    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="content">
            {html_content}
        </div>
    </body>
    </html>
    """
    
    return html_page

@router.get("/summary", response_class=HTMLResponse)
async def get_documentation_summary():
    """
    Get documentation summary page
    """
    summary_path = DOCS_BASE_PATH / "API_DOCUMENTATION_SUMMARY.md"
    
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Documentation summary not found")
    
    with open(summary_path, 'r') as f:
        md_content = f.read()
    
    html_content = markdown.markdown(md_content, extensions=['extra', 'toc', 'tables'])
    
    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation Summary</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="content">
            {html_content}
        </div>
    </body>
    </html>
    """
    
    return html_page

@router.get("/{category}/{filename}", response_class=HTMLResponse)
async def get_documentation_file(category: str, filename: str):
    """
    Get specific documentation file
    """
    # Ensure filename ends with .md
    if not filename.endswith('.md'):
        filename += '.md'
    
    file_path = DOCS_BASE_PATH / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Documentation file not found: {category}/{filename}")
    
    with open(file_path, 'r') as f:
        md_content = f.read()
    
    html_content = markdown.markdown(md_content, extensions=['extra', 'toc', 'tables', 'codehilite'])
    
    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{filename.replace('.md', '').replace('-', ' ').title()}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            h1 {{
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .nav {{
                margin-bottom: 20px;
            }}
            .nav a {{
                margin-right: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="nav">
            <a href="/api/v1/documentation/">← Back to Index</a> |
            <a href="/api/v1/documentation/summary">Summary</a> |
            <a href="/docs">Interactive API Docs</a>
        </div>
        <div class="content">
            {html_content}
        </div>
    </body>
    </html>
    """
    
    return html_page

@router.get("/list", response_model=dict)
async def list_documentation_files():
    """
    List all available documentation files
    """
    docs = {}
    
    for category_dir in DOCS_BASE_PATH.iterdir():
        if category_dir.is_dir():
            category_name = category_dir.name
            docs[category_name] = []
            
            for file_path in category_dir.glob("*.md"):
                docs[category_name].append({
                    "filename": file_path.name,
                    "url": f"/api/v1/documentation/{category_name}/{file_path.stem}",
                    "title": file_path.stem.replace('-', ' ').title()
                })
    
    return {
        "categories": docs,
        "total_files": sum(len(files) for files in docs.values()),
        "index_url": "/api/v1/documentation/",
        "summary_url": "/api/v1/documentation/summary"
    }