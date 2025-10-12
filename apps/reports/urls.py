# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet, 
    DashboardViewSet,
    dashboard_stats_view,
    recent_activity_view
)

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'dashboards', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('stats/', dashboard_stats_view, name='dashboard-stats'),
    path('activity/', recent_activity_view, name='recent-activity'),
    path('', include(router.urls)),
]