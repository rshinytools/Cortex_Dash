# ABOUTME: Medidata Rave integration for clinical trial data
# ABOUTME: Connects to Medidata Rave API to fetch study data and datasets

from typing import Dict, Any, List, Optional
from datetime import datetime
import base64
import hashlib
import hmac
import json

from app.services.integrations.base_integration import BaseIntegration, IntegrationType
from app.core.logging import logger

class MedidataRaveIntegration(BaseIntegration):
    """Medidata Rave EDC integration"""
    
    def __init__(self, data_source, db):
        super().__init__(data_source, db)
        self.integration_type = IntegrationType.MEDIDATA_RAVE
        self.base_url = self.get_config_value("base_url", "https://api.mdsol.com")
        self.api_version = "v1"
        
    async def authenticate(self) -> bool:
        """Authenticate with Medidata Rave using OAuth 2.0"""
        
        try:
            client_id = self.get_config_value("client_id")
            client_secret = self.get_config_value("client_secret")
            
            if not client_id or not client_secret:
                raise Exception("Missing authentication credentials")
            
            # OAuth 2.0 token endpoint
            token_url = f"{self.base_url}/oauth2/token"
            
            # Request access token
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "read:studies read:data"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = await self.make_request(
                method="POST",
                url=token_url,
                data=auth_data,
                headers=headers
            )
            
            if response.get("access_token"):
                self.auth_token = response["access_token"]
                self.update_config("auth_token", self.auth_token)
                self.update_config("token_expires", response.get("expires_in", 3600))
                
                logger.info("Successfully authenticated with Medidata Rave")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Medidata Rave authentication failed: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to Medidata Rave"""
        
        try:
            # Authenticate first
            if not self.auth_token:
                if not await self.authenticate():
                    return False
            
            # Test API endpoint
            test_url = f"{self.base_url}/api/{self.api_version}/studies"
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Accept": "application/json"
            }
            
            response = await self.make_request(
                method="GET",
                url=test_url,
                headers=headers,
                params={"limit": 1}
            )
            
            return response is not None
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    async def fetch_studies(self) -> List[Dict[str, Any]]:
        """Fetch available studies from Medidata Rave"""
        
        try:
            if not self.auth_token:
                await self.authenticate()
            
            studies_url = f"{self.base_url}/api/{self.api_version}/studies"
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Accept": "application/json"
            }
            
            response = await self.make_request(
                method="GET",
                url=studies_url,
                headers=headers
            )
            
            studies = []
            for study in response.get("studies", []):
                studies.append({
                    "id": study["oid"],
                    "name": study["name"],
                    "protocol": study.get("protocol_name", ""),
                    "phase": study.get("phase", ""),
                    "status": study.get("status", ""),
                    "site_count": study.get("site_count", 0),
                    "subject_count": study.get("subject_count", 0),
                    "created_date": study.get("created_date", ""),
                    "environment": study.get("environment", "production")
                })
            
            return studies
            
        except Exception as e:
            logger.error(f"Failed to fetch studies: {str(e)}")
            return []
    
    async def fetch_datasets(self, study_id: str) -> List[Dict[str, Any]]:
        """Fetch available datasets for a study"""
        
        try:
            if not self.auth_token:
                await self.authenticate()
            
            # Get study metadata
            metadata_url = f"{self.base_url}/api/{self.api_version}/studies/{study_id}/metadata"
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Accept": "application/json"
            }
            
            response = await self.make_request(
                method="GET",
                url=metadata_url,
                headers=headers
            )
            
            datasets = []
            
            # Extract forms/datasets
            for form in response.get("forms", []):
                datasets.append({
                    "name": form["oid"],
                    "label": form["name"],
                    "type": "clinical_form",
                    "fields": len(form.get("fields", [])),
                    "record_count": form.get("record_count", 0),
                    "last_modified": form.get("last_modified", "")
                })
            
            # Add standard datasets
            standard_datasets = [
                {"name": "DM", "label": "Demographics", "type": "sdtm"},
                {"name": "AE", "label": "Adverse Events", "type": "sdtm"},
                {"name": "CM", "label": "Concomitant Medications", "type": "sdtm"},
                {"name": "LB", "label": "Laboratory", "type": "sdtm"},
                {"name": "VS", "label": "Vital Signs", "type": "sdtm"},
                {"name": "EX", "label": "Exposure", "type": "sdtm"}
            ]
            
            for dataset in standard_datasets:
                # Check if dataset exists
                check_url = f"{self.base_url}/api/{self.api_version}/studies/{study_id}/datasets/{dataset['name']}"
                
                try:
                    response = await self.make_request(
                        method="HEAD",
                        url=check_url,
                        headers=headers
                    )
                    
                    datasets.append({
                        "name": dataset["name"],
                        "label": dataset["label"],
                        "type": dataset["type"],
                        "available": True
                    })
                except:
                    pass
            
            return datasets
            
        except Exception as e:
            logger.error(f"Failed to fetch datasets: {str(e)}")
            return []
    
    async def download_data(self, study_id: str, dataset_name: str) -> bytes:
        """Download clinical data for a specific dataset"""
        
        try:
            if not self.auth_token:
                await self.authenticate()
            
            # Construct data export URL
            export_url = f"{self.base_url}/api/{self.api_version}/studies/{study_id}/datasets/{dataset_name}/export"
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Accept": "text/csv"  # Request CSV format
            }
            
            # Request data export
            response = await self.make_request(
                method="POST",
                url=export_url,
                headers=headers,
                json={
                    "format": "csv",
                    "include_audit": False,
                    "include_signatures": False
                }
            )
            
            # Get export job ID
            job_id = response.get("job_id")
            
            if not job_id:
                raise Exception("Failed to initiate data export")
            
            # Poll for export completion
            status_url = f"{self.base_url}/api/{self.api_version}/export-jobs/{job_id}"
            
            max_attempts = 60  # 5 minutes with 5-second intervals
            for attempt in range(max_attempts):
                status_response = await self.make_request(
                    method="GET",
                    url=status_url,
                    headers=headers
                )
                
                if status_response.get("status") == "completed":
                    # Download the exported file
                    download_url = status_response.get("download_url")
                    
                    if download_url:
                        async with self.session.get(download_url, headers=headers) as response:
                            if response.status == 200:
                                return await response.read()
                    
                    break
                    
                elif status_response.get("status") == "failed":
                    raise Exception(f"Export failed: {status_response.get('error')}")
                
                # Wait before next poll
                await asyncio.sleep(5)
            
            raise Exception("Export timed out")
            
        except Exception as e:
            logger.error(f"Failed to download data: {str(e)}")
            raise e
    
    async def fetch_study_metadata(self, study_id: str) -> Dict[str, Any]:
        """Fetch detailed study metadata"""
        
        try:
            if not self.auth_token:
                await self.authenticate()
            
            metadata_url = f"{self.base_url}/api/{self.api_version}/studies/{study_id}"
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Accept": "application/json"
            }
            
            response = await self.make_request(
                method="GET",
                url=metadata_url,
                headers=headers
            )
            
            return {
                "study_oid": response.get("oid"),
                "study_name": response.get("name"),
                "protocol": response.get("protocol_name"),
                "sponsor": response.get("sponsor_name"),
                "therapeutic_area": response.get("therapeutic_area"),
                "phase": response.get("phase"),
                "status": response.get("status"),
                "sites": response.get("sites", []),
                "subjects": response.get("subject_count", 0),
                "visits": response.get("visits", []),
                "forms": response.get("forms", []),
                "created_date": response.get("created_date"),
                "last_modified": response.get("last_modified")
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch study metadata: {str(e)}")
            return {}
    
    async def fetch_subject_data(
        self,
        study_id: str,
        subject_id: Optional[str] = None,
        site_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch subject-level data"""
        
        try:
            if not self.auth_token:
                await self.authenticate()
            
            subjects_url = f"{self.base_url}/api/{self.api_version}/studies/{study_id}/subjects"
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Accept": "application/json"
            }
            
            params = {}
            if subject_id:
                params["subject_id"] = subject_id
            if site_id:
                params["site_id"] = site_id
            
            response = await self.make_request(
                method="GET",
                url=subjects_url,
                headers=headers,
                params=params
            )
            
            subjects = []
            for subject in response.get("subjects", []):
                subjects.append({
                    "subject_id": subject["subject_id"],
                    "site_id": subject["site_id"],
                    "site_name": subject.get("site_name", ""),
                    "enrollment_date": subject.get("enrollment_date"),
                    "status": subject.get("status"),
                    "randomization_number": subject.get("randomization_number"),
                    "treatment_arm": subject.get("treatment_arm"),
                    "completion_date": subject.get("completion_date"),
                    "last_visit": subject.get("last_visit")
                })
            
            return subjects
            
        except Exception as e:
            logger.error(f"Failed to fetch subject data: {str(e)}")
            return []