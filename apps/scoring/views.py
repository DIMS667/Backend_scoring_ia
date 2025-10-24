# ============================================
# apps/scoring/views.py - CORRIGÉ POUR RÉCUPÉRER LE BON SCORE
# ============================================

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Import core
from core.permissions import IsAgent
from core.exceptions import InsufficientScoreException

from .models import CreditScore, PaymentHistory, Transaction
from .serializers import CreditScoreSerializer, PaymentHistorySerializer, TransactionSerializer
from .services import calculate_score
from apps.demands.models import CreditDemand


class CreditScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CreditScore.objects.all()
    serializer_class = CreditScoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Filtrer par demand_id si fourni (NOUVEAU)
        demand_id = self.request.query_params.get('demand_id')
        if demand_id:
            if user.role == 'CLIENT':
                return CreditScore.objects.filter(demand_id=demand_id, demand__client=user)
            else:
                return CreditScore.objects.filter(demand_id=demand_id)
        
        # Filtrage par rôle
        if user.role == 'CLIENT':
            return CreditScore.objects.filter(demand__client=user)
        return CreditScore.objects.all()
    
    @action(detail=False, methods=['get'])
    def by_demand(self, request):
        """NOUVEAU : Récupérer le score d'une demande spécifique"""
        demand_id = request.query_params.get('demand_id')
        
        if not demand_id:
            return Response(
                {'error': 'demand_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Vérifier que la demande existe et que l'utilisateur peut la voir
            demand = CreditDemand.objects.get(id=demand_id)
            
            if request.user.role == 'CLIENT' and demand.client != request.user:
                return Response(
                    {'error': 'Accès non autorisé'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Récupérer le score
            try:
                score = CreditScore.objects.get(demand=demand)
                serializer = self.get_serializer(score)
                return Response(serializer.data)
            except CreditScore.DoesNotExist:
                return Response(
                    {'error': 'Score non calculé pour cette demande'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except CreditDemand.DoesNotExist:
            return Response(
                {'error': 'Demande non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAgent])
    def calculate(self, request):
        """Calculer le score pour une demande spécifique"""
        demand_id = request.data.get('demand_id')
        
        if not demand_id:
            return Response(
                {'error': 'demand_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            demand = CreditDemand.objects.get(id=demand_id)
            score = calculate_score(demand)
            serializer = self.get_serializer(score)
            return Response(serializer.data)
            
        except CreditDemand.DoesNotExist:
            return Response(
                {'error': 'Demande non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class PaymentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentHistory.objects.all()
    serializer_class = PaymentHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'CLIENT':
            return PaymentHistory.objects.filter(client=user)
        
        client_id = self.request.query_params.get('client_id')
        if client_id:
            return PaymentHistory.objects.filter(client_id=client_id)
        
        return PaymentHistory.objects.none()


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'CLIENT':
            return Transaction.objects.filter(client=user)
        
        client_id = self.request.query_params.get('client_id')
        if client_id:
            return Transaction.objects.filter(client_id=client_id)
        
        return Transaction.objects.none()