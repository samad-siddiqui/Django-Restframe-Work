from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import CustomUser, Profile, TimelineEvent, Task, Notification


@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


@receiver(post_save, sender=Task)
def log_task_creation(sender, instance, created, **kwargs):
    if created:
        TimelineEvent.objects.create(
            project=instance.project,
            user=instance.assigned_by,
            action='task_created',
            description=f"Task '{instance.title}' was created."
        )
        # Notify all team members
        for member in instance.project.team_member.all():
            Notification.objects.create(
                user=member,
                message=f"A new task '{instance.title}' has been created."
            )
    else:
        TimelineEvent.objects.create(
            project=instance.project,
            user=instance.assigned_by,
            action='task_updated',
            description=f"Task '{instance.title}' was updated."
        )
        for member in instance.project.team_member.all():
            Notification.objects.create(
                user=member,
                message=f"Task '{instance.title}' has been updated."
            )


@receiver(post_delete, sender=Task)
def log_task_deletion(sender, instance, **kwargs):
    TimelineEvent.objects.create(
        project=instance.project,
        user=instance.assigned_by,
        action='task_deleted',
        description=f"Task '{instance.title}' was deleted."
    )
    for member in instance.project.team_member.all():
        Notification.objects.create(
            user=member,
            message=f"Task '{instance.title}' has been deleted."
        )
