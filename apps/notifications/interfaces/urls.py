from django.urls import path

from .views import (
    FollowUpDoneView,
    FollowUpListView,
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationUnreadCountView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications"),
    path("unread-count/", NotificationUnreadCountView.as_view(), name="notifications-unread-count"),
    path("read-all/", NotificationReadAllView.as_view(), name="notifications-read-all"),
    path("<uuid:id>/read/", NotificationReadView.as_view(), name="notification-read"),
    path("followups/", FollowUpListView.as_view(), name="followups"),
    path("followups/<uuid:id>/done/", FollowUpDoneView.as_view(), name="followup-done"),
]
