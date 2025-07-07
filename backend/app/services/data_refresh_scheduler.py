# ABOUTME: Data refresh scheduler service for scheduling automatic data refreshes
# ABOUTME: Manages refresh schedules, executes scheduled tasks, and tracks refresh history

from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from celery import Celery
from croniter import croniter
import logging

from app.core.db import get_db
from app.models.organization import Organization
from app.models.study import Study

logger = logging.getLogger(__name__)


class DataRefreshScheduler:
    """Service for scheduling and managing automatic data refreshes."""
    
    def __init__(self, db_session: Session, celery_app: Optional[Celery] = None):
        self.db = db_session
        self.celery_app = celery_app
        
    def create_refresh_schedule(
        self,
        study_id: str,
        schedule_name: str,
        cron_expression: str,
        data_sources: List[str],
        refresh_type: str = 'incremental',
        enabled: bool = True,
        notification_settings: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a new data refresh schedule.
        
        Args:
            study_id: Study identifier
            schedule_name: Human-readable schedule name
            cron_expression: Cron expression for scheduling
            data_sources: List of data sources to refresh
            refresh_type: Type of refresh ('full' or 'incremental')
            enabled: Whether schedule is active
            notification_settings: Email/alert settings for completion/errors
            
        Returns:
            Created schedule information
        """
        try:
            # Validate cron expression
            if not self._validate_cron_expression(cron_expression):
                raise ValueError(f"Invalid cron expression: {cron_expression}")
            
            # Validate study exists
            study = self.db.query(Study).filter(Study.id == study_id).first()
            if not study:
                raise ValueError(f"Study not found: {study_id}")
            
            # Create schedule record
            schedule_data = {
                'id': f"schedule_{study_id}_{int(datetime.utcnow().timestamp())}",
                'study_id': study_id,
                'schedule_name': schedule_name,
                'cron_expression': cron_expression,
                'data_sources': data_sources,
                'refresh_type': refresh_type,
                'enabled': enabled,
                'notification_settings': notification_settings or {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'next_run': self._calculate_next_run(cron_expression),
                'last_run': None,
                'run_count': 0,
                'success_count': 0,
                'error_count': 0
            }
            
            # Store in database (this would use actual model)
            schedule_id = self._store_schedule(schedule_data)
            
            # Register with scheduler if enabled
            if enabled:
                self._register_scheduled_task(schedule_id, schedule_data)
            
            logger.info(f"Created refresh schedule {schedule_id} for study {study_id}")
            
            return {
                'schedule_id': schedule_id,
                'status': 'created',
                'next_run': schedule_data['next_run'].isoformat(),
                'message': f"Schedule '{schedule_name}' created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating refresh schedule: {str(e)}")
            raise
    
    def update_refresh_schedule(
        self,
        schedule_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing refresh schedule.
        
        Args:
            schedule_id: Schedule identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated schedule information
        """
        try:
            schedule = self._get_schedule(schedule_id)
            if not schedule:
                raise ValueError(f"Schedule not found: {schedule_id}")
            
            # Validate updates
            if 'cron_expression' in updates:
                if not self._validate_cron_expression(updates['cron_expression']):
                    raise ValueError(f"Invalid cron expression: {updates['cron_expression']}")
                updates['next_run'] = self._calculate_next_run(updates['cron_expression'])
            
            # Update schedule
            schedule.update(updates)
            schedule['updated_at'] = datetime.utcnow()
            
            # Update scheduled task if enabled
            if schedule.get('enabled', False):
                self._register_scheduled_task(schedule_id, schedule)
            else:
                self._unregister_scheduled_task(schedule_id)
            
            # Store updates
            self._update_schedule(schedule_id, schedule)
            
            logger.info(f"Updated refresh schedule {schedule_id}")
            
            return {
                'schedule_id': schedule_id,
                'status': 'updated',
                'next_run': schedule.get('next_run', '').isoformat() if schedule.get('next_run') else None,
                'message': "Schedule updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating refresh schedule: {str(e)}")
            raise
    
    def delete_refresh_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """
        Delete a refresh schedule.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Deletion confirmation
        """
        try:
            schedule = self._get_schedule(schedule_id)
            if not schedule:
                raise ValueError(f"Schedule not found: {schedule_id}")
            
            # Unregister scheduled task
            self._unregister_scheduled_task(schedule_id)
            
            # Delete from database
            self._delete_schedule(schedule_id)
            
            logger.info(f"Deleted refresh schedule {schedule_id}")
            
            return {
                'schedule_id': schedule_id,
                'status': 'deleted',
                'message': "Schedule deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting refresh schedule: {str(e)}")
            raise
    
    def get_refresh_schedules(
        self,
        study_id: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get refresh schedules.
        
        Args:
            study_id: Optional study filter
            enabled_only: Whether to return only enabled schedules
            
        Returns:
            List of schedule information
        """
        try:
            schedules = self._get_schedules(study_id, enabled_only)
            
            result = []
            for schedule in schedules:
                schedule_info = {
                    'schedule_id': schedule['id'],
                    'study_id': schedule['study_id'],
                    'schedule_name': schedule['schedule_name'],
                    'cron_expression': schedule['cron_expression'],
                    'data_sources': schedule['data_sources'],
                    'refresh_type': schedule['refresh_type'],
                    'enabled': schedule['enabled'],
                    'next_run': schedule.get('next_run', '').isoformat() if schedule.get('next_run') else None,
                    'last_run': schedule.get('last_run', '').isoformat() if schedule.get('last_run') else None,
                    'run_count': schedule.get('run_count', 0),
                    'success_count': schedule.get('success_count', 0),
                    'error_count': schedule.get('error_count', 0),
                    'success_rate': self._calculate_success_rate(schedule),
                    'created_at': schedule['created_at'].isoformat(),
                    'updated_at': schedule['updated_at'].isoformat()
                }
                result.append(schedule_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting refresh schedules: {str(e)}")
            return []
    
    def execute_refresh_now(
        self,
        schedule_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a refresh immediately.
        
        Args:
            schedule_id: Schedule identifier
            force: Whether to force execution even if disabled
            
        Returns:
            Execution status
        """
        try:
            schedule = self._get_schedule(schedule_id)
            if not schedule:
                raise ValueError(f"Schedule not found: {schedule_id}")
            
            if not schedule.get('enabled', False) and not force:
                raise ValueError("Schedule is disabled. Use force=True to execute anyway.")
            
            # Execute refresh task
            execution_id = self._execute_refresh_task(schedule)
            
            # Update schedule
            schedule['last_run'] = datetime.utcnow()
            schedule['run_count'] = schedule.get('run_count', 0) + 1
            self._update_schedule(schedule_id, schedule)
            
            logger.info(f"Executed refresh schedule {schedule_id} immediately")
            
            return {
                'schedule_id': schedule_id,
                'execution_id': execution_id,
                'status': 'executing',
                'message': "Refresh started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error executing refresh now: {str(e)}")
            raise
    
    def get_refresh_history(
        self,
        schedule_id: Optional[str] = None,
        study_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get refresh execution history.
        
        Args:
            schedule_id: Optional schedule filter
            study_id: Optional study filter
            limit: Maximum number of records to return
            
        Returns:
            List of execution history records
        """
        try:
            history = self._get_refresh_history(schedule_id, study_id, limit)
            
            result = []
            for execution in history:
                execution_info = {
                    'execution_id': execution['id'],
                    'schedule_id': execution['schedule_id'],
                    'study_id': execution['study_id'],
                    'started_at': execution['started_at'].isoformat(),
                    'completed_at': execution.get('completed_at', '').isoformat() if execution.get('completed_at') else None,
                    'status': execution['status'],
                    'refresh_type': execution['refresh_type'],
                    'data_sources': execution['data_sources'],
                    'records_processed': execution.get('records_processed', 0),
                    'records_updated': execution.get('records_updated', 0),
                    'records_added': execution.get('records_added', 0),
                    'duration_seconds': execution.get('duration_seconds', 0),
                    'error_message': execution.get('error_message'),
                    'execution_details': execution.get('execution_details', {})
                }
                result.append(execution_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting refresh history: {str(e)}")
            return []
    
    def pause_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Pause a refresh schedule."""
        return self.update_refresh_schedule(schedule_id, {'enabled': False})
    
    def resume_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Resume a paused refresh schedule."""
        return self.update_refresh_schedule(schedule_id, {'enabled': True})
    
    def get_schedule_status(self, schedule_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a refresh schedule.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Detailed schedule status
        """
        try:
            schedule = self._get_schedule(schedule_id)
            if not schedule:
                raise ValueError(f"Schedule not found: {schedule_id}")
            
            # Get recent executions
            recent_executions = self._get_refresh_history(schedule_id, None, 5)
            
            # Calculate health metrics
            health_score = self._calculate_schedule_health(schedule, recent_executions)
            
            return {
                'schedule_id': schedule_id,
                'schedule_name': schedule['schedule_name'],
                'enabled': schedule['enabled'],
                'health_score': health_score,
                'next_run': schedule.get('next_run', '').isoformat() if schedule.get('next_run') else None,
                'last_run': schedule.get('last_run', '').isoformat() if schedule.get('last_run') else None,
                'success_rate': self._calculate_success_rate(schedule),
                'average_duration': self._calculate_average_duration(recent_executions),
                'recent_executions': len(recent_executions),
                'last_error': self._get_last_error(recent_executions),
                'data_sources_count': len(schedule.get('data_sources', [])),
                'refresh_type': schedule['refresh_type'],
                'cron_expression': schedule['cron_expression']
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule status: {str(e)}")
            raise
    
    def _validate_cron_expression(self, cron_expression: str) -> bool:
        """Validate cron expression."""
        try:
            croniter(cron_expression)
            return True
        except Exception:
            return False
    
    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time based on cron expression."""
        try:
            cron = croniter(cron_expression, datetime.utcnow())
            return cron.get_next(datetime)
        except Exception:
            return datetime.utcnow() + timedelta(hours=1)  # Default to 1 hour
    
    def _register_scheduled_task(self, schedule_id: str, schedule: Dict[str, Any]) -> None:
        """Register task with scheduler."""
        # This would integrate with Celery beat or similar scheduler
        logger.info(f"Registered scheduled task for {schedule_id}")
    
    def _unregister_scheduled_task(self, schedule_id: str) -> None:
        """Unregister task from scheduler."""
        logger.info(f"Unregistered scheduled task for {schedule_id}")
    
    def _execute_refresh_task(self, schedule: Dict[str, Any]) -> str:
        """Execute the actual refresh task."""
        execution_id = f"exec_{schedule['id']}_{int(datetime.utcnow().timestamp())}"
        
        # This would execute the actual data refresh
        # For now, just create an execution record
        execution_data = {
            'id': execution_id,
            'schedule_id': schedule['id'],
            'study_id': schedule['study_id'],
            'started_at': datetime.utcnow(),
            'status': 'running',
            'refresh_type': schedule['refresh_type'],
            'data_sources': schedule['data_sources']
        }
        
        self._store_execution(execution_data)
        
        # Simulate async execution
        if self.celery_app:
            # self.celery_app.send_task('data_refresh.execute', args=[execution_id])
            pass
        
        return execution_id
    
    def _calculate_success_rate(self, schedule: Dict[str, Any]) -> float:
        """Calculate success rate for a schedule."""
        run_count = schedule.get('run_count', 0)
        success_count = schedule.get('success_count', 0)
        
        if run_count == 0:
            return 100.0
        
        return (success_count / run_count) * 100
    
    def _calculate_schedule_health(
        self,
        schedule: Dict[str, Any],
        recent_executions: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall health score for a schedule."""
        health_score = 100.0
        
        # Penalize for disabled schedules
        if not schedule.get('enabled', False):
            health_score -= 50
        
        # Success rate impact
        success_rate = self._calculate_success_rate(schedule)
        health_score = health_score * (success_rate / 100)
        
        # Recent failures impact
        if recent_executions:
            recent_failures = sum(1 for ex in recent_executions[:3] if ex['status'] == 'failed')
            health_score -= recent_failures * 10
        
        # Last run recency impact
        if schedule.get('last_run'):
            hours_since_last = (datetime.utcnow() - schedule['last_run']).total_seconds() / 3600
            if hours_since_last > 48:  # More than 2 days
                health_score -= 20
        
        return max(0.0, min(100.0, health_score))
    
    def _calculate_average_duration(self, executions: List[Dict[str, Any]]) -> float:
        """Calculate average execution duration."""
        completed_executions = [
            ex for ex in executions 
            if ex.get('duration_seconds') is not None
        ]
        
        if not completed_executions:
            return 0.0
        
        total_duration = sum(ex['duration_seconds'] for ex in completed_executions)
        return total_duration / len(completed_executions)
    
    def _get_last_error(self, executions: List[Dict[str, Any]]) -> Optional[str]:
        """Get the last error message from executions."""
        for execution in executions:
            if execution['status'] == 'failed' and execution.get('error_message'):
                return execution['error_message']
        return None
    
    # Database operations (these would use actual models)
    def _store_schedule(self, schedule_data: Dict[str, Any]) -> str:
        """Store schedule in database."""
        # This would use actual SQLModel/SQLAlchemy models
        return schedule_data['id']
    
    def _get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule from database."""
        # This would query actual database
        return None
    
    def _update_schedule(self, schedule_id: str, schedule_data: Dict[str, Any]) -> None:
        """Update schedule in database."""
        pass
    
    def _delete_schedule(self, schedule_id: str) -> None:
        """Delete schedule from database."""
        pass
    
    def _get_schedules(
        self,
        study_id: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get schedules from database."""
        # This would query actual database
        return []
    
    def _store_execution(self, execution_data: Dict[str, Any]) -> None:
        """Store execution record in database."""
        pass
    
    def _get_refresh_history(
        self,
        schedule_id: Optional[str] = None,
        study_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get refresh history from database."""
        return []


def get_data_refresh_scheduler(db: Session = None) -> DataRefreshScheduler:
    """Get data refresh scheduler instance."""
    if db is None:
        db = next(get_db())
    return DataRefreshScheduler(db)