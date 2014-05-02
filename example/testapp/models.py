from django.db import models

class Report(models.Model):
    title = models.CharField(max_length=100, default='untitled')
    message = models.TextField(max_length=2048, default='')
    status = models.IntegerField(default=7)