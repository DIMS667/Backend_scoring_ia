"""
Services métier pour les demandes de crédit
"""
from django.utils import timezone
from .models import CreditDemand
from apps.notifications.models import Notification

def notify_demand_submitted(demand):
    """Notifier qu'une demande a été soumise"""
    # Notification au client
    Notification.objects.create(
        user=demand.client,
        notification_type='DEMAND_SUBMITTED',
        title='Demande soumise',
        message=f'Votre demande de crédit #{demand.id} a été soumise avec succès.',
        link=f'/demands/{demand.id}'
    )

def notify_demand_decision(demand, approved=True):
    """Notifier d'une décision sur une demande"""
    notification_type = 'DEMAND_APPROVED' if approved else 'DEMAND_REJECTED'
    title = 'Demande approuvée' if approved else 'Demande rejetée'
    message = f'Votre demande de crédit #{demand.id} a été {"approuvée" if approved else "rejetée"}.'
    
    Notification.objects.create(
        user=demand.client,
        notification_type=notification_type,
        title=title,
        message=message,
        link=f'/demands/{demand.id}'
    )

def calculate_monthly_payment(amount, duration_months, interest_rate):
    """Calcul de la mensualité"""
    if interest_rate > 0:
        r = float(interest_rate) / 100 / 12
        n = int(duration_months)
        P = float(amount)
        mensualite = P * (r * (1 + r)**n) / ((1 + r)**n - 1)
    else:
        mensualite = float(amount) / int(duration_months)
    
    return round(mensualite, 2)