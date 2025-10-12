"""
Management command pour générer des données fictives
Usage: python manage.py generate_data
"""

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
import random
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker

from apps.accounts.models import User, ClientProfile
from apps.demands.models import CreditDemand, Document, DemandComment
from apps.scoring.models import PaymentHistory, Transaction

fake = Faker('fr_FR')

# Paramètres
NUM_CLIENTS = 80
NUM_AGENTS = 5
NUM_DEMANDS_PER_CLIENT = (1, 3)

CITIES = ['Yaoundé', 'Douala', 'Bafoussam', 'Garoua', 'Maroua', 'Bamenda', 'Ngaoundéré', 'Bertoua']
SECTORS = ['Banque', 'Télécommunications', 'Commerce', 'Industrie', 'Santé', 'Éducation', 'Administration', 'Transport', 'Agriculture']
EMPLOYERS = ['MTN Cameroon', 'Orange Cameroun', 'SONARA', 'ENEO', 'Hôpital Général', 'Ministère', 'CAMTEL', 'SAR']


class Command(BaseCommand):
    help = 'Génère des données fictives pour CreditScoring AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Supprimer les données existantes avant génération',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("GÉNÉRATION DE DONNÉES FICTIVES"))
        self.stdout.write("=" * 60)

        if options['clean']:
            self.stdout.write("\nSuppression des données existantes...")
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("✓ Données supprimées"))

        agents = self.create_agents()
        clients = self.create_clients()
        self.create_payment_history(clients)
        self.create_transactions(clients)
        self.create_demands(clients, agents)

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ GÉNÉRATION TERMINÉE!"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"\nRécapitulatif:")
        self.stdout.write(f"  - Agents: {User.objects.filter(role='AGENT').count()}")
        self.stdout.write(f"  - Clients: {User.objects.filter(role='CLIENT').count()}")
        self.stdout.write(f"  - Demandes: {CreditDemand.objects.count()}")
        self.stdout.write(f"  - Documents: {Document.objects.count()}")
        self.stdout.write(f"  - Commentaires: {DemandComment.objects.count()}")
        self.stdout.write(f"  - Paiements: {PaymentHistory.objects.count()}")
        self.stdout.write(f"  - Transactions: {Transaction.objects.count()}")
        self.stdout.write(f"\nComptes de test:")
        self.stdout.write(self.style.SUCCESS("  Agent: username='agent1', password='password123'"))
        self.stdout.write(self.style.SUCCESS("  Client: username='client1', password='password123'"))

    def create_agents(self):
        self.stdout.write("\nCréation des agents bancaires...")
        agents = []
        for i in range(NUM_AGENTS):
            username = f"agent{i+1}"
            if User.objects.filter(username=username).exists():
                agent = User.objects.get(username=username)
                agents.append(agent)
                continue
            
            agent = User.objects.create_user(
                username=username,
                email=f"agent{i+1}@creditbank.cm",
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number(),
                role='AGENT'
            )
            agents.append(agent)
        self.stdout.write(f"  ✓ {len(agents)} agents créés")
        return agents

    def create_clients(self):
        self.stdout.write(f"\nCréation de {NUM_CLIENTS} clients...")
        clients = []
        
        for i in range(NUM_CLIENTS):
            username = f"client{i+1}"
            if User.objects.filter(username=username).exists():
                client = User.objects.get(username=username)
                clients.append(client)
                continue
            
            user = User.objects.create_user(
                username=username,
                email=f"{username}@email.cm",
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number(),
                role='CLIENT'
            )
            
            birth_date = fake.date_of_birth(minimum_age=21, maximum_age=65)
            monthly_income = random.choice([
                Decimal(random.randint(75000, 150000)),
                Decimal(random.randint(150000, 300000)),
                Decimal(random.randint(300000, 500000)),
                Decimal(random.randint(500000, 1000000)),
            ])
            
            seniority_years = Decimal(random.uniform(0.5, 20))
            existing_credits = random.randint(0, 3)
            monthly_debt = monthly_income * Decimal(random.uniform(0, 0.4)) if existing_credits > 0 else Decimal(0)
            
            ClientProfile.objects.create(
                user=user,
                cni_number=f"CM{random.randint(100000000, 999999999)}",
                birth_date=birth_date,
                birth_place=random.choice(CITIES),
                marital_status=random.choice(['SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED']),
                dependents=random.randint(0, 5),
                address=fake.address(),
                city=random.choice(CITIES),
                employment_status=random.choice(['EMPLOYEE', 'CIVIL_SERVANT', 'SELF_EMPLOYED']),
                employer=random.choice(EMPLOYERS),
                job_title=fake.job(),
                sector=random.choice(SECTORS),
                seniority_years=seniority_years,
                monthly_income=monthly_income,
                existing_credits=existing_credits,
                monthly_debt_payment=monthly_debt,
                bank_seniority_months=random.randint(6, 120),
            )
            
            clients.append(user)
            
            if (i + 1) % 20 == 0:
                self.stdout.write(f"  ✓ {i + 1}/{NUM_CLIENTS} clients créés")
        
        self.stdout.write(f"  ✓ Total: {len(clients)} clients créés")
        return clients

    def create_payment_history(self, clients):
        self.stdout.write("\nCréation de l'historique de paiements...")
        total = 0
        for client in clients:
            profile_type = random.choices(['good', 'medium', 'bad'], weights=[70, 20, 10])[0]
            num_payments = random.randint(5, 30)
            
            for _ in range(num_payments):
                payment_date = fake.date_between(start_date='-2y', end_date='today')
                due_date = payment_date - timedelta(days=random.randint(0, 5))
                
                if profile_type == 'good':
                    days_late, status = 0, 'ON_TIME'
                elif profile_type == 'medium':
                    days_late = random.choice([0, 0, 0, 0, random.randint(1, 15)])
                    status = 'ON_TIME' if days_late == 0 else 'LATE'
                else:
                    days_late = random.choice([0, 0, random.randint(1, 30), random.randint(30, 90)])
                    status = 'DEFAULT' if days_late > 30 else ('LATE' if days_late > 0 else 'ON_TIME')
                
                PaymentHistory.objects.create(
                    client=client,
                    credit_type=random.choice(['CONSUMPTION', 'AUTO', 'REAL_ESTATE']),
                    amount=Decimal(random.randint(50000, 500000)),
                    payment_date=payment_date,
                    due_date=due_date,
                    days_late=days_late,
                    status=status
                )
                total += 1
        
        self.stdout.write(f"  ✓ {total} paiements créés")

    def create_transactions(self, clients):
        self.stdout.write("\nCréation des transactions bancaires...")
        total = 0
        for client in clients:
            balance = Decimal(random.randint(100000, 5000000))
            num_transactions = random.randint(20, 100)
            
            for _ in range(num_transactions):
                transaction_date = fake.date_between(start_date='-1y', end_date='today')
                transaction_type = random.choices(['CREDIT', 'DEBIT'], weights=[40, 60])[0]
                
                if transaction_type == 'CREDIT':
                    amount = Decimal(random.randint(10000, 1000000))
                    balance += amount
                else:
                    amount = Decimal(random.randint(5000, 500000))
                    balance = max(balance - amount, Decimal(0))
                
                Transaction.objects.create(
                    client=client,
                    transaction_date=transaction_date,
                    amount=amount,
                    transaction_type=transaction_type,
                    category=random.choice(['Salaire', 'Achat', 'Retrait', 'Virement', 'Facture']),
                    balance_after=balance
                )
                total += 1
        
        self.stdout.write(f"  ✓ {total} transactions créées")

    def create_demands(self, clients, agents):
        self.stdout.write("\nCréation des demandes, documents et commentaires...")
        total_demands = 0
        document_types = [choice[0] for choice in Document.DOCUMENT_TYPE_CHOICES]
        
        for client in clients:
            num_demands = random.randint(*NUM_DEMANDS_PER_CLIENT)
            
            for _ in range(num_demands):
                credit_type = random.choice(['CONSUMPTION', 'AUTO', 'REAL_ESTATE', 'BUSINESS'])
                
                if credit_type == 'CONSUMPTION':
                    amount, duration = Decimal(random.randint(500000, 5000000)), random.choice([12, 18, 24, 36])
                elif credit_type == 'AUTO':
                    amount, duration = Decimal(random.randint(3000000, 15000000)), random.choice([24, 36, 48, 60])
                elif credit_type == 'REAL_ESTATE':
                    amount, duration = Decimal(random.randint(10000000, 50000000)), random.choice([120, 180, 240])
                else:
                    amount, duration = Decimal(random.randint(2000000, 20000000)), random.choice([12, 24, 36, 48])
                
                demand_status = random.choices(
                    ['DRAFT', 'SUBMITTED', 'PENDING_ANALYST', 'APPROVED', 'REJECTED'],
                    weights=[10, 40, 30, 15, 5]
                )[0]
                
                created_at = fake.date_time_between(start_date='-6m', end_date='now')
                submitted_at = created_at + timedelta(hours=random.randint(1, 48)) if demand_status != 'DRAFT' else None
                decision_date = submitted_at + timedelta(days=random.randint(1, 7)) if demand_status in ['APPROVED', 'REJECTED'] else None
                
                demand = CreditDemand.objects.create(
                    client=client,
                    assigned_agent=random.choice(agents) if demand_status != 'DRAFT' else None,
                    credit_type=credit_type,
                    amount=amount,
                    duration_months=duration,
                    purpose=fake.text(max_nb_chars=200),
                    status=demand_status,
                    decision_date=decision_date,
                    decision_comment=fake.text(max_nb_chars=150) if decision_date else '',
                    approved_amount=amount * Decimal(random.uniform(0.8, 1.0)) if demand_status == 'APPROVED' else None,
                    approved_duration=duration if demand_status == 'APPROVED' else None,
                    interest_rate=Decimal(random.uniform(7.5, 12.0)) if demand_status == 'APPROVED' else None,
                    created_at=created_at,
                    submitted_at=submitted_at,
                )
                total_demands += 1
                
                # Documents
                if demand.status != 'DRAFT':
                    for _ in range(random.randint(2, 5)):
                        doc_type = random.choice(document_types)
                        filename = f"fake_{doc_type.lower()}_{demand.id}.pdf"
                        file_content = ContentFile(b"Fake file content", name=filename)
                        
                        Document.objects.create(
                            demand=demand,
                            document_type=doc_type,
                            file=file_content,
                            original_filename=filename,
                            file_size=random.randint(50000, 2000000)
                        )
                
                # Commentaires
                if demand.assigned_agent:
                    for _ in range(random.randint(0, 3)):
                        DemandComment.objects.create(
                            demand=demand,
                            author=demand.assigned_agent,
                            content=fake.sentence(nb_words=15),
                            is_internal=random.choice([True, False])
                        )
        
        self.stdout.write(f"  ✓ {total_demands} demandes créées")