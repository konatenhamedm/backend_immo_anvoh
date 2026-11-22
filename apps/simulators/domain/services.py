from decimal import ROUND_HALF_UP, Decimal

from .entities import (
    BorrowingCapacityInput,
    BorrowingCapacityResult,
    InvestmentSimulationInput,
    InvestmentSimulationResult,
)


def _round_currency(val: Decimal) -> Decimal:
    """Arrondit au franc CFA le plus proche."""
    return val.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _round_percentage(val: Decimal) -> Decimal:
    """Arrondit les pourcentages à 2 décimales."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class FinancialCalculationDomainService:
    """
    Règles métier financières pures pour le marché immobilier ivoirien.
    Isolé de tout framework (aucun import Django / DB).
    """

    @staticmethod
    def calculate_investment_yield(data: InvestmentSimulationInput) -> InvestmentSimulationResult:
        notary_fees = data.purchase_price * data.notary_fees_rate
        total_investment_cost = data.purchase_price + notary_fees

        # Montant financé par la banque
        loan_amount = max(Decimal("0"), total_investment_cost - data.down_payment)

        # Calcul de la mensualité de prêt standard
        monthly_payment = Decimal("0")
        if loan_amount > Decimal("0") and data.loan_duration_years > 0:
            monthly_rate = (data.annual_interest_rate / Decimal("100")) / Decimal("12")
            total_months = data.loan_duration_years * 12

            if monthly_rate > Decimal("0"):
                # Formule bancaire standard: M = C * [t / (1 - (1 + t)^(-n))]
                # En notation Python Decimal:
                numerator = monthly_rate * ((Decimal("1") + monthly_rate) ** total_months)
                denominator = ((Decimal("1") + monthly_rate) ** total_months) - Decimal("1")
                monthly_payment = loan_amount * (numerator / denominator)
            else:
                monthly_payment = loan_amount / Decimal(total_months)

        # Calcul des rentabilités annuelles
        annual_rent = data.monthly_rent_estimated * Decimal("12")
        annual_charges = data.monthly_charges * Decimal("12")
        annual_taxes = annual_rent * (data.tax_rate / Decimal("100"))

        # Rentabilité brute (%) = (Loyer annuel / Prix d'achat) * 100
        gross_yield = (annual_rent / data.purchase_price) * Decimal("100") if data.purchase_price > 0 else Decimal("0")

        # Rentabilité nette (%) = ((Loyer annuel - Charges - Taxes) / Coût total projet) * 100
        net_annual_income = annual_rent - annual_charges - annual_taxes
        net_yield = (
            (net_annual_income / total_investment_cost) * Decimal("100") if total_investment_cost > 0 else Decimal("0")
        )

        # Cash-flow
        monthly_taxes = annual_taxes / Decimal("12")
        monthly_net_cash_flow = data.monthly_rent_estimated - monthly_payment - data.monthly_charges - monthly_taxes
        annual_net_cash_flow = monthly_net_cash_flow * Decimal("12")

        # Effort d'épargne (si cashflow négatif, c'est ce que l'investisseur doit injecter chaque mois)
        monthly_savings_effort = abs(monthly_net_cash_flow) if monthly_net_cash_flow < Decimal("0") else Decimal("0")

        return InvestmentSimulationResult(
            loan_amount=_round_currency(loan_amount),
            monthly_loan_payment=_round_currency(monthly_payment),
            gross_yield_percentage=_round_percentage(gross_yield),
            net_yield_percentage=_round_percentage(net_yield),
            monthly_cash_flow=_round_currency(monthly_net_cash_flow),
            annual_cash_flow=_round_currency(annual_net_cash_flow),
            total_investment_cost=_round_currency(total_investment_cost),
            monthly_savings_effort=_round_currency(monthly_savings_effort),
        )

    @staticmethod
    def calculate_borrowing_capacity(data: BorrowingCapacityInput) -> BorrowingCapacityResult:
        total_monthly_income = data.monthly_income + data.secondary_income
        max_allowed_debt = total_monthly_income * data.max_debt_ratio

        # Mensualité disponible
        available_monthly_payment = max(Decimal("0"), max_allowed_debt - data.monthly_existing_credits)

        # Capacité d'emprunt maximale correspondante
        max_borrowable = Decimal("0")
        if available_monthly_payment > Decimal("0") and data.loan_duration_years > 0:
            monthly_rate = (data.annual_interest_rate / Decimal("100")) / Decimal("12")
            total_months = data.loan_duration_years * 12

            if monthly_rate > Decimal("0"):
                # Formule inverse de l'emprunt: C = M * [ (1 - (1+t)^(-n)) / t ]
                factor = (((Decimal("1") + monthly_rate) ** total_months) - Decimal("1")) / (
                    monthly_rate * ((Decimal("1") + monthly_rate) ** total_months)
                )
                max_borrowable = available_monthly_payment * factor
            else:
                max_borrowable = available_monthly_payment * Decimal(total_months)

        total_purchasing_power = max_borrowable + data.available_down_payment

        return BorrowingCapacityResult(
            max_monthly_payment=_round_currency(available_monthly_payment),
            max_borrowable_amount=_round_currency(max_borrowable),
            total_purchasing_power=_round_currency(total_purchasing_power),
        )
