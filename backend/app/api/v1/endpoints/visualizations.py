# ABOUTME: API endpoints for specialized clinical trial visualizations and statistical analysis
# ABOUTME: Handles statistical plots like survival curves, forest plots, waterfall plots, and correlation matrices

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime, timedelta
import uuid
import random
import math

from app.api.deps import get_db, get_current_user
from app.models import User, Study, Message
from app.core.permissions import Permission, require_permission

router = APIRouter()


@router.post("/studies/{study_id}/visualizations/correlation-matrix", response_model=Dict[str, Any])
async def generate_correlation_matrix(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Generate correlation matrix for selected variables.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    dataset = config.get("dataset", "ADSL")
    variables = config.get("variables", [])
    correlation_method = config.get("method", "pearson")  # pearson, spearman, kendall
    
    # TODO: Implement actual correlation calculation
    # For now, return mock correlation matrix
    
    # Generate mock correlation data
    n_vars = len(variables) if variables else 5
    mock_variables = variables or [f"VAR{i+1}" for i in range(n_vars)]
    
    # Create correlation matrix
    correlation_data = []
    for i in range(n_vars):
        row = []
        for j in range(n_vars):
            if i == j:
                row.append(1.0)
            else:
                # Generate realistic correlation values
                corr = random.uniform(-0.8, 0.8)
                row.append(round(corr, 3))
        correlation_data.append(row)
    
    # Ensure matrix is symmetric
    for i in range(n_vars):
        for j in range(i):
            correlation_data[i][j] = correlation_data[j][i]
    
    return {
        "study_id": str(study_id),
        "dataset": dataset,
        "variables": mock_variables,
        "method": correlation_method,
        "correlation_matrix": correlation_data,
        "sample_size": 1250,
        "missing_data": {
            var: random.randint(0, 50) for var in mock_variables
        },
        "p_values": [[
            None if i == j else round(random.uniform(0, 0.1), 4)
            for j in range(n_vars)
        ] for i in range(n_vars)],
        "significant_correlations": [
            {
                "var1": mock_variables[0],
                "var2": mock_variables[1],
                "correlation": 0.75,
                "p_value": 0.001,
                "interpretation": "Strong positive correlation"
            }
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/studies/{study_id}/visualizations/survival-curve", response_model=Dict[str, Any])
async def generate_survival_curve(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Generate Kaplan-Meier survival curve data.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    dataset = config.get("dataset", "ADTTE")
    time_var = config.get("time_variable", "AVAL")
    event_var = config.get("event_variable", "CNSR")
    group_var = config.get("group_variable", "TRT01P")
    
    # TODO: Implement actual survival analysis
    # For now, return mock survival curve data
    
    groups = ["Placebo", "Drug A 10mg", "Drug A 20mg"]
    time_points = list(range(0, 365, 30))  # Monthly intervals for a year
    
    survival_data = {}
    for group in groups:
        # Generate decreasing survival probabilities
        survival_probs = [1.0]
        n_at_risk = [random.randint(400, 450)]
        events = [0]
        censored = [0]
        
        for i, t in enumerate(time_points[1:], 1):
            # Simulate survival probability decrease
            prev_prob = survival_probs[-1]
            decrease = random.uniform(0.02, 0.08) * (1 if group == "Placebo" else 0.6)
            new_prob = max(0, prev_prob - decrease)
            survival_probs.append(round(new_prob, 3))
            
            # Update at risk, events, censored
            prev_at_risk = n_at_risk[-1]
            new_events = random.randint(5, 20)
            new_censored = random.randint(0, 5)
            n_at_risk.append(max(0, prev_at_risk - new_events - new_censored))
            events.append(new_events)
            censored.append(new_censored)
        
        survival_data[group] = {
            "time": time_points,
            "survival_probability": survival_probs,
            "n_at_risk": n_at_risk,
            "events": events,
            "censored": censored,
            "confidence_interval_lower": [
                max(0, p - 0.05) for p in survival_probs
            ],
            "confidence_interval_upper": [
                min(1, p + 0.05) for p in survival_probs
            ]
        }
    
    # Calculate median survival time
    median_survival = {}
    for group, data in survival_data.items():
        for i, prob in enumerate(data["survival_probability"]):
            if prob < 0.5:
                median_survival[group] = data["time"][i]
                break
        else:
            median_survival[group] = None  # Not reached
    
    return {
        "study_id": str(study_id),
        "dataset": dataset,
        "analysis_type": "Kaplan-Meier",
        "groups": groups,
        "survival_data": survival_data,
        "median_survival": median_survival,
        "hazard_ratio": {
            "Drug A 10mg vs Placebo": {
                "value": 0.65,
                "ci_lower": 0.48,
                "ci_upper": 0.88,
                "p_value": 0.005
            },
            "Drug A 20mg vs Placebo": {
                "value": 0.52,
                "ci_lower": 0.38,
                "ci_upper": 0.71,
                "p_value": 0.001
            }
        },
        "log_rank_test": {
            "chi_square": 12.5,
            "df": 2,
            "p_value": 0.002
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/studies/{study_id}/visualizations/forest-plot", response_model=Dict[str, Any])
async def generate_forest_plot(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Generate forest plot data for subgroup analysis.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    endpoint = config.get("endpoint", "Primary Endpoint")
    subgroups = config.get("subgroups", ["Age", "Sex", "Region", "Baseline"])
    
    # TODO: Implement actual subgroup analysis
    # For now, return mock forest plot data
    
    forest_data = {
        "endpoint": endpoint,
        "overall_effect": {
            "estimate": 0.75,
            "ci_lower": 0.62,
            "ci_upper": 0.91,
            "p_value": 0.003,
            "label": "Overall",
            "n_treatment": 625,
            "n_control": 623
        },
        "subgroups": []
    }
    
    # Generate subgroup data
    subgroup_configs = {
        "Age": [
            {"label": "<65 years", "n_ratio": 0.6},
            {"label": "≥65 years", "n_ratio": 0.4}
        ],
        "Sex": [
            {"label": "Male", "n_ratio": 0.55},
            {"label": "Female", "n_ratio": 0.45}
        ],
        "Region": [
            {"label": "North America", "n_ratio": 0.35},
            {"label": "Europe", "n_ratio": 0.40},
            {"label": "Asia-Pacific", "n_ratio": 0.25}
        ],
        "Baseline": [
            {"label": "Low", "n_ratio": 0.33},
            {"label": "Medium", "n_ratio": 0.34},
            {"label": "High", "n_ratio": 0.33}
        ]
    }
    
    for subgroup_name, categories in subgroup_configs.items():
        if subgroup_name in subgroups:
            subgroup_data = {
                "subgroup": subgroup_name,
                "categories": []
            }
            
            for cat in categories:
                # Generate effect size with some variation
                base_effect = forest_data["overall_effect"]["estimate"]
                variation = random.uniform(-0.2, 0.2)
                effect = base_effect + variation
                
                # Calculate CI based on sample size
                n_total = 1248
                n_cat = int(n_total * cat["n_ratio"])
                ci_width = 0.3 / math.sqrt(n_cat / 100)  # Wider CI for smaller samples
                
                category_data = {
                    "label": cat["label"],
                    "estimate": round(effect, 2),
                    "ci_lower": round(effect - ci_width/2, 2),
                    "ci_upper": round(effect + ci_width/2, 2),
                    "p_value": round(random.uniform(0.001, 0.1), 3),
                    "n_treatment": n_cat // 2,
                    "n_control": n_cat // 2,
                    "favors": "treatment" if effect < 1 else "control"
                }
                subgroup_data["categories"].append(category_data)
            
            # Add interaction test
            subgroup_data["interaction_p_value"] = round(random.uniform(0.1, 0.8), 3)
            forest_data["subgroups"].append(subgroup_data)
    
    forest_data["heterogeneity"] = {
        "i_squared": 15.2,
        "p_value": 0.45,
        "interpretation": "Low heterogeneity"
    }
    
    return forest_data


@router.post("/studies/{study_id}/visualizations/waterfall-plot", response_model=Dict[str, Any])
async def generate_waterfall_plot(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Generate waterfall plot for tumor response data.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    dataset = config.get("dataset", "ADRS")
    response_var = config.get("response_variable", "PCHG")
    group_var = config.get("group_variable", "TRT01P")
    
    # TODO: Implement actual waterfall plot data generation
    # For now, return mock data
    
    # Generate mock patient response data
    n_patients = 120
    patient_data = []
    
    for i in range(n_patients):
        # Generate response values with realistic distribution
        if i < n_patients * 0.7:  # 70% responders
            change = random.uniform(-100, -20)  # Tumor reduction
        else:  # 30% non-responders
            change = random.uniform(-20, 50)  # Stable or progression
        
        patient = {
            "patient_id": f"SUBJ-{i+1:04d}",
            "change_percent": round(change, 1),
            "best_response": (
                "CR" if change <= -100 else
                "PR" if change <= -30 else
                "SD" if change <= 20 else
                "PD"
            ),
            "treatment_group": random.choice(["Drug A 10mg", "Drug A 20mg"]),
            "duration_weeks": random.randint(4, 52),
            "ongoing": random.choice([True, False])
        }
        patient_data.append(patient)
    
    # Sort by change percent for waterfall effect
    patient_data.sort(key=lambda x: x["change_percent"])
    
    # Calculate response rates
    response_summary = {
        "CR": len([p for p in patient_data if p["best_response"] == "CR"]),
        "PR": len([p for p in patient_data if p["best_response"] == "PR"]),
        "SD": len([p for p in patient_data if p["best_response"] == "SD"]),
        "PD": len([p for p in patient_data if p["best_response"] == "PD"])
    }
    
    orr = (response_summary["CR"] + response_summary["PR"]) / n_patients * 100
    dcr = (response_summary["CR"] + response_summary["PR"] + response_summary["SD"]) / n_patients * 100
    
    return {
        "study_id": str(study_id),
        "dataset": dataset,
        "patient_data": patient_data,
        "response_summary": response_summary,
        "overall_response_rate": round(orr, 1),
        "disease_control_rate": round(dcr, 1),
        "median_duration_of_response": 32.5,
        "thresholds": {
            "partial_response": -30,
            "progressive_disease": 20
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/studies/{study_id}/visualizations/swimmer-plot", response_model=Dict[str, Any])
async def generate_swimmer_plot(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Generate swimmer plot for patient treatment timeline visualization.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    sort_by = config.get("sort_by", "duration")  # duration, response, treatment
    show_events = config.get("show_events", ["response", "progression", "death"])
    
    # Generate swimmer plot data
    n_patients = 50
    swimmer_data = []
    
    for i in range(n_patients):
        # Generate patient timeline
        treatment_start = 0
        treatment_duration = random.randint(4, 104)  # 4-104 weeks
        
        # Generate events
        events = []
        
        # Response event
        if random.random() > 0.3:  # 70% have response
            response_time = random.randint(4, min(12, treatment_duration))
            events.append({
                "type": "response",
                "time": response_time,
                "label": random.choice(["PR", "CR"])
            })
        
        # Progression event
        if random.random() > 0.4 and treatment_duration > 20:
            progression_time = random.randint(20, treatment_duration - 4)
            events.append({
                "type": "progression",
                "time": progression_time,
                "label": "PD"
            })
        
        # Death event
        if random.random() > 0.95:  # 5% death rate
            death_time = treatment_duration
            events.append({
                "type": "death",
                "time": death_time,
                "label": "Death"
            })
            ongoing = False
        else:
            ongoing = random.random() > 0.3  # 70% ongoing
        
        patient = {
            "patient_id": f"SUBJ-{i+1:04d}",
            "treatment_group": random.choice(["Drug A 10mg", "Drug A 20mg"]),
            "treatment_start": treatment_start,
            "treatment_duration": treatment_duration,
            "ongoing": ongoing,
            "events": events,
            "best_response": (
                "CR" if any(e["label"] == "CR" for e in events) else
                "PR" if any(e["label"] == "PR" for e in events) else
                "SD" if not any(e["type"] == "progression" for e in events) else
                "PD"
            )
        }
        swimmer_data.append(patient)
    
    # Sort based on configuration
    if sort_by == "duration":
        swimmer_data.sort(key=lambda x: x["treatment_duration"], reverse=True)
    elif sort_by == "response":
        response_order = {"CR": 0, "PR": 1, "SD": 2, "PD": 3}
        swimmer_data.sort(key=lambda x: response_order.get(x["best_response"], 4))
    
    return {
        "study_id": str(study_id),
        "swimmer_data": swimmer_data,
        "time_unit": "weeks",
        "max_time": max(p["treatment_duration"] for p in swimmer_data),
        "event_types": {
            "response": {"symbol": "circle", "color": "#10b981"},
            "progression": {"symbol": "triangle", "color": "#ef4444"},
            "death": {"symbol": "cross", "color": "#000000"}
        },
        "treatment_groups": {
            "Drug A 10mg": {"color": "#3b82f6"},
            "Drug A 20mg": {"color": "#8b5cf6"}
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/studies/{study_id}/visualizations/spider-plot", response_model=Dict[str, Any])
async def generate_spider_plot(
    study_id: uuid.UUID,
    config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Generate spider plot for individual patient tumor burden over time.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract configuration
    highlight_responders = config.get("highlight_responders", True)
    time_points = config.get("time_points", [0, 6, 12, 18, 24, 30, 36, 42, 48])  # weeks
    
    # Generate spider plot data
    n_patients = 30
    spider_data = []
    
    for i in range(n_patients):
        # Determine if patient is responder
        is_responder = random.random() > 0.3  # 70% responders
        
        # Generate tumor burden changes over time
        measurements = []
        baseline = 100
        current_value = baseline
        
        for time_point in time_points:
            if time_point == 0:
                measurements.append({
                    "time": time_point,
                    "value": baseline,
                    "percent_change": 0
                })
            else:
                # Responders show decrease, non-responders show increase/stability
                if is_responder:
                    change = random.uniform(-10, -2)
                else:
                    change = random.uniform(-5, 10)
                
                current_value = max(0, current_value + change)
                percent_change = ((current_value - baseline) / baseline) * 100
                
                measurements.append({
                    "time": time_point,
                    "value": round(current_value, 1),
                    "percent_change": round(percent_change, 1)
                })
                
                # Stop if patient progresses significantly
                if percent_change > 20:
                    break
        
        patient = {
            "patient_id": f"SUBJ-{i+1:04d}",
            "treatment_group": random.choice(["Drug A 10mg", "Drug A 20mg"]),
            "measurements": measurements,
            "is_responder": is_responder,
            "best_response_percent": min(m["percent_change"] for m in measurements),
            "color": "#10b981" if is_responder else "#ef4444"
        }
        spider_data.append(patient)
    
    return {
        "study_id": str(study_id),
        "spider_data": spider_data,
        "time_unit": "weeks",
        "reference_lines": [
            {"y": -30, "label": "PR threshold", "color": "#10b981", "style": "dashed"},
            {"y": 20, "label": "PD threshold", "color": "#ef4444", "style": "dashed"},
            {"y": 0, "label": "Baseline", "color": "#6b7280", "style": "solid"}
        ],
        "summary": {
            "total_patients": n_patients,
            "responders": len([p for p in spider_data if p["is_responder"]]),
            "best_response_range": {
                "min": min(p["best_response_percent"] for p in spider_data),
                "max": max(p["best_response_percent"] for p in spider_data)
            }
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/studies/{study_id}/visualizations/insights", response_model=Dict[str, Any])
async def get_data_insights(
    study_id: uuid.UUID,
    dataset: Optional[str] = Query(None, description="Specific dataset to analyze"),
    insight_types: Optional[List[str]] = Query(None, description="Types of insights to generate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Generate automated insights from study data using statistical analysis.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement actual insight generation using ML/statistical analysis
    # For now, return mock insights
    
    insights = {
        "study_id": str(study_id),
        "generated_at": datetime.utcnow().isoformat(),
        "insights": []
    }
    
    # Generate different types of insights
    insight_categories = [
        {
            "category": "enrollment",
            "severity": "info",
            "title": "Enrollment Ahead of Schedule",
            "description": "Current enrollment rate is 15% above projected targets",
            "details": {
                "current_enrolled": 892,
                "projected_enrolled": 775,
                "days_ahead": 12,
                "top_performing_sites": ["Site 003", "Site 007", "Site 012"]
            },
            "recommendations": [
                "Consider reducing recruitment efforts at top sites to avoid over-enrollment",
                "Reallocate resources to underperforming sites"
            ],
            "visualizations": ["enrollment_trend", "site_performance_map"]
        },
        {
            "category": "safety",
            "severity": "warning",
            "title": "Increased AE Rate in Elderly Population",
            "description": "Subjects ≥75 years showing 25% higher AE rate compared to younger cohorts",
            "details": {
                "ae_rate_elderly": 0.42,
                "ae_rate_younger": 0.34,
                "most_common_aes": ["Dizziness", "Fatigue", "Nausea"],
                "statistical_significance": "p=0.023"
            },
            "recommendations": [
                "Review dosing guidelines for elderly subjects",
                "Consider protocol amendment for closer monitoring"
            ],
            "visualizations": ["ae_by_age_group", "forest_plot_age"]
        },
        {
            "category": "data_quality",
            "severity": "success",
            "title": "Improved Data Quality Metrics",
            "description": "Query rate decreased by 30% over last month",
            "details": {
                "current_query_rate": 2.1,
                "previous_query_rate": 3.0,
                "best_performing_sites": ["Site 005", "Site 009"],
                "most_improved": "Site 014"
            },
            "recommendations": [
                "Share best practices from top sites",
                "Continue current training initiatives"
            ],
            "visualizations": ["query_trend", "site_quality_heatmap"]
        },
        {
            "category": "efficacy_signal",
            "severity": "info",
            "title": "Positive Efficacy Trend Detected",
            "description": "Early analysis shows promising results in primary endpoint",
            "details": {
                "responder_rate_treatment": 0.68,
                "responder_rate_placebo": 0.45,
                "confidence_interval": "95% CI: 0.15-0.31",
                "n_evaluated": 450
            },
            "recommendations": [
                "Continue monitoring for consistency",
                "Prepare for potential interim analysis"
            ],
            "visualizations": ["waterfall_plot", "spider_plot"]
        },
        {
            "category": "site_performance",
            "severity": "warning",
            "title": "Site Variability in Protocol Compliance",
            "description": "Significant differences in protocol deviation rates across sites",
            "details": {
                "high_deviation_sites": ["Site 002", "Site 011"],
                "deviation_rate_range": {"min": 2.1, "max": 12.5},
                "most_common_deviations": ["Visit window violations", "Incorrect dosing"]
            },
            "recommendations": [
                "Conduct targeted retraining at high-deviation sites",
                "Implement additional monitoring visits"
            ],
            "visualizations": ["site_deviation_chart", "protocol_compliance_map"]
        }
    ]
    
    # Filter by requested insight types if specified
    if insight_types:
        insights["insights"] = [
            i for i in insight_categories 
            if i["category"] in insight_types
        ]
    else:
        insights["insights"] = insight_categories
    
    # Add summary statistics
    insights["summary"] = {
        "total_insights": len(insights["insights"]),
        "by_severity": {
            "warning": len([i for i in insights["insights"] if i["severity"] == "warning"]),
            "info": len([i for i in insights["insights"] if i["severity"] == "info"]),
            "success": len([i for i in insights["insights"] if i["severity"] == "success"])
        },
        "actionable_items": sum(len(i.get("recommendations", [])) for i in insights["insights"])
    }
    
    return insights


@router.post("/studies/{study_id}/visualizations/custom", response_model=Dict[str, Any])
async def create_custom_visualization(
    study_id: uuid.UUID,
    viz_config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.CREATE_WIDGETS))
) -> Any:
    """
    Create a custom visualization with user-defined parameters.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract visualization configuration
    viz_type = viz_config.get("type")
    name = viz_config.get("name")
    description = viz_config.get("description", "")
    config = viz_config.get("config", {})
    
    # TODO: Implement actual custom visualization creation
    
    new_viz = {
        "id": str(uuid.uuid4()),
        "study_id": str(study_id),
        "name": name,
        "description": description,
        "type": viz_type,
        "config": config,
        "created_by": current_user.full_name or current_user.email,
        "created_at": datetime.utcnow().isoformat(),
        "status": "processing",
        "preview_available": False,
        "estimated_completion": (datetime.utcnow() + timedelta(seconds=30)).isoformat()
    }
    
    return new_viz