FROM python:3.11-slim

# Python runtime settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install uv only
RUN pip install --no-cache-dir uv

# Install project dependencies
COPY pyproject.toml ./
COPY uv.lock* ./

RUN uv sync --no-dev

# Copy application source after dependencies
COPY app ./app
COPY agents ./agents
COPY inference.py ./
COPY grader.py ./
COPY pytest.ini ./
COPY README.md ./

EXPOSE 7860

CMD ["uv", "run", "uvicorn", "app.server.app:app", "--host", "0.0.0.0", "--port", "8000"]