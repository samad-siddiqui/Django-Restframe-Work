from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from home.manager import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    manager = models.ForeignKey(CustomUser,
                                on_delete=models.CASCADE,
                                related_name='projects')
    members = models.ManyToManyField(CustomUser,
                                     related_name='project_members',
                                     blank=True)

    def __str__(self):
        return self.name
