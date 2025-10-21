# Dockerfile para Monitor PL Brasil
# ====================================

# Base image
FROM python:3.10-slim

# Metadados
LABEL maintainer="Monitor PL Brasil"
LABEL description="Sistema de monitoramento parlamentar brasileiro"
LABEL version="1.0.0"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (para cache de camadas)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretórios necessários
RUN mkdir -p data database

# Expõe portas
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Comando padrão
CMD ["python", "-m", "src.main"]

