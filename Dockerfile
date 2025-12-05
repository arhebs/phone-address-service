FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install dependencies using Poetry (including dev deps for in-container testing)
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Copy application source
COPY . .

# Default command runs the FastAPI app with Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

