
# core/validators.py
from django.core.exceptions import ValidationError
from datetime import date

def validate_cni_number(value):
    """Valide le format du numéro CNI camerounais"""
    if not value.startswith('CM') or len(value) != 11:
        raise ValidationError('Format CNI invalide (doit commencer par CM et avoir 11 caractères)')

def validate_phone_number(value):
    """Valide le format du numéro de téléphone camerounais"""
    if not value.startswith(('+237', '6', '2')) or len(value.replace('+237', '').replace(' ', '')) != 9:
        raise ValidationError('Format téléphone invalide')

def validate_age(birth_date):
    """Valide que l'âge est entre 21 et 65 ans"""
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if age < 21 or age > 65:
        raise ValidationError('L\'âge doit être entre 21 et 65 ans')

def validate_amount(amount, min_amount=10000, max_amount=100000000):
    """Valide que le montant est dans les limites"""
    if amount < min_amount or amount > max_amount:
        raise ValidationError(f'Le montant doit être entre {min_amount} et {max_amount} FCFA')