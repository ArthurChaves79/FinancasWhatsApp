FROM python:3.12

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libpng-dev \
    libopenblas-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "FinancasWhastApp:app"]