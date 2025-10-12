# serializers.py
from rest_framework import serializers
from .models import BusinessRule, RuleEvaluation, CreditProduct

class BusinessRuleSerializer(serializers.ModelSerializer):
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    
    class Meta:
        model = BusinessRule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by']

class RuleEvaluationSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    
    class Meta:
        model = RuleEvaluation
        fields = '__all__'
        read_only_fields = ['evaluated_at']

class CreditProductSerializer(serializers.ModelSerializer):
    credit_type_display = serializers.CharField(source='get_credit_type_display', read_only=True)
    
    class Meta:
        model = CreditProduct
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']