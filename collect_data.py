"""
collect_data.py — Descarga datos de la API Jolpica F1 y guarda los CSV en ./data/
Ejecutar una sola vez: python collect_data.py
"""
import os, time, requests, pandas as pd

BASE_URL = "https://api.jolpi.ca/ergast/f1"
YEARS = list(range(2020, 2026))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)


def get_json(url, params=None):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def paginate(endpoint):
    offset, limit, items = 0, 100, []
    while True:
        data = get_json(f"{BASE_URL}/{endpoint}", {"limit": limit, "offset": offset})
        mr = data["MRData"]
        if "RaceTable" in mr:
            chunk = mr["RaceTable"].get("Races", [])
        elif "DriverTable" in mr:
            chunk = mr["DriverTable"].get("Drivers", [])
        else:
            chunk = []
        items.extend(chunk)
        total = int(mr["total"])
        offset += limit
        if offset >= total:
            break
        time.sleep(0.3)
    return items


# ── races_base ─────────────────────────────────────────────────────────────────
print("Descargando races_base...", flush=True)
rows = []
for y in YEARS:
    print(f"  {y}", end=" ", flush=True)
    for r in paginate(f"{y}/races.json"):
        rows.append({
            "season": r.get("season"),
            "round": r.get("round"),
            "raceName": r.get("raceName"),
            "date": r.get("date"),
            "circuitId": r.get("Circuit", {}).get("circuitId"),
            "circuitName": r.get("Circuit", {}).get("circuitName"),
            "locality": r.get("Circuit", {}).get("Location", {}).get("locality"),
            "country": r.get("Circuit", {}).get("Location", {}).get("country"),
            "lat": r.get("Circuit", {}).get("Location", {}).get("lat"),
            "long": r.get("Circuit", {}).get("Location", {}).get("long"),
        })
races_base = pd.DataFrame(rows)
races_base.to_csv(f"{OUT}/races_base.csv", index=False)
print(f"\n  → {races_base.shape}", flush=True)


# ── drivers_base ───────────────────────────────────────────────────────────────
print("Descargando drivers_base...", flush=True)
rows = []
for d in paginate("drivers.json"):
    rows.append({
        "driverId": d.get("driverId"),
        "code": d.get("code"),
        "givenName": d.get("givenName"),
        "familyName": d.get("familyName"),
        "nationality": d.get("nationality"),
    })
drivers_base = pd.DataFrame(rows).drop_duplicates()
drivers_base.to_csv(f"{OUT}/drivers_base.csv", index=False)
print(f"  → {drivers_base.shape}", flush=True)


# ── qualifying_base ────────────────────────────────────────────────────────────
print("Descargando qualifying_base...", flush=True)
rows = []
for y in YEARS:
    print(f"  {y}", end=" ", flush=True)
    for race in paginate(f"{y}/qualifying.json"):
        s, rnd = race.get("season"), race.get("round")
        rName = race.get("raceName")
        cId = race.get("Circuit", {}).get("circuitId")
        cName = race.get("Circuit", {}).get("circuitName")
        for q in race.get("QualifyingResults", []):
            rows.append({
                "season": s, "round": rnd, "raceName": rName,
                "circuitId": cId, "circuitName": cName,
                "driverId": q.get("Driver", {}).get("driverId"),
                "givenName": q.get("Driver", {}).get("givenName"),
                "familyName": q.get("Driver", {}).get("familyName"),
                "constructorId": q.get("Constructor", {}).get("constructorId"),
                "constructorName": q.get("Constructor", {}).get("name"),
                "quali_position": q.get("position"),
                "q1": q.get("Q1"), "q2": q.get("Q2"), "q3": q.get("Q3"),
            })
qualifying_base = pd.DataFrame(rows)
qualifying_base.to_csv(f"{OUT}/qualifying_base.csv", index=False)
print(f"\n  → {qualifying_base.shape}", flush=True)


# ── results_base + f1_positions_base ──────────────────────────────────────────
print("Descargando results_base...", flush=True)
rows = []
for y in YEARS:
    print(f"  {y}", end=" ", flush=True)
    for race in paginate(f"{y}/results.json"):
        s, rnd = race.get("season"), race.get("round")
        rName = race.get("raceName")
        cId = race.get("Circuit", {}).get("circuitId")
        cName = race.get("Circuit", {}).get("circuitName")
        country = race.get("Circuit", {}).get("Location", {}).get("country")
        for res in race.get("Results", []):
            rows.append({
                "season": s, "round": rnd, "raceName": rName,
                "circuitId": cId, "circuitName": cName, "country": country,
                "driverId": res.get("Driver", {}).get("driverId"),
                "code": res.get("Driver", {}).get("code"),
                "givenName": res.get("Driver", {}).get("givenName"),
                "familyName": res.get("Driver", {}).get("familyName"),
                "constructorId": res.get("Constructor", {}).get("constructorId"),
                "constructorName": res.get("Constructor", {}).get("name"),
                "grid_position": res.get("grid"),
                "final_position": res.get("position"),
                "positionText": res.get("positionText"),
                "points": res.get("points"),
                "laps": res.get("laps"),
                "status": res.get("status"),
                "time_millis": res.get("Time", {}).get("millis"),
                "time_text": res.get("Time", {}).get("time"),
            })

results_base = pd.DataFrame(rows)
results_base.to_csv(f"{OUT}/results_base.csv", index=False)
print(f"\n  → {results_base.shape}", flush=True)

# Derived table
f1 = results_base.copy()
for c in ["grid_position", "final_position", "points", "laps"]:
    f1[c] = pd.to_numeric(f1[c], errors="coerce")
f1["positions_gained"] = f1["grid_position"] - f1["final_position"]
f1.to_csv(f"{OUT}/f1_positions_base.csv", index=False)
print(f"f1_positions_base → {f1.shape}", flush=True)

print("\n¡Todos los datos descargados correctamente!", flush=True)
