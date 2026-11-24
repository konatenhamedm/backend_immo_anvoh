"""Accès au compte sans mot de passe connu : réinitialisation par lien et connexion par code (e-mail).

Principe commun : ne jamais révéler si une adresse e-mail est inscrite (la réponse est toujours la même).
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.users.infrastructure.models import LoginCode, User

CODE_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5
RESEND_AFTER = timedelta(seconds=60)


def _send(user: User, subject: str, body: str) -> None:
    send_mail(
        subject=subject,
        message=f"{body}\n\n— THIEBBRO IMMO",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,  # une messagerie en panne ne doit ni bloquer ni trahir l'existence du compte
    )


def _active_user(email: str) -> User | None:
    return User.objects.filter(email__iexact=email.strip(), is_active=True).first()


def send_password_reset(email: str) -> None:
    user = _active_user(email)
    if not user:
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL.rstrip('/')}/mot-de-passe/nouveau?uid={uid}&token={token}"
    _send(
        user,
        "Réinitialisation de votre mot de passe",
        f"Bonjour,\n\nPour choisir un nouveau mot de passe, ouvrez ce lien (valable quelques heures) :\n{link}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message : votre mot de passe reste inchangé.",
    )


def reset_password(uid: str, token: str, new_password: str) -> User | None:
    """Renvoie l'utilisateur si le lien est valide (le nouveau mot de passe est alors enregistré), sinon None."""
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)), is_active=True)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None
    if not default_token_generator.check_token(user, token):
        return None
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])  # le jeton devient invalide : il dépend du mot de passe
    return user


def send_login_code(email: str) -> None:
    user = _active_user(email)
    if not user:
        return
    last = user.login_codes.first()
    if last and timezone.now() - last.created_at < RESEND_AFTER:
        return  # un seul code par minute
    code = f"{secrets.randbelow(10**6):06d}"
    user.login_codes.filter(used=False).update(used=True)
    LoginCode.objects.create(user=user, code_hash=make_password(code), expires_at=timezone.now() + CODE_TTL)
    _send(
        user,
        f"Votre code de connexion : {code}",
        f"Bonjour,\n\nVotre code de connexion est {code}. Il est valable 10 minutes.\n"
        "Ne le communiquez à personne. Si vous n'avez rien demandé, ignorez ce message.",
    )


def verify_login_code(email: str, code: str) -> User | None:
    user = _active_user(email)
    if not user:
        return None
    entry = user.login_codes.filter(used=False, expires_at__gt=timezone.now()).first()
    if not entry or entry.attempts >= MAX_ATTEMPTS:
        return None
    entry.attempts += 1
    if not check_password(code.strip(), entry.code_hash):
        entry.save(update_fields=["attempts"])
        return None
    entry.used = True
    entry.save(update_fields=["used", "attempts"])
    return user
