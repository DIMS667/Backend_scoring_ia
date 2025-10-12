
from django.db import models
from apps.demands.models import CreditDemand

class CreditScore(models.Model):
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Risque Faible'),
        ('MEDIUM', 'Risque Modéré'),
        ('HIGH', 'Risque Élevé'),
        ('VERY_HIGH', 'Risque Très Élevé'),
    ]
    
    demand = models.OneToOneField(CreditDemand, on_delete=models.CASCADE, related_name='score')
    score_value = models.IntegerField(verbose_name="Score (0-1000)")
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES)
    
    # Facteurs contributifs
    factors_positive = models.JSONField(default=list, verbose_name="Facteurs positifs")
    factors_negative = models.JSONField(default=list, verbose_name="Facteurs négatifs")
    
    # Détails techniques
    model_version = models.CharField(max_length=50, default='v1.0')
    features_used = models.JSONField(default=dict, verbose_name="Features utilisées")
    shap_values = models.JSONField(default=dict, verbose_name="Valeurs SHAP")
    
    # Recommandation IA
    ai_recommendation = models.CharField(max_length=20, choices=[
        ('AUTO_APPROVE', 'Approbation automatique'),
        ('MANUAL_REVIEW', 'Examen manuel requis'),
        ('AUTO_REJECT', 'Rejet automatique'),
    ])
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Niveau de confiance (%)")
    
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'credit_scores'
        verbose_name = 'Score de Crédit'
        verbose_name_plural = 'Scores de Crédit'
    
    def __str__(self):
        return f"Score {self.score_value} - Demande #{self.demand.id}"


class PaymentHistory(models.Model):
    """Historique des paiements d'un client (pour le scoring)"""
    client = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='payment_history')
    credit_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    due_date = models.DateField()
    days_late = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('ON_TIME', 'À temps'),
        ('LATE', 'En retard'),
        ('DEFAULT', 'Défaut'),
    ])
    
    class Meta:
        db_table = 'payment_history'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Paiement {self.client.get_full_name()} - {self.payment_date}"


class Transaction(models.Model):
    """Transactions bancaires d'un client (pour analyse comportementale)"""
    client = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=[
        ('CREDIT', 'Crédit'),
        ('DEBIT', 'Débit'),
    ])
    category = models.CharField(max_length=50, blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} FCFA - {self.transaction_date}"