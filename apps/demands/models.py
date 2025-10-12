from django.db import models
from apps.accounts.models import User

class CreditDemand(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('SUBMITTED', 'Soumise'),
        ('IN_ANALYSIS', 'En analyse'),
        ('PENDING_ANALYST', 'En attente analyste'),
        ('APPROVED', 'Approuvée'),
        ('REJECTED', 'Rejetée'),
        ('CANCELLED', 'Annulée'),
    ]
    
    CREDIT_TYPE_CHOICES = [
        ('CONSUMPTION', 'Crédit à la consommation'),
        ('REAL_ESTATE', 'Crédit immobilier'),
        ('AUTO', 'Crédit automobile'),
        ('BUSINESS', 'Crédit professionnel'),
    ]
    
    # Relations
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demands')
    assigned_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_demands')
    
    # Credit details
    credit_type = models.CharField(max_length=20, choices=CREDIT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant demandé (FCFA)")
    duration_months = models.IntegerField(verbose_name="Durée (mois)")
    purpose = models.TextField(verbose_name="Objet du crédit")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Decision
    decision_date = models.DateTimeField(null=True, blank=True)
    decision_comment = models.TextField(blank=True)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    approved_duration = models.IntegerField(null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'credit_demands'
        ordering = ['-created_at']
        verbose_name = 'Demande de Crédit'
        verbose_name_plural = 'Demandes de Crédit'
    
    def __str__(self):
        return f"Demande #{self.id} - {self.client.get_full_name()} - {self.amount} FCFA"
    
    @property
    def monthly_payment(self):
        """Calcul mensualité approximative (formule simplifiée)"""
        if self.approved_amount and self.approved_duration and self.interest_rate:
            P = float(self.approved_amount)
            r = float(self.interest_rate) / 100 / 12
            n = int(self.approved_duration)
            if r > 0:
                mensualite = P * (r * (1 + r)**n) / ((1 + r)**n - 1)
            else:
                mensualite = P / n
            return round(mensualite, 2)
        return None


class Document(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('CNI', 'Carte Nationale d\'Identité'),
        ('PAYSLIP', 'Bulletin de salaire'),
        ('PROOF_OF_ADDRESS', 'Justificatif de domicile'),
        ('BANK_STATEMENT', 'Relevé bancaire'),
        ('OTHER', 'Autre'),
    ]
    
    demand = models.ForeignKey(CreditDemand, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="Taille en octets")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - Demande #{self.demand.id}"


class DemandComment(models.Model):
    demand = models.ForeignKey(CreditDemand, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Visible uniquement par les agents")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'demand_comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Commentaire de {self.author.get_full_name()} sur demande #{self.demand.id}"