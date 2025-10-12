from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreditDemandViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r'', CreditDemandViewSet, basename='demand')
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]