FROM python:3.11-slim

# Evitar prompts interativos durante apt-get
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar ffmpeg (necessário para yt-dlp combinar vídeo+áudio)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY . .

# Criar diretório de downloads dentro do container
RUN mkdir -p /app/downloads

# Expor a porta (Render injeta $PORT, default 8000)
EXPOSE 8000

# Arrancar o servidor FastAPI da API wrapper
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
