from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.simulators.application.use_cases import (
    CalculateInvestmentYieldUseCase,
    EstimateBorrowingCapacityUseCase
)
from apps.simulators.interfaces.serializers import (
    InvestmentSimulationInputSerializer,
    InvestmentSimulationOutputSerializer,
    BorrowingCapacityInputSerializer,
    BorrowingCapacityOutputSerializer
)

class InvestmentYieldSimulationView(APIView):
    """
    Contrôleur API pour calculer la rentabilité brute/nette et le cash-flow d'un investissement immobilier.
    """
    @extend_schema(
        summary="Calculer la rentabilité financière d'un investissement",
        description="Prend en compte le prix d'achat, l'apport, le taux bancaire, la durée, le loyer estimé, les charges et la fiscalité.",
        request=InvestmentSimulationInputSerializer,
        responses={200: InvestmentSimulationOutputSerializer},
        tags=["Simulateurs Financiers"]
    )
    def post(self, request):
        serializer = InvestmentSimulationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = CalculateInvestmentYieldUseCase()
        domain_input = serializer.to_domain()
        result = use_case.execute(domain_input)

        response_serializer = InvestmentSimulationOutputSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class BorrowingCapacitySimulationView(APIView):
    """
    Contrôleur API pour calculer la capacité d'emprunt maximale et le pouvoir d'achat immobilier.
    """
    @extend_schema(
        summary="Estimer la capacité d'achat et d'emprunt",
        description="Calcule la mensualité maximale supportable (règle des 33% d'endettement) et le budget total disponible.",
        request=BorrowingCapacityInputSerializer,
        responses={200: BorrowingCapacityOutputSerializer},
        tags=["Simulateurs Financiers"]
    )
    def post(self, request):
        serializer = BorrowingCapacityInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = EstimateBorrowingCapacityUseCase()
        domain_input = serializer.to_domain()
        result = use_case.execute(domain_input)

        response_serializer = BorrowingCapacityOutputSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
