"""Une vente conclue (étape VENTE) : on date la vente et on enregistre l'événement, quel que soit l'écran qui a déplacé le prospect."""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.analytics.application.recorder import record
from apps.analytics.domain.events import SALE
from apps.crm.infrastructure.models import Lead, PipelineStage


@receiver(pre_save, sender=Lead)
def lead_pre_save(sender, instance, raw=False, **kwargs):
    instance._was_sold = False
    if raw:
        return
    if instance.pk:
        old = sender.objects.filter(pk=instance.pk).values_list("stage", flat=True).first()
        instance._was_sold = old == PipelineStage.VENTE
    if instance.stage == PipelineStage.VENTE and not instance._was_sold and instance.converted_at is None:
        instance.converted_at = timezone.now()
    elif instance.stage != PipelineStage.VENTE and instance._was_sold:
        instance.converted_at = None  # vente annulée par l'équipe (prospect remis dans le pipeline)


@receiver(post_save, sender=Lead)
def lead_post_save(sender, instance, raw=False, **kwargs):
    if raw or instance.stage != PipelineStage.VENTE or getattr(instance, "_was_sold", False):
        return
    record(SALE, channel=instance.acquisition_channel, properties={"source": instance.source, "lead": str(instance.pk)})
