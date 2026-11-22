from django.urls import path

from .views import BorrowingCapacitySimulationView, InvestmentYieldSimulationView

urlpatterns = [
    path("calculate-investment/", InvestmentYieldSimulationView.as_view(), name="calculate-investment"),
    path("borrowing-capacity/", BorrowingCapacitySimulationView.as_view(), name="borrowing-capacity"),
]
