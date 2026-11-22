from rest_framework import generics, status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from apps.users.infrastructure.models import User, IdentityStatus
from .permissions import IsAdminRole
from .throttling import ScopedThrottleMixin
from .serializers import (
    RegisterUserSerializer,
    UserProfileSerializer,
    AdminUserSerializer,
    IdentityDocumentSerializer,
    PasswordChangeSerializer,
    LoginInputSerializer,
    AuthTokenResponseSerializer
)


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh), 'user': UserProfileSerializer(user).data}


@extend_schema(tags=["Authentification & Profil"])
class RegisterView(ScopedThrottleMixin, generics.CreateAPIView):
    """Écran 03 : Inscription. Génère les jetons JWT à la création du compte."""
    throttle_scope = 'auth'
    queryset = User.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(_tokens_for(user), status=status.HTTP_201_CREATED)


@extend_schema(tags=["Authentification & Profil"], request=LoginInputSerializer, responses={200: AuthTokenResponseSerializer})
class LoginView(ScopedThrottleMixin, generics.GenericAPIView):
    """Connexion par e-mail et mot de passe : jetons JWT + profil."""
    throttle_scope = 'auth'
    serializer_class = LoginInputSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, email=serializer.validated_data['email'], password=serializer.validated_data['password'])
        if not user:
            return Response({'detail': 'Email ou mot de passe incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(_tokens_for(user), status=status.HTTP_200_OK)


@extend_schema(tags=["Authentification & Profil"])
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Écran 18 : informations personnelles et « Mon projet »."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["Authentification & Profil"], request=IdentityDocumentSerializer, responses={200: UserProfileSerializer})
class IdentityDocumentView(APIView):
    """Dépôt de la pièce d'identité : le compte passe « en cours de vérification »."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = IdentityDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.identity_document = serializer.validated_data['document']
        user.identity_status = IdentityStatus.EN_ATTENTE
        user.save(update_fields=['identity_document', 'identity_status', 'updated_at'])
        return Response(UserProfileSerializer(user).data)


@extend_schema(tags=["Authentification & Profil"], request=PasswordChangeSerializer, responses={200: AuthTokenResponseSerializer},
               summary="Changer son mot de passe (renvoie de nouveaux jetons)")
class PasswordChangeView(ScopedThrottleMixin, APIView):
    throttle_scope = 'auth'
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password', 'updated_at'])
        return Response(_tokens_for(request.user))


@extend_schema(tags=["Back-office Utilisateurs"])
class UserListCreateAdminView(generics.ListCreateAPIView):
    """Liste filtrable (?q=, ?role=, ?status=actif|suspendu|verification) et création de comptes."""
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by('-created_at')
        params = self.request.query_params
        if params.get('q'):
            q = params['q']
            qs = qs.filter(Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone_number__icontains=q))
        if params.get('role'):
            qs = qs.filter(role=params['role'])
        status_filter = params.get('status')
        if status_filter == 'suspendu':
            qs = qs.filter(is_active=False)
        elif status_filter == 'verification':
            qs = qs.filter(is_active=True, identity_status=IdentityStatus.EN_ATTENTE)
        elif status_filter == 'actif':
            qs = qs.filter(is_active=True)
        return qs


@extend_schema(tags=["Back-office Utilisateurs"])
class UserDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    lookup_field = 'id'

    def perform_destroy(self, instance):
        if instance == self.request.user:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Vous ne pouvez pas supprimer votre propre compte.'})
        instance.delete()
