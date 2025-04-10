from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .serializers import ProjectSerializer, ProfileSerializer, TaskSerializer
from .serializers import AssignSerializer
# from .utils import get_user_projects
from .models import Profile, Project, Task
from rest_framework.decorators import action
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

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = serializer.save(assignee=profile)

        return Response(self.get_serializer(task).data,
                        status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        user = self.request.user
        profile = Profile.objects.get(user=user)
        if profile.role != 'manager' or task.assignee != user:
            return Response({
                "detail": "You do not have permission to update this task"
            }, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

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
        profile = user.profile  # Guaranteed to exist due to signal

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
