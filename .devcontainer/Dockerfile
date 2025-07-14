FROM --platform=amd64 mcr.microsoft.com/devcontainers/python:3.12-bookworm

# Set Debian version for Azure Functions Core Tools installation
ENV DEBIAN_VERSION=12

# Install prerequisites
RUN apt-get update && apt-get install gpg wget -y

# Download and setup Microsoft GPG key
RUN wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | tee /usr/share/keyrings/microsoft-prod.gpg

# Download and setup Microsoft repository
RUN wget -q https://packages.microsoft.com/config/debian/$DEBIAN_VERSION/prod.list && \
    mv prod.list /etc/apt/sources.list.d/microsoft-prod.list

# Set proper ownership for repository files
RUN chown root:root /usr/share/keyrings/microsoft-prod.gpg && \
    chown root:root /etc/apt/sources.list.d/microsoft-prod.list

# Install Azure Functions Core Tools
RUN apt-get update && apt-get install azure-functions-core-tools-4 -y

# Install libicu-dev dependency
RUN apt-get update && apt-get install libicu-dev -y

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
