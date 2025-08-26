# ABOUTME: Email notification service for backup and restore operations
# ABOUTME: Sends success and failure notifications to administrators with detailed information

from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from app.core.config import settings
from app.models.user import User
from sqlmodel import Session, select
from app.core.db import engine


class BackupEmailService:
    """Service for sending backup-related email notifications"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
        
    async def send_backup_success_email(
        self,
        user_id: str,
        backup_details: Dict[str, Any]
    ) -> None:
        """Send email notification for successful backup"""
        
        # Get user and all system admins
        recipients = await self._get_recipients(user_id)
        
        subject = f"✅ Backup Successful - {backup_details['filename']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
                .details {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .details-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .details-row:last-child {{ border-bottom: none; }}
                .label {{ font-weight: bold; color: #495057; }}
                .value {{ color: #212529; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
                .success-icon {{ font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2><span class="success-icon">✅</span> Backup Completed Successfully</h2>
                </div>
                <div class="content">
                    <p>The backup operation has completed successfully. All data has been securely archived and verified.</p>
                    
                    <div class="details">
                        <h3>Backup Details:</h3>
                        <div class="details-row">
                            <span class="label">Filename:</span>
                            <span class="value">{backup_details['filename']}</span>
                        </div>
                        <div class="details-row">
                            <span class="label">Size:</span>
                            <span class="value">{backup_details['size_mb']:.2f} MB</span>
                        </div>
                        <div class="details-row">
                            <span class="label">Checksum:</span>
                            <span class="value" style="font-family: monospace; font-size: 11px;">{backup_details['checksum'][:16]}...</span>
                        </div>
                        <div class="details-row">
                            <span class="label">Created At:</span>
                            <span class="value">{backup_details['created_at']}</span>
                        </div>
                        <div class="details-row">
                            <span class="label">Backup ID:</span>
                            <span class="value" style="font-family: monospace;">{backup_details['backup_id']}</span>
                        </div>
                    </div>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>The backup has been stored in the secure backup location</li>
                        <li>Checksum verification has been completed</li>
                        <li>You can download this backup from the admin panel</li>
                        <li>This backup will be retained according to the retention policy</li>
                    </ul>
                    
                    <div class="footer">
                        <p><strong>21 CFR Part 11 Compliance Notice:</strong><br>
                        This backup operation has been logged in the audit trail. The backup file includes checksums for data integrity verification. All backup operations are performed by authenticated users and tracked for compliance purposes.</p>
                        
                        <p>This is an automated notification from the Clinical Dashboard Backup System.<br>
                        Generated at: {datetime.utcnow().isoformat()}Z</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(recipients, subject, html_content)
    
    async def send_backup_failure_email(
        self,
        user_id: str,
        error_details: Dict[str, Any]
    ) -> None:
        """Send email notification for failed backup"""
        
        recipients = await self._get_recipients(user_id)
        
        subject = f"❌ Backup Failed - Immediate Attention Required"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
                .error-box {{ background-color: #fff5f5; border: 1px solid #feb2b2; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .details {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
                .error-icon {{ font-size: 24px; }}
                .code {{ background-color: #f1f1f1; padding: 10px; font-family: monospace; font-size: 12px; border-radius: 3px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2><span class="error-icon">❌</span> Backup Failed</h2>
                </div>
                <div class="content">
                    <div class="error-box">
                        <p><strong>⚠️ The backup operation has failed and requires immediate attention.</strong></p>
                    </div>
                    
                    <div class="details">
                        <h3>Error Details:</h3>
                        <p><strong>Error Message:</strong></p>
                        <div class="code">{error_details.get('error', 'Unknown error occurred')}</div>
                        
                        <p><strong>Timestamp:</strong> {error_details.get('timestamp', datetime.utcnow().isoformat())}Z</p>
                        <p><strong>Backup Type:</strong> {error_details.get('backup_type', 'full')}</p>
                    </div>
                    
                    <p><strong>Recommended Actions:</strong></p>
                    <ol>
                        <li>Check system disk space availability</li>
                        <li>Verify database connectivity</li>
                        <li>Review system logs for additional details</li>
                        <li>Ensure backup directory permissions are correct</li>
                        <li>Retry the backup operation manually</li>
                        <li>Contact system administrator if the issue persists</li>
                    </ol>
                    
                    <p><strong>⚠️ Important:</strong> Regular backups are critical for data recovery. Please resolve this issue as soon as possible to maintain data protection compliance.</p>
                    
                    <div class="footer">
                        <p><strong>21 CFR Part 11 Compliance Notice:</strong><br>
                        This backup failure has been logged in the audit trail. Immediate action is required to maintain compliance with data protection requirements.</p>
                        
                        <p>This is an automated alert from the Clinical Dashboard Backup System.<br>
                        Generated at: {datetime.utcnow().isoformat()}Z</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(recipients, subject, html_content)
    
    async def send_restore_success_email(
        self,
        user_id: str,
        restore_details: Dict[str, Any]
    ) -> None:
        """Send email notification for successful restore"""
        
        recipients = await self._get_recipients(user_id)
        
        subject = f"✅ System Restore Completed - {restore_details['backup_filename']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #17a2b8; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
                .details {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .warning-box {{ background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔄 System Restore Completed Successfully</h2>
                </div>
                <div class="content">
                    <p>The system has been successfully restored from backup. All data and configurations have been restored to the selected point in time.</p>
                    
                    <div class="details">
                        <h3>Restore Details:</h3>
                        <p><strong>Backup File:</strong> {restore_details['backup_filename']}</p>
                        <p><strong>Restore Completed:</strong> {restore_details['restored_at']}</p>
                        <p><strong>Backup ID:</strong> <code>{restore_details['backup_id']}</code></p>
                        {f'<p><strong>Safety Backup Created:</strong> <code>{restore_details.get("safety_backup_id", "N/A")}</code></p>' if restore_details.get('safety_backup_id') else ''}
                    </div>
                    
                    <div class="warning-box">
                        <p><strong>⚠️ Important Post-Restore Actions:</strong></p>
                        <ol>
                            <li>Verify system functionality and data integrity</li>
                            <li>Check all critical workflows are operational</li>
                            <li>Review audit logs for any anomalies</li>
                            <li>Notify users that the restore is complete</li>
                            <li>Document the restore operation in compliance records</li>
                        </ol>
                    </div>
                    
                    <p><strong>System Status:</strong></p>
                    <ul>
                        <li>✅ Database restored and operational</li>
                        <li>✅ File system restored</li>
                        <li>✅ Configuration settings applied</li>
                        <li>✅ Data integrity verified</li>
                    </ul>
                    
                    <div class="footer">
                        <p><strong>21 CFR Part 11 Compliance Notice:</strong><br>
                        This restore operation has been logged in the audit trail. A safety backup was created before the restore operation (if enabled). All restore operations are tracked for compliance purposes.</p>
                        
                        <p>This is an automated notification from the Clinical Dashboard Backup System.<br>
                        Generated at: {datetime.utcnow().isoformat()}Z</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(recipients, subject, html_content)
    
    async def send_restore_failure_email(
        self,
        user_id: str,
        error_details: Dict[str, Any]
    ) -> None:
        """Send email notification for failed restore"""
        
        recipients = await self._get_recipients(user_id)
        
        subject = f"❌ CRITICAL: System Restore Failed"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #721c24; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
                .critical-box {{ background-color: #f8d7da; border: 2px solid #dc3545; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .details {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
                .code {{ background-color: #f1f1f1; padding: 10px; font-family: monospace; font-size: 12px; border-radius: 3px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🚨 CRITICAL: System Restore Failed</h2>
                </div>
                <div class="content">
                    <div class="critical-box">
                        <p><strong>⛔ IMMEDIATE ACTION REQUIRED</strong></p>
                        <p>The system restore operation has failed. The system may be in an inconsistent state and requires immediate attention from the system administrator.</p>
                    </div>
                    
                    <div class="details">
                        <h3>Failure Details:</h3>
                        <p><strong>Error Message:</strong></p>
                        <div class="code">{error_details.get('error', 'Unknown error occurred during restore')}</div>
                        
                        <p><strong>Backup File:</strong> {error_details.get('backup_filename', 'Unknown')}</p>
                        <p><strong>Failure Time:</strong> {error_details.get('timestamp', datetime.utcnow().isoformat())}Z</p>
                        {f'<p><strong>Safety Backup Available:</strong> <code>{error_details.get("safety_backup_id", "None")}</code></p>' if error_details.get('safety_backup_id') else '<p><strong>Safety Backup:</strong> Not available</p>'}
                    </div>
                    
                    <p><strong>🔴 CRITICAL ACTIONS REQUIRED:</strong></p>
                    <ol style="color: #dc3545; font-weight: bold;">
                        <li>DO NOT attempt any further operations until the system state is verified</li>
                        <li>Contact the system administrator or DBA immediately</li>
                        <li>If a safety backup was created, attempt to restore from it</li>
                        <li>Check database connectivity and integrity</li>
                        <li>Review system and application logs for details</li>
                        <li>Document all actions taken for compliance records</li>
                    </ol>
                    
                    <p><strong>Recovery Options:</strong></p>
                    <ul>
                        <li>Restore from the safety backup (if available)</li>
                        <li>Restore from the previous known good backup</li>
                        <li>Manual database recovery procedures</li>
                        <li>Contact vendor support if needed</li>
                    </ul>
                    
                    <div class="footer">
                        <p><strong>21 CFR Part 11 Compliance Notice:</strong><br>
                        This restore failure has been logged in the audit trail. System integrity must be verified and documented before resuming operations. All recovery actions must be documented for compliance purposes.</p>
                        
                        <p><strong>This is a CRITICAL alert from the Clinical Dashboard Backup System.</strong><br>
                        Generated at: {datetime.utcnow().isoformat()}Z</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(recipients, subject, html_content, is_critical=True)
    
    async def _get_recipients(self, user_id: str) -> List[str]:
        """Get email recipients (user + all system admins)"""
        recipients = []
        
        with Session(engine) as session:
            # Get the user who initiated the action
            user = session.get(User, user_id)
            if user and user.email:
                recipients.append(user.email)
            
            # Get all system admins
            stmt = select(User).where(User.is_superuser == True, User.is_active == True)
            admins = session.exec(stmt).all()
            
            for admin in admins:
                if admin.email and admin.email not in recipients:
                    recipients.append(admin.email)
        
        return recipients
    
    async def _send_email(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        is_critical: bool = False
    ) -> None:
        """Send email to recipients"""
        
        if not recipients:
            print("No recipients for email notification")
            return
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(recipients)
            
            # Add priority header for critical emails
            if is_critical:
                msg['X-Priority'] = '1'
                msg['Priority'] = 'urgent'
                msg['Importance'] = 'high'
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
                print(f"Email sent successfully to {len(recipients)} recipients")
                
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            # Don't raise exception to avoid breaking backup/restore operations


    async def send_backup_deletion_email(
        self,
        user_id: str,
        backup_details: Dict[str, Any]
    ) -> None:
        """Send email notification for backup deletion"""
        
        # Get user and all system admins
        recipients = await self._get_recipients(user_id)
        
        subject = f"🗑️ Backup Deleted - {backup_details['filename']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
                .details {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .details-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .details-row:last-child {{ border-bottom: none; }}
                .label {{ font-weight: bold; color: #495057; }}
                .value {{ color: #212529; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🗑️ Backup Deleted</h2>
                </div>
                <div class="content">
                    <p>A backup has been deleted from the system. This action has been logged for audit purposes.</p>
                    
                    <div class="details">
                        <h3>Deletion Details:</h3>
                        <div class="details-row">
                            <span class="label">Filename:</span>
                            <span class="value">{backup_details['filename']}</span>
                        </div>
                        <div class="details-row">
                            <span class="label">Backup ID:</span>
                            <span class="value" style="font-family: monospace;">{backup_details['backup_id']}</span>
                        </div>
                        <div class="details-row">
                            <span class="label">Deleted At:</span>
                            <span class="value">{backup_details['deleted_at']}</span>
                        </div>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong> This backup has been permanently deleted and cannot be recovered. 
                        This action has been recorded in the audit log for compliance purposes.
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated notification from the Clinical Dashboard Backup System.</p>
                        <p>For 21 CFR Part 11 compliance, all backup deletions are logged and tracked.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        await self._send_email(recipients, subject, html_content)
        print(f"Deletion notification sent to {len(recipients)} recipients")

# Singleton instance
backup_email_service = BackupEmailService()