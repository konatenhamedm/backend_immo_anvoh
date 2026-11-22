from django.urls import path

from .views import (
    ConfirmPaymentView,
    InvestmentDocumentUploadView,
    InvestmentStatsView,
    MyInvestmentsView,
    PlanAdminDetailView,
    PlanAdminListCreateView,
    PlanListView,
    RevenueEntryCreateView,
    SubscribeView,
    SubscriptionAdminDetailView,
    SubscriptionAdminListView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="investment-plans"),
    path("subscriptions/", SubscribeView.as_view(), name="investment-subscribe"),
    path("me/", MyInvestmentsView.as_view(), name="my-investments"),
    path("admin/plans/", PlanAdminListCreateView.as_view(), name="admin-plans"),
    path("admin/plans/<uuid:id>/", PlanAdminDetailView.as_view(), name="admin-plan-detail"),
    path("admin/stats/", InvestmentStatsView.as_view(), name="admin-investment-stats"),
    path("admin/subscriptions/", SubscriptionAdminListView.as_view(), name="admin-subscriptions"),
    path("admin/subscriptions/<uuid:id>/", SubscriptionAdminDetailView.as_view(), name="admin-subscription-detail"),
    path(
        "admin/subscriptions/<uuid:id>/revenues/", RevenueEntryCreateView.as_view(), name="admin-subscription-revenue"
    ),
    path(
        "admin/subscriptions/<uuid:id>/documents/",
        InvestmentDocumentUploadView.as_view(),
        name="admin-subscription-documents",
    ),
    path("admin/entries/<uuid:id>/confirm/", ConfirmPaymentView.as_view(), name="admin-entry-confirm"),
]
