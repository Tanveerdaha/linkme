"""URL routes for /api/v1/account/."""

from django.urls import path

from apps.accounts.account_views import (
    AccountDeleteView,
    AccountExportView,
    AccountRestoreView,
    AccountStatusView,
)

app_name = "account"

urlpatterns = [
    path("", AccountDeleteView.as_view(), name="delete"),
    path("status/", AccountStatusView.as_view(), name="status"),
    path("restore/", AccountRestoreView.as_view(), name="restore"),
    path("export/", AccountExportView.as_view(), name="export"),
]
