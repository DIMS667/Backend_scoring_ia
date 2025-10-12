# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from core.permissions import IsAgent
from .models import Report, Dashboard
from .serializers import ReportSerializer, DashboardSerializer
from .services import (
    generate_portfolio_report,
    generate_performance_report,
    generate_risk_report,
    generate_compliance_report,
    get_dashboard_stats,
    get_recent_activity
)

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Seuls les agents peuvent voir les rapports
        if self.request.user.role == 'AGENT':
            return Report.objects.all()
        return Report.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate_portfolio(self, request):
        """Générer un rapport portefeuille"""
        if request.user.role != 'AGENT':
            return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
        
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date et end_date sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = generate_portfolio_report(
            datetime.strptime(start_date, '%Y-%m-%d').date(),
            datetime.strptime(end_date, '%Y-%m-%d').date()
        )
        
        # Créer le rapport
        report = Report.objects.create(
            name=f"Rapport Portefeuille {start_date} à {end_date}",
            report_type='PORTFOLIO',
            format='JSON',
            period_start=start_date,
            period_end=end_date,
            data=data,
            summary=data.get('summary', {}),
            generated_by=request.user
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def generate_performance(self, request):
        """Générer un rapport de performance"""
        if request.user.role != 'AGENT':
            return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
        
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date et end_date sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = generate_performance_report(
            datetime.strptime(start_date, '%Y-%m-%d').date(),
            datetime.strptime(end_date, '%Y-%m-%d').date()
        )
        
        report = Report.objects.create(
            name=f"Rapport Performance {start_date} à {end_date}",
            report_type='PERFORMANCE',
            format='JSON',
            period_start=start_date,
            period_end=end_date,
            data=data,
            summary=data.get('processing', {}),
            generated_by=request.user
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def generate_risk(self, request):
        """Générer un rapport de risque"""
        if request.user.role != 'AGENT':
            return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
        
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date et end_date sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = generate_risk_report(
            datetime.strptime(start_date, '%Y-%m-%d').date(),
            datetime.strptime(end_date, '%Y-%m-%d').date()
        )
        
        report = Report.objects.create(
            name=f"Rapport Risque {start_date} à {end_date}",
            report_type='RISK',
            format='JSON',
            period_start=start_date,
            period_end=end_date,
            data=data,
            summary={'risk_exposure': data.get('risk_exposure', {})},
            generated_by=request.user
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def generate_compliance(self, request):
        """Générer un rapport de conformité"""
        if request.user.role != 'AGENT':
            return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
        
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date et end_date sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = generate_compliance_report(
            datetime.strptime(start_date, '%Y-%m-%d').date(),
            datetime.strptime(end_date, '%Y-%m-%d').date()
        )
        
        report = Report.objects.create(
            name=f"Rapport Conformité {start_date} à {end_date}",
            report_type='COMPLIANCE',
            format='JSON',
            period_start=start_date,
            period_end=end_date,
            data=data,
            summary=data.get('portfolio', {}),
            generated_by=request.user
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(request):
    """Récupérer les statistiques du dashboard"""
    stats = get_dashboard_stats(request.user)
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activity_view(request):
    """Récupérer l'activité récente"""
    limit = int(request.query_params.get('limit', 10))
    activities = get_recent_activity(request.user, limit)
    return Response(activities)


class DashboardViewSet(viewsets.ModelViewSet):
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Dashboard.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
