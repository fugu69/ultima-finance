import sqlite3
import decimal
from tabulate import tabulate
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


# Add this code at the top of your script, with your other imports.
# It tells sqlite3 how to handle Decimal objects.
def adapt_decimal(d):
    return str(d)


sqlite3.register_adapter(Decimal, adapt_decimal)

decimal.getcontext().prec = 28


class SQLManager:

    def __init__(self, db_path="sales_october.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                sql_statements = [
                    """CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY,
                        date TEXT DEFAULT (DATE('now')),
                        amount NUMERIC,
                        type TEXT,
                        commission NUMERIC
                    );""",
                ]

                for statement in sql_statements:
                    cursor.execute(statement)
                    conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Failed to init database: {e}")
        else:
            print("Tables created")

    # Helper functions

    @staticmethod
    def to_decimal(amount):
        return Decimal(str(amount))

    @staticmethod
    def calculate_commission_decimal(amount_decimal, sale_type):
        if sale_type == "sale":
            return (amount_decimal * Decimal("0.02")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        elif sale_type == "presentation":
            return (amount_decimal * Decimal("0.03")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            raise ValueError(
                f"Invalid type '{sale_type}'. Cannot calculate commission."
            )

    def add_sale(self, amount, sale_type):
        try:
            amount_decimal = SQLManager.to_decimal(amount)
        except InvalidOperation:
            print("Enter valid number")
            return
        else:
            if amount_decimal > 0:

                # Convert the string input to a Decimal object
                amount_decimal = SQLManager.to_decimal(amount)
                # Calculate commissions using Decimal for precision
                commission = SQLManager.calculate_commission_decimal(
                    amount_decimal, sale_type
                )
                allowed_types = ["sale", "presentation"]

                if sale_type not in allowed_types:
                    print("Invalid type")
                    return

                updates = ["amount", "type", "commission"]
                values = [amount, sale_type, commission]

                try:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        sql = f"""INSERT INTO sales ({', '.join(updates)}) VALUES (?, ?, ?);"""
                        cursor.execute(sql, values)
                        conn.commit()
                except sqlite3.Error as e:
                    print(f"Error adding sale: {e}")
                else:
                    print("Sale added!")
            else:
                print("Inter a positive integer")

    def update_sale(self, id, date=None, amount=None, sale_type=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                updates = []
                values = []

                if date is not None:
                    updates.append("date=?")
                    values.append(date)

                if amount is not None or sale_type is not None:
                    stored_values = cursor.execute(
                        """SELECT amount, type FROM sales WHERE id=?""", (id,)
                    ).fetchone()

                    if stored_values:
                        stored_amount, stored_sale_type = stored_values
                    else:
                        print("No entry found")
                        return

                    new_amount = amount if amount is not None else stored_amount
                    new_amount_decimal = SQLManager.to_decimal(new_amount)
                    new_sale_type = (
                        sale_type if sale_type is not None else stored_sale_type
                    )
                    new_commission = SQLManager.calculate_commission_decimal(
                        new_amount_decimal, new_sale_type
                    )

                    updates.extend(["amount=?", "type=?", "commission=?"])
                    values.extend([new_amount, new_sale_type, new_commission])

                if not updates:
                    print("Nothing to commit")
                    return

                values.append(id)
                cursor.execute(
                    f"""UPDATE sales SET {', '.join(updates)} WHERE id=?""", values
                )
                conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Failed to update: {e}")

    def fetch_all_sales(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT * FROM sales;""")
                rows = cursor.fetchall()
                headers = ["id", "Date", "Amount", "Type", "Commission"]
                total_sales = sum(Decimal(row[2]) for row in rows)
                total_commission = sum(Decimal(row[4]) for row in rows)

                table_data = rows.copy()

                table_data.append(
                    (
                        "TOTAL",
                        "",
                        str(total_sales),
                        "",
                        str(total_commission),
                    )
                )

                print(
                    tabulate(
                        table_data, headers=headers, tablefmt="grid", floatfmt=".2f"
                    )
                )
        except FileNotFoundError:
            print("No records yet")

        except sqlite3.Error as e:
            print(f"Error fetching data: {e}")

    def delete_sale(self, id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""DELETE FROM sales WHERE id = ?""", (id,))
                conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Error deleting sale: {e}")
