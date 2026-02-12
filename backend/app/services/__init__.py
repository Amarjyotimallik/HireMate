"""
Services Package
"""

from app.services.auth_service import (
    create_user,
    authenticate_user,
    refresh_tokens,
    get_user_by_id,
    get_current_user_from_token,
    get_first_active_user,
)
from app.services.task_service import (
    create_task,
    get_task_by_id,
    get_tasks,
    update_task,
    delete_task,
    get_tasks_by_ids,
    get_suggested_task_ids,
)
from app.services.question_service import generate_questions_from_resume
from app.services.attempt_service import (
    create_attempt,
    get_attempt_by_id,
    get_attempt_by_token,
    validate_and_get_assessment,
    start_assessment,
    complete_assessment,
    update_task_progress,
    lock_attempt,
    delete_attempt,
    get_attempts,
    extend_attempt_expiry,
)
from app.services.event_service import (
    log_event,
    log_events_batch,
    get_events_for_attempt,
    get_events_for_task,
    validate_option_id,
)
from app.services.metrics_service import (
    compute_metrics,
    get_metrics,
)
from app.services.skill_service import (
    generate_skill_profile,
    get_skill_profile,
    get_candidates_with_skills,
)
from app.services.live_metrics_service import (
    compute_live_metrics,
    get_active_assessments,
    get_completed_assessments,
)
from app.services.email_service import send_assessment_email
from app.services.bulk_assessment_service import (
    create_bulk_job,
    get_bulk_job,
    get_bulk_jobs_for_recruiter,
    process_bulk_resumes,
    get_active_jobs,
)

__all__ = [
    # Auth
    "create_user",
    "authenticate_user",
    "refresh_tokens",
    "get_user_by_id",
    "get_current_user_from_token",
    "get_first_active_user",
    # Task
    "create_task",
    "get_task_by_id",
    "get_tasks",
    "update_task",
    "delete_task",
    "get_tasks_by_ids",
    "get_suggested_task_ids",
    "generate_questions_from_resume",
    # Attempt
    "create_attempt",
    "get_attempt_by_id",
    "get_attempt_by_token",
    "validate_and_get_assessment",
    "start_assessment",
    "complete_assessment",
    "update_task_progress",
    "lock_attempt",
    "delete_attempt",
    "get_attempts",
    "extend_attempt_expiry",
    # Event
    "log_event",
    "log_events_batch",
    "get_events_for_attempt",
    "get_events_for_task",
    "validate_option_id",
    # Metrics
    "compute_metrics",
    "get_metrics",
    # Skill
    "generate_skill_profile",
    "get_skill_profile",
    "get_candidates_with_skills",
    # Live Metrics
    "compute_live_metrics",
    "get_active_assessments",
    "get_completed_assessments",
    # Email
    "send_assessment_email",
    # Bulk
    "create_bulk_job",
    "get_bulk_job",
    "get_bulk_jobs_for_recruiter",
    "process_bulk_resumes",
    "get_active_jobs",
]
