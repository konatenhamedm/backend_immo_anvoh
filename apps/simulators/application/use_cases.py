from apps.simulators.domain.entities import (
    InvestmentSimulationInput,
    InvestmentSimulationResult,
    BorrowingCapacityInput,
    BorrowingCapacityResult
)
from apps.simulators.domain.services import FinancialCalculationDomainService

class CalculateInvestmentYieldUseCase:
    """Use Case : Calculer la rentabilité financière et le cash-flow d'un investissement."""
    
    def __init__(self, calculation_service: FinancialCalculationDomainService = None):
        self.calculation_service = calculation_service or FinancialCalculationDomainService()

    def execute(self, input_data: InvestmentSimulationInput) -> InvestmentSimulationResult:
        # Ici peuvent intervenir des règles applicatives : audit log, métriques, etc.
        return self.calculation_service.calculate_investment_yield(input_data)


class EstimateBorrowingCapacityUseCase:
    """Use Case : Estimer la capacité d'emprunt d'un client particulier / diaspora."""

    def __init__(self, calculation_service: FinancialCalculationDomainService = None):
        self.calculation_service = calculation_service or FinancialCalculationDomainService()

    def execute(self, input_data: BorrowingCapacityInput) -> BorrowingCapacityResult:
        return self.calculation_service.calculate_borrowing_capacity(input_data)
