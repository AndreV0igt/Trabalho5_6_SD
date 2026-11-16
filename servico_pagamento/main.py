from fastapi import FastAPI
from common import configure_chaos

app = FastAPI(title="Servico de pagamento simulado")
inject = configure_chaos(app)

@app.get("/authorize/{order_id}")
async def authorize(order_id: str):
    await inject()
    # Operacao simulada e sem efeitos financeiros: repeticao segura.
    return {"order_id": order_id, "authorized": True}
