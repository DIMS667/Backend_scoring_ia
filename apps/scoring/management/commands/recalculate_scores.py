"""
Commande Django pour recalculer les scores
Usage: python manage.py recalculate_scores
"""

from django.core.management.base import BaseCommand
from apps.demands.models import CreditDemand
from apps.scoring.services import calculate_score


class Command(BaseCommand):
    help = 'Recalcule les scores pour toutes les demandes soumises'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Recalculer même les scores existants',
        )
        
        parser.add_argument(
            '--demand-id',
            type=int,
            help='Recalculer le score pour une demande spécifique',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== RECALCUL DES SCORES ===\n'))
        
        if options['demand_id']:
            # Recalculer pour une demande spécifique
            try:
                demand = CreditDemand.objects.get(id=options['demand_id'])
                score = calculate_score(demand)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Score recalculé pour demande #{demand.id}: {score.score_value}'
                    )
                )
            except CreditDemand.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Demande #{options["demand_id"]} introuvable'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erreur: {str(e)}'))
            return
        
        # Récupérer les demandes
        if options['all']:
            demands = CreditDemand.objects.exclude(status='DRAFT')
        else:
            # Seulement celles sans score
            demands = CreditDemand.objects.exclude(status='DRAFT').filter(score__isnull=True)
        
        total = demands.count()
        self.stdout.write(f'📊 {total} demandes à traiter\n')
        
        success = 0
        errors = 0
        
        for i, demand in enumerate(demands, 1):
            try:
                score = calculate_score(demand)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ [{i}/{total}] Demande #{demand.id} - Score: {score.score_value}'
                    )
                )
                success += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ [{i}/{total}] Demande #{demand.id} - Erreur: {str(e)}'
                    )
                )
                errors += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Terminé: {success} succès, {errors} erreurs'))