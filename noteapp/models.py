from django.db import models
from django.contrib.auth.models import User


class Note(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notes')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notes')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
