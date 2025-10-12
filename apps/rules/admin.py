# apps/rules/admin.py
from django.contrib import admin
from .models import BusinessRule, RuleEvaluation, CreditProduct

@admin.register(BusinessRule)
class BusinessRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'credit_type', 'is_active', 'priority']
    list_filter = ['rule_type', 'is_active', 'credit_type']
    search_fields = ['name', 'description']
    ordering = ['-priority']

@admin.register(RuleEvaluation)
class RuleEvaluationAdmin(admin.ModelAdmin):
    list_display = ['demand', 'rule', 'passed', 'evaluated_at']
    list_filter = ['passed', 'evaluated_at']
    search_fields = ['demand__id', 'rule__name']

@admin.register(CreditProduct)
class CreditProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'credit_type', 'min_amount', 'max_amount', 'base_interest_rate', 'is_active']
    list_filter = ['credit_type', 'is_active']
    search_fields = ['name', 'description']