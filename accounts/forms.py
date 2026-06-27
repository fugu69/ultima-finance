from django import forms
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "class": (
                        "w-full px-5 py-3 bg-white border border-gray-300 rounded-full text-sm text-gray-900 "
                        "placeholder-gray-400 focus:outline-none focus:border-gray-950 focus:ring-1 focus:ring-gray-950 "
                        "transition duration-150 ease-in-out"
                    ),
                    "placeholder": "example@domain.com",
                }
            )


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "class": (
                        "w-full px-5 py-3 bg-white border border-gray-300 rounded-full text-sm text-gray-900 "
                        "placeholder-gray-400 focus:outline-none focus:border-gray-950 focus:ring-1 focus:ring-gray-950 "
                        "transition duration-150 ease-in-out"
                    ),
                    "placeholder": f"Введите {field.label.lower()}",
                }
            )


class CustomUserCreationForm(UserCreationForm):
    INPUT_STYLE = (
        'w-full px-5 py-3 bg-white border border-gray-300 rounded-full text-sm text-gray-900 '
        'placeholder-gray-400 focus:outline-none focus:border-gray-950 focus:ring-1 focus:ring-gray-950 '
        'transition duration-150 ease-in-out'
    )

    # Явно переопределяем виджеты полей, чтобы Django не подсовывал дефолтные
    username = forms.CharField(
        label="Имя пользователя (Username)",
        widget=forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Введите имя пользователя'})
    )
    
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={'class': INPUT_STYLE, 'placeholder': 'example@mail.com'})
    )
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Придумайте пароль'})
    )
    
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Повторите пароль'})
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Очищаем громоздкие стандартные подсказки Django под паролями
        for field_name in self.fields:
            self.fields[field_name].help_text = ""


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields  # __all__ by default


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "class": (
                        "w-full px-5 py-3 bg-white border border-gray-300 rounded-full text-sm text-gray-900 "
                        "placeholder-gray-400 focus:outline-none focus:border-gray-950 focus:ring-1 focus:ring-gray-950 "
                        "transition duration-150 ease-in-out"
                    ),
                    "placeholder": f"Введите {field.label.lower()}",
                }
            )
