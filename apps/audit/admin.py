# apps/audit/admin.py
from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'entity_type', 'entity_id', 'timestamp']
    list_filter = ['action', 'entity_type', 'timestamp']
    search_fields = ['user__username', 'description', 'entity_type']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'