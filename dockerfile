FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# Dockerfile for the Stock Alerts Project
# This Dockerfile sets up a Python environment for the Stock Alerts Project.
# It installs the necessary dependencies and runs the Django application.
# The application is configured to run on port 8000.
# It uses a slim version of Python 3.11 to keep the image size small.
# The working directory is set to /app, where the application code is copied.