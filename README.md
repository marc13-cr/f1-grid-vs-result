# F1 · Parrilla de salida vs. Resultado final (2020–2025)

Visualización interactiva que analiza hasta qué punto la **posición de parrilla condiciona el resultado final** en Fórmula 1, y cómo varía esa relación según el circuito, la temporada y las condiciones meteorológicas.

**Visualización:** [https://marc13-cr.github.io/f1-grid-vs-result/](https://marc13-cr.github.io/f1-grid-vs-result/)

Práctica Final — Visualización de Datos · Universitat Oberta de Catalunya (UOC)  
Autor: Marc Masramon Martí

---

## Estructura del proyecto

```
f1_dashboard/
├── collect_data.py      # Descarga datos de la API Jolpica F1
├── collect_weather.py   # Descarga datos meteorológicos de Open-Meteo
├── build_html.py        # Genera index.html y dashboard.html
├── index.html           # Dashboard autocontenido (GitHub Pages)
├── dashboard.html       # Idem (nombre alternativo)
├── data/
│   ├── races_base.csv
│   ├── drivers_base.csv
│   ├── qualifying_base.csv
│   ├── results_base.csv
│   ├── f1_positions_base.csv
│   └── weather_base.csv
└── assets/
    └── custom.css       # Estilos del servidor Dash (no necesario para index.html)
```

---

## Reproducir localmente

### 1. Requisitos

```bash
pip install -r requirements.txt
```

O con conda:

```bash
conda env create -f environment.yml
conda activate f1-viz
```

### 2. Descargar datos de F1

```bash
python collect_data.py
```

Descarga ~131 carreras de las temporadas 2020–2025 desde la [API Jolpica F1](https://github.com/jolpica/jolpica-f1) (sin clave).

### 3. Descargar datos meteorológicos

```bash
python collect_weather.py
```

Descarga precipitación, temperatura y viento para cada carrera desde [Open-Meteo](https://open-meteo.com/) (sin clave).

### 4. Generar el dashboard

```bash
python build_html.py
```

Genera `index.html` y `dashboard.html` — archivos autocontenidos que se abren directamente en el navegador sin necesidad de servidor.

---

## Fuentes de datos

| Fuente | Descripción | URL |
|--------|-------------|-----|
| Jolpica F1 API | Resultados, clasificaciones, circuitos y pilotos F1 | https://github.com/jolpica/jolpica-f1 |
| Open-Meteo | Datos meteorológicos históricos | https://open-meteo.com |

---

## Visualizaciones incluidas

1. **Posición final media por posición de salida** — línea con banda de confianza; scatter individual por circuito
2. **Índice de rigidez por circuito** — correlación de Spearman entre parrilla y resultado
3. **Evolución temporal** — cómo cambia la rigidez entre 2020 y 2025
4. **Heatmap circuito × temporada** — visión cruzada de la rigidez
5. **Distribución de movilidad** — dot plot con rango IQR por circuito
6. **Clima y competitividad** — correlación entre precipitación y movilidad de posiciones

---

## Tecnologías

- **Python 3.12** — recogida y procesamiento de datos
- **pandas · scipy · requests** — análisis y peticiones HTTP
- **Plotly.js 2.35** — gráficos interactivos (CDN, sin instalación)
- **HTML/CSS/JavaScript** — dashboard autocontenido

---

## Licencia

Este proyecto se publica bajo la licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
