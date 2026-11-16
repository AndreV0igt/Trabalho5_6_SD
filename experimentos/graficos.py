import csv
import statistics
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt

out = Path("resultados")
groups = defaultdict(list)
with (out/"metricas.csv").open(encoding="utf-8") as file:
    for row in csv.DictReader(file):
        if row["scenario"] in ("normal","erro","latencia"):
            groups[f'{row["scenario"]}\nresiliencia={row["resilient"]}'].append(row)
for name, ylabel, function in [
    ("latencia", "Latencia media (ms)", lambda g: statistics.mean(float(r["latency_ms"]) for r in g)),
    ("sucesso", "Taxa de sucesso (%)", lambda g: 100*statistics.mean(r["status"]=="200" for r in g)),
    ("p95", "Latencia p95 (ms)", lambda g: sorted(float(r["latency_ms"]) for r in g)[__import__("math").ceil(.95*len(g))-1])
]:
    plt.figure(figsize=(10,5))
    plt.bar(list(groups), [function(g) for g in groups.values()])
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(out/f"{name}.png", dpi=150)
    plt.close()
