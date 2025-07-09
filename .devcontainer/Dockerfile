FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# Install Python packages globally available to all users
RUN pip3 --disable-pip-version-check --no-cache-dir install \
    black \
    flake8 \
    pylint \
    pytest \
    jupyter

# Create workspace directory
WORKDIR /workspace

# Copy requirements file
COPY requirements.txt .
COPY requirements_dev.txt .

# Install Python dependencies
RUN pip3 --disable-pip-version-check --no-cache-dir install -r requirements_dev.txt
RUN pip3 --disable-pip-version-check --no-cache-dir install -r requirements.txt
