import uuid
from django.db import models
from django.conf import settings
from apps.properties.infrastructure.models import Property

class PipelineStage(models.TextChoices):
    NOUVEAU = 'NOUVEAU', 'Nouveau'
    CONTACTE = 'CONTACTE', 'Contacté'
    QUALIFIE = 'QUALIFIE', 'Qualifié'
    RDV = 'RDV', 'RDV fixé'
    VISITE = 'VISITE', 'Visite effectuée'
    PROPOSITION = 'PROPOSITION', 'Proposition formulée'
    NEGOCIATION = 'NEGOCIATION', 'Négociation'
    RESERVATION = 'RESERVATION', 'Réservation'
    VENTE = 'VENTE', 'Vente conclue (Succès)'
    PERDU = 'PERDU', 'Perdu / Sans suite'


class LeadTemperature(models.TextChoices):
    TRES_CHAUD = 'TRES_CHAUD', 'Très chaud (90-100)'
    CHAUD = 'CHAUD', 'Chaud (70-89)'
    TIEDE = 'TIEDE', 'Tiède (40-69)'
    FROID = 'FROID', 'Froid (0-39)'


class LeadSource(models.TextChoices):
    APPLICATION = 'APPLICATION', 'Application Mobile'
    SITE_WEB = 'SITE_WEB', 'Site Web'
    WHATSAPP = 'WHATSAPP', 'WhatsApp'
    TROUVER_MON_BIEN = 'TROUVER_MON_BIEN', 'Formulaire Trouver mon bien'
    DEMANDE_INFO = 'DEMANDE_INFO', 'Demande d\'information sur bien'
    VISITE = 'VISITE', 'Demande de visite'
    ESPACE_DIASPORA = 'ESPACE_DIASPORA', 'Espace Diaspora'
    SIMULATEUR = 'SIMULATEUR', 'Simulateur financier'
    AUTRE = 'AUTRE', 'Autre'


