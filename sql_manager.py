import sqlite3
import decimal
from tabulate import tabulate
from decimal import Decimal, ROUND_HALF_UP


# Add this code at the top of your script, with your other imports.
# It tells sqlite3 how to handle Decimal objects.
def adapt_decimal(d):
    return str(d)


sqlite3.register_adapter(Decimal, adapt_decimal)

decimal.getcontext().prec = 28


class SQLManager:

    def __init__(self, db_path="sales.db"):
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
    def calculate_sale_commission_decimal(amount_decimal):
        return (amount_decimal * Decimal("0.02")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calculate_presentation_commission_decimal(amount_decimal):
        return (amount_decimal * Decimal("0.03")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def add_sale(self, amount, type):
        # Convert the string input to a Decimal object
        amount_decimal = SQLManager.to_decimal(amount)

        # Calculate commissions using Decimal for precision
        sale_commission = SQLManager.calculate_sale_commission_decimal(amount_decimal)
        presentation_commission = SQLManager.calculate_presentation_commission_decimal(
            amount_decimal
        )
        if type == "sale":
            insert_statement = (
                """INSERT INTO sales(amount, commission, type) VALUES (?, ?, ?);"""
            )
            data = (amount_decimal, sale_commission, type)
        elif type == "presentation":
            insert_statement = (
                """INSERT INTO sales(amount, commission, type) VALUES (?, ?, ?);"""
            )
            data = (amount_decimal, presentation_commission, type)
        else:
            print("Provide valid data.")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(insert_statement, data)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding sale: {e}")
        else:
            print("Sale added!")

    def update_sale(self, id, amount, type=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                update_statement = (
                    """UPDATE sales SET amount=?, commission=?, type=? WHERE id = ?;"""
                )
                amount_decimal = SQLManager.to_decimal(amount)
                sale_commission = SQLManager.calculate_sale_commission_decimal(
                    amount_decimal
                )
                presentation_commission = (
                    SQLManager.calculate_presentation_commission_decimal(amount_decimal)
                )

                if type is None:
                    # .execute returns pointer to the data (cursor points to data)
                    # .fetchone() returns found data in the convinient container (tuple)
                    stored_type = cursor.execute(
                        """SELECT type FROM sales WHERE id = ?""", (id,)
                    ).fetchone()
                    print("data found")
                    # check the value of the tuple(type,)
                    if stored_type[0] == "sale":
                        data = (amount, sale_commission, stored_type[0], id)
                        print("sale type found")
                    elif stored_type[0] == "presentation":
                        data = (amount, presentation_commission, stored_type[0], id)
                        print("presentation type found")
                    else:
                        print("No type found")
                        return
                elif type == "sale":
                    data = (amount, sale_commission, type, id)
                elif type == "presentation":
                    data = (amount, presentation_commission, type, id)

                cursor.execute(update_statement, data)
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
