"""
Signals Django pour les demandes de crédit
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
    
    AuditLog.objects.create(
        user=instance.client if created else instance.assigned_agent,
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
    CALCUL AUTOMATIQUE DU SCORE dès qu'une demande est soumise
    """
    # Calculer le score uniquement si la demande est soumise et n'a pas encore de score
    if instance.status in ['SUBMITTED', 'PENDING_ANALYST', 'IN_ANALYSIS']:
        # Vérifier si un score existe déjà
        from apps.scoring.models import CreditScore
        
        if not hasattr(instance, 'score') or not CreditScore.objects.filter(demand=instance).exists():
            # Calculer le score automatiquement
            from apps.scoring.services import calculate_score
            
            try:
                calculate_score(instance)
                print(f"✅ Score calculé automatiquement pour la demande #{instance.id}")
            except Exception as e:
                print(f"❌ Erreur calcul score pour demande #{instance.id}: {str(e)}")