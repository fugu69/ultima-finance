from django.db import models


class Sale(models.Model):
    class PaymentChoices(models.TextChoices):
        TRANSFER = "TR", "Transfer"
        CASH_THAI_BAHT = "THB", "Thai Baht"
        CASH_US_DOLLAR = "USD", "US Dollar"
        CARD = "CARD", "Card"
        GUIDE_CREDIT = "GC", "Guide Credit"

    # max_digits include decimal_places, so choose wisely
    sale_amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_type = models.CharField(
        max_length=4, choices=PaymentChoices.choices,
        default=PaymentChoices.CASH_THAI_BAHT
    )

    def __str__(self) -> str:
        return f"{self.sale_amount}, {self.payment_type}"
