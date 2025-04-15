from celery import shared_task
from django.utils import timezone
from .models import Project, Notification, TimelineEvent
from datetime import datetime


@shared_task
def print_heartbeat():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] 🟢 Celery is alive.")


@shared_task
def check_overdue_projects():
    """
    Celery task to identify all due and overdue projects and return their
    details.
    - Overdue: Projects with end_date before today.
    - Due: Projects with end_date equal to today.
    Returns a dictionary with lists of due and overdue projects.
    """
    today = timezone.now().date()
    # Fetch current date
    # Overdue projects: end_date is before today
    overdue_projects = Project.objects.filter(
        end_date__isnull=False,
        end_date__date__lt=today
    )

    # Due projects: date part of end_date is today
    due_projects = Project.objects.filter(
        end_date__isnull=False,
        end_date__date=today
    )
    # Prepare notifications and timeline events
    notifications = []
    timeline_events = []

    # Process overdue projects
    for project in overdue_projects:
        # Notify team members
        for member in project.team_member.all():
            notifications.append(
                Notification(
                    user=member,
                    message=f"Project '{project.title}'(due {
                        project.end_date.date()})."
                )
            )
        # Log timeline event (no user, since no manager)
        timeline_events.append(
            TimelineEvent(
                project=project,
                user=None,  # Nullable field, so safe
                action='task_updated',  # Using existing choice
                description=f"Project '{project.title}' marked as overdue."
            )
        )
    # Process due projects
    for project in due_projects:
        # Notify team members
        for member in project.team_member.all():
            notifications.append(
                Notification(
                    user=member,
                    message=f"Project '{
                        project.title
                        }' you’re assigned to is due today."
                )
            )

    # Bulk create notifications and timeline events
    Notification.objects.bulk_create(notifications)
    TimelineEvent.objects.bulk_create(timeline_events)

    # Prepare response
    result = {
        'due_projects': list(due_projects.values('id', 'title', 'end_date')),
        'overdue_projects': list(overdue_projects.values(
            'id', 'title', 'end_date')),
        'due_count': due_projects.count(),
        'overdue_count': overdue_projects.count(),
        'timestamp': timezone.now().isoformat()
    }

    return result


