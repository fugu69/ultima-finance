from django.urls import path

from .views import (
    LandingPageView,
    HomePageView,
    SaleDetailView,
    SaleCreateView,
    SaleUpdateView,
    SaleDeleteView,
    CommentCreateView,
)

urlpatterns = [
    path(
        "sale/<int:sale_pk>/comment/",
        CommentCreateView.as_view(),
        name="comment_create",
    ),
    path("sale/<int:pk>/update/", SaleUpdateView.as_view(), name="sale_update"),
    path("sale/<int:pk>/delete/", SaleDeleteView.as_view(), name="sale_delete"),
    path("sale/<int:pk>/", SaleDetailView.as_view(), name="sale_detail"),
    path("sale/create/", SaleCreateView.as_view(), name="sale_create"),
    path("dashboard/", LandingPageView.as_view(), name="dashboard"),
    path("", HomePageView.as_view(), name="home"),
]
