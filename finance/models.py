from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.urls import reverse


class Sale(models.Model):
    class PaymentChoices(models.TextChoices):
        TRANSFER = "TR", "Transfer"
        CASH_THAI_BAHT = "THB", "Thai Baht"
        CASH_US_DOLLAR = "USD", "US Dollar"
        CARD = "CARD", "Card"
        GUIDE_CREDIT = "GC", "Guide Credit"

    # max_digits include decimal_places, so choose wisely
    sale_amount = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    payment_type = models.CharField(
        max_length=4,
        choices=PaymentChoices.choices,
        default=PaymentChoices.CASH_THAI_BAHT,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    salesman = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sales"
    )

    class Meta:
        ordering = ["-created_at"]

    def get_absolute_url(self):
        return reverse("sale_detail", kwargs={"pk": self.pk})

    def __str__(self) -> str:
        return f"{self.sale_amount}, {self.payment_type}"


class Comment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="comments")
    comment = models.CharField(max_length=140)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )

    def __str__(self):
        return self.comment

    def get_absolute_url(self):
        return reverse("sale_detail", kwargs={"pk": self.sale.pk})


class Presentation(models.Model):
    presenter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="presentations"
    )

    group_sales_total = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )

    group_identifier = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def get_absolute_url(self):
        return reverse("presentation_detail", kwargs={"pk": self.pk})

    def __str__(self) -> str:
        return f"Group identifier: {self.group_identifier}, sales total {self.group_sales_total}"