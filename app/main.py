from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
# Import db and the Sale model from your application package
from . import db
from .models import Sale

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/", methods=["GET", "POST"])
@login_required # All main sales logic requires a logged-in user
def index():
    now = datetime.now()
    
    if request.method == "POST":
        sale_amount = request.form["sale_amount"]
        sale_type = request.form["sale_type"]
        sale_date_str = request.form["sale_date"]

        try:
            sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d")
            
            # 1. Create the Sale object
            new_sale = Sale.create(sale_amount, sale_type)
            new_sale.sale_date = sale_date
            
            # 2. KEY CHANGE: TIE SALE TO THE CURRENT USER
            new_sale.user_id = current_user.id 
            
            db.session.add(new_sale)
            db.session.commit()
        except Exception as e:
            print(f"Error creating sale: {e}")
            db.session.rollback()
        
        return redirect(url_for("main.index"))

    # KEY CHANGE: Only fetch sales belonging to the current user
    sales = Sale.query.filter_by(user_id=current_user.id).order_by(Sale.sale_date.desc()).all()
    
    # Temporarily calculate totals here (See Model Adjustment below for better way)
    sales_total, presentations_total = Sale.get_sales_totals(now.year, now.month, user_id=current_user.id)
    
    return render_template(
        "index.html",
        sales=sales,
        sales_total=sales_total,
        presentations_total=presentations_total,
        datetime=datetime,
    )
    
@main_blueprint.route("/delete/<int:id>")
@login_required # Protect the route
def delete_sale(id):
    # KEY CHANGE: Fetch the sale AND check that the current user owns it
    sale_to_delete = Sale.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    try:
        db.session.delete(sale_to_delete)
        db.session.commit()
        return redirect(url_for("main.index"))
    except Exception as e:
        # A flash message would be better here than a simple string return
        return f"Error when deleting: {e}"


@main_blueprint.route("/update/<int:id>", methods=["GET", "POST"])
@login_required # Protect the route
def update_sale(id):
    # KEY CHANGE: Fetch the sale AND check that the current user owns it
    sale_to_update = Sale.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == "POST":
        try:
            sale_to_update.sale_date = datetime.strptime(
                request.form["sale_date"], "%Y-%m-%d"
            )
            sale_to_update.sale_amount = Sale.to_decimal(request.form["sale_amount"])
            sale_to_update.sale_type = request.form["sale_type"]

            # Recalculate commission (logic remains the same)
            sale_to_update.commission = Sale.calculate_commission(
                sale_to_update.sale_amount, sale_to_update.sale_type
            )

            db.session.commit()
            return redirect(url_for("main.index"))
        except Exception as e:
            return f"Error when updating: {e}"
    else:
        # Assuming you have an 'update.html' template
        return render_template("update.html", sale_to_update=sale_to_update)

@main_blueprint.route("/profile")
@login_required
def profile():
    return render_template("profile.html", name=current_user.name)
