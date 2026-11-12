from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    UserProfileView,
    IdentityDocumentView,
    PasswordChangeView,
    UserListCreateAdminView,
    UserDetailAdminView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/identity/', IdentityDocumentView.as_view(), name='user-identity'),
    path('profile/password/', PasswordChangeView.as_view(), name='user-password'),
    path('users/', UserListCreateAdminView.as_view(), name='admin-users-list'),
    path('users/<int:id>/', UserDetailAdminView.as_view(), name='admin-user-detail'),
]
