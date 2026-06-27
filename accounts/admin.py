from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = ('document_number', 'first_name', 'last_name', 'role', 'gender', 'socioeconomic_stratum', 'is_staff', 'is_active')
    list_filter = ('role', 'gender', 'socioeconomic_stratum', 'is_staff', 'is_active', 'is_superuser')

    fieldsets = (
        ('Credenciales', {
            'fields': ('document_number', 'password')
        }),
        ('Información personal', {
            'fields': ('first_name', 'last_name', 'email', 'gender', 'socioeconomic_stratum', 'role')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas importantes', {
            'fields': ('last_login',)
        }),
    )

    add_fieldsets = (
        ('Crear usuario', {
            'classes': ('wide',),
            'fields': ('document_number', 'first_name', 'last_name', 'email', 'gender', 'socioeconomic_stratum', 'role', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    search_fields = ('document_number', 'first_name', 'last_name', 'email')
    ordering = ('document_number',)
