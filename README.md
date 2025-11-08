# PROJECT STRUCTURE

ultima_finance_project/
└── app/
    ├── __init__.py          # Flask app factory and configuration
    ├── auth.py              # Authentication routes (login, signup, logout)
    ├── main.py              # Main application routes (home, profile)
    ├── models.py            # User model and database schema
    └── templates/
        ├── base.html        # Base template with navigation
        ├── index.html       # Home page with sales dashboard
        ├── login.html       # Login form
        ├── signup.html      # Registration form
        ├── profile.html     # Protected user profile page
        └── update.html      # Edit sale entry
    └── static/
        └── css/
            └── main.css
    └── instance/
        └── database_name.sqlite
    ├── migrations/
    ├── requirements.txt     # Libraries and dependencies
    ├── run.py               # Start the programm on a local server
    ├── .dockerignore
    ├── Dockerfile
    ├── docker-compose.yml
    └── README.md