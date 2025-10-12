# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessRuleViewSet, RuleEvaluationViewSet, CreditProductViewSet

router = DefaultRouter()
router.register(r'rules', BusinessRuleViewSet, basename='rule')
router.register(r'evaluations', RuleEvaluationViewSet, basename='evaluation')
router.register(r'products', CreditProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]