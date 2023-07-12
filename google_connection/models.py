from django.db import models


class User(models.Model):
    email = models.EmailField(unique=True)
    user_key = models.TextField()

    def __str__(self):
        return self.email
