from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Sale, Comment

User = get_user_model()

# =====================================================================
# 1. ТЕСТЫ ДОСТУПА, СТАТУС-КОДОВ И ШАБЛОНОВ ДАШБОРДА
# =====================================================================
class DashboardAccessAndTemplateTests(TestCase):

    def setUp(self):
        self.user_dima = User.objects.create_user(username="dima", password="password123")
        self.user_alex = User.objects.create_user(username="alex", password="password123")
        
        Sale.objects.create(salesman=self.user_dima, sale_amount=Decimal("1000.00"), payment_type="THB")
        Sale.objects.create(salesman=self.user_alex, sale_amount=Decimal("5000.00"), payment_type="THB")
        
        self.dashboard_url = reverse("dashboard")

    def test_dashboard_anonymous_redirect(self):
        """Анонимный пользователь должен перенаправляться на логин (302)"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_renders_correct_template_and_status(self):
        """Авторизованный юзер получает 200 OK и правильный набор шаблонов"""
        self.client.login(username="dima", password="password123")
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "finance/home.html")
        self.assertTemplateUsed(response, "base.html")

    def test_dashboard_shows_only_owner_sales(self):
        """Менеджер изолирован и видит в контексте только свои сделки"""
        self.client.login(username="dima", password="password123")
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(len(response.context["sales"]), 1)
        self.assertContains(response, "1000")
        self.assertNotContains(response, "5000")


# =====================================================================
# 2. ТЕСТЫ БИЗНЕС-ЛОГИКИ И АГРЕГАЦИИ СУММ
# =====================================================================
class DashboardAggregationTests(TestCase):

    def setUp(self):
        self.user_dima = User.objects.create_user(username="dima", password="password123")
        
        Sale.objects.create(salesman=self.user_dima, sale_amount=Decimal("1000"), payment_type="THB")
        Sale.objects.create(salesman=self.user_dima, sale_amount=Decimal("1500.50"), payment_type="CARD")

    def test_dashboard_total_amount_aggregation(self):
        """Сумма сделок в контексте считается корректно математически"""
        self.client.login(username="dima", password="password123")
        response = self.client.get(reverse("dashboard"))
        
        self.assertEqual(response.context["total_sale_amount"], Decimal("2500.5"))
        self.assertContains(response, "2500.50")


# =====================================================================
# 3. ТЕСТЫ ЖИЗНЕННОГО ЦИКЛА СДЕЛКИ (ПРОСМОТР, ИЗМЕНЕНИЕ, РЕДИРЕКТЫ)
# =====================================================================
class SaleLifecycleTests(TestCase):

    def setUp(self):
        self.user_dima = User.objects.create_user(username="dima", password="password123")
        self.sale = Sale.objects.create(salesman=self.user_dima, sale_amount=Decimal("1000.00"), payment_type="THB")
        
        self.detail_url = reverse("sale_detail", kwargs={"pk": self.sale.pk})
        self.create_url = reverse("sale_create")
        self.update_url = reverse("sale_update", kwargs={"pk": self.sale.pk})

    def test_sale_detail_renders_correct_template(self):
        """Страница деталей сделки отдает 200 OK и использует правильный шаблон"""
        self.client.login(username="dima", password="password123")
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "finance/sale_detail.html")

    def test_sale_create_valid_data(self):
        """Успешное создание сделки через POST форму"""
        self.client.login(username="dima", password="password123")
        response = self.client.post(self.create_url, {"sale_amount": "3000.00", "payment_type": "CARD"})
        
        self.assertEqual(Sale.objects.filter(salesman=self.user_dima).count(), 2)
        self.assertTrue(Sale.objects.filter(sale_amount=Decimal("3000.00")).exists())

    def test_sale_update_redirect_to_dashboard(self):
        """Умный редирект на дашборд при редактировании с флагом ?next=dashboard"""
        self.client.login(username="dima", password="password123")
        response = self.client.post(f"{self.update_url}?next=dashboard", {"sale_amount": "1200.00", "payment_type": "THB"})
        self.assertRedirects(response, reverse("dashboard"))

    def test_sale_update_redirect_to_detail(self):
        """Дефолтный возврат в карточку деталей после сохранения изменений"""
        self.client.login(username="dima", password="password123")
        response = self.client.post(self.update_url, {"sale_amount": "1300.00", "payment_type": "THB"})
        self.assertRedirects(response, self.detail_url)


# =====================================================================
# 4. ТЕСТЫ СИСТЕМЫ КОММЕНТАРИЕВ
# =====================================================================
class SaleCommentTests(TestCase):

    def setUp(self):
        self.user_dima = User.objects.create_user(username="dima", password="password123")
        self.sale = Sale.objects.create(salesman=self.user_dima, sale_amount=Decimal("1000.00"), payment_type="THB")
        self.comment_url = reverse("comment_create", kwargs={"sale_pk": self.sale.pk})

    def test_comment_creation_and_redirect(self):
        """Добавление новой заметки сохраняет её в базу и возвращает на детальный вид"""
        self.client.login(username="dima", password="password123")
        
        response = self.client.post(self.comment_url, {"comment": "Документы отправлены клиенту"})
        
        self.assertRedirects(response, reverse("sale_detail", kwargs={"pk": self.sale.pk}))
        self.assertEqual(Comment.objects.count(), 1)
        
        comment_entry = Comment.objects.first()
        self.assertEqual(comment_entry.comment, "Документы отправлены клиенту")
        self.assertEqual(comment_entry.sale, self.sale)