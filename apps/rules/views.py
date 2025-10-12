# ============================================
# apps/rules/views.py - VERSION COMPLÈTE
# ============================================

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Import core
from core.permissions import IsAgent

from .models import BusinessRule, RuleEvaluation, CreditProduct
from .serializers import BusinessRuleSerializer, RuleEvaluationSerializer, CreditProductSerializer
from .engine import evaluate_all_rules, check_product_eligibility
from apps.demands.models import CreditDemand


class BusinessRuleViewSet(viewsets.ModelViewSet):
    queryset = BusinessRule.objects.all()
    serializer_class = BusinessRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'AGENT':
            return BusinessRule.objects.all()
        return BusinessRule.objects.filter(is_active=True)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAgent()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'])
    def evaluate_demand(self, request):
        """Évaluer les règles pour une demande"""
        demand_id = request.data.get('demand_id')
        
        try:
            demand = CreditDemand.objects.get(id=demand_id)
            
            if request.user.role == 'CLIENT' and demand.client != request.user:
                return Response(
                    {'error': 'Permission refusée'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            result = evaluate_all_rules(demand)
            
            return Response({
                'all_passed': result['all_passed'],
                'summary': result['summary'],
                'evaluations': RuleEvaluationSerializer(result['evaluations'], many=True).data
            })
            
        except CreditDemand.DoesNotExist:
            return Response(
                {'error': 'Demande non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class RuleEvaluationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RuleEvaluation.objects.all()
    serializer_class = RuleEvaluationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'CLIENT':
            return RuleEvaluation.objects.filter(demand__client=user)
        return RuleEvaluation.objects.all()


class CreditProductViewSet(viewsets.ModelViewSet):
    queryset = CreditProduct.objects.filter(is_active=True)
    serializer_class = CreditProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAgent()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'])
    def check_eligibility(self, request, pk=None):
        """Vérifier l'éligibilité pour un produit"""
        product = self.get_object()
        demand_id = request.data.get('demand_id')
        
        try:
            demand = CreditDemand.objects.get(id=demand_id)
            result = check_product_eligibility(demand, product)
            return Response(result)
            
        except CreditDemand.DoesNotExist:
            return Response(
                {'error': 'Demande non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )