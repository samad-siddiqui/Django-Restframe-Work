from django.urls import path, include
from .views import UserRegistrationView, UserLoginView, LogOutView
from rest_framework.routers import DefaultRouter
from .views import (
     ProjectViewSet,
     ProjectListViewSet,
     ProjectDetailViewSet,
     ProjectUpdateViewSet,
     ProjectDeleteViewSet
     )

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'list', ProjectListViewSet, basename='project-list')
router.register(r'detail', ProjectDetailViewSet, basename='project-detail')
router.register(r'update', ProjectUpdateViewSet, basename='project-update')
router.register(r'delete', ProjectDeleteViewSet, basename='project-delete')

urlpatterns = [
    path('api/register/',
         UserRegistrationView.as_view(),
         name='user-register'),
    path('api/login/',
         UserLoginView.as_view(),
         name='user-login'),
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
