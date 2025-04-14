from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import ProjectSerializer, ProfileSerializer, TaskSerializer
from .serializers import DocumentSerializer, CommentSerializer
from .serializers import TimelineEventSerializer, NotificationSerializer
# from .utils import get_user_projects
from .models import Profile, Project, Task, Document, Comment
from .models import TimelineEvent, Notification
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

# from rest_framework import serializers


class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class UserLoginView(APIView):

#     def post(self, request):
#         serializer = UserLoginSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data.get('user')
#         # refresh = RefreshToken.for_user(user)
#         # access_token = str(refresh.access_token)
#         # refresh_token = str(refresh)

#         return Response({
#             'email': user.email,
#             'message': "Login successful",
#             # 'access_token': access_token,
#             # 'refresh_token': refresh_token,
#             # 'access_token_expires_in': 3600,
#             # 'refresh_token_expires_in': 86400,
#         }, status=status.HTTP_200_OK)


class LogOutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            print(f"Received refresh token: {refresh_token}")
            token = RefreshToken(refresh_token)
            print("Before blacklisting:", token)
            token.blacklist()
            print("After blacklisting:", token)
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response({"detail": "Refresh token is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {e}")
            return Response({"detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        if user.is_superuser or profile.role == 'manager':
            return Project.objects.all()
        else:
            # Only show projects the user is a part of or assigned to
            return Project.objects.filter(team_member=user)

    def create(self, request, *args, **kwargs):
        user = request.user
        # Check if profile exists and fetch the profile
        profile = Profile.objects.get(user=user)
        # Check if the user is a manager or superuser
        if not user.is_superuser and profile.role != 'manager':
            return Response({
                "detail": "You do not have permission to create a project."
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(team_member=[user])
        # Proceed with the project creation if the checks pass
        return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

    def update(self, request, *args, **kwargs):
        project = self.get_object()
        user = self.request.user
        profile = Profile.objects.get(user=user)
        if profile.role != 'manager' or project.manager != user:
            return Response({
                "detail": "You do not have permission to update this project"
            }, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        user = self.request.user
        profile = Profile.objects.get(user=user)
        # Check if the user is a manager and part of the project team
        if profile.role == 'manager' and user in project.team_member.all():
            return super().destroy(request, *args, **kwargs)
        else:
            return Response({
                "detail": "You do not have permission to delete this project"
            }, status=status.HTTP_403_FORBIDDEN)


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Check if the user is a manager or superuser
        if user.is_superuser or Profile.objects.get(
                    user=user).role == 'manager':
            return Profile.objects.all()
        else:
            return Profile.objects.filter(user=user)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        # Check if the user is a manager or superuser
        if profile.user == user:
            return super().destroy(request, *args, **kwargs)
        else:
            return Response({
                "detail": "You do not have permission to delete this profile"
            }, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        # Check if the user is a manager or superuser
        if profile.user == user:
            return super().update(request, *args, **kwargs)
        else:
            return Response({
                "detail": "You do not have permission to update this profile"
            }, status=status.HTTP_403_FORBIDDEN)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        if user.is_superuser or profile.role == 'manager':
            return Task.objects.all()
        else:
            # Only show tasks the user is a part of or assigned to
            return Task.objects.filter(project__team_member=user)

    def create(self, request, *args, **kwargs):
        user = request.user
        profile = Profile.objects.get(user=user)

        if not user.is_superuser and profile.role != 'manager':
            return Response({
                "detail": "You do not have permission to create a task."
            }, status=status.HTTP_403_FORBIDDEN)
        # return super().create(request, *args, **kwargs)
    
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(assignee=profile)

        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        user = self.request.user
        profile = Profile.objects.get(user=user)
        if profile.role != 'manager' and task.assignee != user:
            return Response({
                "detail": "You do not have permission to update this task"
            }, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(assigned_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        user = self.request.user
        profile = Profile.objects.get(user=user)
        # Check if the user is a manager and part of the project team
        if profile.role == 'manager' and user in task.project.team_member.all(
        ):
            return super().destroy(request, *args, **kwargs)
        else:
            return Response({
                "detail": "You do not have permission to delete this task"
            }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'], url_path='assign',
            permission_classes=[IsAuthenticated])
    def assign(self, request, pk=None):
        task = self.get_object()
        user = request.user
        profile = user.profile

        if profile.role != "manager":
            return Response({
                "detail": "You do not have permission to assign this task."
            }, status=status.HTTP_403_FORBIDDEN)

        assignee_id = request.data.get("assignee_id")
        print(f"Assignee ID: {assignee_id}")
        if not assignee_id:
            return Response({
                "detail": "assignee_id is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            assignee_profile = Profile.objects.get(id=assignee_id)
        except Profile.DoesNotExist:
            return Response({
                "detail": "Assignee not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Optional: Check if assignee user is part of the project
        if assignee_profile.user not in task.project.team_member.all():
            return Response({
                "detail": "User is not a member of this project."
            }, status=status.HTTP_400_BAD_REQUEST)

        task.assignee = assignee_profile
        task.save()

        return Response({
            "detail": f"Task assigned to {assignee_profile.user.email}."
        }, status=status.HTTP_200_OK)


class DocumentViewSet(viewsets.ModelViewSet):
    document = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        if project_id:
            return self.queryset.filter(project_id=project_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        project_id = self.request.data.get('project')
        project = get_object_or_404(Project, id=project_id)
        if self.request.user not in project.team_member.all():
            raise PermissionDenied("You are not part of this project.")
        serializer.save(project_id=project_id)


class CommentViewSet(viewsets.ModelViewSet):
    task = Task.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Comment.objects.all()
        else:
            return Comment.objects.filter(task__project__team_member=user)

    def create(self, request, *args, **kwargs):
        user = request.user
        task_id = request.data.get('task')

        if not task_id:
            return Response(
                {"detail": "Task ID is required to add a comment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {"detail": "Task not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_superuser or user in task.project.team_member.all():
            return super().create(request, *args, **kwargs)

        return Response(
            {
                "detail": "You don't have permission to add comments."},
            status=status.HTTP_403_FORBIDDEN
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        user = self.request.user
        if user.is_superuser or user in task.project.team_member.all():
            return super().update(request, *args, **kwargs)
        return Response(
            {"detail": "You do not have permission to update comments."},
            status=status.HTTP_403_FORBIDDEN
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        task = comment.task
        project = task.project
        user = self.request.user
        profile = Profile.objects.get(user=user)

        if (
            user.is_superuser or
            (profile.role == 'manager' and user in project.team_member.all())
            or
            comment.author == user
        ):
            return super().destroy(request, *args, **kwargs)

        return Response(
            {"detail": "You do not have permission to delete this comment."},
            status=status.HTTP_403_FORBIDDEN
        )


class TimelineEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TimelineEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TimelineEvent.objects.all().order_by('-created_at')
        return TimelineEvent.objects.filter(
            project__team_member=user).order_by('-created_at')


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(user=user)

    @action(detail=True, methods=['PUT'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'detail': 'Notification marked as read.'})
