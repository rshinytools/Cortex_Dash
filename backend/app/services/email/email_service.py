# ABOUTME: Centralized email service that uses database-stored SMTP settings
# ABOUTME: Handles email sending, queuing, templating, and retry logic

import smtplib
import emails  # type: ignore
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID
import logging
from jinja2 import Template, Environment, BaseLoader
from pathlib import Path

from sqlmodel import Session, select
from app.core.db import engine
from app.core.encryption import encryption_service
from app.models.email_settings import (
    EmailSettings, EmailTemplate, EmailQueue, 
    EmailHistory, UserEmailPreferences,
    EmailStatus, DigestFrequency
)
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """Centralized email service using database configuration"""
    
    def __init__(self):
        self._smtp_settings: Optional[EmailSettings] = None
        self._last_settings_load: Optional[datetime] = None
        self._settings_cache_duration = timedelta(minutes=5)
    
    def _get_smtp_settings(self, session: Session) -> Optional[EmailSettings]:
        """Get active SMTP settings from database with caching"""
        now = datetime.utcnow()
        
        # Check cache
        if (self._smtp_settings and 
            self._last_settings_load and 
            now - self._last_settings_load < self._settings_cache_duration):
            return self._smtp_settings
        
        # Load from database
        statement = select(EmailSettings).where(EmailSettings.is_active == True)
        settings = session.exec(statement).first()
        
        if settings:
            # Decrypt password
            if settings.smtp_password:
                settings.smtp_password = encryption_service.decrypt(settings.smtp_password)
            
            self._smtp_settings = settings
            self._last_settings_load = now
            
        return settings
    
    def _render_template(
        self, 
        template: EmailTemplate, 
        variables: Dict[str, Any]
    ) -> tuple[str, str]:
        """Render email template with variables"""
        # Create Jinja environment
        env = Environment(loader=BaseLoader())
        
        # Render subject
        subject_template = env.from_string(template.subject)
        subject = subject_template.render(**variables)
        
        # Render HTML body
        html_template = env.from_string(template.html_template)
        html_content = html_template.render(**variables)
        
        # Render plain text if available
        plain_content = ""
        if template.plain_text_template:
            plain_template = env.from_string(template.plain_text_template)
            plain_content = plain_template.render(**variables)
        
        return subject, html_content
    
    def _should_send_to_user(
        self, 
        session: Session,
        user_id: UUID, 
        notification_type: str
    ) -> bool:
        """Check if user wants to receive this type of notification"""
        statement = select(UserEmailPreferences).where(
            UserEmailPreferences.user_id == user_id
        )
        preferences = session.exec(statement).first()
        
        if not preferences:
            # No preferences set, send by default
            return True
        
        # Check specific notification type
        preference_map = {
            "account_created": "receive_account_updates",
            "password_reset": "receive_account_updates",
            "study_created": "receive_study_updates",
            "data_uploaded": "receive_data_updates",
            "backup_created": "receive_backup_notifications",
            "backup_restored": "receive_backup_notifications",
            "backup_deleted": "receive_backup_notifications",
            "pipeline_completed": "receive_pipeline_updates",
            "pipeline_failed": "receive_pipeline_updates",
            "security_alert": "receive_security_alerts",
            "system_maintenance": "receive_system_alerts",
        }
        
        pref_field = preference_map.get(notification_type, "receive_system_alerts")
        return getattr(preferences, pref_field, True)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send an email immediately using current SMTP settings"""
        
        with Session(engine) as session:
            # Get SMTP settings
            settings = self._get_smtp_settings(session)
            if not settings:
                raise ValueError("No active email settings found")
            
            # Create email message
            message = emails.Message(
                subject=subject,
                html=html_content,
                text=plain_content,
                mail_from=(settings.smtp_from_name or "System", settings.smtp_from_email),
                cc=cc_emails,
                bcc=bcc_emails
            )
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    message.attach(
                        filename=attachment.get("filename"),
                        content_disposition="attachment",
                        data=attachment.get("data")
                    )
            
            # Configure SMTP options
            smtp_options = {
                "host": settings.smtp_host,
                "port": settings.smtp_port,
                "timeout": settings.smtp_timeout
            }
            
            if settings.smtp_use_tls:
                smtp_options["tls"] = True
            elif settings.smtp_use_ssl:
                smtp_options["ssl"] = True
            
            if settings.smtp_username:
                smtp_options["user"] = settings.smtp_username
            if settings.smtp_password:
                smtp_options["password"] = settings.smtp_password
            
            # Send email
            start_time = datetime.utcnow()
            try:
                response = message.send(to=to_email, smtp=smtp_options)
                send_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log to history
                history = EmailHistory(
                    recipient_email=to_email,
                    subject=subject,
                    status="sent",
                    sent_at=datetime.utcnow(),
                    send_duration_ms=int(send_duration),
                    provider_response={"status": "success"}
                )
                session.add(history)
                session.commit()
                
                logger.info(f"Email sent successfully to {to_email}")
                return {
                    "success": True,
                    "message_id": str(history.id),
                    "duration_ms": send_duration
                }
                
            except Exception as e:
                logger.error(f"Failed to send email to {to_email}: {str(e)}")
                
                # Log failure to history
                history = EmailHistory(
                    recipient_email=to_email,
                    subject=subject,
                    status="failed",
                    provider_response={"error": str(e)}
                )
                session.add(history)
                session.commit()
                
                raise
    
    async def queue_email(
        self,
        to_email: str,
        template_key: str,
        variables: Dict[str, Any],
        user_id: Optional[UUID] = None,
        priority: int = 5,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """Queue an email for sending using a template"""
        
        with Session(engine) as session:
            # Check user preferences if user_id provided
            if user_id and not self._should_send_to_user(session, user_id, template_key):
                logger.info(f"User {user_id} has opted out of {template_key} notifications")
                return None
            
            # Get template
            statement = select(EmailTemplate).where(
                EmailTemplate.template_key == template_key,
                EmailTemplate.is_active == True
            )
            template = session.exec(statement).first()
            
            if not template:
                raise ValueError(f"Template '{template_key}' not found or inactive")
            
            # Render template
            subject, html_content = self._render_template(template, variables)
            
            # Create queue entry
            queue_entry = EmailQueue(
                recipient_email=to_email,
                subject=subject,
                html_content=html_content,
                template_id=template.id,
                template_variables=variables,
                priority=priority,
                scheduled_at=scheduled_at,
                queue_metadata=metadata or {},
                created_by=user_id
            )
            
            session.add(queue_entry)
            session.commit()
            session.refresh(queue_entry)
            
            logger.info(f"Email queued: {queue_entry.id} for {to_email}")
            return queue_entry.id
    
    async def process_queue(self, batch_size: int = 10) -> Dict[str, Any]:
        """Process pending emails in the queue"""
        
        with Session(engine) as session:
            # Get pending emails ordered by priority and scheduled time
            now = datetime.utcnow()
            statement = (
                select(EmailQueue)
                .where(
                    EmailQueue.status == EmailStatus.PENDING,
                    (EmailQueue.scheduled_at == None) | (EmailQueue.scheduled_at <= now),
                    EmailQueue.attempts < EmailQueue.max_attempts
                )
                .order_by(EmailQueue.priority, EmailQueue.created_at)
                .limit(batch_size)
            )
            
            queue_items = session.exec(statement).all()
            
            results = {
                "processed": 0,
                "sent": 0,
                "failed": 0,
                "errors": []
            }
            
            for item in queue_items:
                # Update status to sending
                item.status = EmailStatus.SENDING
                item.attempts += 1
                session.add(item)
                session.commit()
                
                try:
                    # Send email
                    await self.send_email(
                        to_email=item.recipient_email,
                        subject=item.subject,
                        html_content=item.html_content,
                        plain_content=item.plain_text_content,
                        metadata=item.queue_metadata
                    )
                    
                    # Update status to sent
                    item.status = EmailStatus.SENT
                    item.sent_at = datetime.utcnow()
                    results["sent"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send queued email {item.id}: {str(e)}")
                    
                    # Update status and schedule retry
                    item.status = EmailStatus.FAILED
                    item.error_message = str(e)
                    
                    if item.attempts < item.max_attempts:
                        # Schedule retry with exponential backoff
                        retry_delay = 300 * (2 ** (item.attempts - 1))  # 5min, 10min, 20min
                        item.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
                        item.status = EmailStatus.PENDING
                    
                    results["failed"] += 1
                    results["errors"].append({
                        "id": str(item.id),
                        "error": str(e)
                    })
                
                session.add(item)
                session.commit()
                results["processed"] += 1
            
            logger.info(f"Queue processing complete: {results}")
            return results
    
    async def test_smtp_connection(self) -> Dict[str, Any]:
        """Test SMTP connection with current settings"""
        
        with Session(engine) as session:
            settings = self._get_smtp_settings(session)
            if not settings:
                return {
                    "success": False,
                    "error": "No active email settings found"
                }
            
            try:
                # Try to establish SMTP connection
                if settings.smtp_use_ssl:
                    server = smtplib.SMTP_SSL(
                        settings.smtp_host, 
                        settings.smtp_port,
                        timeout=settings.smtp_timeout
                    )
                else:
                    server = smtplib.SMTP(
                        settings.smtp_host,
                        settings.smtp_port,
                        timeout=settings.smtp_timeout
                    )
                    if settings.smtp_use_tls:
                        server.starttls()
                
                # Try to authenticate if credentials provided
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                
                # Close connection
                server.quit()
                
                return {
                    "success": True,
                    "message": "SMTP connection successful",
                    "host": settings.smtp_host,
                    "port": settings.smtp_port
                }
                
            except Exception as e:
                logger.error(f"SMTP connection test failed: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def send_test_email(self, to_email: str) -> Dict[str, Any]:
        """Send a test email to verify configuration"""
        
        try:
            result = await self.send_email(
                to_email=to_email,
                subject="Test Email - Clinical Dashboard",
                html_content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background-color: #4CAF50; color: white; padding: 20px; border-radius: 5px; }
                        .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>Test Email Successful!</h2>
                        </div>
                        <div class="content">
                            <p>This is a test email from your Clinical Dashboard system.</p>
                            <p>If you're receiving this email, your SMTP settings are configured correctly.</p>
                            <p><strong>Configuration Details:</strong></p>
                            <ul>
                                <li>Sent at: {timestamp}</li>
                                <li>System: Clinical Dashboard</li>
                                <li>Environment: Production</li>
                            </ul>
                        </div>
                    </div>
                </body>
                </html>
                """.replace("{timestamp}", datetime.utcnow().isoformat()),
                plain_content=f"Test email from Clinical Dashboard sent at {datetime.utcnow().isoformat()}"
            )
            
            return {
                "success": True,
                "message": f"Test email sent successfully to {to_email}",
                **result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
email_service = EmailService()