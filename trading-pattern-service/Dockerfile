FROM python:3.11-slim
WORKDIR /app
COPY ./app /app/app
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy psycopg2-binary requests
EXPOSE 8000
CMD ["sh", "-c", "python /app/app/wait_for_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]