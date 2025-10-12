# apps/scoring/admin.py
from django.contrib import admin
from .models import CreditScore, PaymentHistory, Transaction

@admin.register(CreditScore)
class CreditScoreAdmin(admin.ModelAdmin):
    list_display = ['demand', 'score_value', 'risk_level', 'ai_recommendation', 'calculated_at']
    list_filter = ['risk_level', 'ai_recommendation', 'calculated_at']
    search_fields = ['demand__id', 'demand__client__username']
    readonly_fields = ['calculated_at']

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['client', 'credit_type', 'amount', 'payment_date', 'status', 'days_late']
    list_filter = ['status', 'credit_type', 'payment_date']
    search_fields = ['client__username', 'client__email']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['client', 'transaction_date', 'transaction_type', 'amount', 'balance_after']
    list_filter = ['transaction_type', 'transaction_date', 'category']
    search_fields = ['client__username']
    date_hierarchy = 'transaction_date'