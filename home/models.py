from django.db import models
from PIL import Image
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .manager import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    last_login = models.DateTimeField(auto_now=True)
    phone_number = models.CharField(max_length=11, unique=True,
                                    blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def has_prem(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Profile(models.Model):

    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('QA', 'QA'),
        ('developer', 'Developer'),
        ('engineer', 'Engineer'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True, null=True)
    image = models.ImageField(
        default='default.jpg', blank=True,
        upload_to='profile_pics/')

    contact = models.IntegerField(blank=True, null=True)

    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default='developer')

    def __str__(self):
        return f'{self.user.username}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


class Project(models.Model):

    title = models.CharField(max_length=20, blank=False)
    description = models.TextField(max_length=500, blank=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    team_member = models.ManyToManyField(CustomUser, related_name="projects")

    def __str__(self):
        return self.title


class Task(models.Model):

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('review', 'Review'),
        ('working', 'Working'),
        ('awaiting_release', 'Awaiting Release'),
        ('waiting_qa', 'Waiting QA')
    ]
    title = models.CharField(max_length=20, blank=False)
    description = models.TextField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks")
    assignee = models.ForeignKey(
        Profile, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tasks")

    assigned_by = models.ForeignKey(CustomUser, null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='assigned_tasks')

    def __str__(self):
        return self.title

    @property
    def get_comments(self):
        return self.comments.all()


class Document(models.Model):
    name = models.CharField(max_length=10, blank=False)
    description = models.TextField(max_length=500, blank=True)
    file = models.FileField(upload_to='documents/')
    version = models.FloatField(default=1.0)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="documents")

    def __str__(self):
        return f"{self.name} (v{self.version})"


class Comment(models.Model):
    text = models.TextField(max_length=500, blank=False, null=True)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.email} - {self.task.title}"


class TimelineEvent(models.Model):
    ACTION_CHOICES = [
        ('task_created', 'Task Created'),
        ('task_updated', 'Task Updated'),
        ('comment_added', 'Comment Added'),
        ('document_uploaded', 'Document Uploaded'),
        ('project_overdue', 'Project Overdue'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                related_name='timeline_events')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user.email} on {self.created_at}"


class Notification(models.Model):
    user = models.ForeignKey(CustomUser,
                             on_delete=models.CASCADE,
                             related_name='notifications')
    message = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message}"

    class Meta:
        ordering = ['-created_at']
