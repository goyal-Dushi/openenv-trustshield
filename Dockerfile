FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# install uv
RUN pip install --no-cache-dir uv

# copy dependency files first
COPY pyproject.toml ./
COPY uv.lock* ./

# install deps into local venv
RUN uv sync --no-dev

# copy source code
COPY app ./app
COPY inference.py ./
COPY grader.py ./
COPY README.md ./

EXPOSE 7860

CMD ["uv", "run", "uvicorn", "app.server.app:app", "--host", "0.0.0.0", "--port", "7860"]