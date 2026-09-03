FROM python:3.12-slim

WORKDIR /app

COPY files/requirements.txt files/requirements.txt
RUN pip install --no-cache-dir -r files/requirements.txt

COPY files/ files/
COPY frontend/ frontend/

WORKDIR /app/files
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
