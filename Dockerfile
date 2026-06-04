FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY CRIMan.py SQLLiteInitializeCRIMan.py smtptosms.py ./
COPY templates/ templates/
COPY static/ static/

VOLUME ["/app/data"]

ENV FLASK_APP=CRIMan.py
ENV CRIIT_DB_PATH=/app/data/CRIMan.db

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "CRIMan:CRIMan"]
