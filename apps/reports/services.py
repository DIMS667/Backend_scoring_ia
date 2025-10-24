"""
Services de génération de rapports et analytics - CORRIGÉ DÉFINITIVEMENT
"""
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, Q
from decimal import Decimal
from apps.demands.models import CreditDemand
from apps.scoring.models import CreditScore
from apps.accounts.models import ClientProfile

def generate_portfolio_report(start_date, end_date):
    """Génère un rapport sur le portefeuille de crédits"""
    
    # CORRECTION : utiliser created_at au lieu de submitted_at
    demands = CreditDemand.objects.filter(
        created_at__date__range=[start_date, end_date]
    )
    
    # Statistiques globales
    total_demands = demands.count()
    total_amount = demands.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Par statut
    by_status = demands.values('status').annotate(
        count=Count('id'),
        amount=Sum('amount')
    )
    
    # CORRECTION : Par type de crédit - calculer avg_amount séparément
    by_type_data = []
    for credit_type_value, credit_type_label in CreditDemand.CREDIT_TYPE_CHOICES:
        type_demands = demands.filter(credit_type=credit_type_value)
        count = type_demands.count()
        amount = type_demands.aggregate(Sum('amount'))['amount__sum'] or 0
        avg_amount = type_demands.aggregate(Avg('amount'))['amount__avg'] or 0
        
        if count > 0:  # Inclure seulement les types avec des demandes
            by_type_data.append({
                'credit_type': credit_type_value,
                'count': count,
                'amount': float(amount),
                'avg_amount': float(avg_amount)
            })
    
    # Taux d'approbation
    approved = demands.filter(status='APPROVED').count()
    rejected = demands.filter(status='REJECTED').count()
    processed = approved + rejected
    approval_rate = (approved / processed * 100) if processed > 0 else 0
    
    # Montant moyen
    avg_amount = demands.aggregate(Avg('amount'))['amount__avg'] or 0
    
    # Évolution mensuelle (pour graphique)
    monthly_evolution = []
    current_date = start_date
    while current_date <= end_date:
        month_demands = demands.filter(
            created_at__year=current_date.year,
            created_at__month=current_date.month
        )
        monthly_evolution.append({
            'month': current_date.strftime('%Y-%m'),
            'count': month_demands.count(),
            'amount': float(month_demands.aggregate(Sum('amount'))['amount__sum'] or 0)
        })
        # Passer au mois suivant
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return {
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'summary': {
            'total_demands': total_demands,
            'total_amount': float(total_amount),
            'avg_amount': float(avg_amount),
            'approval_rate': round(approval_rate, 2),
            'approved': approved,
            'rejected': rejected,
        },
        'by_status': [
            {
                'status': item['status'],
                'count': item['count'],
                'amount': float(item['amount'] or 0)
            } for item in by_status
        ],
        'by_type': by_type_data,
        'monthly_evolution': monthly_evolution,
    }


def generate_performance_report(start_date, end_date):
    """Génère un rapport de performance"""
    
    # CORRECTION : utiliser created_at au lieu de submitted_at
    demands = CreditDemand.objects.filter(
        created_at__date__range=[start_date, end_date]
    )
    
    # Délai moyen de traitement
    processed_demands = demands.filter(
        decision_date__isnull=False
    )
    
    avg_processing_days = 0
    if processed_demands.exists():
        total_days = sum([
            (d.decision_date.date() - d.created_at.date()).days 
            for d in processed_demands
        ])
        avg_processing_days = total_days / processed_demands.count()
    
    # Performance par agent
    agent_stats = demands.filter(
        assigned_agent__isnull=False
    ).values(
        'assigned_agent__first_name',
        'assigned_agent__last_name'
    ).annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='APPROVED')),
        rejected=Count('id', filter=Q(status='REJECTED')),
    )
    
    # Distribution des scores
    scores = CreditScore.objects.filter(
        demand__in=demands
    )
    
    score_distribution = {
        'low_risk': scores.filter(risk_level='LOW').count(),
        'medium_risk': scores.filter(risk_level='MEDIUM').count(),
        'high_risk': scores.filter(risk_level='HIGH').count(),
        'very_high_risk': scores.filter(risk_level='VERY_HIGH').count(),
    }
    
    avg_score = scores.aggregate(Avg('score_value'))['score_value__avg'] or 0
    
    # Données pour graphiques
    score_ranges = [
        {'range': '0-300', 'count': scores.filter(score_value__lt=300).count()},
        {'range': '300-500', 'count': scores.filter(score_value__gte=300, score_value__lt=500).count()},
        {'range': '500-700', 'count': scores.filter(score_value__gte=500, score_value__lt=700).count()},
        {'range': '700-850', 'count': scores.filter(score_value__gte=700, score_value__lt=850).count()},
        {'range': '850-1000', 'count': scores.filter(score_value__gte=850).count()},
    ]
    
    return {
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'processing': {
            'avg_processing_days': round(avg_processing_days, 1),
            'total_processed': processed_demands.count(),
        },
        'agents': list(agent_stats),
        'scoring': {
            'avg_score': round(avg_score, 0),
            'distribution': score_distribution,
            'score_ranges': score_ranges,
        }
    }


