from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class InvestmentSimulationInput:
    """Paramètres d'entrée pour la simulation financière d'un investissement."""

    purchase_price: Decimal  # Prix d'achat du bien (FCFA)
    down_payment: Decimal  # Apport personnel (FCFA)
    annual_interest_rate: Decimal  # Taux annuel bancaire en pourcentage (ex: 7.5 pour 7.5%)
    loan_duration_years: int  # Durée de l'emprunt en années (ex: 15 ou 20)
    monthly_rent_estimated: Decimal  # Loyer mensuel estimé (FCFA)
    monthly_charges: Decimal = Decimal("0")  # Charges mensuelles (copropriété, entretien, etc.)
    tax_rate: Decimal = Decimal("0")  # Fiscalité / prélèvement forfaitaire en % (ex: 5%)
    notary_fees_rate: Decimal = Decimal("0.08")  # Frais de notaire / mutation (par défaut ~8% en CI)


@dataclass(frozen=True)
class InvestmentSimulationResult:
    """Résultats calculés de la simulation."""

    loan_amount: Decimal  # Montant emprunté
    monthly_loan_payment: Decimal  # Mensualité bancaire
    gross_yield_percentage: Decimal  # Rentabilité brute annuelle (%)
    net_yield_percentage: Decimal  # Rentabilité nette annuelle (%)
    monthly_cash_flow: Decimal  # Cash-flow mensuel net (Loyer - Mensualité - Charges - Impôts)
    annual_cash_flow: Decimal  # Cash-flow annuel net
    total_investment_cost: Decimal  # Coût global d'acquisition (prix + notaire)
    monthly_savings_effort: Decimal  # Effort d'épargne mensuel nécessaire (si cashflow < 0)


@dataclass(frozen=True)
class BorrowingCapacityInput:
    """Paramètres pour estimer la capacité d'emprunt (simulateur de capacité d'achat)."""

    monthly_income: Decimal  # Salaire ou revenus principaux
    secondary_income: Decimal = Decimal("0")  # Revenus complémentaires
    monthly_existing_credits: Decimal = Decimal("0")  # Crédits en cours
    monthly_charges: Decimal = Decimal("0")  # Charges courantes (loyer, famille…) : spec écran 11
    available_down_payment: Decimal = Decimal("0")  # Apport disponible
    loan_duration_years: int = 20  # Durée en années
    annual_interest_rate: Decimal = Decimal("7.5")  # Taux annuel standard bancaire CI (7.5%)
    max_debt_ratio: Decimal = Decimal("0.33")  # Taux d'endettement max recommandé (33%)


@dataclass(frozen=True)
class BorrowingCapacityResult:
    """Résultat de la capacité d'achat estimée."""

    max_monthly_payment: Decimal  # Mensualité maximale supportable
    max_borrowable_amount: Decimal  # Montant empruntable maximal
    total_purchasing_power: Decimal  # Budget d'achat global max (Emprunt + Apport disponible)
