// ABOUTME: API client functions for backup and restore operations
// ABOUTME: Handles all backup-related API calls including scheduling and cloud storage

import { secureApiClient } from './secure-client';

export interface BackupMetadata {
  backup_type: string;
  created_at: string;
  created_by: string;
  description?: string;
  version: string;
  system_info: {
    platform: string;
    api_version: string;
  };
}

export interface Backup {
  id: string;
  filename: string;
  size_mb: number;
  checksum: string;
  description?: string;
  created_by: string;
  created_by_name?: string;
  created_by_email: string;
  created_at: string;
  metadata: BackupMetadata;
  status?: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
  estimated_size_mb?: number;
  cloud_storage?: {
    provider: 'aws' | 'azure' | 'gcp';
    location: string;
    uploaded_at?: string;
  };
}

export interface CreateBackupRequest {
  description?: string;
  backup_type: 'full' | 'database' | 'files';
  upload_to_cloud?: boolean;
  cloud_provider?: 'aws' | 'azure' | 'gcp';
}

export interface CreateBackupResponse {
  success: boolean;
  backup_id: string;
  filename: string;
  size_mb: number;
  checksum: string;
  created_at: string;
}

export interface RestoreBackupRequest {
  create_safety_backup: boolean;
}

export interface RestoreBackupResponse {
  success: boolean;
  backup_id: string;
  backup_filename: string;
  safety_backup_id?: string;
  restored_at: string;
}

export interface BackupSchedule {
  id: string;
  name: string;
  backup_type: 'full' | 'database' | 'files';
  schedule: {
    frequency: 'hourly' | 'daily' | 'weekly' | 'monthly';
    time?: string;
    day_of_week?: number;
    day_of_month?: number;
  };
  retention_days: number;
  is_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  upload_to_cloud?: boolean;
  cloud_provider?: 'aws' | 'azure' | 'gcp';
  created_at: string;
  updated_at: string;
}

export interface CloudStorageConfig {
  provider: 'aws' | 'azure' | 'gcp';
  enabled: boolean;
  bucket_name?: string;
  region?: string;
  access_key?: string;
  secret_key?: string;
  connection_string?: string;
  auto_upload: boolean;
  retention_days: number;
}

export interface BackupStatistics {
  total_backups: number;
  total_size_mb: number;
  average_size_mb: number;
  last_backup_at?: string;
  next_scheduled_at?: string;
  success_rate: number;
  average_duration_seconds: number;
  storage_usage: {
    local: number;
    cloud: number;
    total: number;
  };
}

// Backup CRUD operations
export const backupApi = {
  // List all backups
  async listBackups(limit = 50): Promise<Backup[]> {
    const response = await secureApiClient.get('/backups', {
      params: { limit }
    });
    return response.data;
  },

  // Get specific backup
  async getBackup(backupId: string): Promise<Backup> {
    const response = await secureApiClient.get(`/backup/${backupId}`);
    return response.data;
  },

  // Create new backup
  async createBackup(request: CreateBackupRequest): Promise<CreateBackupResponse> {
    const response = await secureApiClient.post('/backup', request);
    return response.data;
  },

  // Restore from backup
  async restoreBackup(
    backupId: string,
    request: RestoreBackupRequest
  ): Promise<RestoreBackupResponse> {
    const response = await secureApiClient.post(
      `/restore/${backupId}`,
      request
    );
    return response.data;
  },

  // Download backup file
  async downloadBackup(backupId: string): Promise<Blob> {
    const response = await secureApiClient.get(
      `/backup/${backupId}/download`,
      {
        responseType: 'blob'
      }
    );
    return response.data;
  },

  // Verify backup integrity
  async verifyBackup(backupId: string): Promise<{
    backup_id: string;
    valid: boolean;
    message: string;
  }> {
    const response = await secureApiClient.post(
      `/backup/${backupId}/verify`
    );
    return response.data;
  },

  // Delete backup (if allowed)
  async deleteBackup(backupId: string): Promise<void> {
    await secureApiClient.delete(`/backup/${backupId}`);
  },

  // Get backup statistics
  async getStatistics(): Promise<BackupStatistics> {
    const response = await secureApiClient.get('/backup/statistics');
    return response.data;
  },

  // Estimate backup size
  async estimateBackupSize(backupType: 'full' | 'database' | 'files'): Promise<{
    estimated_size_mb: number;
    database_size_mb: number;
    files_size_mb: number;
    compression_ratio: number;
  }> {
    const response = await secureApiClient.get('/backup/estimate', {
      params: { backup_type: backupType }
    });
    return response.data;
  }
};

// Schedule management
export const scheduleApi = {
  // List all schedules
  async listSchedules(): Promise<BackupSchedule[]> {
    const response = await secureApiClient.get('/backup/schedules');
    return response.data;
  },

  // Get specific schedule
  async getSchedule(scheduleId: string): Promise<BackupSchedule> {
    const response = await secureApiClient.get(`/backup/schedules/${scheduleId}`);
    return response.data;
  },

  // Create new schedule
  async createSchedule(schedule: Omit<BackupSchedule, 'id' | 'created_at' | 'updated_at'>): Promise<BackupSchedule> {
    const response = await secureApiClient.post('/backup/schedules', schedule);
    return response.data;
  },

  // Update schedule
  async updateSchedule(scheduleId: string, schedule: Partial<BackupSchedule>): Promise<BackupSchedule> {
    const response = await secureApiClient.put(`/backup/schedules/${scheduleId}`, schedule);
    return response.data;
  },

  // Delete schedule
  async deleteSchedule(scheduleId: string): Promise<void> {
    await secureApiClient.delete(`/backup/schedules/${scheduleId}`);
  },

  // Toggle schedule active/inactive
  async toggleSchedule(scheduleId: string, isActive: boolean): Promise<void> {
    await secureApiClient.post(`/backup/schedules/${scheduleId}/toggle`, {
      is_active: isActive
    });
  }
};

// Cloud storage configuration
export const cloudStorageApi = {
  // Get current configuration
  async getConfig(): Promise<CloudStorageConfig> {
    const response = await secureApiClient.get('/backup/cloud-storage');
    return response.data;
  },

  // Update configuration
  async updateConfig(config: CloudStorageConfig): Promise<CloudStorageConfig> {
    const response = await secureApiClient.put('/backup/cloud-storage', config);
    return response.data;
  },

  // Test cloud connection
  async testConnection(provider: 'aws' | 'azure' | 'gcp'): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await secureApiClient.post('/backup/cloud-storage/test', {
      provider
    });
    return response.data;
  },

  // Upload existing backup to cloud
  async uploadToCloud(backupId: string, provider: 'aws' | 'azure' | 'gcp'): Promise<{
    success: boolean;
    location: string;
  }> {
    const response = await secureApiClient.post(`/backup/${backupId}/upload-cloud`, {
      provider
    });
    return response.data;
  }
};

// WebSocket connection for real-time progress
export function connectBackupWebSocket(onProgress: (data: any) => void): WebSocket | null {
  // For now, return null as WebSocket is not implemented on backend
  // When implemented, it should use ws://localhost:3000 for CSP compliance
  // or update the CSP policy to allow ws://localhost:8000
  
  // Mock WebSocket for now - just return null
  // const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3000';
  // const ws = new WebSocket(`${wsUrl}/ws/backup-progress`);
  // ws.onmessage = (event) => {
  //   const data = JSON.parse(event.data);
  //   onProgress(data);
  // };
  // return ws;
  
  return null;
}