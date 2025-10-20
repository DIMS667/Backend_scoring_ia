from django.contrib import admin
from .models import CreditDemand, Document, DemandComment

@admin.register(CreditDemand)
class CreditDemandAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'reference', 
        'client', 
        'credit_type', 
        'amount', 
        'status', 
        'created_at',  # CHANGÉ : submitted_at → created_at
        'assigned_agent'
    ]
    
    list_filter = [
        'status', 
        'credit_type', 
        'created_at',  # CHANGÉ : submitted_at → created_at
        'decision_date'
    ]
    
    search_fields = [
        'reference', 
        'client__email', 
        'client__first_name', 
        'client__last_name'
    ]
    
    readonly_fields = [
        'reference', 
        'created_at', 
        'updated_at',  # SUPPRIMÉ : submitted_at
        'monthly_payment'
    ]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'client', 'assigned_agent', 'status')
        }),
        ('Détails du crédit', {
            'fields': ('credit_type', 'amount', 'duration_months', 'purpose')
        }),
        ('Décision', {
            'fields': ('decision_date', 'decision_comment', 'approved_amount', 'approved_duration', 'interest_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = ['client', 'assigned_agent']
    date_hierarchy = 'created_at'  # CHANGÉ : submitted_at → created_at
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'assigned_agent')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'demand',
        'document_type',
        'original_filename',
        'file_size',
        'uploaded_at'
    ]
    
    list_filter = [
        'document_type',
        'uploaded_at'
    ]
    
    search_fields = [
        'demand__reference',
        'original_filename'
    ]
    
    readonly_fields = [
        'file_size',
        'uploaded_at'
    ]
    
    raw_id_fields = ['demand']


@admin.register(DemandComment)
class DemandCommentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'demand',
        'author',
        'is_internal',
        'created_at'
    ]
    
    list_filter = [
        'is_internal',
        'created_at'
    ]
    
    search_fields = [
        'demand__reference',
        'author__email',
        'content'
    ]
    
    readonly_fields = [
        'created_at'
    ]
    
    raw_id_fields = ['demand', 'author']