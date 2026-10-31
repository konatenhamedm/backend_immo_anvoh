from rest_framework import serializers
from apps.users.infrastructure.models import User, UserRole, ProjectObjective, ProjectTimeframe

class RegisterUserSerializer(serializers.ModelSerializer):
    """DTO d'inscription (Écran 03 Inscription)."""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'phone_number', 'email',
            'password', 'country_of_residence', 'is_diaspora', 'role'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        country = validated_data.get('country_of_residence', 'Côte d\'Ivoire')
        if country.lower() not in ['côte d\'ivoire', 'cote d\'ivoire', 'ci']:
            validated_data['is_diaspora'] = True
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """DTO pour consultation et modification de profil (Écran 18 Profil)."""
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'country_of_residence', 'is_diaspora', 'role',
            'project_objective', 'project_budget', 'project_down_payment',
            'project_zone', 'project_timeframe', 'notifications_enabled',
            'created_at'
        ]
        read_only_fields = ['id', 'email', 'created_at']


class LoginInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AuthTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserProfileSerializer()
