from django.contrib import admin
from django.urls import path, include

from accounts.views import (
    SafeLoginView,
    SafePasswordResetView,
    SafePasswordResetConfirmView,
    SafePasswordResetDoneView,
    SafePasswordResetCompleteView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", SafeLoginView.as_view(), name="login"),
    path(
        "accounts/password_reset/",
        SafePasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        SafePasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "accounts/password_reset/done/",
        SafePasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/done/",
        SafePasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("finance.urls")),
]
