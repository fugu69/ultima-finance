from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Sale, Comment, Presentation

User = get_user_model()


# =====================================================================
# 1. ТЕСТЫ ДОСТУПА, СТАТУС-КОДОВ И ВЕНТИЛЯЦИИ ВКЛАДОК ДАШБОРДА
# =====================================================================
class DashboardAccessAndTemplateTests(TestCase):

    def setUp(self):
        self.user_biba = User.objects.create_user(username="biba", password="password123")
        self.user_boba = User.objects.create_user(username="boba", password="password123")
        
        # Создаем тестовые продажи
        Sale.objects.create(salesman=self.user_biba, sale_amount=Decimal("1000.00"), payment_type="THB")
        Sale.objects.create(salesman=self.user_boba, sale_amount=Decimal("5000.00"), payment_type="THB")
        
        # Создаем тестовые презентации
        Presentation.objects.create(presenter=self.user_biba, group_sales_total=Decimal("3000.00"), group_identifier="Group A")
        Presentation.objects.create(presenter=self.user_boba, group_sales_total=Decimal("7000.00"), group_identifier="Group B")
        
        self.dashboard_url = reverse("dashboard")

    def test_dashboard_anonymous_redirect(self):
        """Анонимный пользователь должен перенаправляться на логин (302)"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_renders_correct_template_and_status(self):
        """Авторизованный юзер получает 200 OK и правильный набор шаблонов"""
        self.client.login(username="biba", password="password123")
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "finance/home.html")

    def test_dashboard_default_tab_is_sales(self):
        """По умолчанию (без параметров) открывается вкладка продаж с изоляцией данных"""
        self.client.login(username="biba", password="password123")
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.context["active_tab"], "sales")
        # Должна быть только продажа Бибы
        self.assertEqual(len(response.context["items"]), 1)
        self.assertIsInstance(response.context["items"][0], Sale)
        self.assertContains(response, "1000.00")
        self.assertNotContains(response, "5000.00")

    def test_dashboard_switching_to_presentations_tab(self):
        """При передаче ?tab=presentations дашборд переключается на презентации текущего юзера"""
        self.client.login(username="biba", password="password123")
        response = self.client.get(f"{self.dashboard_url}?tab=presentations")
        
        self.assertEqual(response.context["active_tab"], "presentations")
        # Должна быть только презентация Бибы
        self.assertEqual(len(response.context["items"]), 1)
        self.assertIsInstance(response.context["items"][0], Presentation)
        self.assertContains(response, "Group A")
        self.assertNotContains(response, "Group B")


# =====================================================================
# 2. ТЕСТЫ БИЗНЕС-ЛОГИКИ И АГРЕГАЦИИ СУММ
# =====================================================================
class DashboardAggregationTests(TestCase):

    def setUp(self):
        self.user_biba = User.objects.create_user(username="biba", password="password123")
        
        # Насыпаем продаж
        Sale.objects.create(salesman=self.user_biba, sale_amount=Decimal("1000.00"), payment_type="THB")
        Sale.objects.create(salesman=self.user_biba, sale_amount=Decimal("1500.50"), payment_type="CARD")
        
        # Насыпаем презентаций
        Presentation.objects.create(presenter=self.user_biba, group_sales_total=Decimal("2000.00"), group_identifier="A")
        Presentation.objects.create(presenter=self.user_biba, group_sales_total=Decimal("4500.25"), group_identifier="B")

        self.dashboard_url = reverse("dashboard")

    def test_sales_aggregation_is_correct(self):
        """Сумма на вкладке продаж считается корректно математически"""
        self.client.login(username="biba", password="password123")
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.context["total_amount"], Decimal("2500.50"))

    def test_presentations_aggregation_is_correct(self):
        """Сумма на вкладке презентаций считается корректно математически"""
        self.client.login(username="biba", password="password123")
        response = self.client.get(f"{self.dashboard_url}?tab=presentations")
        
        self.assertEqual(response.context["total_amount"], Decimal("6500.25"))


# =====================================================================
# 3. ТЕСТЫ ЖИЗНЕННОГО ЦИКЛА СДЕЛКИ (ПРОСМОТР, ИЗМЕНЕНИЕ, РЕДИРЕКТЫ)
# =====================================================================
class SaleLifecycleTests(TestCase):

    def setUp(self):
        self.user_biba = User.objects.create_user(username="biba", password="password123")
        self.user_boba = User.objects.create_user(username="boba", password="password123")
        self.sale = Sale.objects.create(salesman=self.user_biba, sale_amount=Decimal("1000.00"), payment_type="THB")
        
        self.detail_url = reverse("sale_detail", kwargs={"pk": self.sale.pk})
        self.create_url = reverse("sale_create")
        self.update_url = reverse("sale_update", kwargs={"pk": self.sale.pk})
        self.delete_url = reverse("sale_delete", kwargs={"pk": self.sale.pk})

    def test_sale_detail_renders_correct_template(self):
        """Страница деталей сделки отдает 200 OK владельцу"""
        self.client.login(username="biba", password="password123")
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_sale_detail_isolation(self):
        """Чужой менеджер не может смотреть детали чужой продажи (403 Forbidden)"""
        self.client.login(username="boba", password="password123")
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 403)

    def test_sale_create_valid_data_and_direct_redirect(self):
        """После успешного создания продажи редиректит СРАЗУ на дашборд"""
        self.client.login(username="biba", password="password123")
        response = self.client.post(self.create_url, {"sale_amount": "3000.00", "payment_type": "CARD"})
        
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(Sale.objects.filter(salesman=self.user_biba).count(), 2)

    def test_sale_update_redirect_to_dashboard_with_param(self):
        """Редирект на дашборд при изменении с флагом ?next=dashboard"""
        self.client.login(username="biba", password="password123")
        response = self.client.post(f"{self.update_url}?next=dashboard", {"sale_amount": "1200.00", "payment_type": "THB"})
        self.assertRedirects(response, reverse("dashboard"))

    def test_sale_delete_flow(self):
        """Удаление продажи перенаправляет на дашборд и стирает запись"""
        self.client.login(username="biba", password="password123")
        response = self.client.post(self.delete_url)
        
        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(Sale.objects.filter(pk=self.sale.pk).exists())


# =====================================================================
# 4. ТЕСТЫ ЖИЗНЕННОГО ЦИКЛА ПРЕЗЕНТАЦИЙ (ГЛАВНЫЙ ИСПРАВЛЕННЫЙ БАГ)
# =====================================================================
class PresentationLifecycleTests(TestCase):

    def setUp(self):
        self.user_biba = User.objects.create_user(username="biba", password="password123")
        self.user_boba = User.objects.create_user(username="boba", password="password123")
        self.presentation = Presentation.objects.create(
            presenter=self.user_biba, 
            group_sales_total=Decimal("4000.00"), 
            group_identifier="Batch 1"
        )
        
        self.create_url = reverse("presentation_create")
        self.detail_url = reverse("presentation_detail", kwargs={"pk": self.presentation.pk})
        self.update_url = reverse("presentation_update", kwargs={"pk": self.presentation.pk})
        self.delete_url = reverse("presentation_delete", kwargs={"pk": self.presentation.pk})

    def test_presentation_create_redirects_to_presentations_tab(self):
        """Создание презентации редиректит СРАЗУ на дашборд со вкладкой презентаций"""
        self.client.login(username="biba", password="password123")
        response = self.client.post(self.create_url, {
            "group_sales_total": "5500.00",
            "group_identifier": "Batch 2"
        })
        
        # Проверяем прямой редирект на нужную вкладку дашборда
        expected_url = f"{reverse('dashboard')}?tab=presentations"
        self.assertRedirects(response, expected_url)
        
        new_presentation = Presentation.objects.get(group_identifier="Batch 2")
        self.assertEqual(new_presentation.presenter, self.user_biba)

    def test_presentation_update_with_next_param(self):
        """Редактирование презентации с ?next=dashboard возвращает на дашборд + вкладку презентаций"""
        self.client.login(username="biba", password="password123")
        response = self.client.post(
            f"{self.update_url}?next=dashboard", 
            {"group_sales_total": "9000.00", "group_identifier": "Updated Batch"}
        )
        
        expected_url = f"{reverse('dashboard')}?tab=presentations"
        self.assertRedirects(response, expected_url)

    def test_presentation_delete_redirects_to_presentations_tab(self):
        """Удаление презентации возвращает менеджера строго на вкладку презентаций дашборда"""
        self.client.login(username="biba", password="password123")
        response = self.client.post(self.delete_url)
        
        expected_url = f"{reverse('dashboard')}?tab=presentations"
        self.assertRedirects(response, expected_url)
        self.assertFalse(Presentation.objects.filter(pk=self.presentation.pk).exists())

    def test_presentation_security_isolation(self):
        """Чужой юзер поймает 403 ошибку при попытке изменить или удалить чужую презентацию"""
        self.client.login(username="boba", password="password123")
        
        # Попытка зайти в детали
        response_detail = self.client.get(self.detail_url)
        self.assertEqual(response_detail.status_code, 403)
        
        # Попытка отредактировать
        response_update = self.client.post(self.update_url, {"group_sales_total": "10.00"})
        self.assertEqual(response_update.status_code, 403)


# =====================================================================
# 5. ТЕСТЫ СИСТЕМЫ КОММЕНТАРИЕВ И ОПТИМИЗАЦИИ ЛЕНДИНГА
# =====================================================================
class SaleCommentAndLandingTests(TestCase):

    def setUp(self):
        self.user_biba = User.objects.create_user(username="biba", password="password123")
        self.sale = Sale.objects.create(salesman=self.user_biba, sale_amount=Decimal("1000.00"), payment_type="THB")
        self.comment_url = reverse("comment_create", kwargs={"sale_pk": self.sale.pk})

    def test_comment_creation_and_redirect(self):
        """Добавление новой заметки сохраняет её в базу и возвращает на детальный вид"""
        self.client.login(username="biba", password="password123")
        response = self.client.post(self.comment_url, {"comment": "Документы отправлены клиенту"})
        
        self.assertRedirects(response, reverse("sale_detail", kwargs={"pk": self.sale.pk}))
        self.assertEqual(Comment.objects.count(), 1)

    def test_landing_page_redirects_authenticated_user(self):
        """Если авторизованный пользователь забрел на лендинг '', его отправляет на 'dashboard'"""
        self.client.login(username="biba", password="password123")
        response = self.client.get(reverse("home"))
        
        self.assertRedirects(response, reverse("dashboard"))