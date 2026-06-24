from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.db.models import Sum
from django.urls import reverse_lazy


from .models import Sale


class HomePageView(ListView):
    model = Sale
    template_name = "finance/home.html"
    context_object_name = "sales"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # aggregate() вернет словарь вида: {'sale_amount__sum': 15400.00}
        # name__sum is name convention
        total_sum = Sale.objects.aggregate(Sum("sale_amount"))
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


class SaleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sale
    template_name = "finance/sale_update.html"
    fields = ["sale_amount", "payment_type"]
    success_url = reverse_lazy("home")

    def test_func(self):
        obj = self.get_object()
        return obj.salesman == self.request.user


class SaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Sale
    template_name = "finance/sale_delete.html"
    success_url = reverse_lazy("home")

    def test_func(self):
        obj = self.get_object()
        return obj.salesman == self.request.user
