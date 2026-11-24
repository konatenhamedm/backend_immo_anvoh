"""Crée une tâche de relance pour chaque prospect sans activité depuis N jours. À planifier une fois par jour (cron)."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crm.infrastructure.models import CRMSettings, Lead
from apps.notifications.application.service import notify
from apps.notifications.domain import kinds
from apps.notifications.infrastructure.models import FollowUpStatus, FollowUpTask

CLOSED_STAGES = ("VENTE", "PERDU")


class Command(BaseCommand):
    help = "Crée les tâches de relance des prospects inactifs (et prévient leur conseiller)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Inactivité en jours (défaut : réglage « Relance après » du back-office)",
        )
        parser.add_argument("--dry-run", action="store_true", help="Affiche ce qui serait créé, sans rien écrire")

    def handle(self, *args, days=None, dry_run=False, **options):
        days = days if days is not None else CRMSettings.load().followup_after_days
        limit = timezone.now() - timedelta(days=days)
        # Un prospect qui a déjà une relance ouverte n'en reçoit pas une deuxième.
        open_leads = FollowUpTask.objects.filter(status=FollowUpStatus.OUVERTE).values("lead_id")
        stale = (
            Lead.objects.exclude(stage__in=CLOSED_STAGES)
            .filter(last_interaction_at__lt=limit)
            .exclude(id__in=open_leads)
            .select_related("assigned_agent")
        )
        created = 0
        for lead in stale:
            reason = f"Aucune activité depuis {days} jour{'s' if days > 1 else ''}"
            if dry_run:
                self.stdout.write(f"[dry-run] {lead.full_name} ({lead.get_stage_display()}) — {reason}")
                continue
            task = FollowUpTask.objects.create(
                lead=lead, assigned_to=lead.assigned_agent, reason=reason, due_date=timezone.localdate()
            )
            created += 1
            if lead.assigned_agent is not None:
                notify(
                    lead.assigned_agent,
                    kinds.FOLLOWUP_DUE,
                    f"Relance à effectuer : {lead.full_name}",
                    f"{reason}. Étape : {lead.get_stage_display()}. Téléphone : {lead.phone_number}",
                    f"/admin/crm?lead={lead.pk}",
                    dedupe_key=f"followup:{task.pk}",
                )
        self.stdout.write(
            self.style.SUCCESS(f"{created} relance(s) créée(s)." if not dry_run else "Simulation terminée.")
        )
