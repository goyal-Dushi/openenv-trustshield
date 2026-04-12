FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# copy dependency files first
COPY requirements.txt ./

# install deps into local venv
RUN pip install --no-cache-dir -r requirements.txt

# copy source code
COPY app ./app
COPY inference.py ./
COPY grader.py ./
COPY server ./server

EXPOSE 7860

CMD ["uvicorn", "app.server.app:app", "--host", "0.0.0.0", "--port", "7860"]