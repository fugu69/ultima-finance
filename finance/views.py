from django.views.generic import ListView
from django.db.models import Sum


from .models import Sale

class HomePageView(ListView):
    model = Sale
    template_name = 'finance/home.html'
    context_object_name = 'sales'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # aggregate() вернет словарь вида: {'sale_amount__sum': 15400.00}
        # name__sum is name convention
        total_sum = Sale.objects.aggregate(Sum('sale_amount'))
        context['total_sale_amount'] = total_sum['sale_amount__sum'] or 0

        return context