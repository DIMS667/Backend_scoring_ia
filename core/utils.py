
# core/utils.py
import random
import string
from datetime import datetime, timedelta, date

def generate_reference_number(prefix='CR'):
    """Génère un numéro de référence unique"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{timestamp}{random_part}"

def format_currency(amount):
    """Formate un montant en FCFA"""
    return f"{amount:,.0f} FCFA"

def calculate_age(birth_date):
    """Calcule l'âge à partir de la date de naissance"""
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_next_business_day(start_date, days=1):
    """Retourne le prochain jour ouvrable"""
    current = start_date
    while days > 0:
        current += timedelta(days=1)
        # Sauter les weekends (5=samedi, 6=dimanche)
        if current.weekday() < 5:
            days -= 1
    return current