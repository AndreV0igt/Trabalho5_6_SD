FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common.py .
COPY servico_pedidos servico_pedidos
COPY servico_estoque servico_estoque
COPY servico_pagamento servico_pagamento
