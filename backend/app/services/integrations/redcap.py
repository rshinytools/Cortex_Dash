# ABOUTME: REDCap integration for research data capture
# ABOUTME: Connects to REDCap API for clinical research data management

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import csv
import io

from app.services.integrations.base_integration import BaseIntegration, IntegrationType
from app.core.logging import logger

class REDCapIntegration(BaseIntegration):
    """REDCap (Research Electronic Data Capture) integration"""
    
    def __init__(self, data_source, db):
        super().__init__(data_source, db)
        self.integration_type = IntegrationType.REDCAP
        self.api_url = self.get_config_value("api_url")
        self.api_token = self.get_config_value("api_token")
        
    async def authenticate(self) -> bool:
        """Authenticate with REDCap using API token"""
        
        try:
            # REDCap uses token-based auth, no separate authentication needed
            if not self.api_token:
                raise Exception("Missing API token")
            
            if not self.api_url:
                raise Exception("Missing API URL")
            
            # Test token validity
            data = {
                "token": self.api_token,
                "content": "project",
                "format": "json"
            }
            
            response = await self.make_request(
                method="POST",
                url=self.api_url,
                data=data
            )
            
            if response and "project_title" in response:
                self.auth_token = self.api_token
                logger.info("Successfully authenticated with REDCap")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"REDCap authentication failed: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to REDCap"""
        
        try:
            # Test API endpoint - get project info
            data = {
                "token": self.api_token,
                "content": "project",
                "format": "json"
            }
            
            response = await self.make_request(
                method="POST",
                url=self.api_url,
                data=data
            )
            
            return response is not None and "project_title" in response
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    async def fetch_studies(self) -> List[Dict[str, Any]]:
        """Fetch project information from REDCap"""
        
        try:
            # Get project info
            data = {
                "token": self.api_token,
                "content": "project",
                "format": "json"
            }
            
            response = await self.make_request(
                method="POST",
                url=self.api_url,
                data=data
            )
            
            if response:
                # REDCap typically manages one project per API token
                # But we can get project details
                project = {
                    "id": response.get("project_id", ""),
                    "name": response.get("project_title", ""),
                    "purpose": response.get("purpose", ""),
                    "purpose_other": response.get("purpose_other", ""),
                    "is_longitudinal": response.get("is_longitudinal", 0),
                    "has_repeating_instruments": response.get("has_repeating_instruments_or_events", 0),
                    "surveys_enabled": response.get("surveys_enabled", 0),
                    "record_count": await self.get_record_count(),
                    "creation_time": response.get("creation_time", ""),
                    "production_time": response.get("production_time", ""),
                    "in_production": response.get("in_production", 0)
                }
                
                return [project]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch studies: {str(e)}")
            return []
    
    async def fetch_datasets(self, study_id: str) -> List[Dict[str, Any]]:
        """Fetch available forms/instruments from REDCap"""
        
        try:
            # Get instrument list
            data = {
                "token": self.api_token,
                "content": "instrument",
                "format": "json"
            }
            
            response = await self.make_request(
                method="POST",
                url=self.api_url,
                data=data
            )
            
            datasets = []
            
            if response:
                for instrument in response:
                    # Get instrument metadata
                    metadata = await self.get_instrument_metadata(instrument["instrument_name"])
                    
                    datasets.append({
                        "name": instrument["instrument_name"],
                        "label": instrument["instrument_label"],
                        "type": "instrument",
                        "field_count": len(metadata),
                        "has_repeating": await self.is_repeating_instrument(instrument["instrument_name"])
                    })
            
            # Add standard export options
            standard_exports = [
                {"name": "all_data", "label": "All Data", "type": "export"},
                {"name": "demographics", "label": "Demographics", "type": "export"},
                {"name": "events", "label": "Events", "type": "export"},
                {"name": "arms", "label": "Study Arms", "type": "export"},
                {"name": "reports", "label": "Reports", "type": "export"}
            ]
            
            datasets.extend(standard_exports)
            
            return datasets
            
        except Exception as e:
            logger.error(f"Failed to fetch datasets: {str(e)}")
            return []
    
    async def download_data(self, study_id: str, dataset_name: str) -> bytes:
        """Download data from REDCap"""
        
        try:
            if dataset_name == "all_data":
                return await self.export_all_records()
            elif dataset_name == "demographics":
                return await self.export_demographics()
            elif dataset_name == "events":
                return await self.export_events()
            elif dataset_name == "arms":
                return await self.export_arms()
            elif dataset_name == "reports":
                return await self.export_reports()
            else:
                # Export specific instrument
                return await self.export_instrument(dataset_name)
            
        except Exception as e:
            logger.error(f"Failed to download data: {str(e)}")
            raise e
    
    async def export_all_records(self) -> bytes:
        """Export all records from REDCap"""
        
        data = {
            "token": self.api_token,
            "content": "record",
            "format": "csv",
            "type": "flat",
            "rawOrLabel": "raw",
            "rawOrLabelHeaders": "raw",
            "exportCheckboxLabel": "false",
            "exportSurveyFields": "true",
            "exportDataAccessGroups": "true"
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_url,
            data=data
        )
        
        if isinstance(response, str):
            return response.encode("utf-8")
        elif isinstance(response, bytes):
            return response
        else:
            # Convert JSON to CSV if needed
            return self.json_to_csv(response)
    
    async def export_instrument(self, instrument_name: str) -> bytes:
        """Export data for a specific instrument"""
        
        data = {
            "token": self.api_token,
            "content": "record",
            "format": "csv",
            "type": "flat",
            "forms": instrument_name,
            "rawOrLabel": "raw",
            "exportCheckboxLabel": "false"
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_url,
            data=data
        )
        
        if isinstance(response, str):
            return response.encode("utf-8")
        elif isinstance(response, bytes):
            return response
        else:
            return self.json_to_csv(response)
    
    async def export_demographics(self) -> bytes:
        """Export demographic data"""
        
        # Get demographic fields
        metadata = await self.get_metadata()
        
        demo_fields = ["record_id"]
        for field in metadata:
            if field.get("field_name", "").lower() in ["age", "sex", "gender", "race", "ethnicity", "dob"]:
                demo_fields.append(field["field_name"])
        
        data = {
            "token": self.api_token,
            "content": "record",
            "format": "csv",
            "type": "flat",
            "fields": ",".join(demo_fields),
            "rawOrLabel": "label"
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_url,
            data=data
        )
        
        if isinstance(response, str):
            return response.encode("utf-8")
        elif isinstance(response, bytes):
            return response
        else:
            return self.json_to_csv(response)
    
    async def export_events(self) -> bytes:
        """Export event data for longitudinal projects"""
        
        data = {
            "token": self.api_token,
            "content": "event",
            "format": "csv"
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_url,
            data=data
        )
        
        if isinstance(response, str):
            return response.encode("utf-8")
        elif isinstance(response, bytes):
            return response
        else:
            return self.json_to_csv(response)
    
    async def export_arms(self) -> bytes:
        """Export study arms data"""
        
        data = {
            "token": self.api_token,
            "content": "arm",
            "format": "csv"
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_url,
            data=data
        )
        
        if isinstance(response, str):
            return response.encode("utf-8")
        elif isinstance(response, bytes):
            return response
        else:
            return self.json_to_csv(response)
    
    async def export_reports(self) -> bytes:
        """Export report data"""
        
        # Get list of reports
        data = {
            "token": self.api_token,
            "content": "report",
            "format": "json"
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_url,
            data=data
        )
        
        # Create summary CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["report_id", "report_name", "description"]
        )
        writer.writeheader()
        
        if response:
            for report in response:
                writer.writerow({
                    "report_id": report.get("report_id"),
                    "report_name": report.get("report_name"),
                    "description": report.get("description", "")
                })
        
        return output.getvalue().encode("utf-8")
    
    async def get_record_count(self) -> int:
        """Get total record count"""
        
        try:
            data = {
                "token": self.api_token,
                "content": "record",
                "format": "json",
                "fields": "record_id"
            }
            
            response = await self.make_request(
                method="POST",
                url=self.api_url,
                data=data
            )
            
            if response and isinstance(response, list):
                return len(response)
            
            return 0
            
        except:
            return 0
    
    async def get_metadata(self) -> List[Dict[str, Any]]:
        """Get project metadata"""
        
        data = {
            "token": self.api_token,
            "content": "metadata",
            "format": "json"
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_url,
            data=data
        )
        
        return response if response else []
    
    async def get_instrument_metadata(self, instrument_name: str) -> List[Dict[str, Any]]:
        """Get metadata for specific instrument"""
        
        data = {
            "token": self.api_token,
            "content": "metadata",
            "format": "json",
            "forms": instrument_name
        }
        
        response = await self.make_request(
            method="POST",
            url=self.api_url,
            data=data
        )
        
        return response if response else []
    
    async def is_repeating_instrument(self, instrument_name: str) -> bool:
        """Check if instrument is repeating"""
        
        try:
            data = {
                "token": self.api_token,
                "content": "repeatingFormsEvents",
                "format": "json"
            }
            
            response = await self.make_request(
                method="POST",
                url=self.api_url,
                data=data
            )
            
            if response:
                for item in response:
                    if item.get("form_name") == instrument_name:
                        return True
            
            return False
            
        except:
            return False
    
    def json_to_csv(self, json_data: List[Dict[str, Any]]) -> bytes:
        """Convert JSON data to CSV"""
        
        if not json_data:
            return b""
        
        output = io.StringIO()
        
        # Get all unique keys
        all_keys = set()
        for record in json_data:
            all_keys.update(record.keys())
        
        writer = csv.DictWriter(output, fieldnames=sorted(all_keys))
        writer.writeheader()
        
        for record in json_data:
            writer.writerow(record)
        
        return output.getvalue().encode("utf-8")