# core/permissions.py
from rest_framework.permissions import BasePermission

class IsAgent(BasePermission):
    """Permission pour les agents uniquement"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'AGENT'

class IsClient(BasePermission):
    """Permission pour les clients uniquement"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'CLIENT'

class IsOwnerOrAgent(BasePermission):
    """Permission pour le propriétaire ou un agent"""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'AGENT':
            return True
        return obj.client == request.user