from django.db import models

class Payment(models.Model):
    PROVIDERS = (
        ('flouci', 'Flouci'),
        ('konnect', 'Konnect'),
        ('stripe', 'Stripe'),
    )

    STATUS = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    provider = models.CharField(max_length=50, choices=PROVIDERS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    customer_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider} - {self.amount} - {self.status}"
