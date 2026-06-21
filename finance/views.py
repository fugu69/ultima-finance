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


class SaleCreateView(CreateView):
    model = Sale
    template_name = "finance/sale_create.html"
    fields = ["sale_amount", "salesman", "payment_type"]
    success_url = reverse_lazy("home")


class SaleDetailView(DetailView):
    model = Sale
    template_name = "finance/sale_detail.html"


class SaleUpdateView(UpdateView):
    model = Sale
    template_name = "finance/sale_update.html"
    fields = ["sale_amount", "payment_type"]


class SaleDeleteView(DeleteView):
    model = Sale
    template_name = "finance/sale_delete.html"
    success_url = reverse_lazy("home")
