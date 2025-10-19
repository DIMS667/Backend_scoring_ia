import numpy as np
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Sum
from .models import CreditScore, PaymentHistory, Transaction

def calculate_score(demand):
    """Calcul du score de crédit pour une demande - VERSION AMÉLIORÉE"""
    
    client = demand.client
    
    # Vérifier si le profil existe
    try:
        profile = client.client_profile
    except:
        # Si pas de profil, créer un score par défaut
        score = CreditScore.objects.create(
            demand=demand,
            score_value=400,
            risk_level='VERY_HIGH',
            factors_positive=[],
            factors_negative=[{'factor': 'Profil client incomplet', 'value': 'N/A', 'impact': -200}],
            model_version='v1.0-mvp',
            features_used={},
            shap_values={},
            ai_recommendation='MANUAL_REVIEW',
            confidence_level=50.0,
        )
        return score
    
    # Extraction des features
    features = extract_features(client, profile, demand)
    
    # Calcul du score (algorithme amélioré)
    score_value = compute_advanced_score(features)
    
    # Détermination du niveau de risque
    risk_level = determine_risk_level(score_value)
    
    # Identification des facteurs
    factors_positive, factors_negative = identify_factors(features, score_value)
    
    # Recommandation IA
    ai_recommendation, confidence = generate_recommendation(score_value, features)
    
    # Calcul SHAP values (simulé mais réaliste)
    shap_values = simulate_shap_values(features)
    
    # Sauvegarde du score
    score, created = CreditScore.objects.update_or_create(
        demand=demand,
        defaults={
            'score_value': score_value,
            'risk_level': risk_level,
            'factors_positive': factors_positive,
            'factors_negative': factors_negative,
            'model_version': 'v1.1-advanced',
            'features_used': features,
            'shap_values': shap_values,
            'ai_recommendation': ai_recommendation,
            'confidence_level': confidence,
        }
    )
    
    return score


def extract_features(client, profile, demand):
    """Extraction des features pour le scoring - VERSION AMÉLIORÉE"""
    
    # Features profil
    age = (datetime.now().date() - profile.birth_date).days / 365.25
    debt_ratio = float(profile.debt_ratio)
    monthly_income = float(profile.monthly_income)
    seniority_years = float(profile.seniority_years)
    
    # Features demande
    requested_amount = float(demand.amount)
    duration_months = demand.duration_months
    loan_to_income_ratio = (requested_amount / duration_months) / monthly_income if monthly_income > 0 else 999
    
    # Ratio montant/revenu annuel
    amount_to_annual_income = requested_amount / (monthly_income * 12) if monthly_income > 0 else 999
    
    # Historique paiements
    payment_stats = get_payment_statistics(client)
    
    # Transactions bancaires
    transaction_stats = get_transaction_statistics(client)
    
    # Capacité de remboursement
    monthly_payment_estimate = requested_amount / duration_months * 1.08
    available_income = monthly_income - float(profile.monthly_debt_payment)
    payment_capacity = (monthly_payment_estimate / available_income * 100) if available_income > 0 else 200
    
    features = {
        # Démographiques
        'age': float(age),
        'dependents': int(profile.dependents),
        'marital_status': str(profile.marital_status),
        
        # Professionnels
        'employment_status': str(profile.employment_status),
        'monthly_income': float(monthly_income),
        'seniority_years': float(seniority_years),
        'sector': str(profile.sector) if profile.sector else '',
        
        # Financiers
        'debt_ratio': float(debt_ratio),
        'existing_credits': int(profile.existing_credits),
        'monthly_debt_payment': float(profile.monthly_debt_payment),
        'bank_seniority_months': int(profile.bank_seniority_months),
        'available_income': float(available_income),
        'payment_capacity': float(payment_capacity),
        
        # Demande
        'requested_amount': float(requested_amount),
        'duration_months': int(duration_months),
        'loan_to_income_ratio': float(loan_to_income_ratio),
        'amount_to_annual_income': float(amount_to_annual_income),
        'credit_type': str(demand.credit_type),
        
        # Historique
        'total_payments': int(payment_stats['total']),
        'late_payments': int(payment_stats['late']),
        'default_payments': int(payment_stats['default']),
        'avg_days_late': float(payment_stats['avg_days_late']),
        'on_time_rate': float(payment_stats['on_time_rate']),
        
        # Comportement bancaire
        'avg_balance': float(transaction_stats['avg_balance']),
        'total_credits': float(transaction_stats['total_credits']),
        'total_debits': float(transaction_stats['total_debits']),
        'transaction_count': int(transaction_stats['transaction_count']),
    }
    
    return features