def generate_risk_report(start_date, end_date):
    """Génère un rapport de risque"""
    
    # CORRECTION : utiliser created_at au lieu de submitted_at
    demands = CreditDemand.objects.filter(
        created_at__date__range=[start_date, end_date]
    )
    
    # Exposition par niveau de risque
    risk_exposure = {}
    for level in ['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']:
        scores = CreditScore.objects.filter(
            demand__in=demands,
            risk_level=level
        )
        
        amount = demands.filter(
            score__risk_level=level,
            status='APPROVED'
        ).aggregate(Sum('approved_amount'))['approved_amount__sum'] or 0
        
        risk_exposure[level] = {
            'count': scores.count(),
            'amount': float(amount)
        }
    
    # Concentration par secteur
    sector_concentration = ClientProfile.objects.filter(
        user__demands__in=demands.filter(status='APPROVED')
    ).values('sector').annotate(
        count=Count('user__demands'),
        amount=Sum('user__demands__approved_amount')
    ).order_by('-amount')[:10]
    
    # CORRECTION : Calculer le ratio d'endettement basé sur les champs existants
    # D'après l'erreur, les champs disponibles sont : monthly_debt_payment, monthly_income
    debt_ratios = []
    profiles = ClientProfile.objects.filter(
        user__demands__in=demands.filter(status='APPROVED')
    ).exclude(monthly_income=0)
    
    for profile in profiles:
        if profile.monthly_income and profile.monthly_income > 0:
            debt_ratio = (profile.monthly_debt_payment / profile.monthly_income) * 100
            debt_ratios.append(debt_ratio)
    
    avg_debt_ratio = sum(debt_ratios) / len(debt_ratios) if debt_ratios else 0
    
    return {
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'risk_exposure': risk_exposure,
        'sector_concentration': [
            {
                'sector': item['sector'] or 'Non spécifié',
                'count': item['count'],
                'amount': float(item['amount'] or 0)
            } for item in sector_concentration
        ],
        'avg_debt_ratio': float(avg_debt_ratio),
    }


def generate_compliance_report(start_date, end_date):
    """Génère un rapport de conformité réglementaire"""
    
    # CORRECTION : utiliser created_at au lieu de submitted_at
    demands = CreditDemand.objects.filter(
        created_at__date__range=[start_date, end_date]
    )
    
    # Conformité COBAC/BEAC
    total_approved_amount = demands.filter(
        status='APPROVED'
    ).aggregate(Sum('approved_amount'))['approved_amount__sum'] or 0
    
    # CORRECTION : Conversion Decimal en float pour éviter l'erreur de multiplication
    total_approved_amount = float(total_approved_amount)
    
    # Classification par durée (court/moyen/long terme)
    short_term = demands.filter(duration_months__lt=24).count()
    medium_term = demands.filter(duration_months__gte=24, duration_months__lt=84).count()
    long_term = demands.filter(duration_months__gte=84).count()
    
    # Taux moyens appliqués
    avg_interest_rate = demands.filter(
        status='APPROVED',
        interest_rate__isnull=False
    ).aggregate(Avg('interest_rate'))['interest_rate__avg'] or 0
    
    # Provisions IFRS9 (simplifié)
    stage1_amount = total_approved_amount * 0.7  # Supposé 70% performant
    stage2_amount = total_approved_amount * 0.2  # 20% underperforming
    stage3_amount = total_approved_amount * 0.1  # 10% non-performing
    
    provisions = {
        'stage1': stage1_amount * 0.01,
        'stage2': stage2_amount * 0.05,
        'stage3': stage3_amount * 1.0,
        'total': stage1_amount * 0.01 + stage2_amount * 0.05 + stage3_amount
    }
    
    return {
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'portfolio': {
            'total_amount': total_approved_amount,
            'short_term': short_term,
            'medium_term': medium_term,
            'long_term': long_term,
            'avg_interest_rate': float(avg_interest_rate),
        },
        'ifrs9_provisions': provisions,
    }


def get_dashboard_stats(user):
    """Génère les statistiques pour le dashboard"""
    
    if user.role == 'CLIENT':
        # Stats client
        demands = CreditDemand.objects.filter(client=user)
        
        return {
            'total_demands': demands.count(),
            'pending': demands.filter(status='PENDING_ANALYST').count(),
            'approved': demands.filter(status='APPROVED').count(),
            'rejected': demands.filter(status='REJECTED').count(),
            'total_approved_amount': float(demands.filter(status='APPROVED').aggregate(Sum('approved_amount'))['approved_amount__sum'] or 0),
        }
    
    else:  # AGENT
        # Stats agent
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        all_demands = CreditDemand.objects.all()
        
        return {
            'total_demands': all_demands.count(),
            'pending_review': all_demands.filter(status='PENDING_ANALYST').count(),
            'approved_today': all_demands.filter(status='APPROVED', decision_date__date=today).count(),
            'approved_week': all_demands.filter(status='APPROVED', decision_date__date__gte=week_ago).count(),
            'approved_month': all_demands.filter(status='APPROVED', decision_date__date__gte=month_ago).count(),
            'total_amount_pending': float(all_demands.filter(status='PENDING_ANALYST').aggregate(Sum('amount'))['amount__sum'] or 0),
            'avg_score': float(CreditScore.objects.all().aggregate(Avg('score_value'))['score_value__avg'] or 0),
        }


def get_recent_activity(user, limit=10):
    """Récupère l'activité récente"""
    
    if user.role == 'CLIENT':
        demands = CreditDemand.objects.filter(client=user).order_by('-updated_at')[:limit]
    else:
        demands = CreditDemand.objects.all().order_by('-updated_at')[:limit]
    
    activities = []
    for demand in demands:
        activities.append({
            'id': demand.id,
            'type': 'demand',
            'action': demand.get_status_display(),
            'client': demand.client.get_full_name(),
            'amount': float(demand.amount),
            'timestamp': demand.updated_at,
        })
    
    return activities