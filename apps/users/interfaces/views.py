from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema

from apps.users.infrastructure.models import User
from .serializers import (
    RegisterUserSerializer,
    UserProfileSerializer,
    LoginInputSerializer,
    AuthTokenResponseSerializer
)

@extend_schema(tags=["Authentification & Profil"])
class RegisterView(generics.CreateAPIView):
    """
    Écran 03 : Inscription utilisateur.
    Génère automatiquement les jetons JWT à la création du compte.
    """
    queryset = User.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Authentification & Profil"],
    request=LoginInputSerializer,
    responses={200: AuthTokenResponseSerializer}
)
class LoginView(generics.GenericAPIView):
    """
    Connexion via Email et Mot de passe.
    Retourne les tokens JWT (Access & Refresh) et les informations du profil.
    """
    serializer_class = LoginInputSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, email=email, password=password)
        if not user:
            return Response(
                {'detail': 'Email ou mot de passe incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["Authentification & Profil"])
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Écran 18 : Consultation et mise à jour des informations personnelles et de "Mon Projet".
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["Back-office Utilisateurs"])
class UserListCreateAdminView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserProfileSerializer


@extend_schema(tags=["Back-office Utilisateurs"])
class UserDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'id'

