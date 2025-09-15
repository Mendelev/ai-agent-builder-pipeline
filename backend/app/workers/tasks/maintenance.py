# backend/app/workers/tasks/maintenance.py
from celery import Task
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.observability import get_logger, agent_duration
from app.models.orchestration import DedupKey, DomainEvent, AuditLog
from datetime import datetime, timedelta, UTC
import os
import shutil
import time

logger = get_logger(__name__)

class MaintenanceTask(Task):
    """Base task for maintenance operations"""
    
    def __init__(self):
        self.db = None
    
    def before_start(self, task_id, args, kwargs):
        """Initialize database session"""
        self.db = SessionLocal()
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Cleanup database session"""
        if self.db:
            self.db.close()

@celery_app.task(
    bind=True,
    base=MaintenanceTask,
    name="maintenance.cleanup_workdirs",
    max_retries=1
)
def cleanup_workdirs(self, retention_days: int = 7):
    """Clean up old working directories"""
    start_time = time.time()
    
    try:
        workdir_base = "/tmp/agent_workdirs"
        if not os.path.exists(workdir_base):
            return {"message": "No workdir to clean"}
        
        cutoff_time = time.time() - (retention_days * 24 * 3600)
        cleaned_count = 0
        
        for dirname in os.listdir(workdir_base):
            dirpath = os.path.join(workdir_base, dirname)
            if os.path.isdir(dirpath):
                # Check directory age
                dir_mtime = os.path.getmtime(dirpath)
                if dir_mtime < cutoff_time:
                    try:
                        shutil.rmtree(dirpath)
                        cleaned_count += 1
                        logger.info(f"Removed old workdir: {dirname}")
                    except Exception as e:
                        logger.error(f"Failed to remove {dirpath}: {e}")
        
        duration = time.time() - start_time
        agent_duration.labels(task='maintenance.cleanup_workdirs').observe(duration)
        
        result = {
            "cleaned_count": cleaned_count,
            "duration_seconds": round(duration, 2)
        }
        
        logger.info("Workdir cleanup completed", extra=result)
        return result
        
    except Exception as e:
        logger.error(f"Error in workdir cleanup: {e}")
        raise

@celery_app.task(
    bind=True,
    base=MaintenanceTask,
    name="maintenance.cleanup_expired_dedup",
    max_retries=1
)
def cleanup_expired_dedup(self):
    """Clean up expired deduplication keys"""
    start_time = time.time()
    
    try:
        # Delete expired dedup keys
        expired = self.db.query(DedupKey).filter(
            DedupKey.expires_at < datetime.now(UTC)
        ).all()
        
        deleted_count = len(expired)
        for key in expired:
            self.db.delete(key)
        
        self.db.commit()
        
        duration = time.time() - start_time
        agent_duration.labels(task='maintenance.cleanup_expired_dedup').observe(duration)
        
        result = {
            "deleted_count": deleted_count,
            "duration_seconds": round(duration, 2)
        }
        
        logger.info("Dedup cleanup completed", extra=result)
        return result
        
    except Exception as e:
        self.db.rollback()
        logger.error(f"Error in dedup cleanup: {e}")
        raise

@celery_app.task(
    bind=True,
    base=MaintenanceTask,
    name="maintenance.process_domain_events",
    max_retries=1
)
def process_domain_events(self, batch_size: int = 100):
    """Process unprocessed domain events"""
    start_time = time.time()
    
    try:
        # Get unprocessed events
        events = self.db.query(DomainEvent).filter(
            DomainEvent.processed_at.is_(None)
        ).limit(batch_size).all()
        
        processed_count = 0
        
        for event in events:
            try:
                # Process event based on type
                if event.event_name.startswith("state_changed_"):
                    # Handle state change events
                    logger.info(f"Processing state change event: {event.event_name}")
                
                elif event.event_name.startswith("agent_"):
                    # Handle agent events
                    logger.info(f"Processing agent event: {event.event_name}")
                
                # Mark as processed
                event.processed_at = datetime.now(UTC)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process event {event.id}: {e}")
        
        self.db.commit()
        
        duration = time.time() - start_time
        agent_duration.labels(task='maintenance.process_domain_events').observe(duration)
        
        result = {
            "processed_count": processed_count,
            "duration_seconds": round(duration, 2)
        }
        
        if processed_count > 0:
            logger.info("Domain events processed", extra=result)
        
        return result
        
    except Exception as e:
        self.db.rollback()
        logger.error(f"Error processing domain events: {e}")
        raise

@celery_app.task(
    bind=True,
    base=MaintenanceTask,
    name="maintenance.retry_failed_tasks",
    max_retries=1
)
def retry_failed_tasks(self, max_retries: int = 3):
    """Retry failed tasks with exponential backoff"""
    start_time = time.time()
    
    try:
        # Find recent failed agent executions
        cutoff = datetime.now(UTC) - timedelta(hours=1)
        failed_logs = self.db.query(AuditLog).filter(
            AuditLog.created_at > cutoff,
            AuditLog.event_type == 'AGENT_FAILED',
            AuditLog.success == False
        ).all()
        
        retried_count = 0
        
        for log in failed_logs:
            # Check retry count
            retry_count = log.details.get('retry_count', 0)
            if retry_count >= max_retries:
                continue
            
            # Calculate backoff delay
            backoff_seconds = min(60 * (2 ** retry_count), 600)  # Max 10 minutes
            
            # Check if enough time has passed
            time_since_failure = (datetime.now(UTC) - log.created_at).total_seconds()
            if time_since_failure < backoff_seconds:
                continue
            
            # Queue retry
            try:
                from app.services.orchestration_service import OrchestrationService
                from app.core.redis_client import redis_client
                
                OrchestrationService.retry_agent(
                    self.db,
                    redis_client,
                    log.project_id,
                    log.agent_type,
                    force=False,
                    metadata={'retry_count': retry_count + 1}
                )
                retried_count += 1
                
            except Exception as e:
                logger.error(f"Failed to retry task for project {log.project_id}: {e}")
        
        duration = time.time() - start_time
        agent_duration.labels(task='maintenance.retry_failed_tasks').observe(duration)
        
        result = {
            "retried_count": retried_count,
            "duration_seconds": round(duration, 2)
        }
        
        if retried_count > 0:
            logger.info("Failed tasks retried", extra=result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrying failed tasks: {e}")
        raise

@celery_app.task(
    bind=True,
    base=MaintenanceTask,
    name="maintenance.enforce_retention",
    max_retries=1
)
def enforce_retention(self, retention_days: int = 90):
    """Enforce audit log retention policy"""
    start_time = time.time()
    
    try:
        # Delete old audit logs
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        
        deleted = self.db.query(AuditLog).filter(
            AuditLog.created_at < cutoff
        ).delete()
        
        self.db.commit()
        
        duration = time.time() - start_time
        agent_duration.labels(task='maintenance.enforce_retention').observe(duration)
        
        result = {
            "deleted_count": deleted,
            "retention_days": retention_days,
            "duration_seconds": round(duration, 2)
        }
        
        logger.info("Retention policy enforced", extra=result)
        return result
        
    except Exception as e:
        self.db.rollback()
        logger.error(f"Error enforcing retention: {e}")
        raise