import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.properties.infrastructure.models import Property


class Lease(models.Model):
    """Bail d'un bien confié en gestion locative à Thiebbro."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='leases')
    tenant_label = models.CharField('Locataire (ex: Famille Assi, Location courte durée)', max_length=150)
    monthly_rent = models.DecimalField('Loyer mensuel (FCFA)', max_digits=12, decimal_places=2)
    occupancy_rate = models.PositiveSmallIntegerField('Taux d\'occupation (%)', default=100)
    management_fee_rate = models.DecimalField('Honoraires de gestion (%)', max_digits=5, decimal_places=2, default=Decimal('8.00'))
    start_date = models.DateField('Début du bail')
    end_date = models.DateField('Fin du bail', null=True, blank=True)
    is_active = models.BooleanField('Bail en cours', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bail en gestion'
        verbose_name_plural = 'Baux en gestion'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.property.reference} — {self.tenant_label}"


class RentStatus(models.TextChoices):
    PAYE = 'PAYE', 'Payé'
    EN_RETARD = 'EN_RETARD', 'En retard'
    IMPAYE = 'IMPAYE', 'Impayé'


class RentPayment(models.Model):
    """Loyer d'un mois donné pour un bail."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='payments')
    period = models.DateField('Mois concerné (1er du mois)')
    amount = models.DecimalField('Montant encaissé (FCFA)', max_digits=12, decimal_places=2, default=Decimal('0'))
    status = models.CharField('Statut', max_length=20, choices=RentStatus.choices, default=RentStatus.PAYE)
    paid_at = models.DateField('Encaissé le', null=True, blank=True)

    class Meta:
        verbose_name = 'Loyer encaissé'
        verbose_name_plural = 'Loyers encaissés'
        ordering = ['-period']
        unique_together = ('lease', 'period')


class PayoutStatus(models.TextChoices):
    PROGRAMME = 'PROGRAMME', 'Programmé'
    VERSE = 'VERSE', 'Versé'


class OwnerPayout(models.Model):
    """Versement des loyers nets au propriétaire."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField('Montant net (FCFA)', max_digits=14, decimal_places=2)
    reference = models.CharField('Référence du virement', max_length=50, blank=True)
    payout_date = models.DateField('Date de versement')
    status = models.CharField('Statut', max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.PROGRAMME)

    class Meta:
        verbose_name = 'Versement propriétaire'
        verbose_name_plural = 'Versements propriétaires'
        ordering = ['-payout_date']
