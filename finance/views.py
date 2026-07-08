from decimal import Decimal
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic import (
    TemplateView,
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.db.models import Sum
from django.urls import reverse, reverse_lazy

from .models import Sale, Comment, Presentation
from .forms import CommentForm


class LandingPageView(TemplateView):
    template_name = "finance/landing.html"

    # Метод dispatch срабатывает ДО того, как вьюха начнет обрабатывать GET или POST.
    # Это идеальное место, чтобы проверить паспорт юзера на входе.
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class HomePageView(LoginRequiredMixin, ListView):
    template_name = "finance/home.html"
    # Меняем имя контекста на универсальное, так как внутри будут либо продажи, либо презентации
    context_object_name = "items"

    def get_queryset(self):
        # 1. Ловим текущий таб из URL (по дефолту — sales)
        self.active_tab = self.request.GET.get("tab", "sales")

        if self.active_tab == "presentations":
            # Возвращаем презентации текущего пользователя
            return Presentation.objects.filter(presenter=self.request.user)

        # Возвращаем продажи + лениво подгружаем комменты, чтобы не плодить N+1 запросы
        return Sale.objects.filter(salesman=self.request.user).prefetch_related("comments")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Передаем имя активного таба в шаблон, чтобы подсветить нужную кнопку
        context["active_tab"] = self.active_tab

        # 2. Считаем общую сумму в зависимости от выбранной вкладки
        if self.active_tab == "presentations":
            total_sum = self.get_queryset().aggregate(Sum("group_sales_total"))
            context["total_amount"] = total_sum["group_sales_total__sum"] or Decimal("0.00")
            context["currency_symbol"] = "฿"
        else:
            total_sum = self.get_queryset().aggregate(Sum("sale_amount"))
            context["total_amount"] = total_sum["sale_amount__sum"] or Decimal("0.00")
            context["currency_symbol"] = "฿"

        return context


# ==========================================
# CRUD ДЛЯ ПРОДАЖ (SALES)
# ==========================================

class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    template_name = "finance/sale_create.html"
    fields = ["sale_amount", "payment_type"]
    # Актуализировано: шлём сразу на дашборд, минуя лендинг
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.salesman = self.request.user
        return super().form_valid(form)


class SaleDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Sale
    template_name = "finance/sale_detail.html"

    def test_func(self):
        obj = self.get_object()
        return obj.salesman == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ["comment"]

    def form_valid(self, form):
        # Привязываем залогиненного юзера к комменту
        form.instance.author = self.request.user
        # Вытаскиваем id продажи из урла и привязываем коммент к ней
        form.instance.sale_id = self.kwargs["sale_pk"]
        return super().form_valid(form)


class SaleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sale
    template_name = "finance/sale_update.html"
    fields = ["sale_amount", "payment_type"]

    def test_func(self):
        obj = self.get_object()
        return obj.salesman == self.request.user
    
    def get_success_url(self):
        next_page = self.request.GET.get("next")
        
        # Актуализировано: прямой редирект на дашборд без захода на хоум
        if next_page == "dashboard":
            return reverse("dashboard")
        
        return reverse("sale_detail", kwargs={"pk": self.object.pk})


class SaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Sale
    template_name = "finance/sale_delete.html"

    def test_func(self):
        obj = self.get_object()
        return obj.salesman == self.request.user

    # Актуализировано: возвращаем сразу на дашборд
    def get_success_url(self):
        return reverse("dashboard")


# ==========================================
# CRUD ДЛЯ ПРЕЗЕНТАЦИЙ (PRESENTATIONS)
# ==========================================

class PresentationCreateView(LoginRequiredMixin, CreateView):
    model = Presentation
    template_name = "finance/presentation_create.html"
    fields = ["group_sales_total", "group_identifier"]

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        # Автоматически назначаем текущего юзера спикером презентации
        form.instance.presenter = self.request.user
        return super().form_valid(form)

    # Актуализировано: возвращаем на дашборд с параметром вкладки презентаций
    def get_success_url(self):
        return f"{reverse('dashboard')}?tab=presentations"


class PresentationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Presentation
    template_name = "finance/presentation_detail.html"

    def test_func(self):
        # Проверяем, что эту презентацию создал именно этот юзер
        obj = self.get_object()
        return obj.presenter == self.request.user


class PresentationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Presentation
    template_name = "finance/presentation_update.html"
    fields = ["group_sales_total", "group_identifier"]

    def test_func(self):
        obj = self.get_object()
        return obj.presenter == self.request.user

    # Актуализировано: исправлена f-строка, параметры ведут на дашборд
    def get_success_url(self):
        next_page = self.request.GET.get("next")
        if next_page == "dashboard":
            return f"{reverse('dashboard')}?tab=presentations"
        
        return reverse("presentation_detail", kwargs={"pk": self.object.pk})


class PresentationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Presentation
    template_name = "finance/presentation_delete.html"

    def test_func(self):
        obj = self.get_object()
        return obj.presenter == self.request.user

    # Актуализировано: исправлена f-строка, удаление возвращает на вкладку презентаций дашборда
    def get_success_url(self):
        return f"{reverse('dashboard')}?tab=presentations"