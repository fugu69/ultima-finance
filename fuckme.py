from sql_manager import SQLManager



class SalesManager:
    def __init__(self):
        self.db = SQLManager()

    def add_sale(self, amount, type="sale"):
        self.db.add_sale(amount, type)

    def add_presentation(self, amount, type="presentation"):
        self.db.add_sale(amount, type)

    def edit_record(self, id, new_date=None, new_amount=None, new_type=None):
        self.db.update_sale(id, new_date, new_amount, new_type)

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
    app.add_sale(amount, type="sale")


def add_new_presentation():
    amount = input("Enter the presentation: ")
    app.add_sale(amount, type="presentation")


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
        new_date = input("Enter a new date (YYYY-MM-DD) or ENTER to skip")
        new_amount = input("Enter a new value or ENTER to skip: ")
        new_type = input("Enter a new type or ENTER to skip")
        app.edit_record(id, new_date or None, new_amount or None, new_type or None)
    elif choice == "4":
        id = input("Enter a valid id: ")
        app.delete_sale(id)
    else:
        print("Invalid input")

# TO-DO:
# 1. Replace id with sale_id
# 2. Move menu into function and run if __main__
# 3. Convert data types in inputs and catch errors earlier
# 4. Ensure that float is used for amounts
# 5. Load data in memory and write when needed
# 5. _get_sale_by_id() to DRY
