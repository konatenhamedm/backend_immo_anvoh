from decimal import Decimal

from rest_framework import serializers

from apps.simulators.domain.entities import BorrowingCapacityInput, InvestmentSimulationInput


class InvestmentSimulationInputSerializer(serializers.Serializer):
    """DTO d'entrée pour la simulation d'investissement (Recherche & Investisseurs)."""

    purchase_price = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("100000"), help_text="Prix d'achat du bien en FCFA"
    )
    down_payment = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0"), help_text="Apport personnel en FCFA"
    )
    annual_interest_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.1"),
        max_value=Decimal("30.0"),
        default=Decimal("7.5"),
        help_text="Taux bancaire annuel en % (ex: 7.5)",
    )
    loan_duration_years = serializers.IntegerField(
        min_value=1, max_value=30, default=15, help_text="Durée du prêt en années (1 à 30)"
    )
    monthly_rent_estimated = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"), help_text="Loyer mensuel estimé en FCFA"
    )
    monthly_charges = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
        help_text="Charges mensuelles en FCFA",
    )
    tax_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), default=Decimal("0"), help_text="Taux fiscal en %"
    )
    notary_fees_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=4,
        min_value=Decimal("0"),
        default=Decimal("0.08"),
        help_text="Frais de notaire (ratio, ex: 0.08 pour 8%)",
    )

    def to_domain(self) -> InvestmentSimulationInput:
        """Convertit le DTO validé en Value Object du Domaine."""
        return InvestmentSimulationInput(**self.validated_data)


class InvestmentSimulationOutputSerializer(serializers.Serializer):
    """DTO de réponse pour la simulation d'investissement."""

    loan_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    monthly_loan_payment = serializers.DecimalField(max_digits=14, decimal_places=2)
    gross_yield_percentage = serializers.DecimalField(max_digits=6, decimal_places=2)
    net_yield_percentage = serializers.DecimalField(max_digits=6, decimal_places=2)
    monthly_cash_flow = serializers.DecimalField(max_digits=14, decimal_places=2)
    annual_cash_flow = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_investment_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    monthly_savings_effort = serializers.DecimalField(max_digits=14, decimal_places=2)


class BorrowingCapacityInputSerializer(serializers.Serializer):
    """DTO d'entrée pour le simulateur de capacité d'achat."""

    monthly_income = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("10000"), help_text="Revenu net mensuel principal (FCFA)"
    )
    secondary_income = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
        help_text="Revenus complémentaires mensuels (FCFA)",
    )
    monthly_existing_credits = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
        help_text="Total des mensualités de crédits en cours (FCFA)",
    )
    monthly_charges = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
        help_text="Charges mensuelles courantes (FCFA)",
    )
    available_down_payment = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
        help_text="Épargne / Apport disponible (FCFA)",
    )
    loan_duration_years = serializers.IntegerField(
        min_value=1, max_value=30, default=20, help_text="Durée du prêt souhaitée en années"
    )
    annual_interest_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.1"),
        default=Decimal("7.5"),
        help_text="Taux bancaire annuel (%)",
    )

    def to_domain(self) -> BorrowingCapacityInput:
        return BorrowingCapacityInput(**self.validated_data)


class BorrowingCapacityOutputSerializer(serializers.Serializer):
    """DTO de réponse pour le simulateur de capacité d'achat."""

    max_monthly_payment = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_borrowable_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_purchasing_power = serializers.DecimalField(max_digits=14, decimal_places=2)
