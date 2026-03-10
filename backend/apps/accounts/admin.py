from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

# Настройка админ-панели для User
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Отображаемые поля
    list_display = ['username', 'email','first_name', 'last_name', 'is_active', 'created_at']
    # Поля, по которым доступна фильтрация
    list_filter = ['is_active','is_staff','is_superuser', 'created_at']
    # Поля, по которым доступен поиск
    search_fields = ['username', 'email', 'first_name', 'last_name']
    # Поле, по которому производится сортировка по умолчанию
    ordering = ['-created_at',]

    # Разбиение полей на группы при редактировании
    fieldsets = [
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name','avatar','bio')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined','created_at', 'updated_at')}),
    ]

    # Форма для создания нового пользователя через admin-панель
    add_fieldsets = [
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2')
        }),
    ]

    # Поля, недоступные для редактирования
    readonly_fields = ['created_at', 'updated_at']