from django.db import models

class api(models.Model):
    api=models.CharField(max_length=100)
    count=models.IntegerField()