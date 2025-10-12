from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from core.permissions import IsAgent, IsOwnerOrAgent
from core.exceptions import InvalidDemandStatusException
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
            return CreditDemand.objects.filter(client=user)
        # Agent voit toutes les demandes
        return CreditDemand.objects.select_related('client', 'assigned_agent').prefetch_related('documents', 'comments')
    
    def perform_create(self, serializer):
        serializer.save(client=self.request.user)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Soumettre une demande"""
        demand = self.get_object()
        
        if demand.status != 'DRAFT':
            return Response(
                {'error': 'Seules les demandes en brouillon peuvent être soumises'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        demand.status = 'SUBMITTED'
        demand.submitted_at = timezone.now()
        demand.save()
        
        # Déclencher le scoring automatique
        from apps.scoring.services import calculate_score
        calculate_score(demand)
        
        serializer = self.get_serializer(demand)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approuver une demande (Agent uniquement)"""
        if request.user.role != 'AGENT':
            return Response(
                {'error': 'Seuls les agents peuvent approuver'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        demand = self.get_object()
        
        demand.status = 'APPROVED'
        demand.decision_date = timezone.now()
        demand.assigned_agent = request.user
        demand.decision_comment = request.data.get('comment', '')
        demand.approved_amount = request.data.get('approved_amount', demand.amount)
        demand.approved_duration = request.data.get('approved_duration', demand.duration_months)
        demand.interest_rate = request.data.get('interest_rate', 8.5)
        demand.save()
        
        serializer = self.get_serializer(demand)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejeter une demande (Agent uniquement)"""
        if request.user.role != 'AGENT':
            return Response(
                {'error': 'Seuls les agents peuvent rejeter'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        demand = self.get_object()
        
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
        
        serializer = self.get_serializer(demand)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Upload un document pour la demande"""
        demand = self.get_object()
        
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(demand=demand)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'CLIENT':
            return Document.objects.filter(demand__client=user)
        return Document.objects.all()