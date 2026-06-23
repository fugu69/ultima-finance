from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


class CustomUser(AbstractUser):
    actual_start_date = models.DateField(null=True, blank=True)
    official_hire_date = models.DateField(null=True, blank=True)

    base_salary = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
