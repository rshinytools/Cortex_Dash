# ABOUTME: Template marketplace API endpoints for browsing, publishing, and managing templates
# ABOUTME: Handles marketplace operations, template ratings, reviews, and download functionality

import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_, func

from ....core.db import get_db
from ....core.permissions import require_user, require_admin, get_current_user
from ....models.dashboard import (
    DashboardTemplate, 
    TemplateVersion, 
    TemplateReview,
    TemplateReviewCreate,
    TemplateExportData,
    DashboardCategory,
    TemplateStatus,
    InheritanceType
)
from ....models.user import User
from ....services.template_validator import TemplateValidatorService, ValidationSeverity
from ....services.template_inheritance import TemplateInheritanceService
from pydantic import BaseModel
import json
from datetime import datetime

router = APIRouter()


class TemplateMarketplaceFilter(BaseModel):
    """Filters for marketplace template search"""
    category: Optional[str] = None
    min_rating: Optional[float] = None
    tags: Optional[List[str]] = None
    search_term: Optional[str] = None
    sort_by: str = "popular"  # popular, rating, recent, downloads, name
    is_verified_only: bool = False


class TemplatePublishRequest(BaseModel):
    """Request model for publishing templates"""
    name: str
    description: str
    category: DashboardCategory
    tags: List[str]
    license: str = "MIT"
    documentation_url: Optional[str] = None
    source_url: Optional[str] = None
    compatibility: List[str] = []
    requirements: List[str] = []
    is_public: bool = True


class TemplateMarketplaceItem(BaseModel):
    """Template item for marketplace listing"""
    id: uuid.UUID
    code: str
    name: str
    description: str
    category: str
    version_string: str
    screenshot_urls: List[str]
    tags: List[str]
    average_rating: Optional[float]
    total_ratings: int
    download_count: int
    creator_name: str
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    license: str = "MIT"


class TemplateDetails(TemplateMarketplaceItem):
    """Extended template details for individual template view"""
    documentation_url: Optional[str] = None
    source_url: Optional[str] = None
    compatibility: List[str]
    requirements: List[str]
    version_history: List[Dict[str, Any]]
    reviews: List[Dict[str, Any]]
    related_templates: List[Dict[str, Any]]


