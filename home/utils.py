from django.db.models import Q
# from rest_framework.permissions import IsAuthenticated
from home.models import Project


def get_user_projects(user):
    return Project.objects.filter(
        Q(manager=user) | Q(members=user)
    )
