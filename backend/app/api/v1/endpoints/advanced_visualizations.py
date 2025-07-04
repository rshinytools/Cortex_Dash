# ABOUTME: Comprehensive API endpoints for advanced NIVO-based visualizations
# ABOUTME: Handles all chart types with dynamic theming, study-specific configurations, and client customization

from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime, timedelta
import uuid
import random
import json

from app.api.deps import get_db, get_current_user
from app.models import User, Study, Organization
from app.core.permissions import Permission, require_permission

router = APIRouter()


# Color themes for different clients
COLOR_THEMES = {
    "default": {
        "primary": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"],
        "secondary": ["#60a5fa", "#34d399", "#fbbf24", "#f87171", "#a78bfa", "#f472b6"],
        "background": "#0f172a",
        "card": "#1e293b",
        "text": "#f1f5f9",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#3b82f6"
    },
    "pharma_blue": {
        "primary": ["#0066cc", "#0052a3", "#003d7a", "#002952", "#001429", "#4d94ff"],
        "secondary": ["#3385ff", "#005ce6", "#0047b3", "#003380", "#001f4d", "#6ba3ff"],
        "background": "#f8fafc",
        "card": "#ffffff",
        "text": "#1e293b",
        "success": "#059669",
        "warning": "#d97706",
        "error": "#dc2626",
        "info": "#0066cc"
    },
    "clinical_green": {
        "primary": ["#059669", "#047857", "#065f46", "#064e3b", "#022c22", "#10b981"],
        "secondary": ["#34d399", "#10b981", "#059669", "#047857", "#065f46", "#6ee7b7"],
        "background": "#f0fdf4",
        "card": "#ffffff",
        "text": "#064e3b",
        "success": "#059669",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#06b6d4"
    }
}


