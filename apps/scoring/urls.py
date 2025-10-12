from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreditScoreViewSet, PaymentHistoryViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'scores', CreditScoreViewSet, basename='score')
router.register(r'payment-history', PaymentHistoryViewSet, basename='payment-history')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]