class Lead(models.Model):
    """
    Fiche CRM Commercial (Écrans 21, 22, 25, 26, 27).
    Stocke tous les prospects générés par l'application et alimente le pipeline Kanban.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Lien optionnel avec un compte utilisateur enregistré
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='leads',
        verbose_name='Compte Utilisateur'
    )

    # Identité prospect
    full_name = models.CharField('Nom complet', max_length=200)
    phone_number = models.CharField('Numéro de téléphone', max_length=30)
    whatsapp_number = models.CharField('Numéro WhatsApp', max_length=30, blank=True)
    email = models.EmailField('Email', blank=True)
    country_of_residence = models.CharField('Pays de résidence', max_length=100, default='Côte d\'Ivoire')
    is_diaspora = models.BooleanField('Réside à l\'étranger (Diaspora)', default=False)

    # Projet immobilier
    objective = models.CharField('Objectif (Habiter, Investir, Louer)', max_length=100, blank=True)
    property_type = models.CharField('Type de bien recherché', max_length=100, blank=True)
    preferred_zone = models.CharField('Zone souhaitée (Cocody, Bingerville...)', max_length=150, blank=True)
    budget = models.DecimalField('Budget envisagé (FCFA)', max_digits=14, decimal_places=2, null=True, blank=True)
    down_payment = models.DecimalField('Apport disponible (FCFA)', max_digits=14, decimal_places=2, null=True, blank=True)
    timeframe = models.CharField('Délai de réalisation', max_length=100, blank=True)

    # Bien identifié / consulté
    consulted_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='leads',
        verbose_name='Bien consulté / concerné'
    )

    # Suivi commercial & Pipeline Kanban
    source = models.CharField('Source du lead', max_length=40, choices=LeadSource.choices, default=LeadSource.APPLICATION)
    stage = models.CharField('Étape Kanban', max_length=30, choices=PipelineStage.choices, default=PipelineStage.NOUVEAU)
    
    # Scoring automatique (Écran 27)
    score = models.PositiveIntegerField('Score d\'intention (0-100)', default=20)
    temperature = models.CharField('Température commerciale', max_length=20, choices=LeadTemperature.choices, default=LeadTemperature.FROID)

    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_crm_leads',
        verbose_name='Conseiller / Agent responsable'
    )
    
    last_interaction_at = models.DateTimeField('Dernière interaction', auto_now=True)
    next_action = models.CharField('Prochaine action prévue', max_length=255, blank=True)
    commercial_notes = models.TextField('Notes & Commentaires de suivi', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Prospect CRM'
        verbose_name_plural = 'Prospects CRM'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} [{self.get_stage_display()}] - Score: {self.score}"


class CRMInteraction(models.Model):
    """
    Historique des interactions commerciales (Écran 09 Clic WhatsApp, Appel, etc.).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField('Type', max_length=50) # WHATSAPP_CLICK, INQUIRY, CALL, NOTE
    details = models.TextField('Détails / Message', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class PropertyInquiry(models.Model):
    """
    Demande d'informations sur un bien spécifique (Écran 08).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='inquiries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='inquiries')
    
    objective = models.CharField('Objectif (Habiter, Investir, Louer, Autre)', max_length=100)
    message = models.TextField('Message du prospect', blank=True)
    is_processed = models.BooleanField('Traité par le conseiller', default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Demande d\'information'
        verbose_name_plural = 'Demandes d\'informations'
        ordering = ['-created_at']


class VisitRequestType(models.TextChoices):
    PHYSIQUE = 'PHYSIQUE', 'Visite physique sur site'
    VISIO = 'VISIO', 'Visio / Visite à distance (Diaspora)'
    VISITE_3D = 'VISITE_3D', 'Visite 3D guidée (Matterport)'


class VisitRequestStatus(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    CONFIRMEE = 'CONFIRMEE', 'Confirmée'
    EFFECTUEE = 'EFFECTUEE', 'Effectuée'
    ANNULEE = 'ANNULEE', 'Annulée'


class VisitRequest(models.Model):
    """
    Demande de prise de rendez-vous / Visite (Écrans 15, 16 et 18).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='visits')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='visits')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='my_visits')

    visit_type = models.CharField('Type de visite', max_length=20, choices=VisitRequestType.choices, default=VisitRequestType.PHYSIQUE)
    status = models.CharField('Statut', max_length=20, choices=VisitRequestStatus.choices, default=VisitRequestStatus.EN_ATTENTE)

    scheduled_date = models.DateField('Date prévue')
    scheduled_time = models.TimeField('Heure prévue')
    notes = models.TextField('Commentaires éventuels', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Demande de visite / RDV'
        verbose_name_plural = 'Demandes de visites / RDV'
        ordering = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return f"Visite de {self.property.title} le {self.scheduled_date} à {self.scheduled_time} ({self.get_status_display()})"


class AlertFrequency(models.TextChoices):
    IMMEDIATE = 'IMMEDIATE', "Dès qu'un bien est publié"
    DAILY = 'DAILY', 'Résumé quotidien'
    WEEKLY = 'WEEKLY', 'Résumé hebdomadaire'


class SearchAlert(models.Model):
    """Alerte de recherche enregistrée par un utilisateur (critères du catalogue)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='search_alerts')
    transaction = models.CharField('Transaction (VENTE/LOCATION, vide = toutes)', max_length=10, blank=True)
    property_type = models.CharField('Type de bien (code, vide = tous)', max_length=30, blank=True)
    commune = models.CharField('Commune (vide = toutes)', max_length=100, blank=True)
    max_budget = models.DecimalField('Budget maximum (FCFA)', max_digits=14, decimal_places=2, null=True, blank=True)
    frequency = models.CharField('Fréquence', max_length=20, choices=AlertFrequency.choices, default=AlertFrequency.IMMEDIATE)
    is_active = models.BooleanField(default=True)
    last_notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Alerte de recherche'
        verbose_name_plural = 'Alertes de recherche'
        ordering = ['-created_at']

    def matches(self, prop) -> bool:
        """Le bien correspond-il aux critères de l'alerte ? (utilisé par l'envoi des notifications)"""
        return ((not self.transaction or prop.transaction == self.transaction)
                and (not self.property_type or prop.property_type == self.property_type)
                and (not self.commune or self.commune.lower() in prop.commune.lower())
                and (self.max_budget is None or prop.price <= self.max_budget))
