# ABOUTME: API endpoints for data quality management
# ABOUTME: Handles quality rules, validation, and issue tracking

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime, timedelta
import uuid

from app.api.deps import get_db, get_current_user
from app.models import User, Study, Message
from app.core.permissions import Permission, require_permission

router = APIRouter()


@router.get("/studies/{study_id}/data-quality/rules", response_model=List[Dict[str, Any]])
async def list_quality_rules(
    study_id: uuid.UUID,
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    severity: Optional[str] = Query(None, enum=["error", "warning", "info"]),
    active_only: bool = Query(True, description="Show only active rules"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    List all data quality rules configured for a study.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement actual rule retrieval
    # For now, return mock rules
    rules = [
        {
            "id": str(uuid.uuid4()),
            "name": "Subject Age Range Check",
            "description": "Ensure all subjects are within protocol-defined age range (18-75)",
            "type": "range_check",
            "severity": "error",
            "active": True,
            "dataset": "ADSL",
            "field": "AGE",
            "condition": {
                "type": "range",
                "min": 18,
                "max": 75,
                "inclusive": True
            },
            "created_at": datetime.utcnow().isoformat(),
            "last_run": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "last_result": "passed",
            "violations_count": 0
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Missing Primary Endpoint",
            "description": "Check for subjects missing primary endpoint data",
            "type": "completeness_check",
            "severity": "error",
            "active": True,
            "dataset": "ADEFF",
            "field": "AVAL",
            "condition": {
                "type": "not_null",
                "where": "PARAMCD = 'PRIMEND'"
            },
            "created_at": datetime.utcnow().isoformat(),
            "last_run": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "last_result": "failed",
            "violations_count": 3
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Adverse Event Date Consistency",
            "description": "AE start date should not be before first dose date",
            "type": "consistency_check",
            "severity": "warning",
            "active": True,
            "dataset": "ADAE",
            "field": "ASTDT",
            "condition": {
                "type": "date_comparison",
                "compare_to": "TRTSDT",
                "operator": ">="
            },
            "created_at": datetime.utcnow().isoformat(),
            "last_run": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "last_result": "warning",
            "violations_count": 12
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Lab Value Outliers",
            "description": "Flag laboratory values outside of 3 standard deviations",
            "type": "statistical_check",
            "severity": "info",
            "active": True,
            "dataset": "LB",
            "field": "LBSTRESN",
            "condition": {
                "type": "statistical",
                "method": "z_score",
                "threshold": 3
            },
            "created_at": datetime.utcnow().isoformat(),
            "last_run": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "last_result": "info",
            "violations_count": 45
        }
    ]
    
    # Apply filters
    if rule_type:
        rules = [r for r in rules if r["type"] == rule_type]
    
    if severity:
        rules = [r for r in rules if r["severity"] == severity]
    
    if active_only:
        rules = [r for r in rules if r["active"]]
    
    return rules


@router.post("/studies/{study_id}/data-quality/rules", response_model=Dict[str, Any])
async def create_quality_rule(
    study_id: uuid.UUID,
    rule_config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Create a new data quality rule for the study.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract rule configuration
    name = rule_config.get("name")
    description = rule_config.get("description", "")
    rule_type = rule_config.get("type")
    severity = rule_config.get("severity", "warning")
    dataset = rule_config.get("dataset")
    field = rule_config.get("field")
    condition = rule_config.get("condition")
    
    if not all([name, rule_type, dataset, condition]):
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: name, type, dataset, condition"
        )
    
    # TODO: Implement actual rule creation logic
    new_rule = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "type": rule_type,
        "severity": severity,
        "active": True,
        "dataset": dataset,
        "field": field,
        "condition": condition,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.full_name or current_user.email,
        "last_modified": datetime.utcnow().isoformat(),
        "last_modified_by": current_user.full_name or current_user.email
    }
    
    return new_rule


@router.post("/studies/{study_id}/data-quality/validate", response_model=Dict[str, Any])
async def run_quality_validation(
    study_id: uuid.UUID,
    validation_options: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Run data quality validation against configured rules.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract validation options
    validation_options = validation_options or {}
    rule_ids = validation_options.get("rule_ids", [])  # Empty means all rules
    datasets = validation_options.get("datasets", [])  # Empty means all datasets
    async_mode = validation_options.get("async", True)
    
    # TODO: Implement actual validation logic
    # For async mode, return job details
    if async_mode:
        return {
            "job_id": str(uuid.uuid4()),
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "estimated_duration_minutes": 5,
            "validation_scope": {
                "total_rules": 25 if not rule_ids else len(rule_ids),
                "total_datasets": 10 if not datasets else len(datasets),
                "total_records": 50000
            }
        }
    
    # For sync mode, return immediate results (mock)
    return {
        "validation_id": str(uuid.uuid4()),
        "completed_at": datetime.utcnow().isoformat(),
        "duration_seconds": 45,
        "summary": {
            "rules_evaluated": 25,
            "rules_passed": 20,
            "rules_failed": 3,
            "rules_warning": 2,
            "total_issues": 60,
            "critical_issues": 3,
            "warning_issues": 12,
            "info_issues": 45
        },
        "results_by_severity": {
            "error": 3,
            "warning": 12,
            "info": 45
        },
        "results_by_dataset": {
            "ADSL": {"passed": 5, "failed": 0, "issues": 0},
            "ADAE": {"passed": 4, "failed": 1, "issues": 12},
            "LB": {"passed": 3, "failed": 1, "issues": 45},
            "ADEFF": {"passed": 4, "failed": 1, "issues": 3}
        }
    }


@router.get("/studies/{study_id}/data-quality/reports", response_model=List[Dict[str, Any]])
async def get_quality_reports(
    study_id: uuid.UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get historical data quality validation reports.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement actual report retrieval
    # For now, return mock reports
    reports = []
    for i in range(5):
        report_date = datetime.utcnow() - timedelta(days=i)
        reports.append({
            "id": str(uuid.uuid4()),
            "validation_date": report_date.isoformat(),
            "triggered_by": "Scheduled" if i % 2 == 0 else current_user.full_name or current_user.email,
            "duration_seconds": 45 + (i * 5),
            "data_version": f"v{5-i}.0",
            "summary": {
                "rules_evaluated": 25,
                "rules_passed": 20 + i,
                "rules_failed": 5 - i,
                "total_issues": 60 - (i * 10),
                "critical_issues": max(0, 3 - i),
                "data_quality_score": 85 + (i * 2)
            },
            "trending": {
                "issues_change": -10 if i > 0 else 0,
                "score_change": 2 if i > 0 else 0
            },
            "report_url": f"/api/v1/studies/{study_id}/data-quality/reports/{uuid.uuid4()}"
        })
    
    # Apply date filters
    if start_date:
        reports = [r for r in reports if datetime.fromisoformat(r["validation_date"]) >= start_date]
    
    if end_date:
        reports = [r for r in reports if datetime.fromisoformat(r["validation_date"]) <= end_date]
    
    return reports[:limit]


@router.get("/studies/{study_id}/data-quality/issues", response_model=Dict[str, Any])
async def get_quality_issues(
    study_id: uuid.UUID,
    severity: Optional[str] = Query(None, enum=["error", "warning", "info"]),
    dataset: Optional[str] = Query(None),
    rule_id: Optional[str] = Query(None),
    status: Optional[str] = Query("open", enum=["open", "resolved", "ignored", "all"]),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get current data quality issues with filtering and pagination.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement actual issue retrieval
    # For now, return mock issues
    all_issues = [
        {
            "id": str(uuid.uuid4()),
            "rule_id": str(uuid.uuid4()),
            "rule_name": "Missing Primary Endpoint",
            "severity": "error",
            "status": "open",
            "dataset": "ADEFF",
            "record_id": "STUDY001-0234",
            "field": "AVAL",
            "description": "Primary endpoint value is missing for Visit 12",
            "detected_date": datetime.utcnow().isoformat(),
            "data_version": "v5.0"
        },
        {
            "id": str(uuid.uuid4()),
            "rule_id": str(uuid.uuid4()),
            "rule_name": "Adverse Event Date Consistency",
            "severity": "warning",
            "status": "open",
            "dataset": "ADAE",
            "record_id": "STUDY001-0145",
            "field": "ASTDT",
            "description": "AE start date (2023-01-15) is before first dose date (2023-01-20)",
            "detected_date": datetime.utcnow().isoformat(),
            "data_version": "v5.0"
        },
        {
            "id": str(uuid.uuid4()),
            "rule_id": str(uuid.uuid4()),
            "rule_name": "Lab Value Outliers",
            "severity": "info",
            "status": "resolved",
            "dataset": "LB",
            "record_id": "STUDY001-0567",
            "field": "LBSTRESN",
            "description": "ALT value (245 U/L) is 4.2 standard deviations above mean",
            "detected_date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "resolved_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "resolved_by": "Dr. Smith",
            "resolution_note": "Confirmed with site - value is correct",
            "data_version": "v5.0"
        }
    ]
    
    # Apply filters
    if severity:
        all_issues = [i for i in all_issues if i["severity"] == severity]
    
    if dataset:
        all_issues = [i for i in all_issues if i["dataset"] == dataset]
    
    if rule_id:
        all_issues = [i for i in all_issues if i["rule_id"] == rule_id]
    
    if status != "all":
        all_issues = [i for i in all_issues if i["status"] == status]
    
    # Calculate total count before pagination
    total_count = len(all_issues)
    
    # Apply pagination
    paginated_issues = all_issues[skip:skip + limit]
    
    return {
        "total_count": total_count,
        "offset": skip,
        "limit": limit,
        "issues": paginated_issues,
        "summary": {
            "open_errors": len([i for i in all_issues if i["status"] == "open" and i["severity"] == "error"]),
            "open_warnings": len([i for i in all_issues if i["status"] == "open" and i["severity"] == "warning"]),
            "open_info": len([i for i in all_issues if i["status"] == "open" and i["severity"] == "info"]),
            "resolved_total": len([i for i in all_issues if i["status"] == "resolved"])
        }
    }


@router.put("/studies/{study_id}/data-quality/issues/{issue_id}/resolve")
async def resolve_quality_issue(
    study_id: uuid.UUID,
    issue_id: uuid.UUID,
    resolution: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Mark a data quality issue as resolved with resolution details.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract resolution details
    resolution_note = resolution.get("note", "")
    action_taken = resolution.get("action_taken", "verified")
    
    # TODO: Implement actual issue resolution logic
    
    return {
        "issue_id": str(issue_id),
        "status": "resolved",
        "resolved_date": datetime.utcnow().isoformat(),
        "resolved_by": current_user.full_name or current_user.email,
        "resolution_note": resolution_note,
        "action_taken": action_taken
    }