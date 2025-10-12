# core/exceptions.py
from rest_framework.exceptions import APIException

class InsufficientScoreException(APIException):
    status_code = 400
    default_detail = 'Score insuffisant pour ce type de crédit'
    default_code = 'insufficient_score'

class InvalidDemandStatusException(APIException):
    status_code = 400
    default_detail = 'Statut de la demande invalide pour cette action'
    default_code = 'invalid_status'

class DocumentUploadException(APIException):
    status_code = 400
    default_detail = 'Erreur lors de l\'upload du document'
    default_code = 'upload_error'