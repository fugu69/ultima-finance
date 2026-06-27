from django.conf import settings
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView

from accounts.forms import (
    CustomUserCreationForm,
    StyledAuthenticationForm,
    StyledPasswordResetForm,
    StyledSetPasswordForm,
)


class RedirectAuthenticatedUserMixin:
    """Миксин для защиты гостевых страниц от авторизованных пользователей"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL) 
        return super().dispatch(request, *args, **kwargs)


# 1. Защищенный и стилизованный Логин
@method_decorator(never_cache, name="dispatch")
class SafeLoginView(auth_views.LoginView):
    form_class = StyledAuthenticationForm
    redirect_authenticated_user = True


# 2. Защищенная форма запроса сброса пароля
@method_decorator(never_cache, name="dispatch")
class SafePasswordResetView(
    RedirectAuthenticatedUserMixin, auth_views.PasswordResetView
):
    form_class = StyledPasswordResetForm


# 3. Страница ввода нового пароля (по ссылке из письма)
@method_decorator(never_cache, name="dispatch")
class SafePasswordResetConfirmView(
    RedirectAuthenticatedUserMixin, auth_views.PasswordResetConfirmView
):
    form_class = StyledSetPasswordForm


# 4. Промежуточная страница "Письмо отправлено"
@method_decorator(never_cache, name="dispatch")
class SafePasswordResetDoneView(
    RedirectAuthenticatedUserMixin, auth_views.PasswordResetDoneView
):
    pass


# 5. Финальная страница "Пароль успешно изменен"
@method_decorator(never_cache, name="dispatch")
class SafePasswordResetCompleteView(
    RedirectAuthenticatedUserMixin, auth_views.PasswordResetCompleteView
):
    pass


# 6. Регистрация нового пользователя (теперь тоже защищена миксином)
@method_decorator(never_cache, name="dispatch")
class SignUpView(RedirectAuthenticatedUserMixin, CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
