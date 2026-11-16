import asyncio
import time
from dataclasses import dataclass
import httpx

class Unavailable(Exception):
    pass

@dataclass
class Circuit:
    threshold: int = 3
    cooldown: float = 5.0
    state: str = "CLOSED"
    failures: int = 0
    opened_at: float = 0
    generation: int = 0
    blocked: int = 0
    transitions: int = 0

    def transition(self, state):
        if self.state != state:
            self.state = state
            self.transitions += 1
            self.generation += 1

    def admit(self):
        if self.state == "OPEN" and time.monotonic() - self.opened_at >= self.cooldown:
            self.transition("HALF_OPEN")
            return self.generation
        if self.state != "CLOSED":
            self.blocked += 1
            raise Unavailable("Circuito aberto ou teste em andamento")
        return self.generation

    def finish(self, token, success):
        if token != self.generation:
            return
        if success:
            self.failures = 0
            self.transition("CLOSED")
        else:
            self.failures += 1
            if self.state == "HALF_OPEN" or self.failures >= self.threshold:
                self.opened_at = time.monotonic()
                self.transition("OPEN")

    def snapshot(self):
        return {"state": self.state, "failures": self.failures,
                "blocked": self.blocked, "transitions": self.transitions}

class Dependency:
    def __init__(self, url):
        self.url = url
        self.circuit = Circuit()
        self.attempts = self.retries = self.errors = 0

    async def get(self, path, resilient=True):
        token = self.circuit.admit() if resilient else None
        success = False
        # A sondagem HALF_OPEN faz apenas uma tentativa.
        limit = 3 if resilient and self.circuit.state != "HALF_OPEN" else 1
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                for attempt in range(limit):
                    self.attempts += 1
                    try:
                        response = await asyncio.wait_for(
                            client.get(self.url + path, timeout=0.5 if resilient else 2.0),
                            timeout=0.5 if resilient else 2.0)
                        if response.status_code < 500 and response.status_code != 429:
                            success = True
                            return response
                    except (httpx.RequestError, asyncio.TimeoutError):
                        pass
                    self.errors += 1
                    if attempt + 1 < limit:
                        self.retries += 1
                        await asyncio.sleep(0.1 * 2 ** attempt)
            raise Unavailable("Dependencia indisponivel")
        finally:
            if resilient:
                self.circuit.finish(token, success)

    def snapshot(self):
        return {**self.circuit.snapshot(), "attempts": self.attempts,
                "retries": self.retries, "errors": self.errors}
