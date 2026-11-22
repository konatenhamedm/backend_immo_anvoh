"""Gestion locative : droits d'accès, saisie par l'équipe, reflet dans l'écran « Revenus » du propriétaire."""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.properties.infrastructure.models import Property, PropertyStatus
from apps.rentals.infrastructure.models import Lease, OwnerPayout, RentPayment
from apps.users.infrastructure.models import User, UserRole

PASSWORD = "Un-Mot2Passe-Solide"


def make_user(email, role):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        first_name="Test",
        last_name=email.split("@")[0],
        phone_number="+2250700000000",
        role=role,
    )


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


class RentalsAdminTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin@test.ci", UserRole.ADMIN)
        self.agent = make_user("agent@test.ci", UserRole.AGENT)
        self.owner = make_user("owner@test.ci", UserRole.PROPRIETAIRE)
        self.prop = Property.objects.create(
            title="Villa louée",
            description="d",
            property_type="VILLA",
            price=Decimal("80000000"),
            commune="Cocody",
            neighborhood="Angré",
            surface_sqm=Decimal("150"),
            status=PropertyStatus.DISPONIBLE,
            owner=self.owner,
        )
        self.admin_client = client_for(self.admin)

    def _lease(self, **extra):
        body = {
            "property": str(self.prop.id),
            "tenant_label": "Famille Assi",
            "monthly_rent": "500000",
            "start_date": "2026-01-01",
            "management_fee_rate": "10",
        }
        body.update(extra)
        return self.admin_client.post("/api/v1/rentals/admin/leases/", body, format="json")

    def test_only_admins_manage_rentals(self):
        for user in (self.agent, self.owner):
            c = client_for(user)
            self.assertEqual(c.get("/api/v1/rentals/admin/leases/").status_code, 403)
            self.assertEqual(c.get("/api/v1/rentals/admin/payments/").status_code, 403)
            self.assertEqual(c.get("/api/v1/rentals/admin/payouts/").status_code, 403)

    def test_lease_validation(self):
        self.assertEqual(self._lease(occupancy_rate=120).status_code, 400)
        self.assertEqual(self._lease(management_fee_rate="150").status_code, 400)
        self.assertEqual(self._lease(end_date="2025-12-31").status_code, 400)
        self.assertEqual(self._lease().status_code, 201)

    def test_payment_defaults_and_correction(self):
        lease = Lease.objects.get(id=self._lease().data["id"])
        r = self.admin_client.post(
            "/api/v1/rentals/admin/payments/",
            {"lease": str(lease.id), "period": "2026-03-17", "amount": "500000", "status": "EN_RETARD"},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["period"], "2026-03-01", "le mois est ramené au 1er")
        self.assertEqual(r.data["property_reference"], self.prop.reference)
        self.assertEqual(r.data["tenant_label"], "Famille Assi")
        self.assertIsNone(r.data["paid_at"])

        # Un loyer en retard est ensuite soldé : la date d'encaissement est posée automatiquement.
        fixed = self.admin_client.patch(
            f"/api/v1/rentals/admin/payments/{r.data['id']}/", {"status": "PAYE"}, format="json"
        )
        self.assertEqual(fixed.status_code, 200)
        self.assertEqual(fixed.data["paid_at"], timezone.localdate().isoformat())

        # Un mois ne peut être saisi qu'une fois par bail.
        dup = self.admin_client.post(
            "/api/v1/rentals/admin/payments/",
            {"lease": str(lease.id), "period": "2026-03-01", "amount": "1", "status": "PAYE"},
            format="json",
        )
        self.assertEqual(dup.status_code, 400)

    def test_payments_can_be_filtered(self):
        lease = Lease.objects.get(id=self._lease().data["id"])
        for month, status in (("2026-01-01", "PAYE"), ("2026-02-01", "IMPAYE")):
            RentPayment.objects.create(
                lease=lease, period=date.fromisoformat(month), amount=Decimal("500000"), status=status
            )
        r = self.admin_client.get("/api/v1/rentals/admin/payments/?status=IMPAYE")
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(self.admin_client.get(f"/api/v1/rentals/admin/payments/?lease={lease.id}").data["count"], 2)

    def test_owner_sees_net_revenue_and_payouts(self):
        lease = Lease.objects.get(id=self._lease(management_fee_rate="10").data["id"])
        today = timezone.localdate().replace(day=1)
        RentPayment.objects.create(lease=lease, period=today, amount=Decimal("500000"), status="PAYE", paid_at=today)
        payout = self.admin_client.post(
            "/api/v1/rentals/admin/payouts/",
            {
                "owner": self.owner.id,
                "amount": "450000",
                "reference": "VIR-001",
                "payout_date": today.isoformat(),
                "status": "VERSE",
            },
            format="json",
        )
        self.assertEqual(payout.status_code, 201)
        self.assertEqual(payout.data["owner_name"], "Test owner")

        summary = client_for(self.owner).get("/api/v1/rentals/owner/summary/")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(Decimal(summary.data["month_revenue"]), Decimal("450000"), "loyer net des 10 % d'honoraires")
        self.assertEqual(len(summary.data["leases"]), 1)
        self.assertEqual(len(summary.data["payouts"]), 1)

        # Un autre propriétaire ne voit rien de ces données.
        other = make_user("other@test.ci", UserRole.PROPRIETAIRE)
        empty = client_for(other).get("/api/v1/rentals/owner/summary/")
        self.assertEqual(empty.data["leases"], [])
        self.assertEqual(OwnerPayout.objects.filter(owner=other).count(), 0)
