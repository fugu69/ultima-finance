from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AuthAndSignupFlowTests(TestCase):

    def setUp(self):
        # Создаем тестового пользователя для проверок редиректов авторизованной зоны
        self.username = "testuser"
        self.email = "test@example.com"
        self.password = "SecurePass123!"
        self.user = User.objects.create_user(
            username=self.username, email=self.email, password=self.password
        )

    # ==========================================
    # 1. ТЕСТЫ РЕГИСТРАЦИИ (GUEST / ANONYMOUS)
    # ==========================================

    def test_signup_page_accessible_by_anonymous_user(self):
        """Анонимный пользователь может открыть страницу регистрации."""
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")

    def test_signup_form_success_with_minimal_fields(self):
        """Регистрация успешна только с username, email и паролями."""
        # Удаляем старого юзера, чтобы не было конфликта уникальности
        User.objects.all().delete()

        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "NewSecurePass123!",
                "password2": "NewSecurePass123!",
            },
        )
        # Ожидаем редирект на страницу логина после успешной регистрации
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))

        # Проверяем, что в БД создана запись и данные верны
        self.assertEqual(User.objects.count(), 1)
        new_user = User.objects.first()
        self.assertEqual(new_user.username, "newuser")
        self.assertEqual(new_user.email, "new@example.com")

    # ==========================================
    # 2. ТЕСТЫ БЕЗОПАСНОСТИ (AUTHENTICATED USER)
    # ==========================================

    def test_authenticated_user_redirected_from_signup(self):
        """Авторизованного пользователя выкидывает со страницы регистрации на дашборд."""
        self.client.login(username=self.username, password=self.password)

        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))

    def test_authenticated_user_redirected_from_login(self):
        """Авторизованного пользователя выкидывает со страницы входа."""
        self.client.login(username=self.username, password=self.password)

        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))

    def test_authenticated_user_redirected_from_password_reset(self):
        """Авторизованного пользователя выкидывает со страниц сброса пароля."""
        self.client.login(username=self.username, password=self.password)

        urls_to_test = [
            "password_reset",
            "password_reset_done",
            "password_reset_complete",
        ]

        for url_name in urls_to_test:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 302)
                self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))

    # ==========================================
    # 3. ТЕСТЫ ИНТЕГРАЦИИ ПОЧТЫ (EMAIL FLOW)
    # ==========================================

    def test_password_reset_sends_email_functional(self):
        """Отправка формы восстановления пароля генерирует реальное письмо в mail.outbox."""
        # Дёргаем реальный POST-запрос формы сброса пароля для нашего юзера
        response = self.client.post(
            reverse("password_reset"), data={"email": self.email}
        )

        # После отправки Django должен перенаправить на страницу password_reset_done
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("password_reset_done"))

        # Проверяем, что в виртуальном почтовом ящике появилось ровно 1 письмо
        self.assertEqual(len(mail.outbox), 1)

        # Вытаскиваем письмо и сверяем его внутренности
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, [self.email])

        # Сверяем точную тему письма из твоего лога
        self.assertEqual(sent_email.subject, "Password reset on testserver")

        # Проверяем базовую часть пути ссылки из твоего конфигуратора урлов
        self.assertIn("/accounts/reset/", sent_email.body)

    # ==========================================
    # 4. ТЕСТЫ КОНТРОЛЯ КЭШИРОВАНИЯ (NEVER_CACHE)
    # ==========================================

    def test_auth_pages_have_cache_control_headers(self):
        """Страницы авторизации содержат заголовки, запрещающие кэширование браузером."""
        urls_to_test = [
            "login",
            "signup",
            "password_reset",
            "password_reset_done",
            "password_reset_complete",
        ]

        for url_name in urls_to_test:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))

                # Проверяем основной современный HTTP/1.1 стандарт управления кэшем
                cache_control = response.headers.get("Cache-Control", "")
                self.assertIn("no-cache", cache_control)
                self.assertIn("no-store", cache_control)
                self.assertIn("must-revalidate", cache_control)
