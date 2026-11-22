"""
Ré-exporte les modèles de `infrastructure/models.py`, comme les autres modules (crm, users, properties).

Ce fichier est nécessaire : Django ne considère qu'une application « a des modèles » (`models_module`) si elle a un
`models.py`. Sans lui, `dumpdata` ignore silencieusement les tables de ce module (donc export_demo_data aussi).
"""

from .infrastructure.models import (
    Lease,
    OwnerPayout,
    RentPayment,
)

__all__ = [
    "Lease",
    "OwnerPayout",
    "RentPayment",
]
