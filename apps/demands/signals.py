"""
Signals Django pour les demandes de crédit - WORKFLOW CORRIGÉ
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CreditDemand
from apps.audit.models import AuditLog

@receiver(post_save, sender=CreditDemand)
def log_demand_changes(sender, instance, created, **kwargs):
    """Enregistrer les modifications des demandes dans l'audit log"""
    
    action = 'CREATE' if created else 'UPDATE'
    
    description = f"Demande #{instance.id} - Montant: {instance.amount} FCFA"
    
    if not created:
        if instance.status == 'APPROVED':
            action = 'APPROVE'
            description = f"Demande #{instance.id} approuvée - Montant: {instance.approved_amount} FCFA"
        elif instance.status == 'REJECTED':
            action = 'REJECT'
            description = f"Demande #{instance.id} rejetée"
        elif instance.status == 'CANCELLED':
            action = 'CANCEL'
            description = f"Demande #{instance.id} annulée par le client"
    
    AuditLog.objects.create(
        user=instance.client if created else (instance.assigned_agent or instance.client),
        action=action,
        entity_type='CreditDemand',
        entity_id=instance.id,
        description=description,
        metadata={
            'status': instance.status,
            'amount': str(instance.amount),
            'credit_type': instance.credit_type,
        }
    )

@receiver(post_save, sender=CreditDemand)
def auto_calculate_score(sender, instance, created, **kwargs):
    """
    NOUVEAU WORKFLOW - CALCUL AUTOMATIQUE DU SCORE
    Score calculé dès la création (plus besoin d'attendre la soumission)
    """
    # Calculer le score UNIQUEMENT à la création
    if created and instance.status == 'PENDING_ANALYST':
        # Vérifier si un score existe déjà
        from apps.scoring.models import CreditScore
        
        if not CreditScore.objects.filter(demand=instance).exists():
            # Calculer le score automatiquement en arrière-plan
            from apps.scoring.services import calculate_score
            
            try:
                score = calculate_score(instance)
                print(f"✅ Score calculé automatiquement pour la demande #{instance.id}: {score.score_value}/1000")
                
                # IMPORTANT: NE PAS CHANGER LE STATUT AUTOMATIQUEMENT
                # L'agent doit TOUJOURS décider manuellement
                # Même si la recommandation IA est AUTO_APPROVE/AUTO_REJECT
                
            except Exception as e:
                print(f"❌ Erreur calcul score pour demande #{instance.id}: {str(e)}")

@receiver(post_save, sender=CreditDemand)
def auto_notify_demand(sender, instance, created, **kwargs):
    """
    Envoyer automatiquement les notifications
    """
    if created:
        # Notification au client : demande créée et en attente
        from .services import notify_demand_submitted
        notify_demand_submitted(instance)
        
        # Notification aux agents : nouvelle demande à examiner
        from apps.notifications.models import Notification
        from apps.accounts.models import User
        
        agents = User.objects.filter(role='AGENT', is_active=True)
        for agent in agents:
            Notification.objects.create(
                user=agent,
                notification_type='NEW_DEMAND_FOR_REVIEW',
                title='Nouvelle demande à examiner',
                message=f'Demande #{instance.id} de {instance.client.get_full_name()} - {instance.amount} FCFA',
                link=f'/agent/demands/{instance.id}'
            )