def compute_advanced_score(features):
    """Calcul AVANCÉ du score (0-1000) avec pondérations réalistes"""
    
    score = 500
    
    # REVENUS ET STABILITÉ (30% du score)
    income = features['monthly_income']
    if income >= 1000000:
        score += 150
    elif income >= 500000:
        score += 120
    elif income >= 300000:
        score += 90
    elif income >= 150000:
        score += 60
    elif income >= 75000:
        score += 30
    else:
        score -= 50
    
    # Ancienneté emploi
    seniority = features['seniority_years']
    if seniority >= 10:
        score += 80
    elif seniority >= 5:
        score += 60
    elif seniority >= 3:
        score += 40
    elif seniority >= 1:
        score += 20
    else:
        score -= 30
    
    # Statut emploi
    if features['employment_status'] == 'CIVIL_SERVANT':
        score += 50
    elif features['employment_status'] == 'EMPLOYEE':
        score += 30
    elif features['employment_status'] == 'SELF_EMPLOYED':
        score += 10
    else:
        score -= 100
    
    # ENDETTEMENT (25% du score)
    debt_ratio = features['debt_ratio']
    if debt_ratio < 15:
        score += 125
    elif debt_ratio < 25:
        score += 100
    elif debt_ratio < 33:
        score += 50
    elif debt_ratio < 40:
        score -= 50
    elif debt_ratio < 50:
        score -= 100
    else:
        score -= 200
    
    # Capacité de paiement
    payment_capacity = features['payment_capacity']
    if payment_capacity < 20:
        score += 80
    elif payment_capacity < 30:
        score += 50
    elif payment_capacity < 40:
        score += 20
    elif payment_capacity < 60:
        score -= 30
    else:
        score -= 100
    
    # HISTORIQUE PAIEMENTS (30% du score)
    late_payments = features['late_payments']
    default_payments = features['default_payments']
    total_payments = features['total_payments']
    on_time_rate = features['on_time_rate']
    
    if default_payments >= 3:
        score -= 400
    elif default_payments == 2:
        score -= 300
    elif default_payments == 1:
        score -= 200
    
    if total_payments > 0:
        if on_time_rate >= 95:
            score += 150
        elif on_time_rate >= 85:
            score += 100
        elif on_time_rate >= 75:
            score += 50
        elif on_time_rate >= 60:
            score -= 50
        else:
            score -= 150
    else:
        score -= 50
    
    avg_days_late = features['avg_days_late']
    if avg_days_late > 30:
        score -= 100
    elif avg_days_late > 15:
        score -= 50
    elif avg_days_late > 7:
        score -= 20
    
    # ANCIENNETÉ BANQUE (10% du score)
    bank_seniority = features['bank_seniority_months']
    if bank_seniority >= 60:
        score += 60
    elif bank_seniority >= 36:
        score += 45
    elif bank_seniority >= 24:
        score += 30
    elif bank_seniority >= 12:
        score += 15
    else:
        score -= 20
    
    # CARACTÉRISTIQUES DU PRÊT (5% du score)
    loan_to_income = features['loan_to_income_ratio']
    if loan_to_income < 0.2:
        score += 40
    elif loan_to_income < 0.4:
        score += 20
    elif loan_to_income < 0.6:
        score += 0
    elif loan_to_income < 0.8:
        score -= 30
    else:
        score -= 80
    
    amount_to_annual = features['amount_to_annual_income']
    if amount_to_annual < 0.5:
        score += 30
    elif amount_to_annual < 1:
        score += 15
    elif amount_to_annual < 2:
        score += 0
    elif amount_to_annual < 4:
        score -= 40
    else:
        score -= 100
    
    if features['credit_type'] == 'REAL_ESTATE':
        score += 20
    elif features['credit_type'] == 'AUTO':
        score += 10
    
    # COMPORTEMENT BANCAIRE
    avg_balance = features['avg_balance']
    if avg_balance > 1000000:
        score += 40
    elif avg_balance > 500000:
        score += 25
    elif avg_balance > 200000:
        score += 15
    
    # ÂGE
    age = features['age']
    if 30 <= age <= 50:
        score += 20
    elif 25 <= age < 30 or 50 < age <= 55:
        score += 10
    elif age < 25:
        score -= 30
    elif age > 60:
        score -= 40
    
    # CHARGES FAMILIALES
    dependents = features['dependents']
    if dependents == 0:
        score += 10
    elif dependents <= 2:
        score += 0
    elif dependents <= 4:
        score -= 20
    else:
        score -= 40
    
    score = max(0, min(1000, int(score)))
    
    return score


