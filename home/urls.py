from django.urls import path, include
from .views import UserRegistrationView, LogOutView
from rest_framework.routers import DefaultRouter
from .views import (
     ProjectViewSet,
     ProfileViewSet,
     TaskViewSet,
     )

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'task', TaskViewSet, basename='task')

urlpatterns = [
    path('api/register/',
         UserRegistrationView.as_view(),
         name='user-register'),
    path('api/logout/',
         LogOutView.as_view(),
         name='user-logout'),
    path('api/',
         include(router.urls)),
    path('api/token/',
         TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('api/token/refresh/',
         TokenRefreshView.as_view(),
         name='token_refresh'),
]
