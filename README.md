# Elite Marathon Predictor 🏃‍♂️

A Monte Carlo simulation engine that predicts elite marathon finish times using real GPX course elevation data, physiological fatigue modelling, heat effects, and DNF probability. Currently configured for the **2026 TCS London Marathon** with the full 35-runner elite men's field.

## How It Works

The predictor layers five models to produce a probabilistic race forecast for each runner:

### 1. Course Profile (`course.py`)
Parses the official London Marathon GPX file at runtime to extract **per-kilometre elevation gain and loss** across all 42 km. Each segment is converted to a pace multiplier using the Minetti cost-of-transport model:
- **Uphill:** +0.033% slower per metre of elevation gain
- **Downhill:** −0.018% faster per metre of elevation loss

Key course features detected from the GPX:
| Section | Kilometres | Elevation |
|---|---|---|
| Blackheath start | 1–3 | Gentle uphill (+5 m → +1 m) |
| Ridge descent | 4–8 | Steep drop (−26 m at km 5) |
| Flat riverside | 9–13 | Near sea level |
| Tower Bridge | 20 | Hardest climb (+7.7 m) |
| Canary Wharf loop | 28–33 | Gradual rise then drop |
| Embankment return | 34–39 | Rolling |
| The Mall finish | 40–42 | Flat |

### 2. Tiered Fatigue Model (`model.py`)
Each simulation draws a fatigue coefficient from a **log-normal distribution** whose median and spread depend on the runner's calibre. This produces realistic variance — most races are normal, some are great days, some are total blow-ups.

| Tier | PB range | Median coeff | Log-normal σ |
|---|---|---|---|
| World-class | sub-2:05 | 0.0008 | 1.0 |
| International | 2:05–2:10 | 0.0014 | 1.1 |
| Sub-elite | 2:10–2:15 | 0.0022 | 1.2 |
| Club-level | 2:15+ | 0.0035 | 1.3 |

The fatigue multiplier activates **after 30 km**:

$$\text{multiplier} = 1 + c \cdot (d - 30)^{1.8} \quad \text{for } d > 30\text{ km}$$

### 3. Heat Model (`model.py`)
Based on **Ely et al. (2007)**, models the effect of ambient temperature on pace:
- Optimal marathon temperature: **8 °C**
- Base penalty: **+0.03% per °C** above optimal
- Progressive drift: penalty ramps from 1.0× at km 1 to 1.8× at km 42 (core temperature rise)
- London's typical race-day temperature: **~15 °C**

### 4. DNF Model (`model.py`)
A per-km DNF hazard activates after 30 km, derived from tier-based overall DNF rates:

| Tier | DNF rate |
|---|---|
| World-class | 3% |
| International | 5% |
| Sub-elite | 7% |
| Club-level | 10% |

### 5. Monte Carlo Simulation (`simulation.py`)
Runs **10,000 simulated races** per runner, each with:
- Base pace derived from the runner's personal best
- Per-km elevation multiplier from the GPX course profile
- Per-simulation fatigue coefficient drawn from log-normal distribution
- Progressive heat penalty based on ambient temperature
- **Asymmetric noise** that grows with distance (σ: 0.5% at km 1 → 2.5% at km 42)
- 20% per-km chance of an exponential "bad patch" spike (cramp, GI, wind)
- Per-km DNF hazard after 30 km

Returns median finish time, percentile bounds (p5–p95), DNF rate, and per-km splits.

## API

### `POST /predict` — Single runner prediction

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pb_time` | `str` | *required* | Personal best in `H:MM:SS` format |
| `temp_celsius` | `float` | `15.0` | Ambient temperature in °C |

```bash
curl -X POST "http://localhost:8000/predict?pb_time=2:02:05"
```

```json
{
  "pb": "2:02:05",
  "predicted_median": "2:03:53",
  "predicted_mean": "2:04:12",
  "best_5_percent": "2:02:10",
  "worst_5_percent": "2:08:00",
  "std_dev_seconds": 102.3,
  "dnf_rate": "2.7%",
  "temp_celsius": 15.0
}
```

### `GET /leaderboard` — Full elite field simulation

| Parameter | Type | Default | Description |
|---|---|---|---|
| `temp_celsius` | `float` | `15.0` | Ambient temperature in °C |
| `simulations` | `int` | `10000` | Number of Monte Carlo iterations per runner |

```bash
curl "http://localhost:8000/leaderboard"
```

Returns all 35 runners ranked by predicted median time, with DNF runners sorted to the bottom.

## Runners (`runners.py`)

The full 2026 TCS London Marathon elite men's field (35 runners), from Sebastian Sawe (2:02:05) to William Mycroft (2:15:54).

## Project Structure

```
elite-marathon-predictor/
├── requirements.txt
├── README.md
└── backend/
    ├── main.py             # FastAPI app — /predict & /leaderboard endpoints
    ├── simulation.py       # Monte Carlo race simulation engine
    ├── model.py            # Fatigue, heat & DNF models
    ├── course.py           # GPX parser → per-km pace multipliers
    ├── runners.py          # 2026 elite men's field (35 runners + PBs)
    └── *.gpx               # London Marathon course GPX file
```

## Getting Started

### Prerequisites
- Python 3.10+

### Setup

```bash
# Clone the repo
git clone https://github.com/frankislamucc/elite-marathon-predictor.git
cd elite-marathon-predictor

# Create a virtual environment & install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the server

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## References

- **GPX source:** TCS London Marathon 2025 official course file
- **Heat model:** Ely et al. (2007) — Impact of weather on marathon-running performance
- **Elevation model:** Minetti et al. (2002) — Energy cost of walking and running at extreme uphill and downhill slopes