def determine_risk_level(score):
    """Détermination du niveau de risque"""
    if score >= 750:
        return 'LOW'
    elif score >= 550:
        return 'MEDIUM'
    elif score >= 350:
        return 'HIGH'
    else:
        return 'VERY_HIGH'


def identify_factors(features, score):
    """Identification DÉTAILLÉE des facteurs positifs et négatifs"""
    
    positive = []
    negative = []
    
    income = features['monthly_income']
    if income >= 500000:
        positive.append({
            'factor': 'Revenu mensuel très élevé',
            'value': f"{income:,.0f} FCFA",
            'impact': 120
        })
    elif income >= 300000:
        positive.append({
            'factor': 'Bon revenu mensuel',
            'value': f"{income:,.0f} FCFA",
            'impact': 90
        })
    elif income < 100000:
        negative.append({
            'factor': 'Revenu mensuel insuffisant',
            'value': f"{income:,.0f} FCFA",
            'impact': -100
        })
    
    seniority = features['seniority_years']
    if seniority >= 5:
        positive.append({
            'factor': 'Excellente stabilité professionnelle',
            'value': f"{seniority:.1f} années",
            'impact': 60
        })
    elif seniority < 1:
        negative.append({
            'factor': 'Ancienneté professionnelle faible',
            'value': f"{seniority:.1f} année(s)",
            'impact': -80
        })
    
    debt_ratio = features['debt_ratio']
    if debt_ratio < 25:
        positive.append({
            'factor': 'Excellent taux d\'endettement',
            'value': f"{debt_ratio:.1f}%",
            'impact': 100
        })
    elif debt_ratio > 40:
        negative.append({
            'factor': 'Taux d\'endettement très élevé',
            'value': f"{debt_ratio:.1f}%",
            'impact': -200
        })
    elif debt_ratio > 33:
        negative.append({
            'factor': 'Taux d\'endettement élevé',
            'value': f"{debt_ratio:.1f}%",
            'impact': -50
        })
    
    on_time_rate = features['on_time_rate']
    total_payments = features['total_payments']
    
    if total_payments > 0:
        if on_time_rate >= 95:
            positive.append({
                'factor': 'Excellent historique de paiements',
                'value': f"{on_time_rate:.1f}% à temps ({total_payments} paiements)",
                'impact': 150
            })
        elif on_time_rate < 75:
            negative.append({
                'factor': 'Historique de retards fréquents',
                'value': f"{on_time_rate:.1f}% à temps",
                'impact': -150
            })
    
    defaults = features['default_payments']
    if defaults > 0:
        negative.append({
            'factor': 'Historique de défauts de paiement',
            'value': f"{defaults} défaut(s)",
            'impact': -defaults * 200
        })
    
    bank_seniority = features['bank_seniority_months']
    if bank_seniority >= 36:
        positive.append({
            'factor': 'Client fidèle de longue date',
            'value': f"{bank_seniority} mois ({bank_seniority//12} ans)",
            'impact': 45
        })
    elif bank_seniority < 12:
        negative.append({
            'factor': 'Relation bancaire récente',
            'value': f"{bank_seniority} mois",
            'impact': -20
        })
    
    payment_capacity = features['payment_capacity']
    if payment_capacity < 30:
        positive.append({
            'factor': 'Excellente capacité de remboursement',
            'value': f"{payment_capacity:.1f}% du revenu disponible",
            'impact': 50
        })
    elif payment_capacity > 60:
        negative.append({
            'factor': 'Capacité de remboursement limitée',
            'value': f"{payment_capacity:.1f}% du revenu disponible",
            'impact': -100
        })
    
    if features['employment_status'] == 'CIVIL_SERVANT':
        positive.append({
            'factor': 'Statut fonctionnaire (stabilité)',
            'value': 'Fonctionnaire',
            'impact': 50
        })
    
    avg_balance = features['avg_balance']
    if avg_balance > 500000:
        positive.append({
            'factor': 'Solde bancaire confortable',
            'value': f"{avg_balance:,.0f} FCFA en moyenne",
            'impact': 25
        })
    
    return positive, negative


