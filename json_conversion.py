import pandas as pd
import json
import ast
import math

CSV_PATH = r"...\step_hypothesis_refiner.csv"
OUT_JSON = r"...\NeRD.json"

def smart_parse(x):
    if pd.isna(x):
        return None
    if not isinstance(x, str):
        return x

    s = x.strip()
    if not s:
        return None

    if s.startswith("{") or s.startswith("["):
        try:
            return ast.literal_eval(s)
        except Exception:
            pass

    try:
        return json.loads(s)
    except Exception:
        return x

def sanitize(obj):
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj

df = pd.read_csv(CSV_PATH)

records = []
for row in df.to_dict(orient="records"):
    parsed = {k: sanitize(smart_parse(v)) for k, v in row.items()}
    records.append(parsed)

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False, allow_nan=False)  # <--- forbid NaN

print("Saved:", OUT_JSON)
print("Cases:", len(records))
