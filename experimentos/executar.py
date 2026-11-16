import csv
import json
import time
from pathlib import Path
import httpx

OUT = Path("resultados")
OUT.mkdir(exist_ok=True)
rows = []
summaries = []
with httpx.Client(timeout=10, trust_env=False) as client:
    def chaos(delay=0, rate=0):
        client.put("http://127.0.0.1:8002/chaos",
                   json={"delay_ms": delay, "error_rate": rate}).raise_for_status()
    def request(scenario, resilient):
        start = time.perf_counter()
        response = client.post("http://127.0.0.1:8000/orders",
            params={"resilient": str(resilient).lower()},
            json={"product_id": 1, "quantity": 1})
        rows.append({"scenario": scenario, "resilient": resilient,
                     "status": response.status_code,
                     "latency_ms": round((time.perf_counter()-start)*1000, 3)})
        return response.status_code
    try:
        for scenario, delay, rate in [("normal",0,0), ("erro",0,1), ("latencia",1200,0)]:
            for resilient in [False, True]:
                chaos(delay, rate)
                client.post("http://127.0.0.1:8000/metrics/reset").raise_for_status()
                start = time.perf_counter()
                for _ in range(12):
                    request(scenario, resilient)
                summaries.append({"scenario":scenario,"resilient":resilient,
                    "duration_s":time.perf_counter()-start,
                    "metrics":client.get("http://127.0.0.1:8000/metrics").json()})
        chaos(rate=1)
        client.post("http://127.0.0.1:8000/metrics/reset").raise_for_status()
        for _ in range(3):
            request("recovery_prepare", True)
        chaos()
        start = time.perf_counter()
        recovered = None
        while time.perf_counter()-start < 15:
            if request("recovery", True) == 200:
                recovered = time.perf_counter()-start
                break
            time.sleep(0.25)
        summaries.append({"recovery_s":recovered,
            "metrics":client.get("http://127.0.0.1:8000/metrics").json()})
    finally:
        chaos()
        if rows:
            with (OUT/"metricas.csv").open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        (OUT/"resumo.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
print("Resultados gravados em resultados/")
