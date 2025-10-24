from rest_framework import serializers
from core.validators import validate_amount, validate_age
from core.utils import format_currency
from .models import CreditDemand, Document, DemandComment
from apps.accounts.serializers import UserSerializer

class DocumentSerializer(serializers.ModelSerializer):
    file_size_display = serializers.SerializerMethodField()
    
    def get_file_size_display(self, obj):
        """Formater la taille du fichier"""
        return f"{obj.file_size / 1024:.1f} KB"
    
    class Meta:
        model = Document
        fields = ['id', 'document_type', 'file', 'original_filename', 'file_size', 'file_size_display', 'uploaded_at']
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
    
    # Ajouter le score - VISIBLE SEULEMENT POUR LES AGENTS
    score_value = serializers.SerializerMethodField()
    
    # Formatage des montants
    amount_display = serializers.SerializerMethodField()
    approved_amount_display = serializers.SerializerMethodField()
    
    def get_score_value(self, obj):
        """Récupérer le score s'il existe - SEULEMENT pour les agents - VERSION CORRIGÉE"""
        request = self.context.get('request')
        if request and request.user.role == 'AGENT':
            try:
                # CORRECTION : Utiliser hasattr pour vérifier l'existence de la relation
                if hasattr(obj, 'score') and obj.score:
                    return obj.score.score_value
                else:
                    # Essayer de récupérer le score depuis la base
                    from apps.scoring.models import CreditScore
                    try:
                        score = CreditScore.objects.get(demand=obj)
                        return score.score_value
                    except CreditScore.DoesNotExist:
                        return None
            except Exception as e:
                print(f"Erreur récupération score pour demande {obj.id}: {str(e)}")
                return None
        return None  # Clients ne voient JAMAIS le score
    
    def get_amount_display(self, obj):
        """Formater le montant"""
        return format_currency(float(obj.amount))
    
    def get_approved_amount_display(self, obj):
        """Formater le montant approuvé"""
        if obj.approved_amount:
            return format_currency(float(obj.approved_amount))
        return None
    
    def validate_amount(self, value):
        """Valider le montant avec le validateur du core"""
        validate_amount(value)
        return value
    
    class Meta:
        model = CreditDemand
        fields = '__all__'
        read_only_fields = ['id', 'client', 'assigned_agent', 'created_at', 'updated_at', 'decision_date']


class CreditDemandListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    credit_type_display = serializers.CharField(source='get_credit_type_display', read_only=True)
    amount_display = serializers.SerializerMethodField()
    
    # Ajouter le score dans la liste - SEULEMENT pour les agents
    score = serializers.SerializerMethodField()
    
    def get_score(self, obj):
        """Récupérer le score s'il existe - SEULEMENT pour les agents - VERSION CORRIGÉE"""
        request = self.context.get('request')
        if request and request.user.role == 'AGENT':
            try:
                # CORRECTION : Utiliser hasattr pour vérifier l'existence de la relation
                if hasattr(obj, 'score') and obj.score:
                    return obj.score.score_value
                else:
                    # Essayer de récupérer le score depuis la base
                    from apps.scoring.models import CreditScore
                    try:
                        score = CreditScore.objects.get(demand=obj)
                        return score.score_value
                    except CreditScore.DoesNotExist:
                        return None
            except Exception as e:
                print(f"Erreur récupération score pour demande {obj.id}: {str(e)}")
                return None
        return None
    
    def get_amount_display(self, obj):
        """Formater le montant"""
        return format_currency(float(obj.amount))
    
    class Meta:
        model = CreditDemand
        fields = [
            'id', 
            'client_name', 
            'credit_type', 
            'credit_type_display', 
            'amount', 
            'amount_display', 
            'duration_months', 
            'status', 
            'status_display', 
            'score', 
            'created_at'  # CHANGÉ : submitted_at → created_at
        ]


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()
    
    class Meta:
        model = Document
        fields = ['document_type', 'file']
    
    def validate_file(self, value):
        """Valider le fichier"""
        # Limite 5MB
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 5MB")
        
        # Types autorisés
        allowed_types = [
            'image/jpeg',
            'image/jpg',
            'image/png',
            'application/pdf',
        ]
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Type de fichier non autorisé (JPG, PNG, PDF uniquement)")
        
        return value
    
    def create(self, validated_data):
        validated_data['original_filename'] = validated_data['file'].name
        validated_data['file_size'] = validated_data['file'].size
        return super().create(validated_data)