# 🚀 Ultima Finance Project

## Project Overview

Ultima Finance is a sales tracking and management dashboard built with **Flask**, **SQLAlchemy**, and **PostgreSQL**. The application is containerized using **Docker** and **Docker Compose** to ensure a consistent, reproducible environment across development and deployment.

---

## 🛠️ Prerequisites

To run this project locally, you must have the following installed:

1.  **Git**
2.  **Docker** and **Docker Compose** (Docker Desktop is recommended)

---

## 📦 Getting Started

### 1. Clone the Repository

```bash
git clone [YOUR_REPO_URL]
cd ultima_finance_project
```

### 2. Configure Environment Variables

Create a file named .env in the project's root directory. This file holds secrets and database credentials.

``` Python
# .env (Example Configuration)

# --- Flask Secret Key ---
# IMPORTANT: Use a long, random value
SECRET_KEY=your_long_and_secure_secret_key

# --- PostgreSQL Connection Details ---
# These are used by Docker Compose to set up the 'db' service
POSTGRES_USER=app_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=sales_db

# Host for local bare-metal commands (Docker Compose overrides this to 'db')
DB_HOST=localhost
```

### 3. Build and Run the Stack

This command builds your Flask app image (using Dockerfile) and starts both the app and db services in the background.

``` bash
# Builds images and starts containers in detached mode
docker compose up -d --build
```

## Initial Setup and Database Migration

You must run Flask-Migrate inside the running container to create the PostgreSQL schema.

### 1. Apply Database Schema

Wait about 10-15 seconds for the db container to fully initialize, then run the migration command:

``` bash
# Executes 'flask db upgrade' inside the 'app' container
docker compose exec app flask db upgrade
```

### 2. Create an Admin User (Optional)

To create an initial admin account with a hashed password, access the Flask shell:

```bash
docker compose exec app flask shell
```

Inside the shell, run your Python code to create the User object and commit it.
``` Python
# 1. Imports
from app import db # Assuming 'app' is your package name
from app.models import User
from werkzeug.security import generate_password_hash 

# If you need to push the context (optional, shell often handles this)
# from app import create_app
# app = create_app()
# app.app_context().push()

# 2. Define Admin Credentials
admin_email = 'new.admin@example.com'
admin_password = 'YourNewSuperSecurePassword' # <-- CHOOSE A STRONG PASSWORD
admin_name = 'New Administrator'

# 3. Hash the Password
hashed_password = generate_password_hash(admin_password, method='sha256')

# 4. Create the User Object
new_admin = User(
    email=admin_email, 
    password=hashed_password, 
    name=admin_name, 
    is_admin=True  # <-- Sets the admin flag
)

# 5. Check if user exists, then add and commit
if User.query.filter_by(email=admin_email).first() is None:
    db.session.add(new_admin)
    db.session.commit()
    print(f"Successfully created admin user: {new_admin.email}")
else:
    print(f"User with email {admin_email} already exists.")
```

## Access the Application

The application is mapped to port 80 on your host machine.

Open your web browser and navigate to:

http://localhost/

## Development Workflow
| Task                  |  Command                          | Reason                                  |
|:----------------------|:---------------------------------:|----------------------------------------:|
| Code Change           | `docker compose restart app`      | Quickly reloads the Gunicorn process    |
|                       |                                   | to pick up Python changes.              |
| Dependency Change     | `docker compose up -d --build`    | Forces a rebuild of the image           |
|                       |                                   | after changing requirements.txt.        |
| View Logs             | `docker compose logs -f app`      | Streams real-time application errors    |
| Stop Services         | `docker compose down`             | Stops and removes containers while      |
|                       |                                   | preserving database data in the volume. |

# PROJECT STRUCTURE

ultima_finance_project/
└── app/
    ├── __init__.py          # Flask app factory and configuration
    ├── auth.py              # Authentication routes (login, signup, logout)
    ├── main.py              # Main application routes (home, profile)
    ├── models.py            # User model and database schema
    └── templates/           # Jinja2 HTML templates
        ├── base.html        # Base template with navigation
        ├── index.html       # Home page with sales dashboard
        ├── login.html       # Login form
        ├── signup.html      # Registration form
        ├── profile.html     # Protected user profile page
        └── update.html      # Edit sale entry
    └── static/
        └── css/
            └── main.css
    ├── migrations/             # Alembic migration history
    ├── requirements.txt        # Python dependency list
    ├── .env                    # Local environment variables (IGNORED by Git)
    ├── .dockerignore           # Specifies files to exclude during Docker build
    ├── Dockerfile              # Instructions for building the 'app' service image
    ├── docker-compose.yml      # Defines the multi-service stack (app + db)
    └── README.md