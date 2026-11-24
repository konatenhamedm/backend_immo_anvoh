from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    GoogleLoginView,
    IdentityDocumentView,
    LoginCodeRequestView,
    LoginCodeVerifyView,
    LoginView,
    PasswordChangeView,
    PasswordForgotView,
    PasswordResetView,
    RegisterView,
    UserDetailAdminView,
    UserListCreateAdminView,
    UserProfileView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("password/forgot/", PasswordForgotView.as_view(), name="password-forgot"),
    path("password/reset/", PasswordResetView.as_view(), name="password-reset"),
    path("google/", GoogleLoginView.as_view(), name="login-google"),
    path("code/request/", LoginCodeRequestView.as_view(), name="login-code-request"),
    path("code/verify/", LoginCodeVerifyView.as_view(), name="login-code-verify"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("profile/identity/", IdentityDocumentView.as_view(), name="user-identity"),
    path("profile/password/", PasswordChangeView.as_view(), name="user-password"),
    path("users/", UserListCreateAdminView.as_view(), name="admin-users-list"),
    path("users/<int:id>/", UserDetailAdminView.as_view(), name="admin-user-detail"),
]
