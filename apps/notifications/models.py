from django.db import models
from apps.accounts.models import User

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('DEMAND_SUBMITTED', 'Demande soumise'),
        ('DEMAND_APPROVED', 'Demande approuvée'),
        ('DEMAND_REJECTED', 'Demande rejetée'),
        ('COMMENT_ADDED', 'Commentaire ajouté'),
        ('DOCUMENT_UPLOADED', 'Document uploadé'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_notification_type_display()}"