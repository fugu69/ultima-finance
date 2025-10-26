from datetime import datetime, timezone
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, extract
from decimal import Decimal, ROUND_HALF_UP


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
db = SQLAlchemy(app)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    sale_amount = db.Column(db.Numeric(10, 2), nullable=False)
    sale_type = db.Column(db.String(50), nullable=False)
    commission = db.Column(db.Numeric(10, 2))

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
    def get_sales_totals(year, month):
        # Aggregate totals

        # fmt: off
        sales_total = (
            db.session.query(func.sum(Sale.sale_amount))
            .filter(Sale.sale_type == "sale")
            .filter(extract("year", Sale.sale_date) == year)
            .filter(extract("month", Sale.sale_date) == month)
            .scalar() or Decimal("0.00")
        )

        presentations_total = (
            db.session.query(func.sum(Sale.sale_amount))
            .filter(Sale.sale_type == "presentation")
            .filter(extract("year", Sale.sale_date) == year)
            .filter(extract("month", Sale.sale_date) == month)
            .scalar() or Decimal("0.00")
        )
        # fmt: on

        return (sales_total, presentations_total)

    def __repr__(self):
        return (
            f"<Sale id={self.id}, date={self.sale_date.isoformat()} "
            f"amount={self.sale_amount}, type={self.sale_type} "
            f"commission={self.commission}> "
        )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sale_amount = request.form["sale_amount"]
        sale_type = request.form["sale_type"]
        sale_date_str = request.form["sale_date"]

        try:
            sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d")
            new_sale = Sale.create(sale_amount, sale_type)
            new_sale.sale_date = sale_date
            db.session.add(new_sale)
            db.session.commit()
        except Exception as e:
            print("Error: ", e)
            db.session.rollback()

        return redirect(url_for("index"))

    now = datetime.now()
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    sales_total, presentations_total = Sale.get_sales_totals(now.year, now.month)
    return render_template(
        "index.html",
        sales=sales,
        sales_total=sales_total,
        presentations_total=presentations_total,
        datetime=datetime,
    )


@app.route("/delete/<int:id>")
def delete_sale(id):
    sale_to_delete = Sale.query.get_or_404(id)

    try:
        db.session.delete(sale_to_delete)
        db.session.commit()
        return redirect("/")
    except Exception as e:
        return f"Error when deleting: {e}"


@app.route("/update/<int:id>", methods=["GET", "POST"])
def update_sale(id):
    sale_to_update = Sale.query.get_or_404(id)
    if request.method == "POST":
        try:
            # Convert form inputs to proper types
            sale_to_update.sale_date = datetime.strptime(
                request.form["sale_date"], "%Y-%m-%d"
            )
            sale_to_update.sale_amount = Sale.to_decimal(request.form["sale_amount"])
            sale_to_update.sale_type = request.form["sale_type"]

            # Recalculate commission
            sale_to_update.commission = Sale.calculate_commission(
                sale_to_update.sale_amount, sale_to_update.sale_type
            )

            db.session.commit()
            return redirect("/")
        except Exception as e:
            return f"Error when updating: {e}"
    else:
        return render_template("update.html", sale_to_update=sale_to_update)


if __name__ == "__main__":
    app.run(debug=True)
