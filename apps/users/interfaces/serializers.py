from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.users.infrastructure.models import SELF_SERVICE_ROLES, User, UserRole
from apps.users.interfaces.permissions import is_admin


class RegisterUserSerializer(serializers.ModelSerializer):
    """DTO d'inscription (Écran 03 Inscription)."""

    password = serializers.CharField(write_only=True, min_length=8)
    # Seuls les profils « grand public » sont accessibles en libre-service ; les autres sont attribués par un admin.
    role = serializers.ChoiceField(
        choices=[(r.value, r.label) for r in SELF_SERVICE_ROLES], default=UserRole.PARTICULIER
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "password",
            "country_of_residence",
            "is_diaspora",
            "role",
        ]
        read_only_fields = ["id"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        country = validated_data.get("country_of_residence", "Côte d'Ivoire")
        if country.lower() not in ["côte d'ivoire", "cote d'ivoire", "ci"]:
            validated_data["is_diaspora"] = True
        return User.objects.create_user(password=password, **validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """DTO pour consultation et modification de son propre profil (Écran 18). Le rôle n'est pas modifiable ici."""

    role_display = serializers.CharField(source="get_role_display", read_only=True)
    identity_status_display = serializers.CharField(source="get_identity_status_display", read_only=True)
    is_admin = serializers.SerializerMethodField()
    # Booléens par clé (new_matches, price_drops, visit_reminders, newsletter) ; les clés sont validées plus bas.
    notification_preferences = serializers.DictField(child=serializers.BooleanField(), required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "country_of_residence",
            "is_diaspora",
            "role",
            "role_display",
            "is_admin",
            "project_objective",
            "project_budget",
            "project_down_payment",
            "project_zone",
            "project_timeframe",
            "notifications_enabled",
            "notification_preferences",
            "identity_status",
            "identity_status_display",
            "created_at",
        ]
        read_only_fields = ["id", "email", "role", "identity_status", "created_at"]

    def get_is_admin(self, obj) -> bool:
        return is_admin(obj)

    def validate_notification_preferences(self, value):
        allowed = {"new_matches", "price_drops", "visit_reminders", "newsletter"}
        if (
            not isinstance(value, dict)
            or not set(value) <= allowed
            or not all(isinstance(v, bool) for v in value.values())
        ):
            raise serializers.ValidationError(f"Clés autorisées : {', '.join(sorted(allowed))} (valeurs booléennes).")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        user = self.context["request"].user
        if not user.check_password(data["current_password"]):
            raise serializers.ValidationError({"current_password": "Mot de passe actuel incorrect."})
        validate_password(data["new_password"], user)
        return data


class IdentityDocumentSerializer(serializers.Serializer):
    """Dépôt de la pièce d'identité (passe le statut à « en cours de vérification »)."""

    document = serializers.FileField()


class AdminUserSerializer(serializers.ModelSerializer):
    """Gestion des comptes par un administrateur (tous les rôles, statut, vérification d'identité)."""

    password = serializers.CharField(write_only=True, min_length=8, required=False)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    identity_status_display = serializers.CharField(source="get_identity_status_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "password",
            "country_of_residence",
            "is_diaspora",
            "role",
            "role_display",
            "is_active",
            "identity_status",
            "identity_status_display",
            "last_login",
            "created_at",
        ]
        read_only_fields = ["id", "last_login", "created_at"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if validated_data.get("role") == UserRole.ADMIN:
            validated_data["is_staff"] = True
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if "role" in validated_data:
            instance.is_staff = validated_data["role"] == UserRole.ADMIN or instance.is_superuser
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AuthTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserProfileSerializer()
