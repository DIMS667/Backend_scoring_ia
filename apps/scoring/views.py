from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
        if user.role == 'CLIENT':
            return CreditScore.objects.filter(demand__client=user)
        return CreditScore.objects.all()
    
    @action(detail=False, methods=['post'])
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
            
            # Vérifier permissions
            if request.user.role == 'CLIENT' and demand.client != request.user:
                return Response(
                    {'error': 'Permission refusée'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Calculer le score
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
        
        # Agent peut voir l'historique d'un client spécifique
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
        
        # Agent peut voir les transactions d'un client spécifique
        client_id = self.request.query_params.get('client_id')
        if client_id:
            return Transaction.objects.filter(client_id=client_id)
        
        return Transaction.objects.none()