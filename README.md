# PROJECT STRUCTURE

ultima_finance_project/
└── app/
    ├── __init__.py          # Flask app factory and configuration
    ├── auth.py              # Authentication routes (login, signup, logout)
    ├── main.py              # Main application routes (home, profile)
    ├── models.py            # User model and database schema
    └── templates/
        ├── base.html        # Base template with navigation
        ├── index.html       # Home page
        ├── login.html       # Login form
        ├── signup.html      # Registration form
        └── profile.html     # Protected user profile page
    ├── instance/
        ├── sales.sqlite
    ├── migrations/
    ├── requirements.txt
    ├── run.py
    └── README.md