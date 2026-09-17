FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY backend ./backend
RUN pip install --no-cache-dir .

RUN mkdir -p /app/data
EXPOSE 8000 1502
CMD ["uvicorn", "gridup.api:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]

