FROM python:3.11.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Pipx
RUN pip install pipx && \
    pipx ensurepath

# Add Pipx binary path to PATH
ENV PATH="/root/.local/bin:$PATH"

# Install Poetry
RUN pipx install poetry

# Copy the pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the app with hot-reload
CMD ["poetry", "run", "uvicorn", "chatbot:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]