# ABOUTME: Medidata Rave API connector for clinical data acquisition
# ABOUTME: Handles authentication, data listing, and SAS dataset downloads

import asyncio
import aiohttp
import base64
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from .base import DataSourceConnector


class MedidataRaveConnector(DataSourceConnector):
    """Connector for Medidata Rave Clinical Data Management System"""
    
    def get_required_config_fields(self) -> List[str]:
        return [
            "base_url",
            "username", 
            "password",
            "study_oid",
            "environment"  # PROD, UAT, DEV
        ]
    
    def _get_auth_header(self) -> str:
        """Get basic auth header"""
        credentials = f"{self.config['username']}:{self.config['password']}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test connection to Medidata Rave"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test with a simple API call
                url = f"{self.config['base_url']}/RaveWebServices/studies"
                headers = {
                    "Authorization": self._get_auth_header(),
                    "Accept": "application/xml"
                }
                
                async with session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        self.log_activity("test_connection", {"status": "success"})
                        return True, None
                    else:
                        error = f"Authentication failed: {response.status}"
                        self.log_activity("test_connection", {"status": "failed"}, False, error)
                        return False, error
                        
        except Exception as e:
            error = f"Connection error: {str(e)}"
            self.log_activity("test_connection", {"status": "error"}, False, error)
            return False, error
    
    async def list_available_data(self) -> List[Dict[str, Any]]:
        """List available datasets from Rave"""
        try:
            datasets = []
            
            # Get available clinical data formats
            async with aiohttp.ClientSession() as session:
                # Clinical data endpoint
                url = f"{self.config['base_url']}/RaveWebServices/studies/{self.config['study_oid']}/datasets"
                headers = {
                    "Authorization": self._get_auth_header(),
                    "Accept": "application/json"
                }
                
                async with session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Standard datasets
                        standard_datasets = [
                            {"id": "raw_sas", "name": "Raw SAS Datasets", "type": "sas", "format": "sas7bdat"},
                            {"id": "raw_csv", "name": "Raw CSV Data", "type": "csv", "format": "csv"},
                            {"id": "sdtm_sas", "name": "SDTM SAS Datasets", "type": "sas", "format": "sas7bdat"},
                            {"id": "audit_trail", "name": "Audit Trail", "type": "audit", "format": "csv"},
                        ]
                        
                        for ds in standard_datasets:
                            datasets.append({
                                "id": ds["id"],
                                "name": ds["name"],
                                "type": ds["type"],
                                "format": ds["format"],
                                "available": True,
                                "last_updated": datetime.utcnow().isoformat(),
                                "size_estimate": "Variable",
                                "description": f"{ds['name']} from Medidata Rave"
                            })
                    
                    self.log_activity("list_data", {"count": len(datasets)})
                    
        except Exception as e:
            self.logger.error(f"Error listing Rave data: {str(e)}")
            self.log_activity("list_data", {"error": str(e)}, False, str(e))
            
        return datasets
    
    async def download_data(
        self,
        dataset_id: str,
        target_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, Optional[str]]:
        """Download dataset from Rave"""
        try:
            self.update_sync_status("downloading")
            
            # Map dataset IDs to Rave export types
            export_map = {
                "raw_sas": "clinical_sas",
                "raw_csv": "clinical_csv", 
                "sdtm_sas": "sdtm_sas",
                "audit_trail": "audit_csv"
            }
            
            if dataset_id not in export_map:
                return False, f"Unknown dataset ID: {dataset_id}"
            
            export_type = export_map[dataset_id]
            
            async with aiohttp.ClientSession() as session:
                # Request data export
                export_url = f"{self.config['base_url']}/RaveWebServices/studies/{self.config['study_oid']}/export"
                headers = {
                    "Authorization": self._get_auth_header(),
                    "Content-Type": "application/json"
                }
                
                export_request = {
                    "exportType": export_type,
                    "environment": self.config['environment'],
                    "includeData": True,
                    "includeMappings": True
                }
                
                # Start export job
                async with session.post(export_url, headers=headers, json=export_request, ssl=False) as response:
                    if response.status != 202:
                        error = f"Export request failed: {response.status}"
                        self.update_sync_status("failed", error)
                        return False, error
                    
                    export_job = await response.json()
                    job_id = export_job.get("jobId")
                
                # Poll for completion
                status_url = f"{export_url}/{job_id}/status"
                max_attempts = 60  # 5 minutes with 5 second intervals
                
                for attempt in range(max_attempts):
                    async with session.get(status_url, headers=headers, ssl=False) as response:
                        if response.status == 200:
                            status_data = await response.json()
                            status = status_data.get("status")
                            
                            if progress_callback:
                                progress = (attempt / max_attempts) * 100
                                progress_callback(progress, f"Export status: {status}")
                            
                            if status == "COMPLETED":
                                download_url = status_data.get("downloadUrl")
                                break
                            elif status == "FAILED":
                                error = "Export job failed"
                                self.update_sync_status("failed", error)
                                return False, error
                    
                    await asyncio.sleep(5)
                else:
                    error = "Export job timed out"
                    self.update_sync_status("failed", error)
                    return False, error
                
                # Download the export file
                async with session.get(download_url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        file_name = f"{dataset_id}_export.zip"
                        file_path = target_path / file_name
                        
                        with open(file_path, "wb") as f:
                            total_size = int(response.headers.get("Content-Length", 0))
                            downloaded = 0
                            
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                if progress_callback and total_size > 0:
                                    progress = (downloaded / total_size) * 100
                                    progress_callback(progress, f"Downloading: {downloaded}/{total_size} bytes")
                        
                        self.update_sync_status("completed")
                        self.log_activity(
                            "download_data",
                            {
                                "dataset_id": dataset_id,
                                "file_path": str(file_path),
                                "size": downloaded
                            }
                        )
                        
                        return True, None
                    else:
                        error = f"Download failed: {response.status}"
                        self.update_sync_status("failed", error)
                        return False, error
                        
        except Exception as e:
            error = f"Download error: {str(e)}"
            self.logger.error(error)
            self.update_sync_status("failed", error)
            self.log_activity("download_data", {"dataset_id": dataset_id}, False, error)
            return False, error
    
    async def get_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """Get metadata for a dataset"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get study metadata
                url = f"{self.config['base_url']}/RaveWebServices/studies/{self.config['study_oid']}/metadata"
                headers = {
                    "Authorization": self._get_auth_header(),
                    "Accept": "application/json"
                }
                
                async with session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        metadata = await response.json()
                        
                        return {
                            "dataset_id": dataset_id,
                            "study_oid": self.config['study_oid'],
                            "environment": self.config['environment'],
                            "protocol_name": metadata.get("protocolName"),
                            "sites": metadata.get("siteCount", 0),
                            "subjects": metadata.get("subjectCount", 0),
                            "forms": metadata.get("formCount", 0),
                            "last_data_change": metadata.get("lastDataChange"),
                            "retrieved_at": datetime.utcnow().isoformat()
                        }
                    
        except Exception as e:
            self.logger.error(f"Error getting metadata: {str(e)}")
            
        return {"dataset_id": dataset_id, "error": "Failed to retrieve metadata"}
    
    async def get_study_info(self) -> Dict[str, Any]:
        """Get detailed study information from Rave"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config['base_url']}/RaveWebServices/studies/{self.config['study_oid']}"
                headers = {
                    "Authorization": self._get_auth_header(),
                    "Accept": "application/json"
                }
                
                async with session.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        return await response.json()
                        
        except Exception as e:
            self.logger.error(f"Error getting study info: {str(e)}")
            
        return {}