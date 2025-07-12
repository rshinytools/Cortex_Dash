# ABOUTME: API endpoints for managing organization and study branding
# ABOUTME: Handles logo and favicon uploads, storage, and retrieval for multi-tenant branding

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Query
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from datetime import datetime
import uuid
import os
import shutil
from PIL import Image
import io

from app.api.deps import get_db, get_current_user
from app.models import User, Study, Organization
from app.core.permissions import Permission, require_permission
from app.core.config import settings

router = APIRouter()

# Allowed file extensions and MIME types
ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico"
}

# Maximum file sizes (in bytes)
MAX_LOGO_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FAVICON_SIZE = 1 * 1024 * 1024  # 1MB

# Default paths for storing branding assets
BRANDING_BASE_PATH = os.path.join("/data/uploads", "branding")
ORG_BRANDING_PATH = os.path.join(BRANDING_BASE_PATH, "organizations")
STUDY_BRANDING_PATH = os.path.join(BRANDING_BASE_PATH, "studies")


@router.post("/organizations/{org_id}/logo", response_model=Dict[str, Any])
async def upload_organization_logo(
    org_id: uuid.UUID,
    logo: UploadFile = File(...),
    theme: Optional[str] = Form("light", description="Theme variant (light/dark)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Upload or update organization logo.
    """
    # Verify organization exists and user has access
    org = db.exec(select(Organization).where(Organization.id == org_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not current_user.is_superuser and str(current_user.org_id) != str(org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate file type
    if logo.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES.values())}"
        )
    
    # Check file size
    contents = await logo.read()
    if len(contents) > MAX_LOGO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_LOGO_SIZE / 1024 / 1024}MB"
        )
    
    # Create directory structure
    org_logo_dir = os.path.join(ORG_BRANDING_PATH, str(org_id))
    os.makedirs(org_logo_dir, exist_ok=True)
    
    # Generate filename
    file_ext = ALLOWED_IMAGE_TYPES[logo.content_type]
    filename = f"logo_{theme}{file_ext}"
    file_path = os.path.join(org_logo_dir, filename)
    
    # Process and save image
    try:
        # For SVG files, save as-is
        if logo.content_type == "image/svg+xml":
            with open(file_path, "wb") as f:
                f.write(contents)
        else:
            # For other formats, process with PIL
            image = Image.open(io.BytesIO(contents))
            
            # Resize if needed (max 500px width while maintaining aspect ratio)
            if image.width > 500:
                ratio = 500 / image.width
                new_size = (500, int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            image.save(file_path, quality=85, optimize=True)
        
        # Generate additional sizes for responsive display
        if logo.content_type != "image/svg+xml":
            generate_logo_sizes(file_path, org_logo_dir, theme)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )
    
    # Update organization branding settings
    if not org.settings:
        org.settings = {}
    
    if "branding" not in org.settings:
        org.settings["branding"] = {}
    
    org.settings["branding"][f"logo_{theme}"] = {
        "filename": filename,
        "url": f"/api/v1/branding/organizations/{org_id}/logo?theme={theme}",
        "uploaded_at": datetime.utcnow().isoformat(),
        "uploaded_by": current_user.email,
        "mime_type": logo.content_type,
        "sizes": {
            "original": filename,
            "medium": f"logo_{theme}_medium{file_ext}" if logo.content_type != "image/svg+xml" else filename,
            "small": f"logo_{theme}_small{file_ext}" if logo.content_type != "image/svg+xml" else filename
        }
    }
    
    db.add(org)
    db.commit()
    
    return {
        "organization_id": str(org_id),
        "theme": theme,
        "logo_url": org.settings["branding"][f"logo_{theme}"]["url"],
        "sizes": org.settings["branding"][f"logo_{theme}"]["sizes"],
        "message": "Logo uploaded successfully"
    }


@router.get("/organizations/{org_id}/logo")
async def get_organization_logo(
    org_id: uuid.UUID,
    theme: str = Query("light", description="Theme variant"),
    size: str = Query("original", description="Size variant (original/medium/small)"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get organization logo.
    """
    # Check if logo exists
    org = db.exec(select(Organization).where(Organization.id == org_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    branding = org.settings.get("branding", {}) if org.settings else {}
    logo_info = branding.get(f"logo_{theme}")
    
    if not logo_info:
        # Return default logo
        default_logo_path = os.path.join(BRANDING_BASE_PATH, "defaults", f"logo_{theme}.png")
        if os.path.exists(default_logo_path):
            return FileResponse(default_logo_path, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Logo not found")
    
    # Get requested size
    sizes = logo_info.get("sizes", {})
    filename = sizes.get(size, logo_info["filename"])
    file_path = os.path.join(ORG_BRANDING_PATH, str(org_id), filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Logo file not found")
    
    return FileResponse(file_path, media_type=logo_info["mime_type"])


@router.post("/organizations/{org_id}/favicon", response_model=Dict[str, Any])
async def upload_organization_favicon(
    org_id: uuid.UUID,
    favicon: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Upload or update organization favicon.
    """
    # Verify organization exists and user has access
    org = db.exec(select(Organization).where(Organization.id == org_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not current_user.is_superuser and str(current_user.org_id) != str(org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate file type
    allowed_favicon_types = ["image/x-icon", "image/vnd.microsoft.icon", "image/png"]
    if favicon.content_type not in allowed_favicon_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Favicon must be .ico or .png"
        )
    
    # Check file size
    contents = await favicon.read()
    if len(contents) > MAX_FAVICON_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FAVICON_SIZE / 1024}KB"
        )
    
    # Create directory structure
    org_favicon_dir = os.path.join(ORG_BRANDING_PATH, str(org_id))
    os.makedirs(org_favicon_dir, exist_ok=True)
    
    # Save favicon
    try:
        # Generate multiple favicon sizes
        if favicon.content_type == "image/png":
            image = Image.open(io.BytesIO(contents))
            
            # Generate standard favicon sizes
            sizes = [16, 32, 48, 64, 128, 256]
            favicon_files = {}
            
            for size in sizes:
                sized_image = image.resize((size, size), Image.Resampling.LANCZOS)
                filename = f"favicon-{size}x{size}.png"
                file_path = os.path.join(org_favicon_dir, filename)
                sized_image.save(file_path, "PNG", optimize=True)
                favicon_files[f"{size}x{size}"] = filename
            
            # Also save as .ico with multiple sizes
            ico_path = os.path.join(org_favicon_dir, "favicon.ico")
            image.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
            favicon_files["ico"] = "favicon.ico"
            
        else:
            # For .ico files, save as-is
            filename = "favicon.ico"
            file_path = os.path.join(org_favicon_dir, filename)
            with open(file_path, "wb") as f:
                f.write(contents)
            favicon_files = {"ico": filename}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing favicon: {str(e)}"
        )
    
    # Update organization branding settings
    if not org.settings:
        org.settings = {}
    
    if "branding" not in org.settings:
        org.settings["branding"] = {}
    
    org.settings["branding"]["favicon"] = {
        "files": favicon_files,
        "url": f"/api/v1/branding/organizations/{org_id}/favicon",
        "uploaded_at": datetime.utcnow().isoformat(),
        "uploaded_by": current_user.email,
        "mime_type": favicon.content_type
    }
    
    db.add(org)
    db.commit()
    
    return {
        "organization_id": str(org_id),
        "favicon_url": org.settings["branding"]["favicon"]["url"],
        "sizes": list(favicon_files.keys()),
        "message": "Favicon uploaded successfully"
    }


@router.get("/organizations/{org_id}/favicon")
async def get_organization_favicon(
    org_id: uuid.UUID,
    size: Optional[str] = Query(None, description="Size (16x16, 32x32, etc.) or 'ico'"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get organization favicon.
    """
    # Check if favicon exists
    org = db.exec(select(Organization).where(Organization.id == org_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    branding = org.settings.get("branding", {}) if org.settings else {}
    favicon_info = branding.get("favicon")
    
    if not favicon_info:
        # Return default favicon
        default_favicon_path = os.path.join(BRANDING_BASE_PATH, "defaults", "favicon.ico")
        if os.path.exists(default_favicon_path):
            return FileResponse(default_favicon_path, media_type="image/x-icon")
        else:
            raise HTTPException(status_code=404, detail="Favicon not found")
    
    # Get requested size or default to .ico
    files = favicon_info.get("files", {})
    if size and size in files:
        filename = files[size]
    else:
        filename = files.get("ico", list(files.values())[0])
    
    file_path = os.path.join(ORG_BRANDING_PATH, str(org_id), filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Favicon file not found")
    
    # Determine mime type
    if filename.endswith(".ico"):
        media_type = "image/x-icon"
    else:
        media_type = "image/png"
    
    return FileResponse(file_path, media_type=media_type)


@router.post("/studies/{study_id}/logo", response_model=Dict[str, Any])
async def upload_study_logo(
    study_id: uuid.UUID,
    logo: UploadFile = File(...),
    theme: Optional[str] = Form("light", description="Theme variant (light/dark)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Upload or update study-specific logo.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate file type
    if logo.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES.values())}"
        )
    
    # Check file size
    contents = await logo.read()
    if len(contents) > MAX_LOGO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_LOGO_SIZE / 1024 / 1024}MB"
        )
    
    # Create directory structure
    study_logo_dir = os.path.join(STUDY_BRANDING_PATH, str(study_id))
    os.makedirs(study_logo_dir, exist_ok=True)
    
    # Generate filename
    file_ext = ALLOWED_IMAGE_TYPES[logo.content_type]
    filename = f"logo_{theme}{file_ext}"
    file_path = os.path.join(study_logo_dir, filename)
    
    # Process and save image (similar to org logo)
    try:
        if logo.content_type == "image/svg+xml":
            with open(file_path, "wb") as f:
                f.write(contents)
        else:
            image = Image.open(io.BytesIO(contents))
            
            if image.width > 400:
                ratio = 400 / image.width
                new_size = (400, int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            image.save(file_path, quality=85, optimize=True)
            generate_logo_sizes(file_path, study_logo_dir, theme)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )
    
    # Update study configuration
    if not study.configuration:
        study.configuration = {}
    
    if "branding" not in study.configuration:
        study.configuration["branding"] = {}
    
    study.configuration["branding"][f"logo_{theme}"] = {
        "filename": filename,
        "url": f"/api/v1/branding/studies/{study_id}/logo?theme={theme}",
        "uploaded_at": datetime.utcnow().isoformat(),
        "uploaded_by": current_user.email,
        "mime_type": logo.content_type,
        "sizes": {
            "original": filename,
            "medium": f"logo_{theme}_medium{file_ext}" if logo.content_type != "image/svg+xml" else filename,
            "small": f"logo_{theme}_small{file_ext}" if logo.content_type != "image/svg+xml" else filename
        }
    }
    
    db.add(study)
    db.commit()
    
    return {
        "study_id": str(study_id),
        "theme": theme,
        "logo_url": study.configuration["branding"][f"logo_{theme}"]["url"],
        "sizes": study.configuration["branding"][f"logo_{theme}"]["sizes"],
        "message": "Study logo uploaded successfully"
    }


@router.get("/studies/{study_id}/logo")
async def get_study_logo(
    study_id: uuid.UUID,
    theme: str = Query("light", description="Theme variant"),
    size: str = Query("original", description="Size variant"),
    fallback_to_org: bool = Query(True, description="Use organization logo if study logo not found"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get study logo with fallback to organization logo.
    """
    # Check if study logo exists
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    branding = study.configuration.get("branding", {}) if study.configuration else {}
    logo_info = branding.get(f"logo_{theme}")
    
    if logo_info:
        # Return study logo
        sizes = logo_info.get("sizes", {})
        filename = sizes.get(size, logo_info["filename"])
        file_path = os.path.join(STUDY_BRANDING_PATH, str(study_id), filename)
        
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type=logo_info["mime_type"])
    
    # Fallback to organization logo if enabled
    if fallback_to_org:
        return await get_organization_logo(study.org_id, theme, size, db)
    
    raise HTTPException(status_code=404, detail="Logo not found")


@router.post("/studies/{study_id}/favicon", response_model=Dict[str, Any])
async def upload_study_favicon(
    study_id: uuid.UUID,
    favicon: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Upload or update study-specific favicon.
    """
    # Similar implementation to organization favicon
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Process favicon (similar to org favicon)
    allowed_favicon_types = ["image/x-icon", "image/vnd.microsoft.icon", "image/png"]
    if favicon.content_type not in allowed_favicon_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Favicon must be .ico or .png"
        )
    
    contents = await favicon.read()
    if len(contents) > MAX_FAVICON_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FAVICON_SIZE / 1024}KB"
        )
    
    # Save favicon with multiple sizes
    study_favicon_dir = os.path.join(STUDY_BRANDING_PATH, str(study_id))
    os.makedirs(study_favicon_dir, exist_ok=True)
    
    # Process and save (same as org favicon logic)
    favicon_files = process_favicon(contents, favicon.content_type, study_favicon_dir)
    
    # Update study configuration
    if not study.configuration:
        study.configuration = {}
    
    if "branding" not in study.configuration:
        study.configuration["branding"] = {}
    
    study.configuration["branding"]["favicon"] = {
        "files": favicon_files,
        "url": f"/api/v1/branding/studies/{study_id}/favicon",
        "uploaded_at": datetime.utcnow().isoformat(),
        "uploaded_by": current_user.email,
        "mime_type": favicon.content_type
    }
    
    db.add(study)
    db.commit()
    
    return {
        "study_id": str(study_id),
        "favicon_url": study.configuration["branding"]["favicon"]["url"],
        "sizes": list(favicon_files.keys()),
        "message": "Study favicon uploaded successfully"
    }


@router.get("/studies/{study_id}/favicon")
async def get_study_favicon(
    study_id: uuid.UUID,
    size: Optional[str] = Query(None, description="Size or 'ico'"),
    fallback_to_org: bool = Query(True, description="Use organization favicon if study favicon not found"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get study favicon with fallback to organization favicon.
    """
    # Check if study favicon exists
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    branding = study.configuration.get("branding", {}) if study.configuration else {}
    favicon_info = branding.get("favicon")
    
    if favicon_info:
        # Return study favicon
        files = favicon_info.get("files", {})
        if size and size in files:
            filename = files[size]
        else:
            filename = files.get("ico", list(files.values())[0])
        
        file_path = os.path.join(STUDY_BRANDING_PATH, str(study_id), filename)
        
        if os.path.exists(file_path):
            media_type = "image/x-icon" if filename.endswith(".ico") else "image/png"
            return FileResponse(file_path, media_type=media_type)
    
    # Fallback to organization favicon if enabled
    if fallback_to_org:
        return await get_organization_favicon(study.org_id, size, db)
    
    raise HTTPException(status_code=404, detail="Favicon not found")


@router.delete("/organizations/{org_id}/branding")
async def delete_organization_branding(
    org_id: uuid.UUID,
    asset_type: str = Query(..., description="Type of asset to delete (logo/favicon/all)"),
    theme: Optional[str] = Query(None, description="Theme variant for logo deletion"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete organization branding assets.
    """
    # Verify organization exists and user has access
    org = db.exec(select(Organization).where(Organization.id == org_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not current_user.is_superuser and str(current_user.org_id) != str(org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete files
    org_branding_dir = os.path.join(ORG_BRANDING_PATH, str(org_id))
    deleted_items = []
    
    if asset_type in ["logo", "all"]:
        if theme:
            # Delete specific theme logo
            logo_files = [f for f in os.listdir(org_branding_dir) if f.startswith(f"logo_{theme}")]
            for file in logo_files:
                os.remove(os.path.join(org_branding_dir, file))
                deleted_items.append(file)
            
            # Update settings
            if org.settings and "branding" in org.settings:
                org.settings["branding"].pop(f"logo_{theme}", None)
        else:
            # Delete all logos
            logo_files = [f for f in os.listdir(org_branding_dir) if f.startswith("logo_")]
            for file in logo_files:
                os.remove(os.path.join(org_branding_dir, file))
                deleted_items.append(file)
            
            # Update settings
            if org.settings and "branding" in org.settings:
                keys_to_remove = [k for k in org.settings["branding"].keys() if k.startswith("logo_")]
                for key in keys_to_remove:
                    org.settings["branding"].pop(key)
    
    if asset_type in ["favicon", "all"]:
        # Delete favicon files
        favicon_files = [f for f in os.listdir(org_branding_dir) if f.startswith("favicon")]
        for file in favicon_files:
            os.remove(os.path.join(org_branding_dir, file))
            deleted_items.append(file)
        
        # Update settings
        if org.settings and "branding" in org.settings:
            org.settings["branding"].pop("favicon", None)
    
    db.add(org)
    db.commit()
    
    return {
        "organization_id": str(org_id),
        "deleted_items": deleted_items,
        "message": f"{asset_type} branding assets deleted successfully"
    }


@router.get("/branding-summary/{org_id}", response_model=Dict[str, Any])
async def get_branding_summary(
    org_id: uuid.UUID,
    include_studies: bool = Query(True, description="Include study-specific branding"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get summary of all branding assets for an organization and its studies.
    """
    # Verify organization exists and user has access
    org = db.exec(select(Organization).where(Organization.id == org_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not current_user.is_superuser and str(current_user.org_id) != str(org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get organization branding
    org_branding = org.settings.get("branding", {}) if org.settings else {}
    
    summary = {
        "organization": {
            "id": str(org_id),
            "name": org.name,
            "branding": {
                "logo_light": org_branding.get("logo_light", {}).get("url") if "logo_light" in org_branding else None,
                "logo_dark": org_branding.get("logo_dark", {}).get("url") if "logo_dark" in org_branding else None,
                "favicon": org_branding.get("favicon", {}).get("url") if "favicon" in org_branding else None,
                "color_theme": org.settings.get("color_theme", "default") if org.settings else "default"
            }
        },
        "studies": []
    }
    
    if include_studies:
        # Get all studies for the organization
        studies = db.exec(select(Study).where(Study.org_id == org_id)).all()
        
        for study in studies:
            study_branding = study.configuration.get("branding", {}) if study.configuration else {}
            
            summary["studies"].append({
                "id": str(study.id),
                "name": study.name,
                "protocol_number": study.protocol_number,
                "branding": {
                    "logo_light": study_branding.get("logo_light", {}).get("url") if "logo_light" in study_branding else None,
                    "logo_dark": study_branding.get("logo_dark", {}).get("url") if "logo_dark" in study_branding else None,
                    "favicon": study_branding.get("favicon", {}).get("url") if "favicon" in study_branding else None,
                    "uses_org_branding": not bool(study_branding)
                }
            })
    
    return summary


# Helper functions
def generate_logo_sizes(original_path: str, output_dir: str, theme: str):
    """Generate multiple sizes for responsive display."""
    try:
        image = Image.open(original_path)
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        ext = os.path.splitext(original_path)[1]
        
        # Generate medium size (250px width)
        if image.width > 250:
            ratio = 250 / image.width
            medium_size = (250, int(image.height * ratio))
            medium_image = image.resize(medium_size, Image.Resampling.LANCZOS)
            medium_path = os.path.join(output_dir, f"{base_name}_medium{ext}")
            medium_image.save(medium_path, quality=85, optimize=True)
        
        # Generate small size (100px width)
        if image.width > 100:
            ratio = 100 / image.width
            small_size = (100, int(image.height * ratio))
            small_image = image.resize(small_size, Image.Resampling.LANCZOS)
            small_path = os.path.join(output_dir, f"{base_name}_small{ext}")
            small_image.save(small_path, quality=85, optimize=True)
            
    except Exception as e:
        # Log error but don't fail the upload
        print(f"Error generating logo sizes: {str(e)}")


def process_favicon(contents: bytes, content_type: str, output_dir: str) -> Dict[str, str]:
    """Process favicon and generate multiple sizes."""
    favicon_files = {}
    
    try:
        if content_type == "image/png":
            image = Image.open(io.BytesIO(contents))
            
            # Generate standard favicon sizes
            sizes = [16, 32, 48, 64, 128, 256]
            
            for size in sizes:
                sized_image = image.resize((size, size), Image.Resampling.LANCZOS)
                filename = f"favicon-{size}x{size}.png"
                file_path = os.path.join(output_dir, filename)
                sized_image.save(file_path, "PNG", optimize=True)
                favicon_files[f"{size}x{size}"] = filename
            
            # Also save as .ico with multiple sizes
            ico_path = os.path.join(output_dir, "favicon.ico")
            image.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
            favicon_files["ico"] = "favicon.ico"
            
        else:
            # For .ico files, save as-is
            filename = "favicon.ico"
            file_path = os.path.join(output_dir, filename)
            with open(file_path, "wb") as f:
                f.write(contents)
            favicon_files = {"ico": filename}
            
    except Exception as e:
        raise Exception(f"Error processing favicon: {str(e)}")
    
    return favicon_files