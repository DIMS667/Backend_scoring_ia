from django.apps import AppConfig


class DemandsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.demands'
    verbose_name = 'Gestion des demandes de crédit'
    
    def ready(self):
        """Importer les signals au démarrage de l'application"""
        import apps.demands.signals