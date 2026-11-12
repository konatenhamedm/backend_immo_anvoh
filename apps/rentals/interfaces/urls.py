from django.urls import path

from .views import (
    LeaseAdminDetailView, LeaseAdminListCreateView, OwnerRentalSummaryView, PayoutAdminDetailView,
    PayoutAdminListCreateView, RentPaymentAdminListCreateView,
)

urlpatterns = [
    path('owner/summary/', OwnerRentalSummaryView.as_view(), name='owner-rental-summary'),
    path('admin/leases/', LeaseAdminListCreateView.as_view(), name='admin-leases'),
    path('admin/leases/<uuid:id>/', LeaseAdminDetailView.as_view(), name='admin-lease-detail'),
    path('admin/payments/', RentPaymentAdminListCreateView.as_view(), name='admin-rent-payments'),
    path('admin/payouts/', PayoutAdminListCreateView.as_view(), name='admin-payouts'),
    path('admin/payouts/<uuid:id>/', PayoutAdminDetailView.as_view(), name='admin-payout-detail'),
]
