import asyncio
import random
from fastapi import HTTPException
from pydantic import BaseModel, Field

class ChaosConfig(BaseModel):
    delay_ms: int = Field(0, ge=0, le=10000)
    error_rate: float = Field(0, ge=0, le=1)

def configure_chaos(app):
    config = ChaosConfig()
    @app.get("/health")
    def health():
        return {"status": "up"}
    @app.get("/chaos")
    def get_chaos():
        return config
    @app.put("/chaos")
    def set_chaos(value: ChaosConfig):
        nonlocal config
        config = value
        return config
    async def inject():
        snapshot = config
        await asyncio.sleep(snapshot.delay_ms / 1000)
        if random.random() < snapshot.error_rate:
            raise HTTPException(503, "Falha injetada")
    return inject
