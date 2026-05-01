from django.urls import path

from .views import ERPSyncStatusView, ERPSyncTriggerView

urlpatterns = [
    path(
        "api/v1/erp-sync/trigger/",
        ERPSyncTriggerView.as_view(),
        name="erp-sync-trigger",
    ),
    path(
        "api/v1/erp-sync/status/<int:log_id>/",
        ERPSyncStatusView.as_view(),
        name="erp-sync-status",
    ),
]
