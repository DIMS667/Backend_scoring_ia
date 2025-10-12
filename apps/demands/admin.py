# apps/demands/admin.py
from django.contrib import admin
from .models import CreditDemand, Document, DemandComment

@admin.register(CreditDemand)
class CreditDemandAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'credit_type', 'amount', 'status', 'submitted_at']
    list_filter = ['status', 'credit_type', 'created_at']
    search_fields = ['client__username', 'client__email']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at', 'decision_date']
    date_hierarchy = 'created_at'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['demand', 'document_type', 'original_filename', 'file_size', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['demand__id', 'original_filename']

@admin.register(DemandComment)
class DemandCommentAdmin(admin.ModelAdmin):
    list_display = ['demand', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['demand__id', 'author__username', 'content']