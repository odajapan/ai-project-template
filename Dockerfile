# Simple development Dockerfile for this template
#
# Usage:
#   docker build -t your_project_name:dev .
#   docker run --rm -it -v "$(pwd):/app" your_project_name:dev bash
#
# This image installs the project in editable mode with dev tools and
# commonly used data-science extras, using the metadata from pyproject.toml.

FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Upgrade pip inside the image
RUN pip install --upgrade pip

# Copy project files into the image
COPY . .

# Install the project plus development and common DS extras
RUN pip install -e .[dev,notebook,viz,docs,cloud]

# Default to an interactive shell; override CMD/ENTRYPOINT as needed in projects
CMD ["bash"]