@router.get("/marketplace", response_model=List[TemplateMarketplaceItem])
async def get_marketplace_templates(
    category: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("popular"),
    tags: Optional[str] = Query(None),  # Comma-separated tags
    verified_only: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get templates from marketplace with filtering and sorting"""
    
    query = db.query(DashboardTemplate).filter(
        DashboardTemplate.is_public == True,
        DashboardTemplate.status == TemplateStatus.PUBLISHED.value
    )
    
    # Apply filters
    if category and category != "all":
        query = query.filter(DashboardTemplate.category == category)
    
    if min_rating:
        query = query.filter(DashboardTemplate.average_rating >= min_rating)
    
    if verified_only:
        # Join with creator to check verification status
        query = query.join(User, DashboardTemplate.created_by == User.id).filter(
            User.is_verified == True
        )
    
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(DashboardTemplate.name).like(search_term),
                func.lower(DashboardTemplate.description).like(search_term),
                DashboardTemplate.tags.op('?&')(search.split())  # PostgreSQL JSON operator
            )
        )
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.filter(DashboardTemplate.tags.op('@>')([tag]))
    
    # Apply sorting
    if sort_by == "rating":
        query = query.order_by(desc(DashboardTemplate.average_rating))
    elif sort_by == "recent":
        query = query.order_by(desc(DashboardTemplate.updated_at))
    elif sort_by == "downloads":
        query = query.order_by(desc(DashboardTemplate.download_count))
    elif sort_by == "name":
        query = query.order_by(asc(DashboardTemplate.name))
    else:  # popular (default)
        # Weighted combination of downloads and ratings
        query = query.order_by(
            desc(
                DashboardTemplate.download_count * 0.7 + 
                func.coalesce(DashboardTemplate.average_rating, 0) * DashboardTemplate.total_ratings * 0.3
            )
        )
    
    templates = query.offset(offset).limit(limit).all()
    
    # Format response
    result = []
    for template in templates:
        creator = db.query(User).filter(User.id == template.created_by).first()
        
        result.append(TemplateMarketplaceItem(
            id=template.id,
            code=template.code,
            name=template.name,
            description=template.description or "",
            category=template.category.value,
            version_string=template.version_string,
            screenshot_urls=template.screenshot_urls or [],
            tags=template.tags or [],
            average_rating=template.average_rating,
            total_ratings=template.total_ratings,
            download_count=template.download_count,
            creator_name=creator.full_name if creator else "Unknown",
            created_at=template.created_at,
            updated_at=template.updated_at,
            is_verified=creator.is_verified if creator else False,
            license="MIT"  # Default for now
        ))
    
    return result


@router.get("/marketplace/{template_id}", response_model=TemplateDetails)
async def get_template_details(
    template_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific template"""
    
    template = db.query(DashboardTemplate).filter(
        DashboardTemplate.id == template_id,
        DashboardTemplate.is_public == True,
        DashboardTemplate.status == TemplateStatus.PUBLISHED.value
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    creator = db.query(User).filter(User.id == template.created_by).first()
    
    # Get version history
    versions = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(desc(TemplateVersion.created_at)).all()
    
    version_history = []
    for version in versions:
        version_history.append({
            "version": version.version_string,
            "release_date": version.created_at.isoformat(),
            "changes": version.change_description.split('\n') if version.change_description else [],
            "breaking_changes": version.breaking_changes
        })
    
    # Get reviews
    reviews = db.query(TemplateReview).filter(
        TemplateReview.template_id == template_id
    ).order_by(desc(TemplateReview.created_at)).limit(10).all()
    
    review_list = []
    for review in reviews:
        reviewer = db.query(User).filter(User.id == review.reviewed_by).first()
        review_list.append({
            "id": str(review.id),
            "user_name": reviewer.full_name if reviewer else "Anonymous",
            "rating": review.rating,
            "review_text": review.review_text or "",
            "created_at": review.created_at.isoformat(),
            "is_verified": review.is_verified_user
        })
    
    # Get related templates (same category, high rated)
    related = db.query(DashboardTemplate).filter(
        DashboardTemplate.category == template.category,
        DashboardTemplate.id != template_id,
        DashboardTemplate.is_public == True,
        DashboardTemplate.status == TemplateStatus.PUBLISHED.value
    ).order_by(desc(DashboardTemplate.average_rating)).limit(3).all()
    
    related_templates = []
    for rel_template in related:
        related_templates.append({
            "id": str(rel_template.id),
            "name": rel_template.name,
            "category": rel_template.category.value,
            "rating": rel_template.average_rating or 0,
            "downloads": rel_template.download_count
        })
    
    return TemplateDetails(
        id=template.id,
        code=template.code,
        name=template.name,
        description=template.description or "",
        category=template.category.value,
        version_string=template.version_string,
        screenshot_urls=template.screenshot_urls or [],
        tags=template.tags or [],
        average_rating=template.average_rating,
        total_ratings=template.total_ratings,
        download_count=template.download_count,
        creator_name=creator.full_name if creator else "Unknown",
        created_at=template.created_at,
        updated_at=template.updated_at,
        is_verified=creator.is_verified if creator else False,
        license="MIT",
        documentation_url=template.documentation_url,
        source_url=None,  # Not stored in current model
        compatibility=[],  # Not stored in current model
        requirements=[],  # Not stored in current model
        version_history=version_history,
        reviews=review_list,
        related_templates=related_templates
    )


@router.post("/marketplace/publish")
async def publish_template(
    template_file: UploadFile = File(...),
    metadata: str = Form(...),
    screenshots: List[UploadFile] = File([]),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Publish a new template to the marketplace"""
    
    try:
        # Parse metadata
        template_metadata = TemplatePublishRequest.parse_raw(metadata)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid metadata: {str(e)}")
    
    # Validate template file
    if not template_file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Template file must be JSON")
    
    try:
        template_content = await template_file.read()
        template_structure = json.loads(template_content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in template file")
    
    # Validate template structure
    validator = TemplateValidatorService()
    is_valid, validation_issues = validator.validate_template_structure(template_structure)
    
    if not is_valid:
        error_issues = [issue for issue in validation_issues if issue.severity == ValidationSeverity.ERROR]
        raise HTTPException(
            status_code=400, 
            detail=f"Template validation failed: {[issue.message for issue in error_issues]}"
        )
    
    # Generate unique code
    base_code = template_metadata.name.lower().replace(' ', '-').replace('_', '-')
    code = base_code
    counter = 1
    while db.query(DashboardTemplate).filter(DashboardTemplate.code == code).first():
        code = f"{base_code}-{counter}"
        counter += 1
    
    # Process screenshots (in a real implementation, upload to cloud storage)
    screenshot_urls = []
    for i, screenshot in enumerate(screenshots):
        if screenshot.filename:
            # In real implementation, upload to S3/GCS and get URLs
            screenshot_urls.append(f"/api/templates/{code}/screenshots/{i}.png")
    
    # Create template
    template = DashboardTemplate(
        code=code,
        name=template_metadata.name,
        description=template_metadata.description,
        category=template_metadata.category,
        template_structure=template_structure,
        tags=template_metadata.tags,
        screenshot_urls=screenshot_urls,
        documentation_url=template_metadata.documentation_url,
        is_public=template_metadata.is_public,
        status=TemplateStatus.PUBLISHED if template_metadata.is_public else TemplateStatus.DRAFT,
        created_by=current_user.id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    # Create initial version entry
    initial_version = TemplateVersion(
        template_id=template.id,
        major_version=template.major_version,
        minor_version=template.minor_version,
        patch_version=template.patch_version,
        change_description="Initial marketplace release",
        template_structure=template_structure,
        is_published=True,
        created_by=current_user.id
    )
    
    db.add(initial_version)
    db.commit()
    
    return {"message": "Template published successfully", "template_id": str(template.id)}


@router.post("/marketplace/{template_id}/download")
async def download_template(
    template_id: uuid.UUID,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Download a template from the marketplace"""
    
    template = db.query(DashboardTemplate).filter(
        DashboardTemplate.id == template_id,
        or_(
            DashboardTemplate.is_public == True,
            DashboardTemplate.created_by == current_user.id
        )
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Increment download count
    template.download_count += 1
    db.commit()
    
    # Get effective template structure (with inheritance resolved)
    inheritance_service = TemplateInheritanceService(db)
    effective_structure = inheritance_service.get_effective_template(template_id)
    
    # Create export data
    export_data = TemplateExportData(
        template=template,
        versions=[],  # Include versions if needed
        metadata={
            "exported_by": current_user.id,
            "export_timestamp": datetime.utcnow(),
            "original_template_id": str(template_id)
        }
    )
    
    return {
        "template": {
            "id": str(template.id),
            "code": template.code,
            "name": template.name,
            "description": template.description,
            "version": template.version_string,
            "structure": effective_structure,
            "metadata": export_data.metadata
        }
    }


@router.post("/marketplace/{template_id}/review", response_model=dict)
async def create_review(
    template_id: uuid.UUID,
    review: TemplateReviewCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Create a review for a template"""
    
    template = db.query(DashboardTemplate).filter(
        DashboardTemplate.id == template_id,
        DashboardTemplate.is_public == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if user already reviewed this template
    existing_review = db.query(TemplateReview).filter(
        TemplateReview.template_id == template_id,
        TemplateReview.reviewed_by == current_user.id
    ).first()
    
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this template")
    
    # Create review
    new_review = TemplateReview(
        template_id=template_id,
        rating=review.rating,
        review_text=review.review_text,
        is_verified_user=current_user.is_verified,
        reviewed_by=current_user.id
    )
    
    db.add(new_review)
    
    # Update template rating statistics
    all_reviews = db.query(TemplateReview).filter(
        TemplateReview.template_id == template_id
    ).all()
    
    total_rating = sum(r.rating for r in all_reviews) + review.rating
    total_count = len(all_reviews) + 1
    
    template.average_rating = total_rating / total_count
    template.total_ratings = total_count
    
    db.commit()
    
    return {"message": "Review created successfully"}


@router.get("/marketplace/{template_id}/reviews")
async def get_template_reviews(
    template_id: uuid.UUID,
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get reviews for a specific template"""
    
    template = db.query(DashboardTemplate).filter(
        DashboardTemplate.id == template_id,
        DashboardTemplate.is_public == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    reviews = db.query(TemplateReview).filter(
        TemplateReview.template_id == template_id
    ).order_by(desc(TemplateReview.created_at)).offset(offset).limit(limit).all()
    
    result = []
    for review in reviews:
        reviewer = db.query(User).filter(User.id == review.reviewed_by).first()
        result.append({
            "id": str(review.id),
            "user_name": reviewer.full_name if reviewer else "Anonymous",
            "rating": review.rating,
            "review_text": review.review_text,
            "created_at": review.created_at.isoformat(),
            "is_verified": review.is_verified_user
        })
    
    return result


@router.get("/marketplace/categories")
async def get_marketplace_categories(db: Session = Depends(get_db)):
    """Get available template categories with counts"""
    
    category_counts = db.query(
        DashboardTemplate.category,
        func.count(DashboardTemplate.id).label('count')
    ).filter(
        DashboardTemplate.is_public == True,
        DashboardTemplate.status == TemplateStatus.PUBLISHED.value
    ).group_by(DashboardTemplate.category).all()
    
    categories = []
    for category, count in category_counts:
        categories.append({
            "value": category.value,
            "label": category.value.title(),
            "count": count
        })
    
    return categories


@router.get("/marketplace/stats")
async def get_marketplace_stats(db: Session = Depends(get_db)):
    """Get marketplace statistics"""
    
    total_templates = db.query(func.count(DashboardTemplate.id)).filter(
        DashboardTemplate.is_public == True,
        DashboardTemplate.status == TemplateStatus.PUBLISHED.value
    ).scalar()
    
    total_downloads = db.query(func.sum(DashboardTemplate.download_count)).filter(
        DashboardTemplate.is_public == True,
        DashboardTemplate.status == TemplateStatus.PUBLISHED.value
    ).scalar() or 0
    
    avg_rating = db.query(func.avg(DashboardTemplate.average_rating)).filter(
        DashboardTemplate.is_public == True,
        DashboardTemplate.status == TemplateStatus.PUBLISHED.value,
        DashboardTemplate.average_rating.isnot(None)
    ).scalar() or 0
    
    total_reviews = db.query(func.count(TemplateReview.id)).join(
        DashboardTemplate, TemplateReview.template_id == DashboardTemplate.id
    ).filter(
        DashboardTemplate.is_public == True,
        DashboardTemplate.status == TemplateStatus.PUBLISHED.value
    ).scalar()
    
    return {
        "total_templates": total_templates,
        "total_downloads": total_downloads,
        "average_rating": round(float(avg_rating), 2),
        "total_reviews": total_reviews
    }