import numpy as np
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Sum
from .models import CreditScore, PaymentHistory, Transaction

def calculate_score(demand):
    """Calcul du score de crédit pour une demande"""
    
    client = demand.client
    profile = client.client_profile
    
    # Extraction des features
    features = extract_features(client, profile, demand)
    
    # Calcul du score (algorithme simplifié pour MVP)
    score_value = compute_score_value(features)
    
    # Détermination du niveau de risque
    risk_level = determine_risk_level(score_value)
    
    # Identification des facteurs
    factors_positive, factors_negative = identify_factors(features, score_value)
    
    # Recommandation IA
    ai_recommendation, confidence = generate_recommendation(score_value, features)
    
    # Calcul SHAP values (simulé pour MVP)
    shap_values = simulate_shap_values(features)
    
    # Sauvegarde du score
    score, created = CreditScore.objects.update_or_create(
        demand=demand,
        defaults={
            'score_value': score_value,
            'risk_level': risk_level,
            'factors_positive': factors_positive,
            'factors_negative': factors_negative,
            'model_version': 'v1.0-mvp',
            'features_used': features,
            'shap_values': shap_values,
            'ai_recommendation': ai_recommendation,
            'confidence_level': confidence,
        }
    )
    
    # Mise à jour du statut de la demande
    if ai_recommendation == 'AUTO_APPROVE':
        demand.status = 'APPROVED'
    elif ai_recommendation == 'AUTO_REJECT':
        demand.status = 'REJECTED'
    else:
        demand.status = 'PENDING_ANALYST'
    
    demand.save()
    
    return score


def extract_features(client, profile, demand):
    """Extraction des features pour le scoring"""
    
    # Features profil
    age = (datetime.now().date() - profile.birth_date).days / 365.25
    debt_ratio = float(profile.debt_ratio)
    monthly_income = float(profile.monthly_income)
    seniority_years = float(profile.seniority_years)
    
    # Features demande
    requested_amount = float(demand.amount)
    duration_months = demand.duration_months
    loan_to_income = (requested_amount / duration_months) / monthly_income if monthly_income > 0 else 0
    
    # Historique paiements
    payment_stats = get_payment_statistics(client)
    
    # Transactions bancaires
    transaction_stats = get_transaction_statistics(client)
    
    features = {
        # Démographiques
        'age': age,
        'dependents': profile.dependents,
        'marital_status': profile.marital_status,
        
        # Professionnels
        'employment_status': profile.employment_status,
        'monthly_income': monthly_income,
        'seniority_years': seniority_years,
        'sector': profile.sector,
        
        # Financiers
        'debt_ratio': debt_ratio,
        'existing_credits': profile.existing_credits,
        'monthly_debt_payment': float(profile.monthly_debt_payment),
        'bank_seniority_months': profile.bank_seniority_months,
        
        # Demande
        'requested_amount': requested_amount,
        'duration_months': duration_months,
        'loan_to_income': loan_to_income,
        'credit_type': demand.credit_type,
        
        # Historique
        'total_payments': payment_stats['total'],
        'late_payments': payment_stats['late'],
        'default_payments': payment_stats['default'],
        'avg_days_late': payment_stats['avg_days_late'],
        
        # Comportement bancaire
        'avg_balance': transaction_stats['avg_balance'],
        'total_credits': transaction_stats['total_credits'],
        'total_debits': transaction_stats['total_debits'],
    }
    
    return features


