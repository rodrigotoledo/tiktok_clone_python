FROM python:3.11-slim

WORKDIR /app

# Copia requirements primeiro (cache!)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 🔥 VOLUME EM TEMPO REAL - copia TUDO da pasta app/
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]