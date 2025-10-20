from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from core.permissions import IsAgent, IsOwnerOrAgent
from core.exceptions import InvalidDemandStatusException, DocumentUploadException
from .models import CreditDemand, Document, DemandComment
from .serializers import (
    CreditDemandSerializer, 
    CreditDemandListSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
    DemandCommentSerializer
)

class CreditDemandViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CreditDemandListSerializer
        return CreditDemandSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'CLIENT':
            # Client voit uniquement ses demandes
            return CreditDemand.objects.filter(client=user).select_related('client', 'assigned_agent', 'score').prefetch_related('documents', 'comments')
        # Agent voit toutes les demandes
        return CreditDemand.objects.select_related('client', 'assigned_agent', 'score').prefetch_related('documents', 'comments')
    
    def get_permissions(self):
        """Permissions différentes selon l'action"""
        if self.action in ['approve', 'reject']:
            return [IsAgent()]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return [IsOwnerOrAgent()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """
        NOUVEAU WORKFLOW : 
        - Création directe avec statut PENDING_ANALYST
        - Score calculé automatiquement en arrière-plan via signals
        - Plus de statut DRAFT/SUBMIT
        """
        # Sauvegarder avec le statut PENDING_ANALYST par défaut
        demand = serializer.save(client=self.request.user)
        
        # Le calcul du score se fait automatiquement via le signal post_save
        # Voir apps/demands/signals.py
    
    # SUPPRIMER la méthode submit() - plus nécessaire
    
    @action(detail=True, methods=['post'], permission_classes=[IsAgent])
    def approve(self, request, pk=None):
        """Approuver une demande (Agent uniquement)"""
        demand = self.get_object()
        
        # Vérifier que la demande peut être approuvée
        if demand.status not in ['PENDING_ANALYST']:
            return Response(
                {'error': 'Cette demande ne peut plus être modifiée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        demand.status = 'APPROVED'
        demand.decision_date = timezone.now()
        demand.assigned_agent = request.user
        demand.decision_comment = request.data.get('comment', '')
        demand.approved_amount = request.data.get('approved_amount', demand.amount)
        demand.approved_duration = request.data.get('approved_duration', demand.duration_months)
        demand.interest_rate = request.data.get('interest_rate', 8.5)
        demand.save()
        
        # Envoyer notification
        from .services import notify_demand_decision
        notify_demand_decision(demand, approved=True)
        
        serializer = self.get_serializer(demand)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAgent])
    def reject(self, request, pk=None):
        """Rejeter une demande (Agent uniquement)"""
        demand = self.get_object()
        
        # Vérifier que la demande peut être rejetée
        if demand.status not in ['PENDING_ANALYST']:
            return Response(
                {'error': 'Cette demande ne peut plus être modifiée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = request.data.get('comment')
        if not comment:
            return Response(
                {'error': 'Un commentaire est obligatoire pour un rejet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        demand.status = 'REJECTED'
        demand.decision_date = timezone.now()
        demand.assigned_agent = request.user
        demand.decision_comment = comment
        demand.save()
        
        # Envoyer notification
        from .services import notify_demand_decision
        notify_demand_decision(demand, approved=False)
        
        serializer = self.get_serializer(demand)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Upload un document pour la demande"""
        demand = self.get_object()
        
        # Les documents peuvent être uploadés uniquement si la demande est en attente
        if demand.status not in ['PENDING_ANALYST']:
            return Response(
                {'error': 'Impossible d\'ajouter des documents à cette demande'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(demand=demand)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                raise DocumentUploadException(str(e))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Ajouter un commentaire"""
        demand = self.get_object()
        
        serializer = DemandCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(demand=demand, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annuler une demande (Client uniquement)"""
        demand = self.get_object()
        
        # Vérifier les permissions
        if request.user != demand.client:
            return Response(
                {'error': 'Seul le client peut annuler sa demande'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que la demande peut être annulée
        if demand.status not in ['PENDING_ANALYST']:
            return Response(
                {'error': 'Cette demande ne peut plus être annulée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        demand.status = 'CANCELLED'
        demand.save()
        
        serializer = self.get_serializer(demand)
        return Response(serializer.data)


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'CLIENT':
            return Document.objects.filter(demand__client=user)
        return Document.objects.all()