def compute_score_value(features):
    """Calcul du score (0-1000) - Algorithme simplifié"""
    
    score = 500  # Base
    
    # Revenus (max +200 points)
    income = features['monthly_income']
    if income >= 500000:
        score += 200
    elif income >= 300000:
        score += 150
    elif income >= 150000:
        score += 100
    elif income >= 75000:
        score += 50
    
    # Ancienneté emploi (max +100 points)
    seniority = features['seniority_years']
    score += min(seniority * 20, 100)
    
    # Taux d'endettement (max +150 points ou -200)
    debt_ratio = features['debt_ratio']
    if debt_ratio < 20:
        score += 150
    elif debt_ratio < 33:
        score += 100
    elif debt_ratio < 40:
        score += 0
    else:
        score -= 200
    
    # Historique paiements (max +200 ou -300)
    late_payments = features['late_payments']
    default_payments = features['default_payments']
    
    if default_payments > 0:
        score -= 300
    elif late_payments == 0:
        score += 200
    elif late_payments <= 2:
        score += 100
    else:
        score -= late_payments * 50
    
    # Ancienneté banque (max +50 points)
    bank_seniority = features['bank_seniority_months']
    score += min(bank_seniority / 2, 50)
    
    # Ratio prêt/revenu (max +100 ou -150)
    loan_to_income = features['loan_to_income']
    if loan_to_income < 0.3:
        score += 100
    elif loan_to_income < 0.5:
        score += 50
    elif loan_to_income > 0.8:
        score -= 150
    
    # Limiter entre 0 et 1000
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
    """Identification des facteurs positifs et négatifs"""
    
    positive = []
    negative = []
    
    # Revenus
    if features['monthly_income'] >= 300000:
        positive.append({
            'factor': 'Revenu mensuel élevé',
            'value': f"{features['monthly_income']:,.0f} FCFA",
            'impact': 150
        })
    elif features['monthly_income'] < 100000:
        negative.append({
            'factor': 'Revenu mensuel faible',
            'value': f"{features['monthly_income']:,.0f} FCFA",
            'impact': -100
        })
    
    # Ancienneté
    if features['seniority_years'] >= 5:
        positive.append({
            'factor': 'Ancienneté professionnelle solide',
            'value': f"{features['seniority_years']} années",
            'impact': 100
        })
    elif features['seniority_years'] < 1:
        negative.append({
            'factor': 'Ancienneté professionnelle faible',
            'value': f"{features['seniority_years']} année(s)",
            'impact': -80
        })
    
    # Endettement
    if features['debt_ratio'] < 20:
        positive.append({
            'factor': 'Faible taux d\'endettement',
            'value': f"{features['debt_ratio']:.1f}%",
            'impact': 150
        })
    elif features['debt_ratio'] > 40:
        negative.append({
            'factor': 'Taux d\'endettement élevé',
            'value': f"{features['debt_ratio']:.1f}%",
            'impact': -200
        })
    
    # Historique paiements
    if features['late_payments'] == 0 and features['total_payments'] > 0:
        positive.append({
            'factor': 'Aucun retard de paiement',
            'value': f"{features['total_payments']} paiements à temps",
            'impact': 200
        })
    elif features['late_payments'] > 0:
        negative.append({
            'factor': 'Retards de paiement',
            'value': f"{features['late_payments']} retard(s)",
            'impact': -features['late_payments'] * 50
        })
    
    if features['default_payments'] > 0:
        negative.append({
            'factor': 'Historique de défaut',
            'value': f"{features['default_payments']} défaut(s)",
            'impact': -300
        })
    
    # Ancienneté banque
    if features['bank_seniority_months'] >= 24:
        positive.append({
            'factor': 'Client fidèle de la banque',
            'value': f"{features['bank_seniority_months']} mois",
            'impact': 50
        })
    
    return positive, negative


def generate_recommendation(score, features):
    """Génération de la recommandation IA"""
    
    confidence = 75.0  # Base
    
    if score >= 800:
        recommendation = 'AUTO_APPROVE'
        confidence = 95.0
    elif score >= 650 and features['default_payments'] == 0:
        recommendation = 'MANUAL_REVIEW'
        confidence = 80.0
    elif score < 400:
        recommendation = 'AUTO_REJECT'
        confidence = 90.0
    else:
        recommendation = 'MANUAL_REVIEW'
        confidence = 70.0
    
    return recommendation, confidence


def simulate_shap_values(features):
    """Simulation des valeurs SHAP pour explicabilité"""
    
    # Contributions simulées (positif = augmente le score)
    shap = {
        'monthly_income': np.random.randint(50, 200) if features['monthly_income'] > 200000 else np.random.randint(-100, 50),
        'debt_ratio': np.random.randint(-200, -50) if features['debt_ratio'] > 40 else np.random.randint(50, 150),
        'seniority_years': np.random.randint(30, 100) if features['seniority_years'] > 3 else np.random.randint(-50, 30),
        'late_payments': np.random.randint(-250, -100) if features['late_payments'] > 0 else np.random.randint(100, 200),
        'bank_seniority_months': np.random.randint(20, 50) if features['bank_seniority_months'] > 12 else np.random.randint(-20, 20),
    }
    
    return {k: int(v) for k, v in shap.items()}


def get_payment_statistics(client):
    """Statistiques de l'historique de paiements"""
    
    payments = PaymentHistory.objects.filter(client=client)
    
    return {
        'total': payments.count(),
        'late': payments.filter(status='LATE').count(),
        'default': payments.filter(status='DEFAULT').count(),
        'avg_days_late': payments.aggregate(Avg('days_late'))['days_late__avg'] or 0,
    }


def get_transaction_statistics(client):
    """Statistiques des transactions bancaires"""
    
    transactions = Transaction.objects.filter(client=client)
    
    return {
        'avg_balance': transactions.aggregate(Avg('balance_after'))['balance_after__avg'] or 0,
        'total_credits': transactions.filter(transaction_type='CREDIT').aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_debits': transactions.filter(transaction_type='DEBIT').aggregate(Sum('amount'))['amount__sum'] or 0,
    }