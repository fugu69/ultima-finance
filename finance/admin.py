from django.contrib import admin
from .models import Sale, Comment, Presentation

# 1. Создаем встроенное отображение для комментариев
class CommentInline(admin.TabularInline): # или admin.StackedInline, если хочешь блоки покрупнее
    model = Comment
    extra = 1  # сколько пустых полей для новых комментов показывать сразу по дефолту

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    # Какие колонки показывать в таблице продаж
    list_display = ["id", "salesman", "sale_amount", "payment_type", "created_at"]
    
    # Фильтры в правой колонке (очень удобно кликать по типам оплаты)
    list_filter = ["payment_type", "created_at"]
    
    # По какому полю кликать, чтобы провалиться внутрь
    list_display_links = ["id", "sale_amount"]

    # Отображаем комментарии на странице каждой продажи в админке
    inlines = [CommentInline]

# Опиционально - создает вкладку с комментами в админке
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    # Колонки для таблицы комментариев
    list_display = ["id", "sale", "author", "comment"]

@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ["id", "presenter", "group_sales_total", "group_identifier", "created_at"]
    list_filter = ["group_identifier", "created_at"]
    list_display_links = ["id", "group_sales_total", "group_identifier"]