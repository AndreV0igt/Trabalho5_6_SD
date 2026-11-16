# Trabalhos 5 e 6 — Tolerância a falhas e Chaos Engineering

Protótipo acadêmico com três processos HTTP independentes: pedidos (8000), estoque (8001) e pagamento simulado (8002). Estoque e pagamento não possuem efeitos persistentes. O objetivo é estudar resiliência, não implementar comércio eletrônico real.

## Execução no Windows (PowerShell)
Abra esta pasta no VS Code:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Se a ativação for bloqueada, use `Set-ExecutionPolicy -Scope Process RemoteSigned` ou chame diretamente `.\.venv\Scripts\python.exe`.

Em três terminais, na raiz do projeto, com o ambiente virtual ativo:
```
python -m uvicorn servico_estoque.main:app --port 8001
python -m uvicorn servico_pagamento.main:app --port 8002
python -m uvicorn servico_pedidos.main:app --port 8000
```
Alternativamente, abra Docker Desktop e execute `docker compose up --build -d`. Confira `docker compose ps`. Não execute simultaneamente a versão local e a Docker.

## Demonstração
Abra http://localhost:8000/docs para pedidos, http://localhost:8001/docs para estoque e http://localhost:8002/docs para pagamento.
Em POST /orders, use {"product_id":1,"quantity":1}. O parâmetro resilient ativa/desativa os mecanismos. A versão sem resiliência mantém timeout de segurança de 2 s; a versão resiliente tem timeout de 0,5 s, até 3 tentativas, backoff de 100/200 ms, circuito após 3 operações malsucedidas e espera de 5 s. Cada dependência tem circuito próprio.

1. Envie pedido normal: HTTP 200.
2. No Swagger de pagamento, PUT /chaos com {"delay_ms":0,"error_rate":1}.
3. Envie quatro pedidos com resilient=true. Os três primeiros falham com 503; o quarto deve falhar rapidamente sem chamada ao pagamento (se ainda dentro de 5 s).
4. Consulte GET /metrics no serviço de pedidos.
5. Restaure PUT /chaos com {"delay_ms":0,"error_rate":0}. Aguarde 5 s e envie novo pedido: deve retornar 200 e fechar circuito.
6. Teste latência com {"delay_ms":1200,"error_rate":0}; restaure depois.
7. Para queda real: `docker compose stop pagamento`, envie pedidos e observe 503. Use `docker compose start pagamento`, aguarde o serviço inicializar e o cooldown, e repita. Sem Docker, interrompa e reinicie o terminal de pagamento.

O fallback retorna NOT_CONFIRMED, nunca confirma pagamento ficticiamente durante falha. /health indica vida do processo, não saúde de todas as dependências. /metrics/reset é somente para laboratório; usar sem carga concorrente.

## Experimentos
Com os três serviços ativos e sem outros testes simultâneos:
```
python -m pytest -q
python experimentos/executar.py
python experimentos/graficos.py
```
A execução gera CSV com latência ponta a ponta e HTTP status, JSON com contadores e duração, gráficos de média, p95 e taxa de sucesso. Vazão observada em requisições/s = 12 / duration_s para cada cenário; vazão útil = quantidade de HTTP 200 / duration_s. O tempo de recuperação é medido desde a remoção da falha até o primeiro pedido bem-sucedido. A carga é sequencial e pequena, não representa capacidade máxima.

## Limitações
Sem persistência, autenticação, reserva real de estoque ou pagamento financeiro. Um worker por serviço; o circuito é local ao processo. A injeção é artificial e controlada, sem testes em produção. Retry é seguro aqui porque as operações remotas são consultas sem efeitos. Em produção, escritas exigem idempotência. A disponibilidade do serviço de pedidos continua sendo um ponto único de falha. Os endpoints de caos são exclusivamente para laboratório. As portas Docker são vinculadas ao loopback.

## Publicação
Crie um repositório no GitHub, depois execute `git init`, `git add .`, `git commit -m "Implementacao de resiliencia"`, `git branch -M main`, configure o remote com a URL real e faça push. Nenhum repositório remoto é criado automaticamente.

## Desligamento
`docker compose down` ou Ctrl+C em cada terminal local.

## Referências para estudo
- https://principlesofchaos.org/
- https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
- https://learn.microsoft.com/en-us/azure/architecture/patterns/retry
- https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- https://fastapi.tiangolo.com/
- https://www.python-httpx.org/
