from . import db
from flask_login import UserMixin
from datetime import datetime, timezone
from sqlalchemy import func, extract
from decimal import Decimal, ROUND_HALF_UP


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)

    sales = db.relationship("Sale", back_populates="user", lazy=True)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    sale_amount = db.Column(db.Numeric(10, 2), nullable=False)
    sale_type = db.Column(db.String(50), nullable=False)
    commission = db.Column(db.Numeric(10, 2))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="sales")

    @staticmethod
    def to_decimal(value):
        """Safely convert string/float to Decimal(0.01 precision)."""
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_commission(amount_decimal, sale_type):
        """Return Decimal commission based on type."""
        rates = {"sale": Decimal("0.02"), "presentation": Decimal("0.03")}
        if sale_type not in rates:
            raise ValueError(
                f"Invalid type '{sale_type}'. Must be 'sale' or 'presentation'"
            )
        return (amount_decimal * rates[sale_type]).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @classmethod
    def create(cls, sale_amount, sale_type):
        """Factory-like method to create and return a Sale instance."""
        amount_decimal = cls.to_decimal(sale_amount)
        commission = cls.calculate_commission(amount_decimal, sale_type)
        return cls(
            sale_amount=amount_decimal, sale_type=sale_type, commission=commission
        )

    @staticmethod
    # KEY CHANGE: Add user_id parameter
    def get_sales_totals(year, month, user_id):
        # Base query to filter by user and date
        base_query = db.session.query(func.sum(Sale.sale_amount)).filter(
            extract("year", Sale.sale_date) == year,
            extract("month", Sale.sale_date) == month,
            Sale.user_id == user_id # KEY CHANGE: Filter by user_id
        )

        sales_total = (
            base_query.filter(Sale.sale_type == "sale")
            .scalar() or Decimal("0.00")
        )

        presentations_total = (
            base_query.filter(Sale.sale_type == "presentation")
            .scalar() or Decimal("0.00")
        )

        return (sales_total, presentations_total)

    def __repr__(self):
        return (
            f"<Sale id={self.id}, date={self.sale_date.isoformat()} "
            f"amount={self.sale_amount}, type={self.sale_type} "
            f"commission={self.commission}> "
        )
