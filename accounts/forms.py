from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.forms import AuthenticationForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = UserCreationForm.Meta.fields + (  # username by default
            "email",
            "actual_start_date",
            "official_hire_date",
            "base_salary",
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields  # __all__ by default

class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': (
                    'w-full px-5 py-3 bg-white border border-gray-300 rounded-full text-sm text-gray-900 '
                    'placeholder-gray-400 focus:outline-none focus:border-gray-950 focus:ring-1 focus:ring-gray-950 '
                    'transition duration-150 ease-in-out'
                ),
                'placeholder': f'Введите {field.label.lower()}'
            })
