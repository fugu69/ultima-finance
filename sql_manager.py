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
        try:
            int_check = int(amount)
        except ValueError:
            print("Enter valid number")
        else:
            if int_check > 0:

                # Convert the string input to a Decimal object
                amount_decimal = SQLManager.to_decimal(amount)
                # Calculate commissions using Decimal for precision
                sale_commission = SQLManager.calculate_sale_commission_decimal(
                    amount_decimal
                )
                presentation_commission = (
                    SQLManager.calculate_presentation_commission_decimal(amount_decimal)
                )
                if type == "sale":
                    insert_statement = """INSERT INTO sales(amount, commission, type) VALUES (?, ?, ?);"""
                    data = (amount_decimal, sale_commission, type)
                elif type == "presentation":
                    insert_statement = """INSERT INTO sales(amount, commission, type) VALUES (?, ?, ?);"""
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
            else:
                print("Inter a positive integer")

    def update_sale(self, id, date=None, amount=None, type=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                updates = []
                values = []

                if date is not None:
                    updates.append("date=?")
                    values.append(date)

                if amount is not None:

                    amount_decimal = SQLManager.to_decimal(amount)

                    if type is None:
                        # .execute returns pointer to the data (cursor points to data)
                        # .fetchone() returns found data in the convinient container (tuple)
                        stored_type = cursor.execute(
                            """SELECT type FROM sales WHERE id = ?""", (id,)
                        ).fetchone()
                        print("data found")
                        # check the value of the tuple(type,)
                        if stored_type[0] == "sale":
                            sale_commission = (
                                SQLManager.calculate_sale_commission_decimal(
                                    amount_decimal
                                )
                            )
                            updates.append("commission=?")
                            values.append(sale_commission)
                            print("sale type found")
                        elif stored_type[0] == "presentation":
                            presentation_commission = (
                                SQLManager.calculate_presentation_commission_decimal(
                                    amount_decimal
                                )
                            )
                            updates.append("commission=?")
                            values.append(presentation_commission)
                            print("presentation type found")
                        else:
                            print("No type found")
                            return
                    elif type == "sale":
                        sale_commission = SQLManager.calculate_sale_commission_decimal(
                            amount_decimal
                        )
                        updates.append("commission=?")
                        values.append(sale_commission)
                        print("sale type found")
                    elif type == "presentation":
                        presentation_commission = (
                            SQLManager.calculate_presentation_commission_decimal(
                                amount_decimal
                            )
                        )
                        updates.append("commission=?")
                        values.append(presentation_commission)
                        print("presentation type found")
                    else:
                        print("Invalid type!")
                        return

                if type is not None:
                    if amount is not None:
                        amount_decimal = SQLManager.to_decimal(amount)
                        if type == "sale":
                            sale_commission = (
                                SQLManager.calculate_sale_commission_decimal(
                                    amount_decimal
                                )
                            )
                            updates.append("amount=?")
                            updates.append("type=?")
                            updates.append("commission=?")
                            values.append(amount)
                            values.append(type)
                            values.append(sale_commission)
                            print("sale type found")
                        elif type == "presentation":
                            presentation_commission = (
                                SQLManager.calculate_presentation_commission_decimal(
                                    amount_decimal
                                )
                            )
                            updates.append("amount=?")
                            updates.append("type=?")
                            updates.append("commission=?")
                            values.append(amount)
                            values.append(type)
                            values.append(presentation_commission)
                            print("presentation type found")
                        else:
                            print("Invalid type!")
                            return
                    elif amount is None:
                        stored_amount = cursor.execute(
                            """SELECT amount FROM sales WHERE id=?""", (id,)
                        ).fetchone()

                        if stored_amount[0]:
                            print("Amount found")
                            stored_amount_decimal = SQLManager.to_decimal(
                                stored_amount[0]
                            )
                            if type == "sale":
                                sale_commission = (
                                    SQLManager.calculate_sale_commission_decimal(
                                        stored_amount_decimal
                                    )
                                )
                                updates.append("type=?")
                                updates.append("commission=?")
                                values.append(type)
                                values.append(sale_commission)
                                print("sale type found")
                            elif type == "presentation":
                                presentation_commission = SQLManager.calculate_presentation_commission_decimal(
                                    stored_amount_decimal
                                )
                                updates.append("type=?")
                                updates.append("commission=?")
                                values.append(type)
                                values.append(presentation_commission)
                                print("presentation type found")
                            else:
                                print("Invalid type!")
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
