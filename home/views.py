from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer, UserLoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .models import Project
from .serializers import ProjectSerializer
from .utils import get_user_projects


class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')
        # refresh = RefreshToken.for_user(user)
        # access_token = str(refresh.access_token)
        # refresh_token = str(refresh)

        return Response({
            'email': user.email,
            'message': "Login successful",
            # 'access_token': access_token,
            # 'refresh_token': refresh_token,
            # 'access_token_expires_in': 3600,
            # 'refresh_token_expires_in': 86400,
        }, status=status.HTTP_200_OK)


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
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_projects(self.request.user)

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(manager=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectListViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_projects(self.request.user)


class ProjectDetailViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_projects(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        project = self.get_object()
        serializer = self.get_serializer(project)
        return Response(serializer.data)


class ProjectUpdateViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_projects(self.request.user)

    def update(self, request, *args, **kwargs):
        project = self.get_object()
        serializer = self.get_serializer(project, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ProjectDeleteViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_projects(self.request.user)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if project.manager != request.user:
            return Response(
                {
                    "detail":
                    "You do not have permission to delete this project."
                },
                status=status.HTTP_403_FORBIDDEN
                )
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
