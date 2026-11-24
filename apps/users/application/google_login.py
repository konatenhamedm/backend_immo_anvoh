"""Connexion avec Google : vérifie le jeton d'identité (ID token) émis pour NOTRE identifiant client, puis connecte le compte.

Règles de sécurité :
- l'adresse e-mail doit être vérifiée par Google ;
- seuls les profils grand public peuvent se connecter ainsi (équipe, notaires : mot de passe) ;
- un compte inconnu est créé en « Particulier », sans mot de passe utilisable.
"""

from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from apps.users.infrastructure.models import SELF_SERVICE_ROLES, User, UserRole


class GoogleLoginError(Exception):
    pass


def verify(credential: str) -> dict:
    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleLoginError("La connexion avec Google n'est pas activée.")
    try:
        claims = id_token.verify_oauth2_token(credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError as e:
        raise GoogleLoginError("Jeton Google invalide ou expiré.") from e
    if not claims.get("email") or not claims.get("email_verified"):
        raise GoogleLoginError("L'adresse e-mail de ce compte Google n'est pas vérifiée.")
    return claims


def login(credential: str) -> User:
    claims = verify(credential)
    email = claims["email"].strip().lower()
    user = User.objects.filter(email__iexact=email).first()
    if user:
        if not user.is_active:
            raise GoogleLoginError("Ce compte est suspendu.")
        if user.role not in SELF_SERVICE_ROLES and user.role != UserRole.PARTICULIER:
            raise GoogleLoginError("Ce compte se connecte avec son mot de passe.")
        return user
    user = User(
        email=email,
        first_name=claims.get("given_name", "") or email.split("@")[0],
        last_name=claims.get("family_name", ""),
        phone_number="",
        role=UserRole.PARTICULIER,
    )
    user.set_unusable_password()
    user.save()
    return user
