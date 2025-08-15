# ABOUTME: Veeva Vault integration for clinical document and data management
# ABOUTME: Connects to Veeva Vault CTMS API for study documents and data

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.services.integrations.base_integration import BaseIntegration, IntegrationType
from app.core.logging import logger

class VeevaVaultIntegration(BaseIntegration):
    """Veeva Vault CTMS integration"""
    
    def __init__(self, data_source, db):
        super().__init__(data_source, db)
        self.integration_type = IntegrationType.VEEVA_VAULT
        self.vault_domain = self.get_config_value("vault_domain")
        self.api_version = self.get_config_value("api_version", "v23.3")
        self.base_url = f"https://{self.vault_domain}/api/{self.api_version}"
        
    async def authenticate(self) -> bool:
        """Authenticate with Veeva Vault using username/password"""
        
        try:
            username = self.get_config_value("username")
            password = self.get_config_value("password")
            
            if not username or not password:
                raise Exception("Missing authentication credentials")
            
            auth_url = f"{self.base_url}/auth"
            
            auth_data = {
                "username": username,
                "password": password
            }
            
            response = await self.make_request(
                method="POST",
                url=auth_url,
                data=auth_data
            )
            
            if response.get("responseStatus") == "SUCCESS":
                self.auth_token = response["sessionId"]
                self.update_config("session_id", self.auth_token)
                
                logger.info("Successfully authenticated with Veeva Vault")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Veeva Vault authentication failed: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to Veeva Vault"""
        
        try:
            if not self.auth_token:
                if not await self.authenticate():
                    return False
            
            # Test API endpoint - get user info
            test_url = f"{self.base_url}/objects/users/me"
            
            headers = {
                "Authorization": self.auth_token,
                "Accept": "application/json"
            }
            
            response = await self.make_request(
                method="GET",
                url=test_url,
                headers=headers
            )
            
            return response.get("responseStatus") == "SUCCESS"
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    async def fetch_studies(self) -> List[Dict[str, Any]]:
        """Fetch available studies from Veeva Vault"""
        
        try:
            if not self.auth_token:
                await self.authenticate()
            
            # Query study objects
            query = "SELECT id, name__v, study_number__v, phase__v, status__v, therapeutic_area__v FROM study__v"
            query_url = f"{self.base_url}/query"
            
            headers = {
                "Authorization": self.auth_token,
                "Accept": "application/json"
            }
            
            response = await self.make_request(
                method="POST",
                url=query_url,
                headers=headers,
                data={"q": query}
            )
            
            studies = []
            if response.get("responseStatus") == "SUCCESS":
                for study in response.get("data", []):
                    studies.append({
                        "id": study["id"],
                        "name": study["name__v"],
                        "study_number": study.get("study_number__v", ""),
                        "phase": study.get("phase__v", ""),
                        "status": study.get("status__v", ""),
                        "therapeutic_area": study.get("therapeutic_area__v", ""),
                        "created_date": study.get("created_date__v", "")
                    })
            
            return studies
            
        except Exception as e:
            logger.error(f"Failed to fetch studies: {str(e)}")
            return []
    
    async def fetch_datasets(self, study_id: str) -> List[Dict[str, Any]]:
        """Fetch available datasets/documents for a study"""
        
        try:
            if not self.auth_token:
                await self.authenticate()
            
            # Query study documents
            query = f"SELECT id, name__v, document_type__v, version__v, status__v FROM documents WHERE study__v = '{study_id}'"
            query_url = f"{self.base_url}/query"
            
            headers = {
                "Authorization": self.auth_token,
                "Accept": "application/json"
            }
            
            response = await self.make_request(
                method="POST",
                url=query_url,
                headers=headers,
                data={"q": query}
            )
            
            datasets = []
            if response.get("responseStatus") == "SUCCESS":
                # Group documents by type
                doc_types = {}
                for doc in response.get("data", []):
                    doc_type = doc.get("document_type__v", "Other")
                    if doc_type not in doc_types:
                        doc_types[doc_type] = []
                    doc_types[doc_type].append(doc)
                
                # Create dataset entries
                for doc_type, docs in doc_types.items():
                    datasets.append({
                        "name": doc_type.replace(" ", "_").lower(),
                        "label": doc_type,
                        "type": "document_collection",
                        "document_count": len(docs),
                        "last_modified": max([d.get("modified_date__v", "") for d in docs] or [""])
                    })
            
            # Add TMF categories as datasets
            tmf_categories = [
                {"name": "trial_management", "label": "Trial Management"},
                {"name": "regulatory", "label": "Regulatory"},
                {"name": "clinical_conduct", "label": "Clinical Conduct"},
                {"name": "safety_reporting", "label": "Safety Reporting"},
                {"name": "data_management", "label": "Data Management"},
                {"name": "statistics", "label": "Statistics"}
            ]
            
            for category in tmf_categories:
                datasets.append({
                    "name": category["name"],
                    "label": category["label"],
                    "type": "tmf_category",
                    "available": True
                })
            
            return datasets
            
        except Exception as e:
            logger.error(f"Failed to fetch datasets: {str(e)}")
            return []
    
    async def download_data(self, study_id: str, dataset_name: str) -> bytes:
        """Download study documents or data"""
        
        try:
            if not self.auth_token:
                await self.authenticate()
            
            # For document collections, export as CSV summary
            if dataset_name.endswith("_documents"):
                return await self.export_document_summary(study_id, dataset_name)
            
            # For TMF categories, export metadata
            if dataset_name in ["trial_management", "regulatory", "clinical_conduct"]:
                return await self.export_tmf_data(study_id, dataset_name)
            
            # Default: export study data
            export_url = f"{self.base_url}/objects/study__v/{study_id}/actions/export"
            
            headers = {
                "Authorization": self.auth_token,
                "Accept": "text/csv"
            }
            
            response = await self.make_request(
                method="POST",
                url=export_url,
                headers=headers,
                json={
                    "format": "CSV",
                    "dataset": dataset_name
                }
            )
            
            if response.get("responseStatus") == "SUCCESS":
                # Get export job ID
                job_id = response.get("job_id")
                
                # Wait for export to complete
                return await self.wait_for_export(job_id)
            
            raise Exception("Failed to initiate export")
            
        except Exception as e:
            logger.error(f"Failed to download data: {str(e)}")
            raise e
    
    async def export_document_summary(self, study_id: str, doc_type: str) -> bytes:
        """Export document summary as CSV"""
        
        try:
            # Query documents
            query = f"""
                SELECT id, name__v, document_number__v, version__v, 
                       status__v, created_date__v, modified_date__v 
                FROM documents 
                WHERE study__v = '{study_id}' AND document_type__v = '{doc_type}'
            """
            
            query_url = f"{self.base_url}/query"
            
            headers = {
                "Authorization": self.auth_token,
                "Accept": "application/json"
            }
            
            response = await self.make_request(
                method="POST",
                url=query_url,
                headers=headers,
                data={"q": query}
            )
            
            if response.get("responseStatus") == "SUCCESS":
                # Convert to CSV
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.DictWriter(
                    output,
                    fieldnames=["id", "name", "document_number", "version", "status", "created_date", "modified_date"]
                )
                writer.writeheader()
                
                for doc in response.get("data", []):
                    writer.writerow({
                        "id": doc.get("id"),
                        "name": doc.get("name__v"),
                        "document_number": doc.get("document_number__v"),
                        "version": doc.get("version__v"),
                        "status": doc.get("status__v"),
                        "created_date": doc.get("created_date__v"),
                        "modified_date": doc.get("modified_date__v")
                    })
                
                return output.getvalue().encode("utf-8")
            
            return b""
            
        except Exception as e:
            logger.error(f"Failed to export document summary: {str(e)}")
            return b""
    
    async def export_tmf_data(self, study_id: str, category: str) -> bytes:
        """Export TMF category data"""
        
        try:
            # Map category to TMF zones
            tmf_zones = {
                "trial_management": ["01.01", "01.02", "01.03"],
                "regulatory": ["02.01", "02.02"],
                "clinical_conduct": ["03.01", "03.02", "03.03"]
            }
            
            zones = tmf_zones.get(category, [])
            
            # Query TMF documents
            zone_filter = " OR ".join([f"tmf_code__v CONTAINS '{zone}'" for zone in zones])
            query = f"""
                SELECT id, name__v, tmf_code__v, artifact_type__v, 
                       status__v, completeness__v 
                FROM tmf_document__v 
                WHERE study__v = '{study_id}' AND ({zone_filter})
            """
            
            query_url = f"{self.base_url}/query"
            
            headers = {
                "Authorization": self.auth_token,
                "Accept": "application/json"
            }
            
            response = await self.make_request(
                method="POST",
                url=query_url,
                headers=headers,
                data={"q": query}
            )
            
            if response.get("responseStatus") == "SUCCESS":
                # Convert to CSV
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.DictWriter(
                    output,
                    fieldnames=["id", "name", "tmf_code", "artifact_type", "status", "completeness"]
                )
                writer.writeheader()
                
                for doc in response.get("data", []):
                    writer.writerow({
                        "id": doc.get("id"),
                        "name": doc.get("name__v"),
                        "tmf_code": doc.get("tmf_code__v"),
                        "artifact_type": doc.get("artifact_type__v"),
                        "status": doc.get("status__v"),
                        "completeness": doc.get("completeness__v")
                    })
                
                return output.getvalue().encode("utf-8")
            
            return b""
            
        except Exception as e:
            logger.error(f"Failed to export TMF data: {str(e)}")
            return b""
    
    async def wait_for_export(self, job_id: str) -> bytes:
        """Wait for export job to complete and download result"""
        
        import asyncio
        
        job_url = f"{self.base_url}/services/jobs/{job_id}"
        
        headers = {
            "Authorization": self.auth_token,
            "Accept": "application/json"
        }
        
        # Poll for completion
        for _ in range(60):  # 5 minutes max
            response = await self.make_request(
                method="GET",
                url=job_url,
                headers=headers
            )
            
            if response.get("data", {}).get("status") == "COMPLETE":
                # Download file
                file_url = response["data"]["result_url"]
                
                async with self.session.get(file_url, headers=headers) as file_response:
                    if file_response.status == 200:
                        return await file_response.read()
            
            elif response.get("data", {}).get("status") == "FAILED":
                raise Exception(f"Export failed: {response.get('data', {}).get('error')}")
            
            await asyncio.sleep(5)
        
        raise Exception("Export timed out")