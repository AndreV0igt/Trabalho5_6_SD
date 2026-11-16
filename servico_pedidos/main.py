import os
import uuid
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from servico_pedidos.resiliencia import Dependency, Unavailable

app = FastAPI(title="Servico de pedidos")
def dependencies():
    return {
        "stock": Dependency(os.getenv("STOCK_URL", "http://127.0.0.1:8001")),
        "payment": Dependency(os.getenv("PAYMENT_URL", "http://127.0.0.1:8002"))
    }
deps = dependencies()

class Order(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)

@app.get("/health")
def health():
    return {"status": "up"}

@app.get("/metrics")
async def metrics():
    return {key: dep.snapshot() for key, dep in deps.items()}

@app.post("/metrics/reset")
async def reset():
    global deps
    deps = dependencies()
    return {"reset": True}

@app.post("/orders")
async def order(value: Order, resilient: bool = True):
    current = deps
    order_id = str(uuid.uuid4())
    start = time.perf_counter()
    stage = "stock"
    try:
        stock = await current[stage].get(f"/stock/{value.product_id}", resilient)
        if stock.status_code == 404:
            raise HTTPException(404, "Produto inexistente")
        if stock.status_code != 200:
            raise Unavailable("Resposta inesperada do estoque")
        if stock.json()["available"] < value.quantity:
            raise HTTPException(409, "Estoque insuficiente")
        stage = "payment"
        payment = await current[stage].get(f"/authorize/{order_id}", resilient)
        if payment.status_code != 200 or not payment.json()["authorized"]:
            raise Unavailable("Pagamento nao autorizado")
        return {"order_id": order_id, "status": "CONFIRMED_SIMULATED",
                "latency_ms": round((time.perf_counter()-start)*1000, 2)}
    except Unavailable as exc:
        raise HTTPException(503, detail={"order_id": order_id,
            "status": "NOT_CONFIRMED", "stage": stage, "reason": str(exc),
            "latency_ms": round((time.perf_counter()-start)*1000, 2)})