def generate_recommendation(score, features):
    """Génération de la recommandation IA"""
    
    confidence = 70.0
    
    has_defaults = features['default_payments'] > 0
    high_debt = features['debt_ratio'] > 50
    low_income = features['monthly_income'] < 75000
    
    if score >= 800 and not has_defaults:
        recommendation = 'AUTO_APPROVE'
        confidence = 95.0
    elif score >= 700 and not has_defaults and not high_debt:
        recommendation = 'MANUAL_REVIEW'
        confidence = 85.0
    elif score >= 550 and not has_defaults:
        recommendation = 'MANUAL_REVIEW'
        confidence = 75.0
    elif score < 400 or has_defaults >= 2 or high_debt:
        recommendation = 'AUTO_REJECT'
        confidence = 90.0
    else:
        recommendation = 'MANUAL_REVIEW'
        confidence = 65.0
    
    return recommendation, confidence


def simulate_shap_values(features):
    """Simulation réaliste des valeurs SHAP"""
    
    shap = {}
    
    if features['monthly_income'] > 300000:
        shap['monthly_income'] = int(np.random.randint(80, 150))
    else:
        shap['monthly_income'] = int(np.random.randint(-80, 40))
    
    if features['debt_ratio'] > 40:
        shap['debt_ratio'] = int(np.random.randint(-200, -100))
    else:
        shap['debt_ratio'] = int(np.random.randint(50, 120))
    
    if features['seniority_years'] > 5:
        shap['seniority_years'] = int(np.random.randint(40, 80))
    else:
        shap['seniority_years'] = int(np.random.randint(-40, 30))
    
    if features['late_payments'] > 0:
        shap['payment_history'] = int(np.random.randint(-250, -80))
    else:
        shap['payment_history'] = int(np.random.randint(100, 200))
    
    shap['bank_seniority'] = int(np.random.randint(10, 50))
    
    return shap


def get_payment_statistics(client):
    """Statistiques COMPLÈTES de l'historique de paiements"""
    
    payments = PaymentHistory.objects.filter(client=client)
    total = payments.count()
    
    if total == 0:
        return {
            'total': 0,
            'late': 0,
            'default': 0,
            'avg_days_late': 0.0,
            'on_time_rate': 0.0,
        }
    
    late = payments.filter(status='LATE').count()
    defaults = payments.filter(status='DEFAULT').count()
    on_time = payments.filter(status='ON_TIME').count()
    avg_days = payments.aggregate(Avg('days_late'))['days_late__avg']
    
    return {
        'total': total,
        'late': late,
        'default': defaults,
        'avg_days_late': float(avg_days) if avg_days else 0.0,
        'on_time_rate': float((on_time / total * 100)) if total > 0 else 0.0,
    }


def get_transaction_statistics(client):
    """Statistiques COMPLÈTES des transactions bancaires"""
    
    transactions = Transaction.objects.filter(client=client)
    
    avg_bal = transactions.aggregate(Avg('balance_after'))['balance_after__avg']
    total_cred = transactions.filter(transaction_type='CREDIT').aggregate(Sum('amount'))['amount__sum']
    total_deb = transactions.filter(transaction_type='DEBIT').aggregate(Sum('amount'))['amount__sum']
    
    return {
        'avg_balance': float(avg_bal) if avg_bal else 0.0,
        'total_credits': float(total_cred) if total_cred else 0.0,
        'total_debits': float(total_deb) if total_deb else 0.0,
        'transaction_count': transactions.count(),
    }