# Dockerfile

# ===== Stage 1: The Builder =====
# Use a slim version of the official Python image as the base.
# Python 3.12 is specified based on your venv path.
FROM python:3.12-slim as builder

# Set the working directory inside the container
WORKDIR /app

# Set environment variables to prevent Python from generating .pyc files and to run in unbuffered mode
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system-level dependencies required for building some Python packages (like bcrypt, numpy)
RUN apt-get update && apt-get install -y build-essential

# Copy the file that lists the Python dependencies
COPY requirements.txt .

# Create a virtual environment to isolate our packages
RUN python -m venv /opt/venv
# Add the venv to the PATH, so 'pip', 'python', etc. are from the venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install all Python dependencies from the requirements file
# --no-cache-dir reduces the image size by not storing the pip cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ===== Stage 2: The Final Production Image =====
# Start from a fresh, clean, slim Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the virtual environment (with all its installed packages) from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy your application source code into the container
COPY . .

# Set the PATH to use the Python interpreter and packages from our venv
ENV PATH="/opt/venv/bin:$PATH"

# Expose port 8000 to allow traffic to the container
EXPOSE 8000

# The command to execute when the container starts.
# It runs the Uvicorn server. --host 0.0.0.0 is crucial to make it accessible from outside the container.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000