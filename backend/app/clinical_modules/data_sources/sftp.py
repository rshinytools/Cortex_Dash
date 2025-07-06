# ABOUTME: SFTP connector for downloading clinical data from SFTP servers
# ABOUTME: Implements standardized folder structure with date-based organization

import asyncio
import asyncssh
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import logging
from datetime import datetime

from .base import DataSourceConnector
from app.clinical_modules.utils.folder_structure import get_study_data_path, ensure_folder_exists


logger = logging.getLogger(__name__)


class SFTPConnector(DataSourceConnector):
    """
    Connector for SFTP servers.
    Downloads data via SFTP and stores in date-based folders.
    """
    
    def get_required_config_fields(self) -> List[str]:
        return [
            "host",
            "port",
            "username",
            "remote_path"
            # password or private_key is optional (one required)
        ]
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test connection to SFTP server.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Prepare connection options
            connect_kwargs = {
                'host': self.config.get('host'),
                'port': self.config.get('port', 22),
                'username': self.config.get('username'),
                'known_hosts': None  # TODO: Implement known_hosts validation
            }
            
            # Add authentication
            if 'password' in self.config:
                connect_kwargs['password'] = self.config['password']
            elif 'private_key' in self.config:
                connect_kwargs['client_keys'] = [self.config['private_key']]
            else:
                return False, "No authentication method provided (password or private_key required)"
            
            # Test connection
            async with asyncssh.connect(**connect_kwargs) as conn:
                # Test if remote path exists
                remote_path = self.config.get('remote_path', '/')
                try:
                    await conn.run(f'test -d {remote_path}')
                    self.log_activity("test_connection", {"status": "success"})
                    return True, None
                except asyncssh.ProcessError:
                    error = f"Remote path does not exist: {remote_path}"
                    self.log_activity("test_connection", {"status": "failed"}, False, error)
                    return False, error
                    
        except asyncssh.PermissionDenied:
            error = "Authentication failed - check username/password or private key"
            self.log_activity("test_connection", {"status": "failed"}, False, error)
            return False, error
        except asyncssh.DisconnectError as e:
            error = f"Connection failed: {str(e)}"
            self.log_activity("test_connection", {"status": "failed"}, False, error)
            return False, error
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            self.log_activity("test_connection", {"status": "failed"}, False, error)
            return False, error
    
    async def list_available_data(self) -> List[Dict[str, Any]]:
        """
        List available files on SFTP server.
        
        Returns:
            List of available files with metadata
        """
        available_files = []
        
        try:
            connect_kwargs = self._get_connection_kwargs()
            
            async with asyncssh.connect(**connect_kwargs) as conn:
                async with conn.start_sftp_client() as sftp:
                    remote_path = self.config.get('remote_path', '/')
                    
                    # List files in remote path
                    for entry in await sftp.readdir(remote_path):
                        if entry.filename.startswith('.'):
                            continue  # Skip hidden files
                            
                        file_path = f"{remote_path}/{entry.filename}"
                        attrs = await sftp.stat(file_path)
                        
                        # Only include regular files (not directories)
                        if attrs.type == asyncssh.FILEXFER_TYPE_REGULAR:
                            available_files.append({
                                "id": entry.filename,
                                "name": entry.filename,
                                "path": file_path,
                                "size": attrs.size,
                                "modified": datetime.fromtimestamp(attrs.mtime).isoformat(),
                                "type": self._get_file_type(entry.filename),
                                "available": True
                            })
                    
                    self.log_activity("list_data", {"count": len(available_files)})
                    
        except Exception as e:
            logger.error(f"Error listing SFTP files: {str(e)}")
            self.log_activity("list_data", {"error": str(e)}, False, str(e))
            
        return available_files
    
    async def download_data(
        self,
        dataset_id: str,
        target_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Download file from SFTP server to date-based folder.
        
        Args:
            dataset_id: Filename to download
            target_path: Local path to save file (will be date-based folder)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.update_sync_status("downloading")
            
            connect_kwargs = self._get_connection_kwargs()
            
            async with asyncssh.connect(**connect_kwargs) as conn:
                async with conn.start_sftp_client() as sftp:
                    remote_path = self.config.get('remote_path', '/')
                    remote_file = f"{remote_path}/{dataset_id}"
                    
                    # Check if file exists
                    try:
                        attrs = await sftp.stat(remote_file)
                        file_size = attrs.size
                    except asyncssh.SFTPError:
                        error = f"File not found on server: {dataset_id}"
                        self.update_sync_status("failed", error)
                        return False, error
                    
                    # Download file to target path (which is already date-based)
                    local_file = target_path / dataset_id
                    
                    # Download with progress
                    bytes_downloaded = 0
                    
                    async def progress_handler(bytes_so_far, total_bytes):
                        nonlocal bytes_downloaded
                        bytes_downloaded = bytes_so_far
                        if progress_callback and total_bytes > 0:
                            progress = (bytes_so_far / total_bytes) * 100
                            progress_callback(progress, f"Downloading: {bytes_so_far}/{total_bytes} bytes")
                    
                    await sftp.get(
                        remote_file,
                        str(local_file),
                        progress_handler=progress_handler if progress_callback else None
                    )
                    
                    self.update_sync_status("completed")
                    self.log_activity(
                        "download_data",
                        {
                            "dataset_id": dataset_id,
                            "file_path": str(local_file),
                            "size": file_size,
                            "remote_path": remote_file
                        }
                    )
                    
                    return True, None
                    
        except Exception as e:
            error = f"Download error: {str(e)}"
            logger.error(error)
            self.update_sync_status("failed", error)
            self.log_activity("download_data", {"dataset_id": dataset_id}, False, error)
            return False, error
    
    async def get_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """Get metadata for a file on SFTP server"""
        try:
            connect_kwargs = self._get_connection_kwargs()
            
            async with asyncssh.connect(**connect_kwargs) as conn:
                async with conn.start_sftp_client() as sftp:
                    remote_path = self.config.get('remote_path', '/')
                    remote_file = f"{remote_path}/{dataset_id}"
                    
                    attrs = await sftp.stat(remote_file)
                    
                    return {
                        "filename": dataset_id,
                        "size": attrs.size,
                        "modified": datetime.fromtimestamp(attrs.mtime).isoformat(),
                        "permissions": str(attrs.permissions),
                        "type": self._get_file_type(dataset_id)
                    }
                    
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            return {"error": str(e)}
    
    def _get_connection_kwargs(self) -> Dict[str, Any]:
        """Get connection kwargs for asyncssh"""
        connect_kwargs = {
            'host': self.config.get('host'),
            'port': self.config.get('port', 22),
            'username': self.config.get('username'),
            'known_hosts': None  # TODO: Implement known_hosts validation
        }
        
        # Add authentication
        if 'password' in self.config:
            connect_kwargs['password'] = self.config['password']
        elif 'private_key' in self.config:
            connect_kwargs['client_keys'] = [self.config['private_key']]
            
        return connect_kwargs
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from extension"""
        ext = Path(filename).suffix.lower()
        
        type_map = {
            '.sas7bdat': 'sas',
            '.xpt': 'sas_transport',
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.zip': 'archive',
            '.txt': 'text',
            '.json': 'json',
            '.xml': 'xml'
        }
        
        return type_map.get(ext, 'unknown')