# Use the official Python 3.12.6-slim image as the base image
FROM python:3.12.6-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN apt-get update && apt-get install -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean

# Add Poetry to the PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy the pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock /app/

# Install the dependencies
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the application's code into the container
COPY . /app

# Command to run the FastAPI server using Uvicorn
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
