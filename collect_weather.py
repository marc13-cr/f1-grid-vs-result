#!/usr/bin/env python3
"""
collect_weather.py — Descarga datos meteorológicos históricos para cada carrera
usando la API Open-Meteo (gratuita, sin clave de API).
Ejecutar una sola vez: python collect_weather.py
"""
import os, time, requests, pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

races = pd.read_csv(os.path.join(DATA, "races_base.csv"))
races["season"] = races["season"].astype(str)
races["round"]  = races["round"].astype(str)
races["lat"]    = pd.to_numeric(races["lat"],  errors="coerce")
races["long"]   = pd.to_numeric(races["long"], errors="coerce")

URL = "https://archive-api.open-meteo.com/v1/archive"

rows = []
for i, r in races.iterrows():
    if pd.isna(r["lat"]) or pd.isna(r["long"]) or pd.isna(r["date"]):
        print(f"  ⚠ Sin coordenadas: {r['raceName']}")
        continue

    params = {
        "latitude":  r["lat"],
        "longitude": r["long"],
        "start_date": r["date"],
        "end_date":   r["date"],
        "daily": "precipitation_sum,temperature_2m_max,wind_speed_10m_max",
        "timezone": "auto",
    }
    try:
        resp  = requests.get(URL, params=params, timeout=30)
        resp.raise_for_status()
        daily = resp.json().get("daily", {})
        prec  = (daily.get("precipitation_sum")   or [None])[0]
        temp  = (daily.get("temperature_2m_max")  or [None])[0]
        wind  = (daily.get("wind_speed_10m_max")  or [None])[0]
    except Exception as e:
        print(f"  ⚠ Error {r['raceName']}: {e}")
        prec = temp = wind = None

    rows.append({
        "season":           r["season"],
        "round":            r["round"],
        "raceName":         r["raceName"],
        "circuitName":      r["circuitName"],
        "country":          r["country"],
        "date":             r["date"],
        "lat":              r["lat"],
        "long":             r["long"],
        "precipitation_mm": prec,
        "temp_max_c":       temp,
        "wind_max_kmh":     wind,
    })
    print(f"  {r['season']} R{r['round']:>2}  {r['raceName']:<40}  "
          f"🌧 {str(prec)+'mm':<8}  🌡 {str(temp)+'°C':<8}  💨 {wind} km/h")
    time.sleep(0.35)   # límite de cortesía

weather = pd.DataFrame(rows)
weather.to_csv(os.path.join(DATA, "weather_base.csv"), index=False)
print(f"\nweather_base → {weather.shape}  guardado en {DATA}")