@router.post("/studies/{study_id}/visualizations/kpi-metrics", response_model=Dict[str, Any])
async def get_kpi_metrics(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get KPI metrics with trends for metric cards.
    """
    # Verify study and get organization for theming
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get organization theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme = org.settings.get("color_theme", "default") if org and org.settings else "default"
    
    # Extract metric configurations
    metrics = config.get("metrics", [])
    time_range = config.get("time_range", "last_30_days")
    comparison_period = config.get("comparison_period", "previous_period")
    
    # Generate KPI data
    kpi_data = {
        "study_id": str(study_id),
        "theme": COLOR_THEMES.get(theme, COLOR_THEMES["default"]),
        "generated_at": datetime.utcnow().isoformat(),
        "metrics": []
    }
    
    # Default metrics if none specified
    if not metrics:
        metrics = [
            {"id": "total_screened", "label": "Total Screened"},
            {"id": "safety_population", "label": "Safety Population"},
            {"id": "itt_population", "label": "ITT Population"},
            {"id": "screen_failures", "label": "Screen Failures"},
            {"id": "total_deaths", "label": "Total Deaths"},
            {"id": "treatment_discontinuation", "label": "Treatment Discontinuation"},
            {"id": "total_aes", "label": "Total AEs"},
            {"id": "total_saes", "label": "Total SAEs"}
        ]
    
    for metric in metrics:
        # Generate realistic values based on metric type
        current_value = 0
        previous_value = 0
        
        if metric["id"] == "total_screened":
            current_value = random.randint(300, 400)
            previous_value = random.randint(250, 350)
        elif metric["id"] == "safety_population":
            current_value = random.randint(200, 250)
            previous_value = random.randint(180, 220)
        elif metric["id"] == "itt_population":
            current_value = random.randint(200, 250)
            previous_value = random.randint(180, 220)
        elif metric["id"] == "screen_failures":
            current_value = random.randint(50, 150)
            previous_value = random.randint(40, 140)
        elif metric["id"] == "total_deaths":
            current_value = random.randint(0, 5)
            previous_value = random.randint(0, 3)
        elif metric["id"] == "total_aes":
            current_value = random.randint(3000, 5000)
            previous_value = random.randint(2800, 4800)
        elif metric["id"] == "total_saes":
            current_value = random.randint(100, 200)
            previous_value = random.randint(90, 190)
        else:
            current_value = random.randint(100, 500)
            previous_value = random.randint(90, 480)
        
        change = current_value - previous_value
        change_percent = (change / previous_value * 100) if previous_value > 0 else 0
        
        kpi_data["metrics"].append({
            "id": metric["id"],
            "label": metric.get("label", metric["id"].replace("_", " ").title()),
            "value": current_value,
            "previous_value": previous_value,
            "change": change,
            "change_percent": round(change_percent, 1),
            "trend": "up" if change > 0 else "down" if change < 0 else "stable",
            "color": kpi_data["theme"]["primary"][0] if change >= 0 else kpi_data["theme"]["error"],
            "unit": metric.get("unit", ""),
            "format": metric.get("format", "number"),
            "sparkline_data": [
                previous_value + random.randint(-10, 10) for _ in range(7)
            ] + [current_value]
        })
    
    return kpi_data


@router.post("/studies/{study_id}/visualizations/geographic-map", response_model=Dict[str, Any])
async def get_geographic_map_data(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get geographic map data for site locations with enrollment status.
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    metric = config.get("metric", "enrollment")
    show_clusters = config.get("show_clusters", True)
    
    # Generate site location data
    sites = []
    
    # North America sites
    na_coords = [
        {"lat": 40.7128, "lng": -74.0060, "city": "New York"},
        {"lat": 41.8781, "lng": -87.6298, "city": "Chicago"},
        {"lat": 34.0522, "lng": -118.2437, "city": "Los Angeles"},
        {"lat": 43.6532, "lng": -79.3832, "city": "Toronto"},
        {"lat": 37.7749, "lng": -122.4194, "city": "San Francisco"},
        {"lat": 42.3601, "lng": -71.0589, "city": "Boston"},
        {"lat": 47.6062, "lng": -122.3321, "city": "Seattle"}
    ]
    
    # Europe sites
    eu_coords = [
        {"lat": 51.5074, "lng": -0.1278, "city": "London"},
        {"lat": 48.8566, "lng": 2.3522, "city": "Paris"},
        {"lat": 52.5200, "lng": 13.4050, "city": "Berlin"},
        {"lat": 41.9028, "lng": 12.4964, "city": "Rome"},
        {"lat": 40.4168, "lng": -3.7038, "city": "Madrid"}
    ]
    
    # Asia-Pacific sites
    apac_coords = [
        {"lat": 35.6762, "lng": 139.6503, "city": "Tokyo"},
        {"lat": -33.8688, "lng": 151.2093, "city": "Sydney"},
        {"lat": 1.3521, "lng": 103.8198, "city": "Singapore"},
        {"lat": 37.5665, "lng": 126.9780, "city": "Seoul"}
    ]
    
    all_coords = na_coords + eu_coords + apac_coords
    
    for i, coord in enumerate(all_coords):
        site = {
            "id": f"SITE-{i+1:03d}",
            "name": f"{coord['city']} Medical Center",
            "latitude": coord["lat"],
            "longitude": coord["lng"],
            "city": coord["city"],
            "country": "USA" if coord in na_coords[:5] else "Canada" if coord in na_coords[5:] else "UK" if coord["city"] == "London" else "Various",
            "status": random.choice(["active", "active", "active", "pending", "closed"]),
            "enrollment": {
                "target": random.randint(20, 50),
                "actual": random.randint(5, 45),
                "screen_failures": random.randint(0, 10)
            },
            "color": "#3b82f6" if random.random() > 0.2 else "#ef4444",  # Most blue, some red
            "size": random.randint(5, 15)
        }
        sites.append(site)
    
    return {
        "study_id": str(study_id),
        "sites": sites,
        "summary": {
            "total_sites": len(sites),
            "active_sites": len([s for s in sites if s["status"] == "active"]),
            "total_enrollment": sum(s["enrollment"]["actual"] for s in sites),
            "total_target": sum(s["enrollment"]["target"] for s in sites),
            "regions": {
                "North America": len(na_coords),
                "Europe": len(eu_coords),
                "Asia-Pacific": len(apac_coords)
            }
        },
        "map_config": {
            "center": {"lat": 20, "lng": 0},
            "zoom": 2,
            "style": "dark" if config.get("dark_mode", True) else "light"
        }
    }


@router.post("/studies/{study_id}/visualizations/bar-chart", response_model=Dict[str, Any])
async def get_bar_chart_data(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get bar chart data supporting simple, grouped, and stacked configurations.
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get organization theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme_name = org.settings.get("color_theme", "default") if org and org.settings else "default"
    theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["default"])
    
    # Extract configuration
    chart_type = config.get("type", "simple")  # simple, grouped, stacked
    x_field = config.get("x_field", "category")
    y_field = config.get("y_field", "value")
    group_by = config.get("group_by")
    orientation = config.get("orientation", "vertical")  # vertical, horizontal
    
    # Generate data based on configuration
    if x_field == "race":
        categories = ["White", "Black or African American", "Asian", "Other", "Unknown"]
    elif x_field == "ethnicity":
        categories = ["Hispanic or Latino", "Not Hispanic or Latino", "Unknown"]
    elif x_field == "cause_of_death":
        categories = ["Disease Progression", "Adverse Event", "Other", "Unknown"]
    elif x_field == "age_group":
        categories = ["<18", "18-39", "40-59", "60-79", "≥80"]
    elif x_field == "gender":
        categories = ["Male", "Female", "Other"]
    else:
        categories = [f"Category {i+1}" for i in range(5)]
    
    data = []
    
    if chart_type == "simple":
        for cat in categories:
            data.append({
                x_field: cat,
                y_field: random.randint(10, 200),
                "color": theme["primary"][0]
            })
    
    elif chart_type in ["grouped", "stacked"]:
        groups = config.get("groups", ["Group A", "Group B", "Group C"])
        for cat in categories:
            item = {x_field: cat}
            for i, group in enumerate(groups):
                item[group] = random.randint(10, 100)
                item[f"{group}Color"] = theme["primary"][i % len(theme["primary"])]
            data.append(item)
    
    return {
        "study_id": str(study_id),
        "chart_type": chart_type,
        "orientation": orientation,
        "data": data,
        "keys": config.get("groups", [y_field]) if chart_type != "simple" else [y_field],
        "index_by": x_field,
        "colors": theme["primary"],
        "theme": {
            "background": theme["background"],
            "text": theme["text"],
            "grid": {"line": {"stroke": theme["text"], "strokeOpacity": 0.1}}
        },
        "config": {
            "margin": {"top": 50, "right": 130, "bottom": 50, "left": 60},
            "padding": 0.3,
            "value_scale": {"type": "linear"},
            "index_scale": {"type": "band", "round": True},
            "enable_label": config.get("show_labels", False),
            "enable_grid_y": True,
            "legends": [{
                "dataFrom": "keys",
                "anchor": "bottom-right",
                "direction": "column",
                "translateX": 120
            }] if chart_type != "simple" else []
        }
    }


@router.post("/studies/{study_id}/visualizations/pie-chart", response_model=Dict[str, Any])
async def get_pie_chart_data(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get pie/donut chart data.
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme_name = org.settings.get("color_theme", "default") if org and org.settings else "default"
    theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["default"])
    
    # Extract configuration
    chart_style = config.get("style", "pie")  # pie, donut
    category = config.get("category", "discontinuation_reason")
    
    # Generate data based on category
    if category == "discontinuation_reason":
        data = [
            {"id": "Adverse Event", "label": "Adverse Event", "value": 45},
            {"id": "Lack of Efficacy", "label": "Lack of Efficacy", "value": 32},
            {"id": "Withdrawal by Subject", "label": "Withdrawal by Subject", "value": 28},
            {"id": "Lost to Follow-up", "label": "Lost to Follow-up", "value": 15},
            {"id": "Death", "label": "Death", "value": 8},
            {"id": "Other", "label": "Other", "value": 12}
        ]
    elif category == "region":
        data = [
            {"id": "North America", "label": "North America", "value": 125},
            {"id": "Europe", "label": "Europe", "value": 98},
            {"id": "Asia-Pacific", "label": "Asia-Pacific", "value": 67},
            {"id": "Latin America", "label": "Latin America", "value": 23}
        ]
    else:
        data = [
            {"id": f"Category {i+1}", "label": f"Category {i+1}", "value": random.randint(10, 100)}
            for i in range(6)
        ]
    
    return {
        "study_id": str(study_id),
        "chart_style": chart_style,
        "data": data,
        "colors": {"scheme": "nivo"},  # Use NIVO color schemes
        "theme": {
            "background": theme["background"],
            "text": {"fill": theme["text"]},
            "labels": {"text": {"fill": theme["text"]}}
        },
        "config": {
            "margin": {"top": 40, "right": 80, "bottom": 80, "left": 80},
            "inner_radius": 0.5 if chart_style == "donut" else 0,
            "pad_angle": 0.7,
            "corner_radius": 3,
            "active_outer_radius_offset": 8,
            "border_width": 1,
            "border_color": {"from": "color", "modifiers": [["darker", 0.2]]},
            "arc_link_labels_skip_angle": 10,
            "arc_link_labels_text_color": theme["text"],
            "arc_link_labels_thickness": 2,
            "arc_link_labels_color": {"from": "color"},
            "arc_labels_skip_angle": 10,
            "arc_labels_text_color": {"from": "color", "modifiers": [["darker", 2]]},
            "legends": [{
                "anchor": "bottom",
                "direction": "row",
                "justify": False,
                "translateX": 0,
                "translateY": 56,
                "items_spacing": 0,
                "items_width": 100,
                "items_height": 18,
                "items_text_color": theme["text"],
                "items_direction": "left-to-right",
                "symbol_size": 18,
                "symbol_shape": "circle"
            }]
        }
    }


@router.post("/studies/{study_id}/visualizations/line-chart", response_model=Dict[str, Any])
async def get_line_chart_data(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get line chart data for time series visualization.
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme_name = org.settings.get("color_theme", "default") if org and org.settings else "default"
    theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["default"])
    
    # Extract configuration
    metric = config.get("metric", "enrollment")
    time_range = config.get("time_range", "last_6_months")
    granularity = config.get("granularity", "weekly")
    
    # Generate time series data
    if metric == "enrollment":
        series = [
            {"id": "Enrolled", "color": theme["success"]},
            {"id": "Screen Failures", "color": theme["error"]}
        ]
        
        # Generate dates
        dates = []
        base_date = datetime.utcnow() - timedelta(days=180)
        for i in range(26):  # 26 weeks
            dates.append((base_date + timedelta(weeks=i)).strftime("%Y-%m-%d"))
        
        # Generate data points
        enrolled_total = 0
        screen_failures_total = 0
        
        data = []
        for i, date in enumerate(dates):
            enrolled_increment = random.randint(8, 15)
            screen_failures_increment = random.randint(2, 5)
            enrolled_total += enrolled_increment
            screen_failures_total += screen_failures_increment
            
            data_point = {"x": date}
            for serie in series:
                if serie["id"] == "Enrolled":
                    data_point["y"] = enrolled_total
                else:
                    data_point["y"] = screen_failures_total
                data.append({**data_point, "serie": serie["id"]})
    
    else:
        # Generic time series
        series = [{"id": "Series 1", "color": theme["primary"][0]}]
        dates = [(datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, 0, -1)]
        data = []
        for date in dates:
            for serie in series:
                data.append({
                    "x": date,
                    "y": random.randint(50, 150),
                    "serie": serie["id"]
                })
    
    # Transform data for NIVO format
    nivo_data = []
    for serie in series:
        serie_data = {
            "id": serie["id"],
            "color": serie["color"],
            "data": [
                {"x": point["x"], "y": point["y"]} 
                for point in data if point["serie"] == serie["id"]
            ]
        }
        nivo_data.append(serie_data)
    
    return {
        "study_id": str(study_id),
        "data": nivo_data,
        "theme": {
            "background": theme["background"],
            "text": {"fill": theme["text"]},
            "grid": {"line": {"stroke": theme["text"], "strokeOpacity": 0.1}},
            "axis": {
                "domain": {"line": {"stroke": theme["text"], "strokeOpacity": 0.3}},
                "legend": {"text": {"fill": theme["text"]}},
                "ticks": {"text": {"fill": theme["text"]}}
            }
        },
        "config": {
            "margin": {"top": 50, "right": 110, "bottom": 50, "left": 60},
            "x_scale": {"type": "time", "format": "%Y-%m-%d", "precision": "day"},
            "x_format": "time:%Y-%m-%d",
            "y_scale": {"type": "linear", "min": "auto", "max": "auto", "stacked": False},
            "y_format": " >-.0f",
            "curve": "catmullRom",
            "axis_bottom": {
                "orient": "bottom",
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": -45,
                "format": "%b %d",
                "legend": "Date",
                "legendOffset": 36,
                "legendPosition": "middle"
            },
            "axis_left": {
                "orient": "left",
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0,
                "legend": "Count",
                "legendOffset": -40,
                "legendPosition": "middle"
            },
            "point_size": 10,
            "point_color": {"theme": "background"},
            "point_border_width": 2,
            "point_border_color": {"from": "serie.color"},
            "line_width": 3,
            "enable_grid_x": False,
            "enable_grid_y": True,
            "enable_points": True,
            "enable_area": config.get("show_area", False),
            "area_opacity": 0.1,
            "use_mesh": True,
            "legends": [{
                "anchor": "bottom-right",
                "direction": "column",
                "justify": False,
                "translateX": 100,
                "translateY": 0,
                "itemsSpacing": 0,
                "itemDirection": "left-to-right",
                "itemWidth": 80,
                "itemHeight": 20,
                "itemOpacity": 0.75,
                "symbolSize": 12,
                "symbolShape": "circle",
                "symbolBorderColor": "rgba(0, 0, 0, .5)"
            }]
        }
    }


@router.post("/studies/{study_id}/visualizations/treemap", response_model=Dict[str, Any])
async def get_treemap_data(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get treemap data for hierarchical visualization (like AE by Body System).
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    hierarchy = config.get("hierarchy", "ae_body_system")
    color_by = config.get("color_by", "severity")
    
    # Generate hierarchical data
    if hierarchy == "ae_body_system":
        data = {
            "name": "Adverse Events",
            "children": [
                {
                    "name": "Nervous system disorders",
                    "children": [
                        {"name": "Headache", "value": 145, "severity": 1},
                        {"name": "Dizziness", "value": 89, "severity": 2},
                        {"name": "Somnolence", "value": 67, "severity": 1},
                        {"name": "Tremor", "value": 23, "severity": 3}
                    ]
                },
                {
                    "name": "Gastrointestinal disorders",
                    "children": [
                        {"name": "Nausea", "value": 123, "severity": 2},
                        {"name": "Vomiting", "value": 78, "severity": 2},
                        {"name": "Diarrhea", "value": 91, "severity": 1},
                        {"name": "Abdominal pain", "value": 45, "severity": 3}
                    ]
                },
                {
                    "name": "General disorders",
                    "children": [
                        {"name": "Fatigue", "value": 167, "severity": 1},
                        {"name": "Pyrexia", "value": 34, "severity": 2},
                        {"name": "Asthenia", "value": 56, "severity": 2},
                        {"name": "Chills", "value": 23, "severity": 1}
                    ]
                },
                {
                    "name": "Respiratory disorders",
                    "children": [
                        {"name": "Cough", "value": 89, "severity": 1},
                        {"name": "Dyspnea", "value": 45, "severity": 3},
                        {"name": "Rhinitis", "value": 34, "severity": 1}
                    ]
                },
                {
                    "name": "Skin disorders",
                    "children": [
                        {"name": "Rash", "value": 67, "severity": 2},
                        {"name": "Pruritus", "value": 45, "severity": 1},
                        {"name": "Erythema", "value": 23, "severity": 2}
                    ]
                }
            ]
        }
    else:
        # Generic hierarchical data
        data = {
            "name": "Root",
            "children": [
                {
                    "name": f"Category {i+1}",
                    "children": [
                        {"name": f"Item {i+1}-{j+1}", "value": random.randint(10, 200), "severity": random.randint(1, 3)}
                        for j in range(random.randint(3, 6))
                    ]
                }
                for i in range(5)
            ]
        }
    
    # Get theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme_name = org.settings.get("color_theme", "default") if org and org.settings else "default"
    theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["default"])
    
    # Color scale for severity
    color_scale = {
        1: theme["success"],  # Mild
        2: theme["warning"],  # Moderate
        3: theme["error"]     # Severe
    }
    
    return {
        "study_id": str(study_id),
        "data": data,
        "identity": "name",
        "value": "value",
        "tile": "squarify",
        "leavesOnly": True,
        "innerPadding": 3,
        "outerPadding": 3,
        "theme": {
            "background": theme["background"],
            "text": {"fill": theme["text"]},
            "labels": {"text": {"fill": "#ffffff", "fontSize": 12}}
        },
        "colors": {"scheme": "nivo"},
        "color_by": color_by,
        "color_scale": color_scale,
        "borderColor": {"from": "color", "modifiers": [["darker", 0.3]]},
        "borderWidth": 2,
        "label": "name",
        "labelTextColor": {"from": "color", "modifiers": [["darker", 3]]},
        "orientLabel": False,
        "labelSkipSize": 12,
        "config": {
            "margin": {"top": 10, "right": 10, "bottom": 10, "left": 10},
            "enable_parent_label": True,
            "parent_label_position": "top",
            "parent_label_padding": 5,
            "parent_label_size": 15,
            "parent_label_text_color": theme["text"]
        }
    }


@router.post("/studies/{study_id}/visualizations/sunburst", response_model=Dict[str, Any])
async def get_sunburst_data(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get sunburst chart data for co-occurrence analysis.
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    analysis_type = config.get("type", "ae_cooccurrence")
    
    # Generate sunburst data
    if analysis_type == "ae_cooccurrence":
        data = {
            "name": "AE Co-occurrence",
            "color": "hsl(0, 0%, 100%)",
            "children": [
                {
                    "name": "Nervous System",
                    "color": "hsl(220, 70%, 50%)",
                    "children": [
                        {
                            "name": "Headache",
                            "color": "hsl(220, 70%, 60%)",
                            "children": [
                                {"name": "→ Nausea", "value": 45, "color": "hsl(220, 70%, 70%)"},
                                {"name": "→ Fatigue", "value": 38, "color": "hsl(220, 70%, 70%)"},
                                {"name": "→ Dizziness", "value": 23, "color": "hsl(220, 70%, 70%)"}
                            ]
                        },
                        {
                            "name": "Dizziness",
                            "color": "hsl(220, 70%, 60%)",
                            "children": [
                                {"name": "→ Headache", "value": 23, "color": "hsl(220, 70%, 70%)"},
                                {"name": "→ Nausea", "value": 19, "color": "hsl(220, 70%, 70%)"}
                            ]
                        }
                    ]
                },
                {
                    "name": "Gastrointestinal",
                    "color": "hsl(140, 70%, 50%)",
                    "children": [
                        {
                            "name": "Nausea",
                            "color": "hsl(140, 70%, 60%)",
                            "children": [
                                {"name": "→ Vomiting", "value": 67, "color": "hsl(140, 70%, 70%)"},
                                {"name": "→ Headache", "value": 45, "color": "hsl(140, 70%, 70%)"},
                                {"name": "→ Fatigue", "value": 34, "color": "hsl(140, 70%, 70%)"}
                            ]
                        },
                        {
                            "name": "Diarrhea",
                            "color": "hsl(140, 70%, 60%)",
                            "children": [
                                {"name": "→ Abdominal Pain", "value": 28, "color": "hsl(140, 70%, 70%)"},
                                {"name": "→ Dehydration", "value": 15, "color": "hsl(140, 70%, 70%)"}
                            ]
                        }
                    ]
                },
                {
                    "name": "General Disorders",
                    "color": "hsl(40, 70%, 50%)",
                    "children": [
                        {
                            "name": "Fatigue",
                            "color": "hsl(40, 70%, 60%)",
                            "children": [
                                {"name": "→ Headache", "value": 38, "color": "hsl(40, 70%, 70%)"},
                                {"name": "→ Nausea", "value": 34, "color": "hsl(40, 70%, 70%)"},
                                {"name": "→ Insomnia", "value": 23, "color": "hsl(40, 70%, 70%)"}
                            ]
                        }
                    ]
                }
            ]
        }
    else:
        # Generic hierarchical data
        data = {
            "name": "Root",
            "color": "hsl(0, 0%, 100%)",
            "children": [
                {
                    "name": f"Level 1-{i+1}",
                    "color": f"hsl({i * 60}, 70%, 50%)",
                    "children": [
                        {
                            "name": f"Level 2-{i+1}-{j+1}",
                            "color": f"hsl({i * 60}, 70%, 60%)",
                            "value": random.randint(10, 100)
                        }
                        for j in range(3)
                    ]
                }
                for i in range(6)
            ]
        }
    
    # Get theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme_name = org.settings.get("color_theme", "default") if org and org.settings else "default"
    theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["default"])
    
    return {
        "study_id": str(study_id),
        "data": data,
        "identity": "name",
        "value": "value",
        "cornerRadius": 2,
        "theme": {
            "background": theme["background"],
            "text": {"fill": theme["text"]}
        },
        "colors": {"scheme": "nivo"},
        "childColor": {"from": "color", "modifiers": [["brighter", 0.4]]},
        "borderWidth": 2,
        "borderColor": theme["background"],
        "config": {
            "margin": {"top": 40, "right": 40, "bottom": 40, "left": 40},
            "inheritColorFromParent": True,
            "animate": True,
            "motionConfig": "gentle",
            "transitionMode": "startAngle",
            "enableArcLabels": True,
            "arcLabelsSkipAngle": 10,
            "arcLabelsTextColor": {"from": "color", "modifiers": [["darker", 3]]}
        }
    }


@router.post("/studies/{study_id}/visualizations/scatter-plot", response_model=Dict[str, Any])
async def get_scatter_plot_data(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get scatter plot data for correlation analysis.
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    x_var = config.get("x_variable", "screening_rate")
    y_var = config.get("y_variable", "enrollment_rate")
    group_by = config.get("group_by", "site")
    
    # Generate scatter data
    if group_by == "site":
        data = []
        for i in range(15):  # 15 sites
            serie_data = {
                "id": f"Site {i+1:03d}",
                "data": [{
                    "x": random.uniform(0.5, 0.95),  # Screening rate
                    "y": random.uniform(0.3, 0.85),  # Enrollment rate
                    "size": random.randint(20, 100)  # Site size
                }]
            }
            data.append(serie_data)
    else:
        # Generic scatter data
        data = [
            {
                "id": f"Group {i+1}",
                "data": [
                    {
                        "x": random.uniform(0, 100),
                        "y": random.uniform(0, 100),
                        "size": random.randint(5, 50)
                    }
                    for _ in range(20)
                ]
            }
            for i in range(3)
        ]
    
    # Get theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme_name = org.settings.get("color_theme", "default") if org and org.settings else "default"
    theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["default"])
    
    return {
        "study_id": str(study_id),
        "data": data,
        "theme": {
            "background": theme["background"],
            "text": {"fill": theme["text"]},
            "grid": {"line": {"stroke": theme["text"], "strokeOpacity": 0.1}},
            "axis": {
                "domain": {"line": {"stroke": theme["text"], "strokeOpacity": 0.3}},
                "legend": {"text": {"fill": theme["text"]}},
                "ticks": {"text": {"fill": theme["text"]}}
            }
        },
        "config": {
            "margin": {"top": 60, "right": 140, "bottom": 70, "left": 90},
            "x_scale": {"type": "linear", "min": 0, "max": 1},
            "x_format": ">-.2f",
            "y_scale": {"type": "linear", "min": 0, "max": 1},
            "y_format": ">-.2f",
            "blend_mode": "multiply",
            "colors": {"scheme": "category10"},
            "node_size": {"key": "size", "values": [20, 100], "sizes": [10, 60]},
            "axis_bottom": {
                "orient": "bottom",
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0,
                "legend": x_var.replace("_", " ").title(),
                "legendPosition": "middle",
                "legendOffset": 46
            },
            "axis_left": {
                "orient": "left",
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0,
                "legend": y_var.replace("_", " ").title(),
                "legendPosition": "middle",
                "legendOffset": -60
            },
            "legends": [{
                "anchor": "bottom-right",
                "direction": "column",
                "justify": False,
                "translateX": 130,
                "translateY": 0,
                "itemWidth": 100,
                "itemHeight": 12,
                "itemsSpacing": 5,
                "symbolSize": 12,
                "symbolShape": "circle",
                "itemDirection": "left-to-right"
            }]
        }
    }


@router.post("/studies/{study_id}/visualizations/heatmap", response_model=Dict[str, Any])
async def get_heatmap_data(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get heatmap data for multi-dimensional analysis.
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    analysis_type = config.get("type", "ae_by_soc_grade")
    
    # Generate heatmap data
    if analysis_type == "ae_by_soc_grade":
        socs = ["Nervous system", "Gastrointestinal", "General", "Respiratory", "Skin", "Cardiac", "Vascular", "Infections"]
        grades = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]
        
        data = []
        for soc in socs:
            for grade in grades:
                # Higher grades are less frequent
                base_value = random.randint(50, 200) if "Grade 1" in grade else \
                           random.randint(20, 100) if "Grade 2" in grade else \
                           random.randint(5, 50) if "Grade 3" in grade else \
                           random.randint(0, 20) if "Grade 4" in grade else \
                           random.randint(0, 5)
                
                data.append({
                    "x": grade,
                    "y": soc,
                    "value": base_value
                })
    else:
        # Generic heatmap data
        x_labels = [f"X{i+1}" for i in range(8)]
        y_labels = [f"Y{i+1}" for i in range(10)]
        
        data = []
        for y in y_labels:
            for x in x_labels:
                data.append({
                    "x": x,
                    "y": y,
                    "value": random.randint(0, 100)
                })
    
    # Get theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme_name = org.settings.get("color_theme", "default") if org and org.settings else "default"
    theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["default"])
    
    return {
        "study_id": str(study_id),
        "data": data,
        "theme": {
            "background": theme["background"],
            "text": {"fill": theme["text"]},
            "axis": {
                "domain": {"line": {"stroke": theme["text"], "strokeOpacity": 0.3}},
                "ticks": {"text": {"fill": theme["text"]}}
            }
        },
        "config": {
            "margin": {"top": 60, "right": 90, "bottom": 60, "left": 90},
            "value_format": ">-.0f",
            "axis_top": {
                "orient": "top",
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": -90
            },
            "axis_left": {
                "orient": "left",
                "tickSize": 5,
                "tickPadding": 5,
                "tickRotation": 0
            },
            "colors": {
                "type": "sequential",
                "scheme": "blues",
                "divergeAt": 0.5
            },
            "empty_color": "#555555",
            "legends": [{
                "anchor": "bottom",
                "translateX": 0,
                "translateY": 30,
                "length": 400,
                "thickness": 8,
                "direction": "row",
                "tickPosition": "after",
                "tickSize": 3,
                "tickSpacing": 4,
                "tickOverlap": False,
                "title": "Count →",
                "titleAlign": "start",
                "titleOffset": 4
            }],
            "annotations": [],
            "label_text_color": {"from": "color", "modifiers": [["darker", 2]]}
        }
    }


@router.get("/studies/{study_id}/visualizations/data-table", response_model=Dict[str, Any])
async def get_data_table_config(
    study_id: uuid.UUID,
    table_type: str = Query(..., description="Type of table (ae_listing, site_summary, etc.)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query("asc", enum=["asc", "desc"]),
    filters: Optional[str] = Query(None, description="JSON encoded filters"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get data table configuration with styling and data.
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme_name = org.settings.get("color_theme", "default") if org and org.settings else "default"
    theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["default"])
    
    # Generate table configuration based on type
    if table_type == "ae_listing":
        columns = [
            {"id": "usubjid", "label": "Subject ID", "type": "text", "width": 120},
            {"id": "aeterm", "label": "AE Term", "type": "text", "width": 200},
            {"id": "aesoc", "label": "System Organ Class", "type": "text", "width": 180},
            {"id": "aesev", "label": "Severity", "type": "severity", "width": 100},
            {"id": "aeser", "label": "Serious", "type": "boolean", "width": 80},
            {"id": "aestdt", "label": "Start Date", "type": "date", "width": 120},
            {"id": "aeendt", "label": "End Date", "type": "date", "width": 120},
            {"id": "aeout", "label": "Outcome", "type": "text", "width": 150},
            {"id": "aerel", "label": "Relationship", "type": "text", "width": 120}
        ]
        
        # Generate sample data
        data = []
        severities = ["MILD", "MODERATE", "SEVERE"]
        outcomes = ["RECOVERED", "RECOVERING", "NOT RECOVERED", "FATAL", "UNKNOWN"]
        relationships = ["NOT RELATED", "UNLIKELY", "POSSIBLE", "PROBABLE", "DEFINITE"]
        
        for i in range(100):  # Generate 100 rows for pagination demo
            severity = random.choice(severities)
            serious = severity == "SEVERE" or random.random() < 0.1
            
            row = {
                "usubjid": f"SUBJ-{random.randint(1, 50):04d}",
                "aeterm": random.choice(["Headache", "Nausea", "Fatigue", "Dizziness", "Rash", "Fever"]),
                "aesoc": random.choice(["Nervous system", "Gastrointestinal", "General", "Skin"]),
                "aesev": severity,
                "aeser": "Y" if serious else "N",
                "aestdt": (datetime.utcnow() - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d"),
                "aeendt": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d") if random.random() > 0.3 else "",
                "aeout": random.choice(outcomes),
                "aerel": random.choice(relationships),
                "_row_color": theme["error"] if serious else theme["warning"] if severity == "MODERATE" else None
            }
            data.append(row)
    
    elif table_type == "site_summary":
        columns = [
            {"id": "site_id", "label": "Site ID", "type": "text", "width": 100},
            {"id": "site_name", "label": "Site Name", "type": "text", "width": 200},
            {"id": "screening", "label": "Screening", "type": "number", "width": 100},
            {"id": "enrolled", "label": "Enrolled", "type": "number", "width": 100},
            {"id": "screen_fail", "label": "Screen Failed", "type": "number", "width": 120},
            {"id": "withdrawn", "label": "Withdrawn", "type": "number", "width": 100},
            {"id": "completed", "label": "Completed", "type": "number", "width": 100},
            {"id": "enrollment_rate", "label": "Enrollment %", "type": "percentage", "width": 120}
        ]
        
        data = []
        for i in range(20):
            screening = random.randint(30, 80)
            enrolled = random.randint(20, screening)
            screen_fail = screening - enrolled
            withdrawn = random.randint(0, enrolled // 4)
            completed = enrolled - withdrawn
            
            row = {
                "site_id": f"S{i+1:03d}",
                "site_name": f"Site {i+1} Medical Center",
                "screening": screening,
                "enrolled": enrolled,
                "screen_fail": screen_fail,
                "withdrawn": withdrawn,
                "completed": completed,
                "enrollment_rate": round(enrolled / screening * 100, 1),
                "_row_color": theme["success"] if enrolled / screening > 0.8 else theme["warning"] if enrolled / screening > 0.6 else theme["error"]
            }
            data.append(row)
    
    else:
        # Generic table
        columns = [
            {"id": f"col{i+1}", "label": f"Column {i+1}", "type": "text", "width": 150}
            for i in range(5)
        ]
        data = [
            {f"col{j+1}": f"Row {i+1} Col {j+1}" for j in range(5)}
            for i in range(50)
        ]
    
    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_data = data[start_idx:end_idx]
    
    return {
        "study_id": str(study_id),
        "table_type": table_type,
        "columns": columns,
        "data": paginated_data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": len(data),
            "total_pages": (len(data) + page_size - 1) // page_size
        },
        "theme": {
            "header_background": theme["card"],
            "header_text": theme["text"],
            "row_background": theme["background"],
            "row_alternate_background": theme["card"],
            "row_text": theme["text"],
            "row_hover": theme["primary"][0] + "20",  # Add transparency
            "border_color": theme["text"] + "20"
        },
        "config": {
            "enable_sorting": True,
            "enable_filtering": True,
            "enable_export": True,
            "enable_column_resize": True,
            "enable_row_selection": True,
            "sticky_header": True,
            "row_height": 40,
            "header_height": 48
        }
    }


@router.get("/studies/{study_id}/visualizations/theme", response_model=Dict[str, Any])
async def get_visualization_theme(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get the current theme configuration for visualizations.
    """
    # Verify study access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get organization theme
    org = db.exec(select(Organization).where(Organization.id == study.org_id)).first()
    theme_name = org.settings.get("color_theme", "default") if org and org.settings else "default"
    theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["default"])
    
    # NIVO theme configuration
    nivo_theme = {
        "background": theme["background"],
        "textColor": theme["text"],
        "fontSize": 11,
        "axis": {
            "domain": {
                "line": {
                    "stroke": theme["text"],
                    "strokeWidth": 1,
                    "strokeOpacity": 0.3
                }
            },
            "legend": {
                "text": {
                    "fontSize": 12,
                    "fill": theme["text"]
                }
            },
            "ticks": {
                "line": {
                    "stroke": theme["text"],
                    "strokeWidth": 1,
                    "strokeOpacity": 0.1
                },
                "text": {
                    "fontSize": 11,
                    "fill": theme["text"]
                }
            }
        },
        "grid": {
            "line": {
                "stroke": theme["text"],
                "strokeWidth": 1,
                "strokeOpacity": 0.1
            }
        },
        "legends": {
            "title": {
                "text": {
                    "fontSize": 11,
                    "fill": theme["text"]
                }
            },
            "text": {
                "fontSize": 11,
                "fill": theme["text"]
            },
            "ticks": {
                "line": {},
                "text": {
                    "fontSize": 10,
                    "fill": theme["text"]
                }
            }
        },
        "annotations": {
            "text": {
                "fontSize": 13,
                "fill": theme["text"],
                "outlineWidth": 2,
                "outlineColor": theme["background"],
                "outlineOpacity": 1
            },
            "link": {
                "stroke": theme["text"],
                "strokeWidth": 1,
                "outlineWidth": 2,
                "outlineColor": theme["background"],
                "outlineOpacity": 1
            },
            "outline": {
                "stroke": theme["text"],
                "strokeWidth": 2,
                "outlineWidth": 2,
                "outlineColor": theme["background"],
                "outlineOpacity": 1
            },
            "symbol": {
                "fill": theme["text"],
                "outlineWidth": 2,
                "outlineColor": theme["background"],
                "outlineOpacity": 1
            }
        },
        "tooltip": {
            "wrapper": {},
            "container": {
                "background": theme["card"],
                "color": theme["text"],
                "fontSize": 12
            },
            "basic": {},
            "chip": {},
            "table": {},
            "tableCell": {},
            "tableCellValue": {}
        }
    }
    
    return {
        "study_id": str(study_id),
        "theme_name": theme_name,
        "color_palette": theme,
        "nivo_theme": nivo_theme,
        "available_themes": list(COLOR_THEMES.keys()),
        "custom_css": {
            "font_family": "'Inter', 'Segoe UI', sans-serif",
            "border_radius": "8px",
            "box_shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
        }
    }