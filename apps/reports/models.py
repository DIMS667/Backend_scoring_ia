from django.db import models
from apps.accounts.models import User

class Report(models.Model):
    """Rapports générés (export, analytiques, conformité)"""
    
    REPORT_TYPE_CHOICES = [
        ('PORTFOLIO', 'Rapport Portefeuille'),
        ('PERFORMANCE', 'Rapport Performance'),
        ('COMPLIANCE', 'Rapport Conformité'),
        ('RISK', 'Rapport Risque'),
        ('COBAC', 'Déclaration COBAC'),
        ('BEAC', 'Déclaration BEAC'),
        ('IFRS9', 'Rapport IFRS9'),
    ]
    
    FORMAT_CHOICES = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nom du rapport")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='PDF')
    
    # Période couverte
    period_start = models.DateField(verbose_name="Début période")
    period_end = models.DateField(verbose_name="Fin période")
    
    # Fichier généré
    file = models.FileField(upload_to='reports/%Y/%m/', blank=True, null=True)
    file_size = models.IntegerField(null=True, blank=True, help_text="Taille en octets")
    
    # Données du rapport
    data = models.JSONField(default=dict, verbose_name="Données du rapport")
    summary = models.JSONField(default=dict, verbose_name="Résumé")
    
    # Métadonnées
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reports_generated')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reports'
        ordering = ['-generated_at']
        verbose_name = 'Rapport'
        verbose_name_plural = 'Rapports'
    
    def __str__(self):
        return f"{self.name} - {self.generated_at.strftime('%Y-%m-%d')}"


class Dashboard(models.Model):
    """Configuration des dashboards personnalisés"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboards')
    name = models.CharField(max_length=200, verbose_name="Nom du dashboard")
    layout = models.JSONField(help_text="Configuration du layout")
    widgets = models.JSONField(help_text="Widgets affichés")
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboards'
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.name}"