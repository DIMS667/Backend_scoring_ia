# apps/reports/admin.py
from django.contrib import admin
from .models import Report, Dashboard

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'format', 'period_start', 'period_end', 'generated_at']
    list_filter = ['report_type', 'format', 'generated_at']
    search_fields = ['name']
    readonly_fields = ['generated_at', 'file_size']
    date_hierarchy = 'generated_at'

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['user__username', 'name']
