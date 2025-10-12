from rest_framework import serializers
from .models import CreditScore, PaymentHistory, Transaction

class CreditScoreSerializer(serializers.ModelSerializer):
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    ai_recommendation_display = serializers.CharField(source='get_ai_recommendation_display', read_only=True)
    
    class Meta:
        model = CreditScore
        fields = '__all__'
        read_only_fields = ['calculated_at']


class PaymentHistorySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentHistory
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'