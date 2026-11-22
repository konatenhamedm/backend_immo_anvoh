"""
Permissions par rôle, partagées par toutes les apps.

- IsAdminRole       : administrateurs (rôle ADMIN, ou superutilisateur Django)
- IsStaffOrAgent    : équipe commerciale (admin + conseillers AGENT)
- IsOwnerRole       : propriétaires et promoteurs (et l'admin, qui saisit sous mandat)
- IsNotaryOrAdmin   : notaires partenaires et administrateurs (file d'accréditation)
- ReadOnlyOr(perm)  : lecture publique, écriture réservée à `perm`
"""

from rest_framework import permissions

from apps.users.infrastructure.models import UserRole


def is_admin(user) -> bool:
    """
    Administrateur de l'API : rôle ADMIN, ou superutilisateur Django.

    Le drapeau Django `is_staff` (accès au site /admin/ de Django) ne donne PAS ce droit : un conseiller marqué
    `is_staff` pour consulter /admin/ reste un conseiller pour l'API. Ne pas ajouter `is_staff` ici.
    """
    return bool(user and user.is_authenticated and (user.role == UserRole.ADMIN or user.is_superuser))


def is_staff_or_agent(user) -> bool:
    return bool(user and user.is_authenticated and (is_admin(user) or user.role == UserRole.AGENT))


def is_owner(user) -> bool:
    return bool(user and user.is_authenticated and user.role in (UserRole.PROPRIETAIRE, UserRole.PROMOTEUR))


def is_notary(user) -> bool:
    return bool(user and user.is_authenticated and user.role == UserRole.NOTAIRE)


class IsAdminRole(permissions.BasePermission):
    message = "Réservé aux administrateurs."

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsStaffOrAgent(permissions.BasePermission):
    message = "Réservé à l'équipe Thiebbro."

    def has_permission(self, request, view):
        return is_staff_or_agent(request.user)


class IsOwnerRole(permissions.BasePermission):
    message = "Réservé aux propriétaires."

    def has_permission(self, request, view):
        return is_owner(request.user) or is_admin(request.user)


class IsNotaryOrAdmin(permissions.BasePermission):
    message = "Réservé aux notaires partenaires et aux administrateurs."

    def has_permission(self, request, view):
        return is_notary(request.user) or is_staff_or_agent(request.user)


def ReadOnlyOr(write_permission):
    """Lecture ouverte à tous ; écriture soumise à `write_permission`."""

    class _ReadOnlyOr(permissions.BasePermission):
        message = getattr(write_permission, "message", "Action non autorisée.")

        def has_permission(self, request, view):
            if request.method in permissions.SAFE_METHODS:
                return True
            return write_permission().has_permission(request, view)

    _ReadOnlyOr.__name__ = f"ReadOnlyOr{write_permission.__name__}"
    return _ReadOnlyOr
