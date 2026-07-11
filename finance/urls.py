from django.urls import path

from .views import (
    LandingPageView,
    HomePageView,
    SaleDetailView,
    SaleCreateView,
    SaleUpdateView,
    SaleDeleteView,
    CommentCreateView,
    PresentationCommentCreateView,
    # Добавляем вьюхи для презентаций
    PresentationCreateView,
    PresentationDetailView,
    PresentationUpdateView,
    PresentationDeleteView,
)

urlpatterns = [
    # Комментарии и Продажи (Sales)
    path(
        "sale/<int:sale_pk>/comment/",
        CommentCreateView.as_view(),
        name="comment_create",
    ),
    path(
        "presentation/<int:presentation_pk>/comment/",
        PresentationCommentCreateView.as_view(),
        name="presentation_comment_create",
    ),
    path("sale/<int:pk>/update/", SaleUpdateView.as_view(), name="sale_update"),
    path("sale/<int:pk>/delete/", SaleDeleteView.as_view(), name="sale_delete"),
    path("sale/<int:pk>/", SaleDetailView.as_view(), name="sale_detail"),
    path("sale/create/", SaleCreateView.as_view(), name="sale_create"),
    
    # Презентации (Presentations)
    path("presentation/<int:pk>/update/", PresentationUpdateView.as_view(), name="presentation_update"),
    path("presentation/<int:pk>/delete/", PresentationDeleteView.as_view(), name="presentation_delete"),
    path("presentation/<int:pk>/", PresentationDetailView.as_view(), name="presentation_detail"),
    path("presentation/create/", PresentationCreateView.as_view(), name="presentation_create"),
    
    # Главные страницы
    path("dashboard/", HomePageView.as_view(), name="dashboard"),
    path("", LandingPageView.as_view(), name="home"),
]