from fastapi import FastAPI, HTTPException
from common import configure_chaos

app = FastAPI(title="Servico de estoque")
inject = configure_chaos(app)
PRODUCTS = {1: 100, 2: 20, 3: 0}

@app.get("/stock/{product_id}")
async def stock(product_id: int):
    await inject()
    if product_id not in PRODUCTS:
        raise HTTPException(404, "Produto inexistente")
    return {"product_id": product_id, "available": PRODUCTS[product_id]}
