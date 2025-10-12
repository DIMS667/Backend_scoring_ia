from django.db import models

class BusinessRule(models.Model):
    """Règles métier configurables pour l'éligibilité au crédit"""
    
    RULE_TYPE_CHOICES = [
        ('ELIGIBILITY', 'Règle d\'éligibilité'),
        ('SCORING_THRESHOLD', 'Seuil de scoring'),
        ('AMOUNT_LIMIT', 'Limite de montant'),
        ('DURATION_LIMIT', 'Limite de durée'),
        ('DEBT_RATIO', 'Taux d\'endettement'),
        ('AGE_LIMIT', 'Limite d\'âge'),
        ('INCOME_REQUIREMENT', 'Revenu minimum'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nom de la règle")
    rule_type = models.CharField(max_length=30, choices=RULE_TYPE_CHOICES)
    credit_type = models.CharField(max_length=20, blank=True, help_text="Type de crédit (vide = toutes)")
    
    # Conditions
    condition = models.JSONField(help_text="Conditions sous forme JSON")
    threshold_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Paramètres
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Ordre d'évaluation (plus élevé = prioritaire)")
    
    # Metadata
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'business_rules'
        ordering = ['-priority', 'rule_type']
        verbose_name = 'Règle Métier'
        verbose_name_plural = 'Règles Métier'
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class RuleEvaluation(models.Model):
    """Résultat de l'évaluation des règles pour une demande"""
    
    demand = models.ForeignKey('demands.CreditDemand', on_delete=models.CASCADE, related_name='rule_evaluations')
    rule = models.ForeignKey(BusinessRule, on_delete=models.CASCADE)
    
    # Résultat
    passed = models.BooleanField(verbose_name="Règle respectée")
    computed_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    message = models.TextField(help_text="Message d'explication")
    
    evaluated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rule_evaluations'
        ordering = ['-evaluated_at']
        verbose_name = 'Évaluation de Règle'
        verbose_name_plural = 'Évaluations de Règles'
    
    def __str__(self):
        status = "✓" if self.passed else "✗"
        return f"{status} {self.rule.name} - Demande #{self.demand.id}"


class CreditProduct(models.Model):
    """Produits de crédit configurables"""
    
    name = models.CharField(max_length=200, verbose_name="Nom du produit")
    credit_type = models.CharField(max_length=20, choices=[
        ('CONSUMPTION', 'Crédit à la consommation'),
        ('REAL_ESTATE', 'Crédit immobilier'),
        ('AUTO', 'Crédit automobile'),
        ('BUSINESS', 'Crédit professionnel'),
    ])
    
    # Limites
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant minimum")
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant maximum")
    min_duration_months = models.IntegerField(verbose_name="Durée minimum (mois)")
    max_duration_months = models.IntegerField(verbose_name="Durée maximum (mois)")
    
    # Taux d'intérêt
    base_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Taux de base (%)")
    min_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Taux minimum (%)")
    max_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Taux maximum (%)")
    
    # Conditions
    min_income_required = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Revenu minimum requis")
    max_debt_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=33, verbose_name="Taux endettement max (%)")
    min_score_required = models.IntegerField(default=400, verbose_name="Score minimum requis")
    
    # Documents requis
    required_documents = models.JSONField(default=list, help_text="Liste des documents obligatoires")
    
    # Statut
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'credit_products'
        verbose_name = 'Produit de Crédit'
        verbose_name_plural = 'Produits de Crédit'
    
    def __str__(self):
        return f"{self.name} ({self.get_credit_type_display()})"