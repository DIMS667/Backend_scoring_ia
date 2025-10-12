"""
Moteur d'évaluation des règles métier
"""
from datetime import datetime
from decimal import Decimal
from .models import BusinessRule, RuleEvaluation, CreditProduct

def evaluate_all_rules(demand):
    """Évalue toutes les règles actives pour une demande"""
    
    client = demand.client
    profile = client.client_profile
    
    # Récupérer toutes les règles actives
    rules = BusinessRule.objects.filter(is_active=True).order_by('-priority')
    
    # Filtrer par type de crédit si spécifié
    applicable_rules = []
    for rule in rules:
        if not rule.credit_type or rule.credit_type == demand.credit_type:
            applicable_rules.append(rule)
    
    results = []
    all_passed = True
    
    for rule in applicable_rules:
        result = evaluate_single_rule(rule, demand, profile)
        
        # Sauvegarder l'évaluation
        evaluation = RuleEvaluation.objects.create(
            demand=demand,
            rule=rule,
            passed=result['passed'],
            computed_value=result.get('computed_value'),
            message=result['message']
        )
        
        results.append(evaluation)
        
        if not result['passed']:
            all_passed = False
    
    return {
        'all_passed': all_passed,
        'evaluations': results,
        'summary': generate_evaluation_summary(results)
    }


def evaluate_single_rule(rule, demand, profile):
    """Évalue une règle spécifique"""
    
    rule_type = rule.rule_type
    
    # Dispatcher vers la fonction appropriée
    if rule_type == 'AGE_LIMIT':
        return evaluate_age_rule(rule, profile)
    elif rule_type == 'INCOME_REQUIREMENT':
        return evaluate_income_rule(rule, profile)
    elif rule_type == 'DEBT_RATIO':
        return evaluate_debt_ratio_rule(rule, profile)
    elif rule_type == 'AMOUNT_LIMIT':
        return evaluate_amount_rule(rule, demand)
    elif rule_type == 'DURATION_LIMIT':
        return evaluate_duration_rule(rule, demand)
    elif rule_type == 'SCORING_THRESHOLD':
        return evaluate_scoring_rule(rule, demand)
    else:
        return {
            'passed': True,
            'message': f"Règle {rule.name} non implémentée"
        }


def evaluate_age_rule(rule, profile):
    """Évalue la règle d'âge"""
    age = (datetime.now().date() - profile.birth_date).days / 365.25
    condition = rule.condition
    
    min_age = condition.get('min_age', 21)
    max_age = condition.get('max_age', 65)
    
    passed = min_age <= age <= max_age
    
    return {
        'passed': passed,
        'computed_value': Decimal(age),
        'message': f"Âge: {age:.0f} ans (requis: {min_age}-{max_age} ans)" if passed else f"Âge non conforme: {age:.0f} ans (requis: {min_age}-{max_age} ans)"
    }


def evaluate_income_rule(rule, profile):
    """Évalue la règle de revenu minimum"""
    income = profile.monthly_income
    min_income = rule.threshold_value or rule.condition.get('min_income', 0)
    
    passed = income >= min_income
    
    return {
        'passed': passed,
        'computed_value': income,
        'message': f"Revenu: {income:,.0f} FCFA (requis: ≥ {min_income:,.0f} FCFA)" if passed else f"Revenu insuffisant: {income:,.0f} FCFA (requis: ≥ {min_income:,.0f} FCFA)"
    }


def evaluate_debt_ratio_rule(rule, profile):
    """Évalue la règle de taux d'endettement"""
    debt_ratio = profile.debt_ratio
    max_ratio = float(rule.threshold_value or rule.condition.get('max_ratio', 40))
    
    passed = debt_ratio <= max_ratio
    
    return {
        'passed': passed,
        'computed_value': Decimal(debt_ratio),
        'message': f"Taux d'endettement: {debt_ratio:.1f}% (max: {max_ratio:.1f}%)" if passed else f"Taux d'endettement trop élevé: {debt_ratio:.1f}% (max: {max_ratio:.1f}%)"
    }


def evaluate_amount_rule(rule, demand):
    """Évalue la règle de montant"""
    amount = demand.amount
    condition = rule.condition
    
    min_amount = Decimal(condition.get('min_amount', 0))
    max_amount = Decimal(condition.get('max_amount', 999999999))
    
    passed = min_amount <= amount <= max_amount
    
    return {
        'passed': passed,
        'computed_value': amount,
        'message': f"Montant: {amount:,.0f} FCFA (plage: {min_amount:,.0f} - {max_amount:,.0f} FCFA)" if passed else f"Montant non conforme: {amount:,.0f} FCFA (plage: {min_amount:,.0f} - {max_amount:,.0f} FCFA)"
    }


def evaluate_duration_rule(rule, demand):
    """Évalue la règle de durée"""
    duration = demand.duration_months
    condition = rule.condition
    
    min_duration = condition.get('min_duration', 0)
    max_duration = condition.get('max_duration', 999)
    
    passed = min_duration <= duration <= max_duration
    
    return {
        'passed': passed,
        'computed_value': Decimal(duration),
        'message': f"Durée: {duration} mois (plage: {min_duration}-{max_duration} mois)" if passed else f"Durée non conforme: {duration} mois (plage: {min_duration}-{max_duration} mois)"
    }


def evaluate_scoring_rule(rule, demand):
    """Évalue la règle de score minimum"""
    try:
        score = demand.score.score_value
        min_score = int(rule.threshold_value or rule.condition.get('min_score', 400))
        
        passed = score >= min_score
        
        return {
            'passed': passed,
            'computed_value': Decimal(score),
            'message': f"Score: {score}/1000 (requis: ≥ {min_score})" if passed else f"Score insuffisant: {score}/1000 (requis: ≥ {min_score})"
        }
    except:
        return {
            'passed': False,
            'message': "Score non calculé"
        }


def generate_evaluation_summary(evaluations):
    """Génère un résumé des évaluations"""
    total = len(evaluations)
    passed = sum(1 for e in evaluations if e.passed)
    failed = total - passed
    
    failed_rules = [e for e in evaluations if not e.passed]
    
    return {
        'total_rules': total,
        'passed': passed,
        'failed': failed,
        'failed_rules': [
            {
                'name': e.rule.name,
                'message': e.message
            }
            for e in failed_rules
        ]
    }


def check_product_eligibility(demand, product):
    """Vérifie l'éligibilité pour un produit spécifique"""
    profile = demand.client.client_profile
    
    checks = []
    
    # Montant
    if not (product.min_amount <= demand.amount <= product.max_amount):
        checks.append(f"Montant non conforme (plage: {product.min_amount:,.0f} - {product.max_amount:,.0f} FCFA)")
    
    # Durée
    if not (product.min_duration_months <= demand.duration_months <= product.max_duration_months):
        checks.append(f"Durée non conforme (plage: {product.min_duration_months}-{product.max_duration_months} mois)")
    
    # Revenu
    if profile.monthly_income < product.min_income_required:
        checks.append(f"Revenu insuffisant (requis: ≥ {product.min_income_required:,.0f} FCFA)")
    
    # Taux d'endettement
    if profile.debt_ratio > float(product.max_debt_ratio):
        checks.append(f"Taux d'endettement trop élevé (max: {product.max_debt_ratio}%)")
    
    # Score
    try:
        if demand.score.score_value < product.min_score_required:
            checks.append(f"Score insuffisant (requis: ≥ {product.min_score_required})")
    except:
        pass
    
    return {
        'eligible': len(checks) == 0,
        'issues': checks
    }