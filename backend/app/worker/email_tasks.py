# ABOUTME: Celery tasks for processing email queue and scheduled email operations
# ABOUTME: Handles background email sending, retries, and scheduled digests

from celery import shared_task
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Dict, Any

from app.services.email.email_service import email_service
from app.models.email_settings import EmailQueue, EmailStatus
from sqlmodel import Session, select
from app.core.db import engine

logger = logging.getLogger(__name__)


@shared_task(name="process_email_queue")
def process_email_queue(batch_size: int = 10) -> Dict[str, Any]:
    """
    Process pending emails in the queue
    This task runs every minute via Celery Beat
    """
    logger.info("Starting email queue processing...")
    
    try:
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Process queue
        result = loop.run_until_complete(
            email_service.process_queue(batch_size=batch_size)
        )
        
        logger.info(f"Email queue processing complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing email queue: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        loop.close()


@shared_task(name="retry_failed_emails")
def retry_failed_emails() -> Dict[str, Any]:
    """
    Retry failed emails that are due for retry
    This task runs every 5 minutes via Celery Beat
    """
    logger.info("Checking for failed emails to retry...")
    
    with Session(engine) as session:
        now = datetime.utcnow()
        
        # Find failed emails that are due for retry
        statement = (
            select(EmailQueue)
            .where(
                EmailQueue.status == EmailStatus.FAILED,
                EmailQueue.next_retry_at != None,
                EmailQueue.next_retry_at <= now,
                EmailQueue.attempts < EmailQueue.max_attempts
            )
        )
        
        failed_emails = session.exec(statement).all()
        
        if not failed_emails:
            logger.info("No failed emails to retry")
            return {"retried": 0}
        
        # Reset status for retry
        retried = 0
        for email in failed_emails:
            email.status = EmailStatus.PENDING
            email.next_retry_at = None
            session.add(email)
            retried += 1
        
        session.commit()
        
        # Process the queue to send these emails
        process_email_queue.delay()
        
        logger.info(f"Scheduled {retried} emails for retry")
        return {"retried": retried}


@shared_task(name="send_email_immediately")
def send_email_immediately(
    to_email: str,
    subject: str,
    html_content: str,
    plain_content: str = None
) -> Dict[str, Any]:
    """
    Send an email immediately without queuing
    Used for urgent notifications
    """
    logger.info(f"Sending immediate email to {to_email}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            email_service.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content
            )
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to send immediate email: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        loop.close()


@shared_task(name="process_scheduled_emails")
def process_scheduled_emails() -> Dict[str, Any]:
    """
    Process emails scheduled for specific times
    This task runs every 5 minutes via Celery Beat
    """
    logger.info("Processing scheduled emails...")
    
    with Session(engine) as session:
        now = datetime.utcnow()
        
        # Find scheduled emails that are due
        statement = (
            select(EmailQueue)
            .where(
                EmailQueue.status == EmailStatus.PENDING,
                EmailQueue.scheduled_at != None,
                EmailQueue.scheduled_at <= now
            )
        )
        
        scheduled_emails = session.exec(statement).all()
        
        if not scheduled_emails:
            logger.info("No scheduled emails to send")
            return {"processed": 0}
        
        # Mark them for immediate processing
        for email in scheduled_emails:
            email.scheduled_at = None  # Clear schedule so they get processed
            session.add(email)
        
        session.commit()
        
        # Process the queue
        process_email_queue.delay()
        
        logger.info(f"Found {len(scheduled_emails)} scheduled emails to process")
        return {"processed": len(scheduled_emails)}


@shared_task(name="send_daily_digest")
def send_daily_digest() -> Dict[str, Any]:
    """
    Send daily digest emails to users who have opted for daily frequency
    This task runs once a day at 9 AM via Celery Beat
    """
    logger.info("Sending daily digest emails...")
    
    # This would aggregate notifications and send digest emails
    # Implementation depends on specific digest requirements
    
    return {"sent": 0}  # Placeholder


@shared_task(name="cleanup_old_email_history")
def cleanup_old_email_history(days: int = 90) -> Dict[str, Any]:
    """
    Clean up old email history records
    This task runs weekly via Celery Beat
    """
    logger.info(f"Cleaning up email history older than {days} days...")
    
    with Session(engine) as session:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old email queue entries that are completed
        statement = (
            select(EmailQueue)
            .where(
                EmailQueue.status.in_([EmailStatus.SENT, EmailStatus.CANCELLED]),
                EmailQueue.created_at < cutoff_date
            )
        )
        
        old_emails = session.exec(statement).all()
        deleted = 0
        
        for email in old_emails:
            session.delete(email)
            deleted += 1
        
        session.commit()
        
        logger.info(f"Deleted {deleted} old email records")
        return {"deleted": deleted}


@shared_task(name="test_email_system")
def test_email_system() -> Dict[str, Any]:
    """
    Test task to verify Celery and email system are working
    """
    logger.info("Testing email system via Celery...")
    
    try:
        # Test SMTP connection
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            email_service.test_smtp_connection()
        )
        
        return {
            "celery": "working",
            "smtp": result
        }
        
    except Exception as e:
        return {
            "celery": "working",
            "smtp": {"success": False, "error": str(e)}
        }
    finally:
        loop.close()