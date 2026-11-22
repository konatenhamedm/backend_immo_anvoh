from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.simulators.domain.entities import BorrowingCapacityInput, InvestmentSimulationInput
from apps.simulators.domain.services import FinancialCalculationDomainService


class SimulatorDomainUnitTest(TestCase):
    """
    Tests Unitaires purs de la couche DOMAIN (Clean Architecture).
    Ne dépend d'aucune base de données, exécution ultra rapide.
    """

    def test_calculate_investment_yield_positive_flow(self):
        # Cas : Achat d'une villa à Bingerville à 50 000 000 FCFA
        # Apport: 10 000 000 FCFA, Emprunt: 40 000 000 + 4 000 000 notaire
        # Loyer mensuel estimé: 450 000 FCFA
        sim_input = InvestmentSimulationInput(
            purchase_price=Decimal("50000000"),
            down_payment=Decimal("10000000"),
            annual_interest_rate=Decimal("7.5"),
            loan_duration_years=15,
            monthly_rent_estimated=Decimal("450000"),
            monthly_charges=Decimal("30000"),
            tax_rate=Decimal("5.0"),
            notary_fees_rate=Decimal("0.08"),
        )

        result = FinancialCalculationDomainService.calculate_investment_yield(sim_input)

        self.assertGreater(result.gross_yield_percentage, Decimal("0"))
        self.assertGreater(result.total_investment_cost, sim_input.purchase_price)
        self.assertEqual(result.loan_amount, Decimal("44000000"))  # 54M total - 10M apport
        self.assertGreater(result.monthly_loan_payment, Decimal("0"))

    def test_calculate_borrowing_capacity(self):
        # Cas : Cadre diaspora avec 2 000 000 FCFA net mensuel, 0 crédit, 15 000 000 FCFA apport
        cap_input = BorrowingCapacityInput(
            monthly_income=Decimal("2000000"),
            secondary_income=Decimal("0"),
            monthly_existing_credits=Decimal("0"),
            available_down_payment=Decimal("15000000"),
            loan_duration_years=20,
            annual_interest_rate=Decimal("7.5"),
            max_debt_ratio=Decimal("0.33"),
        )
        result = FinancialCalculationDomainService.calculate_borrowing_capacity(cap_input)

        # 33% de 2 000 000 = 660 000 FCFA mensualité max
        self.assertEqual(result.max_monthly_payment, Decimal("660000"))
        self.assertGreater(result.max_borrowable_amount, Decimal("50000000"))
        self.assertEqual(result.total_purchasing_power, result.max_borrowable_amount + cap_input.available_down_payment)


class SimulatorAPIIntegrationTest(TestCase):
    """
    Tests d'intégration de la couche INTERFACE / REST API (DRF).
    """

    def setUp(self):
        self.client = APIClient()

    def test_calculate_investment_endpoint(self):
        payload = {
            "purchase_price": "80000000.00",
            "down_payment": "20000000.00",
            "annual_interest_rate": "7.50",
            "loan_duration_years": 15,
            "monthly_rent_estimated": "600000.00",
            "monthly_charges": "40000.00",
            "tax_rate": "5.00",
            "notary_fees_rate": "0.0800",
        }
        response = self.client.post("/api/v1/simulators/calculate-investment/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("monthly_loan_payment", response.data)
        self.assertIn("gross_yield_percentage", response.data)
        self.assertIn("monthly_cash_flow", response.data)

    def test_borrowing_capacity_endpoint(self):
        payload = {
            "monthly_income": "1500000.00",
            "secondary_income": "200000.00",
            "monthly_existing_credits": "150000.00",
            "available_down_payment": "10000000.00",
            "loan_duration_years": 20,
            "annual_interest_rate": "7.50",
        }
        response = self.client.post("/api/v1/simulators/borrowing-capacity/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("max_monthly_payment", response.data)
        self.assertIn("max_borrowable_amount", response.data)
        self.assertIn("total_purchasing_power", response.data)
