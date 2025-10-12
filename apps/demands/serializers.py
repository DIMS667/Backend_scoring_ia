from rest_framework import serializers
from .models import CreditDemand, Document, DemandComment
from apps.accounts.serializers import UserSerializer

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'document_type', 'file', 'original_filename', 'file_size', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class DemandCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = DemandComment
        fields = ['id', 'author', 'content', 'is_internal', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class CreditDemandSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    assigned_agent = UserSerializer(read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    comments = DemandCommentSerializer(many=True, read_only=True)
    monthly_payment = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    credit_type_display = serializers.CharField(source='get_credit_type_display', read_only=True)
    
    class Meta:
        model = CreditDemand
        fields = '__all__'
        read_only_fields = ['id', 'client', 'assigned_agent', 'created_at', 'updated_at', 'submitted_at', 'decision_date']


class CreditDemandListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    credit_type_display = serializers.CharField(source='get_credit_type_display', read_only=True)
    
    class Meta:
        model = CreditDemand
        fields = ['id', 'client_name', 'credit_type', 'credit_type_display', 'amount', 'duration_months', 'status', 'status_display', 'created_at', 'submitted_at']


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()
    
    class Meta:
        model = Document
        fields = ['document_type', 'file']
    
    def validate_file(self, value):
        # Limite 5MB
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 5MB")
        return value
    
    def create(self, validated_data):
        validated_data['original_filename'] = validated_data['file'].name
        validated_data['file_size'] = validated_data['file'].size
        return super().create(validated_data)