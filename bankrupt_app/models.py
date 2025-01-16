from django.db import models

class IsBankrupt(models.Model):
    is_bankrupt = models.BooleanField(default=False)

    def __str__(self):
        return "Bank is bankrupt" if self.is_bankrupt else "Bank is not bankrupt"
