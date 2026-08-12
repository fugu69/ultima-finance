import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.conf import settings
from django.shortcuts import redirect, render
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
from django.views.decorators.http import require_POST
from django.db.models import Sum
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.db import transaction

from .models import Sale, Comment, Presentation, PresentationComment, OutboxEvent
from .forms import CommentForm, PresentationCommentForm
from .tasks import send_single_outbox_event


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
    context_object_name = "items"
    paginate_by = 50

    def get_queryset(self):
        # 1. Ловим текущий таб из URL (по дефолту — sales)
        self.active_tab = self.request.GET.get("tab", "sales")

        if self.active_tab not in ("sales", "presentations"):
            self.active_tab = "sales"

        if self.active_tab == "presentations":
            # Возвращаем презентации текущего пользователя
            return Presentation.objects.filter(
                presenter=self.request.user
            ).prefetch_related("presentation_comments")

        # Возвращаем продажи + лениво подгружаем комменты, чтобы не плодить N+1 запросы
        return Sale.objects.filter(salesman=self.request.user).prefetch_related(
            "comments"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["active_tab"] = self.active_tab

        total = self._get_current_month_total()
        percent = self._get_bonus_percent(total, self.active_tab)

        context["total_amount"] = total
        context["bonus_percent"] = percent
        context["bonus_amount"] = (total * percent / Decimal("100")).quantize(
            Decimal("0.01")
        )
        context["currency_symbol"] = "฿"

        agent_id = self.request.user.id
        fastapi_url = f"{settings.FASTAPI_BASE_URL}/api/transfer/balance/{agent_id}"

        try:
            response = requests.get(fastapi_url, timeout=2)
            if response.status_code == 200:
                transfer_data = response.json()
                
                # 🛠 КОНВЕРТАЦИЯ СТРОК В ЧИСЛА ДЛЯ ШАБЛОНИЗАТОРА
                transfer_data["cash_debt"] = float(transfer_data.get("cash_debt", 0))
                transfer_data["daily_profit"] = float(transfer_data.get("daily_profit", 0))
                transfer_data["monthly_profit"] = float(transfer_data.get("monthly_profit", 0))
                
                # Прогоняем партнеров на случай математики в HTML
                for partner in transfer_data.get("partners", []):
                    partner["debt"] = float(partner.get("debt", 0))
                    partner["partner_profit"] = float(partner.get("partner_profit", 0))
                    
                context["transfer_data"] = transfer_data
            else:
                context["transfer_data"] = None
        except requests.RequestException:
            context["transfer_data"] = None

        return context

    def _get_current_month_total(self):
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        # 2. Считаем общую сумму в зависимости от выбранной вкладки
        if self.active_tab == "presentations":
            return Presentation.objects.filter(
                presenter=self.request.user,
                created_at__date__range=[start_of_month, today],
            ).aggregate(total=Sum("group_sales_total"))["total"] or Decimal("0.00")

        return Sale.objects.filter(
            salesman=self.request.user, created_at__date__range=[start_of_month, today]
        ).aggregate(total=Sum("sale_amount"))["total"] or Decimal("0.00")

    @staticmethod
    def _get_bonus_percent(total: Decimal, tab: str) -> Decimal:
        if tab == "presentations":
            if total < Decimal("1000000"):
                return Decimal("2.50")
            elif total < Decimal("1350000"):
                return Decimal("2.75")
            elif total < Decimal("1500000"):
                return Decimal("3.15")
            elif total < Decimal("2000000"):
                return Decimal("3.35")
            else:
                return Decimal("3.50")

        # Продажи
        if total < Decimal("250000"):
            return Decimal("1.85")
        elif total < Decimal("600000"):
            return Decimal("2.00")
        elif total < Decimal("800000"):
            return Decimal("2.35")
        elif total <= Decimal("1000000"):
            return Decimal("2.75")
        else:
            return Decimal("3.00")


# ==========================================
# CRUD ДЛЯ ПРОДАЖ (SALES)
# ==========================================


class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    template_name = "finance/sale_create.html"
    # 1. Добавили новые поля в список
    fields = [
        "sale_amount",
        "payment_type",
        "client_rate",
        "transfer_amount_rub",
        "partner_name",
        "partner_rate",
    ]

    def get_success_url(self):
        # Метка created=1 скажет HTMX, что пора сделать отложенный опрос
        return f"{reverse('dashboard')}?tab=sales&created=1"

    # 2. ТА САМАЯ МАГИЯ «ЛИПКОЙ» ФОРМЫ
    def get_initial(self):
        initial = super().get_initial()

        last_transfer = (
            Sale.objects.filter(
                salesman=self.request.user, payment_type=Sale.PaymentChoices.TRANSFER
            )
            .order_by("-created_at")
            .first()
        )

        if last_transfer:
            initial["partner_name"] = last_transfer.partner_name
            initial["client_rate"] = last_transfer.client_rate
            initial["partner_rate"] = last_transfer.partner_rate
            initial["payment_type"] = Sale.PaymentChoices.TRANSFER

        return initial

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.salesman = self.request.user

        if form.instance.payment_type != Sale.PaymentChoices.TRANSFER:
            form.instance.transfer_amount_rub = Decimal("0")

        with transaction.atomic():
            response = super().form_valid(form)
            sale = self.object

            if sale.payment_type == Sale.PaymentChoices.TRANSFER:
                payload = {
                    "sale_id": sale.id,
                    "amount": str(sale.sale_amount),
                    "transfer_amount_rub": str(sale.transfer_amount_rub),
                    "salesman_id": sale.salesman_id,
                    "partner_name": sale.partner_name,
                    "client_rate": str(sale.client_rate),
                    "partner_rate": str(sale.partner_rate),
                    "created_at": sale.created_at.isoformat(),
                }

                event = OutboxEvent.objects.create(payload=payload)

                transaction.on_commit(
                    lambda: send_single_outbox_event.delay(event.id)
                )

        return response


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


class PresentationCommentCreateView(LoginRequiredMixin, CreateView):
    model = PresentationComment
    fields = ["comment"]

    def form_valid(self, form):
        # Привязываем залогиненного юзера к комменту
        form.instance.author = self.request.user
        # Вытаскиваем id продажи из урла и привязываем коммент к ней
        form.instance.presentation_id = self.kwargs["presentation_pk"]
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PresentationCommentForm()
        return context


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


@login_required
@require_POST
def reconcile_partner(request):
    partner_name = request.POST.get('partner_name')
    amount = request.POST.get('amount')
    
    if not partner_name or not amount:
        messages.error(request, "Некорректные данные для сверки.")
        return redirect('/dashboard/?tab=sales')

    try:
        amount_float = float(amount)
    except ValueError:
        messages.error(request, "Сумма должна быть числом.")
        return redirect('/dashboard/?tab=sales')

    payload = {
        "agent_id": request.user.id,
        "partner_name": partner_name,
        "amount_received": amount_float
    }

    try:
        fastapi_url = f"{settings.FASTAPI_BASE_URL}/api/transfer/reconcile/"
        response = requests.post(fastapi_url, json=payload, timeout=5)
        
        if response.status_code == 200:
            messages.success(request, f"Сверка по {partner_name} успешно проведена.")
        else:
            messages.error(request, f"Ошибка API: {response.text}")
    except requests.RequestException as e:
        messages.error(request, f"Ошибка связи с сервером FastAPI: {e}")

    return redirect('/dashboard/?tab=sales')


# Вьюха для обработки нажатия кнопки "Сдать кассу"
@login_required
@require_POST
def clear_cash_view(request):
    agent_id = request.user.id
    try:
        fastapi_url = f"{settings.FASTAPI_BASE_URL}/api/transfer/clear_cash/{agent_id}"
        response = requests.post(fastapi_url, timeout=5)
        
        if response.status_code == 200:
            messages.success(request, "Касса успешно инкассирована. Долг обнулен.")
        else:
            messages.error(request, f"Ошибка обнуления: {response.text}")
    except requests.RequestException as e:
        messages.error(request, f"Ошибка связи с сервером: {e}")

    return redirect('/dashboard/?tab=sales')

# Новая вьюха специально для HTMX-запроса
@login_required
def transfer_accordion_view(request):
    agent_id = request.user.id
    fastapi_url = f"{settings.FASTAPI_BASE_URL}/api/transfer/balance/{agent_id}"
    
    try:
        response = requests.get(fastapi_url, timeout=2)
        transfer_data = response.json() if response.status_code == 200 else None
    except requests.RequestException:
        transfer_data = None

    response = render(request, "finance/includes/transfer_accordion.html", {
        "transfer_data": transfer_data
    })

    if transfer_data is not None:
        response.status_code = 286

    return response