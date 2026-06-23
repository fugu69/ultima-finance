from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Creation form
    add_form = CustomUserCreationForm

    # Change form
    form = CustomUserChangeForm
    model = CustomUser

    # 1. Поля, которые мы увидим в общей таблице всех пользователей
    list_display = [
        'username',
        'email',
        'base_salary',
        'actual_start_date',
        'official_hire_date',
    ]

    # 2. Добавляем новые поля на страницу РЕДАКТИРОВАНИЯ пользователя
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('base_salary','actual_start_date','official_hire_date')}),
    )

    # 3. Добавляем новые поля на страницу СОЗДАНИЯ нового пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('base_salary','actual_start_date','official_hire_date')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)