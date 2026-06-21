from django.urls import path

from .views import (
    HomePageView,
    SaleDetailView,
    SaleCreateView,
    SaleUpdateView,
    SaleDeleteView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("sale/<int:pk>/", SaleDetailView.as_view(), name="sale_detail"),
    path("sale/create/", SaleCreateView.as_view(), name="sale_create"),
    path("sale/<int:pk>/update/", SaleUpdateView.as_view(), name="sale_update"),
    path("sale/<int:pk>/delete/", SaleDeleteView.as_view(), name="sale_delete"),
]
