from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Sale, Comment

User = get_user_model()


# =====================================================================
# 1. ТЕСТЫ ДОСТУПА И БЕЗОПАСНОСТИ (МЕНЕДЖЕРЫ И ИХ ДАННЫЕ)
# =====================================================================
class DashboardAccessAndSecurityTests(TestCase):

    def setUp(self):
        self.user_dima = User.objects.create_user(
            username="dima", password="password123"
        )
        self.user_alex = User.objects.create_user(
            username="alex", password="password123"
        )

        Sale.objects.create(
            salesman=self.user_dima, sale_amount=Decimal("1000.00"), payment_type="THB"
        )
        Sale.objects.create(
            salesman=self.user_dima, sale_amount=Decimal("1500.00"), payment_type="CARD"
        )
        Sale.objects.create(
            salesman=self.user_alex, sale_amount=Decimal("5000.00"), payment_type="THB"
        )

        self.dashboard_url = reverse("dashboard")

    def test_dashboard_anonymous_redirect(self):
        """Анонимный пользователь должен перенаправляться на логин"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_shows_only_owner_sales(self):
        """Менеджер видит только свои сделки"""
        self.client.login(username="dima", password="password123")
        response = self.client.get(self.dashboard_url)
        self.assertEqual(len(response.context["sales"]), 2)
        self.assertContains(response, "1000")
        self.assertContains(response, "1500")
        self.assertNotContains(response, "5000")


# =====================================================================
# 2. ТЕСТЫ БИЗНЕС-ЛОГИКИ И АГРЕГАЦИИ СУММ
# =====================================================================
class DashboardAggregationTests(TestCase):

    def setUp(self):
        self.user_dima = User.objects.create_user(
            username="dima", password="password123"
        )
        self.user_alex = User.objects.create_user(
            username="alex", password="password123"
        )

        Sale.objects.create(
            salesman=self.user_dima, sale_amount=Decimal("1000.00"), payment_type="THB"
        )
        Sale.objects.create(
            salesman=self.user_dima, sale_amount=Decimal("1500.00"), payment_type="CARD"
        )
        Sale.objects.create(
            salesman=self.user_alex, sale_amount=Decimal("5000.00"), payment_type="THB"
        )

    def test_dashboard_total_amount_aggregation(self):
        """Сумма сделок агрегируется правильно и только для текущего юзера"""
        self.client.login(username="dima", password="password123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["total_sale_amount"], 2500)
        self.assertContains(response, "2500")


# =====================================================================
# 3. ТЕСТЫ СОЗДАНИЯ И РЕДАКТИРОВАНИЯ СДЕЛКИ (ВКЛЮЧАЯ СМАРТ-РЕДИРЕКТ)
# =====================================================================
class SaleLifecycleTests(TestCase):

    def setUp(self):
        self.user_dima = User.objects.create_user(
            username="dima", password="password123"
        )
        self.sale = Sale.objects.create(
            salesman=self.user_dima, sale_amount=Decimal("1000.00"), payment_type="THB"
        )

        self.create_url = reverse("sale_create")
        self.update_url = reverse("sale_update", kwargs={"pk": self.sale.pk})

    def test_sale_create_valid_data(self):
        """Успешное создание сделки при корректных данных"""
        self.client.login(username="dima", password="password123")
        response = self.client.post(
            self.create_url, {"sale_amount": "3000.00", "payment_type": "CARD"}
        )

        self.assertEqual(Sale.objects.filter(salesman=self.user_dima).count(), 2)
        self.assertTrue(Sale.objects.filter(sale_amount=Decimal("3000.00")).exists())

    def test_sale_update_redirect_to_dashboard(self):
        """Редирект после редактирования на дашборд при наличии ?next=dashboard"""
        self.client.login(username="dima", password="password123")
        response = self.client.post(
            f"{self.update_url}?next=dashboard",
            {"sale_amount": "1200.00", "payment_type": "THB"},
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_sale_update_redirect_to_detail(self):
        """Дефолтный редирект после редактирования обратно в карточку сделки"""
        self.client.login(username="dima", password="password123")
        response = self.client.post(
            self.update_url, {"sale_amount": "1300.00", "payment_type": "THB"}
        )
        self.assertRedirects(
            response, reverse("sale_detail", kwargs={"pk": self.sale.pk})
        )


# =====================================================================
# 4. ТЕСТЫ СИСТЕМЫ КОММЕНТАРИЕВ
# =====================================================================
class SaleCommentTests(TestCase):

    def setUp(self):
        self.user_dima = User.objects.create_user(
            username="dima", password="password123"
        )
        self.sale = Sale.objects.create(
            salesman=self.user_dima, sale_amount=Decimal("1000.00"), payment_type="THB"
        )
        self.comment_url = reverse("comment_create", kwargs={"sale_pk": self.sale.pk})

    def test_comment_creation_and_redirect(self):
        """Создание комментария к конкретной сделке и последующий возврат в карточку"""
        self.client.login(username="dima", password="password123")

        response = self.client.post(
            self.comment_url, {"comment": "Груз отправлен в Бангкок"}
        )

        self.assertRedirects(
            response, reverse("sale_detail", kwargs={"pk": self.sale.pk})
        )
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().comment, "Груз отправлен в Бангкок")
