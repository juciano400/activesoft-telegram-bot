# Imagem oficial do Playwright com Python e Chromium já instalados
FROM mcr.microsoft.com/playwright/python:v1.51.0-jammy

WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir flask anthropic python-dotenv gunicorn playwright

# Instala o Chromium via Playwright
RUN playwright install chromium

# Copia o código
COPY . .

# Porta padrão Railway
ENV PORT=8080

EXPOSE 8080

CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
