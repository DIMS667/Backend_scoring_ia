# apps/demands/apps.py
from django.apps import AppConfig

class DemandsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.demands'
    verbose_name = 'Gestion des Demandes'
    
    def ready(self):
        # Importer les signals
        import apps.demands.signals