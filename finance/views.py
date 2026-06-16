from django.shortcuts import render
from django.views.generic import ListView

from .models import Sale

class HomePageView(ListView):
    model = Sale
    template_name = 'finance/home.html'
    context_object_name = 'sales'