# Start with a small, official Python image. We use 'slim' to keep the size down.
# You mentioned sqlite, which is supported by Python out of the box.
FROM python:3.11-slim

# Set an environment variable for Gunicorn. 
# This tells it where to find the Flask application instance.
# We'll assume your Flask application object is named 'app' inside the 'app' directory's __init__.py.
# The format is: <module_path>:<application_variable_name>
ENV FLASK_APP=app:app

# Set the working directory inside the container. All subsequent commands will run here.
WORKDIR /usr/src/app

# Copy the requirements file into the container.
# We do this first so Docker can use caching if requirements.txt doesn't change.
COPY requirements.txt .

# Install the Python dependencies listed in requirements.txt.
# The 'RUN' command executes a command inside the container during the build process.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire rest of your application code into the working directory.
COPY . .

# Tell Docker that the container will listen on port 8000. 
# We typically use a port like 8000 for Gunicorn, not 5000.
EXPOSE 8000

# The command to run when the container starts. This uses Gunicorn to serve your app.
# The format is gunicorn --bind 0.0.0.0:<port> <module>:<app_instance>
# 0.0.0.0 means listen on all network interfaces.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]