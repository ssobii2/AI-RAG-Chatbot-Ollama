# Use the custom Whisper base image
FROM whisper-base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Install Pipx
RUN pip install pipx && \
    pipx ensurepath

# Add Pipx binary path to PATH
ENV PATH="/root/.local/bin:$PATH"

# Install Poetry
RUN pipx install poetry

# Disable virtualenv creation
RUN poetry config virtualenvs.create false

# Copy the pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the app with hot-reload
CMD ["poetry", "run", "uvicorn", "chatbot:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]