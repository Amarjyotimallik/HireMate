"""
Celery Tasks for Bulk Resume Processing

Each resume is processed as an individual Celery task, enabling:
- Parallel processing across workers
- Rate limiting per worker
- Automatic retries on failure
- Progress tracking via Redis
"""

import json
import uuid
from datetime import datetime

from app.celery_app import celery_app


@celery_app.task(
    bind=True,
    name='app.celery_tasks.process_single_resume',
    max_retries=2,
    default_retry_delay=10,
    rate_limit='10/m',
    acks_late=True,
)
def process_single_resume(self, job_id, file_data, recruiter_id):
    """
    Process a single resume file synchronously in a Celery worker.

    Args:
        job_id: Bulk job ID
        file_data: Dict with 'filename', 'content_b64', 'content_type', 'size'
        recruiter_id: Recruiter user ID

    Returns:
        Dict with processing result
    """
    import asyncio
    import base64

    filename = file_data['filename']
    content = base64.b64decode(file_data['content_b64'])
    content_type = file_data['content_type']
    file_size = file_data['size']

    result = {
        'filename': filename,
        'file_size': file_size,
        'status': 'processing',
        'assessment_id': None,
        'assessment_token': None,
        'candidate_name': None,
        'candidate_email': None,
        'position': None,
        'parsed_skills': [],
        'error_message': None,
        'email_sent': False,
        'email_sent_at': None,
        'processed_at': None,
    }


    try:
        # Run the async processing in a new event loop
        # IMPORTANT: Create fresh loop each time to avoid "Event loop is closed"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _process_resume_async(job_id, content, content_type, filename, file_size, recruiter_id, result)
            )
        finally:
            # Clean up pending tasks before closing
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Run loop one more time to handle cancellations
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()


    except Exception as e:
        result['status'] = 'failed'
        result['error_message'] = str(e)[:500]
        result['processed_at'] = datetime.utcnow().isoformat()
        print(f"[CELERY] Error processing {filename}: {e}")

        # Retry on transient errors (API timeouts, etc.)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

    return result


async def _process_resume_async(job_id, content, content_type, filename, file_size, recruiter_id, result):
    """Async helper to process a single resume using existing services."""
    from app.utils.resume_parser import extract_text_from_file, parse_resume_text
    from app.services.attempt_service import create_attempt
    from app.schemas.attempt import AttemptCreate, CandidateInfo
    from app.db import connect_to_mongodb, close_mongodb_connection

    # Connect to MongoDB (each Celery worker needs its own connection)
    await connect_to_mongodb()

    try:
        # Step 1: Extract text
        text = extract_text_from_file(content, content_type, filename)
        if not text or len(text.strip()) < 10:
            raise ValueError("Could not extract meaningful text from file")

        # Step 2: Parse resume with AI
        parsed = parse_resume_text(text)
        candidate_name = parsed.get('name') or 'Candidate'
        candidate_email = parsed.get('email') or f"candidate_{uuid.uuid4().hex[:8]}@pending.com"
        position = parsed.get('position') or 'General Application'
        skills = parsed.get('skills') or []

        result['candidate_name'] = candidate_name
        result['candidate_email'] = candidate_email
        result['position'] = position
        result['parsed_skills'] = skills

        # Step 3: Create assessment attempt
        attempt_data = AttemptCreate(
            candidate_info=CandidateInfo(
                name=candidate_name,
                email=candidate_email,
                position=position,
                skills=skills,
                resume_text=text,
            ),
            task_ids=[],
            expires_in_days=7,
        )

        attempt = await create_attempt(attempt_data, recruiter_id)

        result['status'] = 'success'
        result['assessment_id'] = attempt.id
        result['assessment_token'] = attempt.token
        result['processed_at'] = datetime.utcnow().isoformat()

        # Update job progress in MongoDB
        from app.db import get_database
        db = get_database()
        await db.bulk_jobs.update_one(
            {'job_id': job_id},
            {
                '$push': {'results': result},
                '$inc': {'processed_count': 1, 'success_count': 1},
                '$set': {'current_file': filename, 'updated_at': datetime.utcnow()},
            },
        )
        
        # Check if this was the last file
        from app.services.bulk_assessment_service import check_celery_job_completion
        await check_celery_job_completion(job_id)

    except ValueError as e:
        result['status'] = 'failed'
        result['error_message'] = str(e)
        result['processed_at'] = datetime.utcnow().isoformat()

        from app.db import get_database
        db = get_database()
        await db.bulk_jobs.update_one(
            {'job_id': job_id},
            {
                '$push': {'results': result},
                '$inc': {'processed_count': 1, 'failed_count': 1},
                '$set': {'current_file': filename, 'updated_at': datetime.utcnow()},
            },
        )

    except Exception as e:
        result['status'] = 'failed'
        result['error_message'] = str(e)[:500]
        result['processed_at'] = datetime.utcnow().isoformat()

        try:
            from app.db import get_database
            db = get_database()
            await db.bulk_jobs.update_one(
                {'job_id': job_id},
                {
                    '$push': {'results': result},
                    '$inc': {'processed_count': 1, 'failed_count': 1},
                    '$set': {'current_file': filename, 'updated_at': datetime.utcnow()},
                },
            )
            
            # Check if this was the last file
            from app.services.bulk_assessment_service import check_celery_job_completion
            await check_celery_job_completion(job_id)
        except Exception:
            pass
        raise

    finally:
        await close_mongodb_connection()

    return result
