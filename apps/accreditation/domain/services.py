"""
Règles métier de l'accréditation notariale.

Cycle d'un bien publié par un propriétaire :
  dépôt (EN_ATTENTE, non visible) → contrôle juridique → cadastre → certification
  → bien publié (DISPONIBLE) avec badge VERIFIE / VERIFICATION_RENFORCEE.
Un refus remet le bien en brouillon avec un motif ; le propriétaire corrige et redépose.
"""

from django.db import transaction
from django.utils import timezone

from apps.accreditation.infrastructure.models import (
    REQUIRED_DOCUMENTS,
    AccreditationFile,
    AccreditationStatus,
    AccreditationStep,
    CertificationLevel,
    DocumentStatus,
)
from apps.properties.infrastructure.models import Property, PropertyStatus, VerificationStatus


class AccreditationError(Exception):
    pass


def ensure_file(prop: Property) -> AccreditationFile:
    """Ouvre (ou rouvre après un refus) le dossier d'accréditation d'un bien."""
    file, created = AccreditationFile.objects.get_or_create(property=prop)
    if not created and file.status == AccreditationStatus.REFUSE:
        file.status = AccreditationStatus.EN_COURS
        file.step = AccreditationStep.DEPOT
        file.refusal_reason = ""
        file.save(update_fields=["status", "step", "refusal_reason", "updated_at"])
    if prop.verification_status not in (VerificationStatus.VERIFIE, VerificationStatus.VERIFICATION_RENFORCEE):
        prop.verification_status = VerificationStatus.EN_ATTENTE
        if prop.status == PropertyStatus.BROUILLON:
            prop.status = PropertyStatus.EN_ATTENTE
        prop.save(update_fields=["verification_status", "status", "updated_at"])
    return file


def missing_documents(file: AccreditationFile) -> list[str]:
    # `.all()` s'appuie sur le prefetch `property__documents` des listes (pas de requête par dossier).
    present = {d.doc_type for d in file.property.documents.all() if d.status != DocumentStatus.REJETE}
    return [d.value for d in REQUIRED_DOCUMENTS if d.value not in present]


def advance(file: AccreditationFile) -> AccreditationFile:
    """Passe à l'étape suivante (jusqu'à « Certification notariale »)."""
    if file.status != AccreditationStatus.EN_COURS:
        raise AccreditationError("Ce dossier n'est plus en cours.")
    if file.step == AccreditationStep.DEPOT and missing_documents(file):
        raise AccreditationError("Pièces obligatoires manquantes : " + ", ".join(missing_documents(file)))
    if file.step >= AccreditationStep.CERTIFICATION:
        raise AccreditationError("Dernière étape atteinte : certifiez ou refusez le dossier.")
    file.step += 1
    file.save(update_fields=["step", "updated_at"])
    return file


@transaction.atomic
def certify(file: AccreditationFile, level: str = CertificationLevel.VERIFIE) -> AccreditationFile:
    """Certifie le dossier et publie le bien avec le badge correspondant."""
    if file.status != AccreditationStatus.EN_COURS:
        raise AccreditationError("Ce dossier n'est plus en cours.")
    if missing_documents(file):
        raise AccreditationError("Pièces obligatoires manquantes : " + ", ".join(missing_documents(file)))
    if level not in CertificationLevel.values:
        raise AccreditationError("Niveau de certification invalide.")
    file.status = AccreditationStatus.CERTIFIE
    file.step = AccreditationStep.CERTIFICATION
    file.certification_level = level
    file.certified_at = timezone.now()
    file.save()

    prop = file.property
    prop.verification_status = level
    if prop.status in (PropertyStatus.BROUILLON, PropertyStatus.EN_ATTENTE):
        prop.status = PropertyStatus.DISPONIBLE
    prop.save(update_fields=["verification_status", "status", "updated_at"])
    return file


@transaction.atomic
def refuse(file: AccreditationFile, reason: str) -> AccreditationFile:
    """Refuse le dossier : le bien repasse en brouillon, invisible, avec le motif."""
    if not reason.strip():
        raise AccreditationError("Indiquez le motif du refus.")
    file.status = AccreditationStatus.REFUSE
    file.refusal_reason = reason.strip()
    file.save(update_fields=["status", "refusal_reason", "updated_at"])

    prop = file.property
    prop.verification_status = VerificationStatus.REFUSE
    prop.status = PropertyStatus.BROUILLON
    prop.save(update_fields=["verification_status", "status", "updated_at"])
    return file
