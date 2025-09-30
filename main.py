from sql_manager import SQLManager


class SalesManager:
    def __init__(self):
        self.db = SQLManager()

    def add_sale(self, amount, sale_type="sale"):
        self.db.add_sale(amount, sale_type)

    def add_presentation(self, amount, sale_type="presentation"):
        self.db.add_sale(amount, sale_type)

    def edit_record(self, id, new_date=None, new_amount=None, new_sale_type=None):
        self.db.update_sale(id, new_date, new_amount, new_sale_type)

    def delete_sale(self, id):
        self.db.delete_sale(id)

    def display_table(self):
        self.db.fetch_all_sales()


app = SalesManager()


def display_menu():
    print("Welcome to Sales Commission Tracker!")
    app.display_table()
    print("Choose an option ('q' to quit): ")
    print("1. Add new sale.")
    print("2. Add new presentation.")
    print("3. Edit record.")
    print("4. Delete record.")


def add_new_sale():
    amount = input("Enter the sale: ")
    app.add_sale(amount, sale_type="sale")


def add_new_presentation():
    amount = input("Enter the presentation: ")
    app.add_sale(amount, sale_type="presentation")


while True:

    display_menu()
    choice = input("Type here: ").lower()
    if choice == "q":
        break
    elif choice == "1":
        add_new_sale()
    elif choice == "2":
        add_new_presentation()
    elif choice == "3":
        id = int(input("Enter a valid id: "))
        new_date = input("Enter a new date (YYYY-MM-DD) or ENTER to skip: ")
        new_amount = input("Enter a new value or ENTER to skip: ")
        new_type = input("Enter a new type or ENTER to skip: ")
        app.edit_record(id, new_date or None, new_amount or None, new_type or None)
    elif choice == "4":
        id = input("Enter a valid id: ")
        app.delete_sale(id)
    else:
        print("Invalid input")
