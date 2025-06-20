FROM python:3.10-slim

ENV HF_HOME=/app/hf_cache


RUN apt-get update && \
    apt-get install -y git curl && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app
RUN mkdir -p /app/hf_cache /app/models \
    && chmod -R 777 /app/hf_cache

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt


COPY . /app


CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port=${PORT:-7860}"]