from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('CLIENT', 'Client'),
        ('AGENT', 'Agent Bancaire'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


class ClientProfile(models.Model):
    MARITAL_STATUS_CHOICES = [
        ('SINGLE', 'Célibataire'),
        ('MARRIED', 'Marié(e)'),
        ('DIVORCED', 'Divorcé(e)'),
        ('WIDOWED', 'Veuf/Veuve'),
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('EMPLOYEE', 'Salarié'),
        ('CIVIL_SERVANT', 'Fonctionnaire'),
        ('SELF_EMPLOYED', 'Indépendant'),
        ('UNEMPLOYED', 'Sans emploi'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    cni_number = models.CharField(max_length=50, unique=True, verbose_name="Numéro CNI")
    birth_date = models.DateField(verbose_name="Date de naissance")
    birth_place = models.CharField(max_length=100, verbose_name="Lieu de naissance")
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, default='SINGLE')
    dependents = models.IntegerField(default=0, verbose_name="Nombre de personnes à charge")
    address = models.TextField(verbose_name="Adresse complète")
    city = models.CharField(max_length=100, default='Yaoundé')
    
    # Professional info
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES)
    employer = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True, verbose_name="Fonction")
    sector = models.CharField(max_length=100, blank=True, verbose_name="Secteur d'activité")
    seniority_years = models.DecimalField(max_digits=4, decimal_places=1, default=0, verbose_name="Ancienneté (années)")
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Revenu mensuel net (FCFA)")
    
    # Banking info
    existing_credits = models.IntegerField(default=0, verbose_name="Nombre de crédits en cours")
    monthly_debt_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Mensualités totales (FCFA)")
    bank_seniority_months = models.IntegerField(default=0, verbose_name="Ancienneté banque (mois)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'client_profiles'
        verbose_name = 'Profil Client'
        verbose_name_plural = 'Profils Clients'
    
    def __str__(self):
        return f"Profile de {self.user.get_full_name()}"
    
    @property
    def debt_ratio(self):
        """Calcul du taux d'endettement"""
        if self.monthly_income > 0:
            return (self.monthly_debt_payment / self.monthly_income) * 100
        return 0