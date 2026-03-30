FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

ENV BRAIN_DATA_DIR=/app/data
ENV TRANSFORMERS_CACHE=/app/data/models

EXPOSE 8765 8766
CMD ["sh", "-c", "python -m src.server & uvicorn src.web:app --host 0.0.0.0 --port 8766 & wait"]
