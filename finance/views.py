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
from django.urls import reverse_lazy


from .models import Sale, Comment
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
    model = Sale
    template_name = "finance/home.html"
    context_object_name = "sales"

    # Перехватываем стандартный запрос к БД и фильтруем его
    def get_queryset(self):
        queryset = super().get_queryset()
        # Из базы поднимутся только строки, где salesman — это тот, кто сейчас залогинен
        return queryset.filter(salesman=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get_queryset() вернет данные для авторизованного пользователя
        # aggregate() вернет словарь вида: {'sale_amount__sum': 15400.00}
        # name__sum is name convention
        total_sum = self.get_queryset().aggregate(Sum("sale_amount"))
        context["total_sale_amount"] = total_sum["sale_amount__sum"] or 0

        return context


class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    template_name = "finance/sale_create.html"
    fields = ["sale_amount", "payment_type"]
    success_url = reverse_lazy("home")

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
    success_url = reverse_lazy("home")

    def test_func(self):
        obj = self.get_object()
        return obj.salesman == self.request.user
    
    def get_success_url(self):
        # Смотрим, какой параметр прилетел в URL (?next=dashboard или ?next=detail)
        next_page = self.request.GET.get("next")
        
        if next_page == "dashboard":
            return reverse_lazy("dashboard")
        
        # По дефолту (или если пришли из карточки) возвращаем на детальный просмотр этой сделки
        return reverse_lazy("sale_detail", kwargs={"pk": self.object.pk})


class SaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Sale
    template_name = "finance/sale_delete.html"

    def test_func(self):
        obj = self.get_object()
        return obj.salesman == self.request.user

    def get_success_url(self):
        # Если удалили из дашборда или карточки, возвращаем на дашборд
        next_page = self.request.GET.get("next")
        
        if next_page == "dashboard":
            return reverse_lazy("dashboard")
            
        # По дефолту после удаления сделки тоже отправляем на дашборд
        return reverse_lazy("dashboard")
