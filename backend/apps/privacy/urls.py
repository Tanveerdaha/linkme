"""Privacy URL routes."""

from django.urls import path

from apps.privacy.views import PrivacySettingsView

app_name = "privacy"

urlpatterns = [
    path("settings/", PrivacySettingsView.as_view(), name="settings"),
]
