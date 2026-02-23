# Elite Marathon Predictor 🏃‍♂️

A Monte Carlo simulation engine that predicts elite marathon finish times using real GPX course elevation data and a physiological fatigue model. Currently configured for the **TCS London Marathon**.

## How It Works

The predictor combines three components to produce a probabilistic race forecast:

### 1. Course Profile (`course.py`)
Parses the official London Marathon GPX file to extract **per-kilometre elevation gain and loss** across all 42 km. Each segment is converted to a pace multiplier using the Minetti cost-of-transport model:
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

### 2. Fatigue Model (`model.py`)
Applies a non-linear fatigue multiplier that activates **after 30 km** (the "wall"):

$$\text{multiplier} = 1 + c \cdot (d - 30)^{1.3} \quad \text{for } d > 30\text{ km}$$

where $c$ is the fatigue coefficient and $d$ is distance in km.

### 3. Monte Carlo Simulation (`simulation.py`)
Runs **10,000 simulated races**, each with:
- Base pace derived from the runner's personal best
- Per-km elevation multiplier from the GPX course profile
- Per-km fatigue multiplier after 30 km
- Random noise (σ = 0.3%) to model natural pace variation

Returns the **mean predicted time**, **5th / 95th percentile bounds**, standard deviation, and **per-km split times**.

## API

A FastAPI server exposes a single endpoint:

```
POST /predict
```

**Parameters:**

| Name | Type | Description |
|---|---|---|
| `pb_time` | `str` | Personal best in `H:MM:SS` format |
| `fatigue_coeff` | `float` | Fatigue coefficient (e.g. `0.0001` for elite, `0.0003` for amateur) |

**Example request:**

```bash
curl -X POST "http://localhost:8000/predict?pb_time=2:01:09&fatigue_coeff=0.0001"
```

**Example response:**

```json
{
  "predicted_mean": "2:01:12",
  "lower_5_percent": "2:00:58",
  "upper_95_percent": "2:01:26",
  "std_dev_seconds": 8.42,
  "per_km_splits": ["0:02:52", "0:02:52", "..."]
}
```

## Project Structure

```
elite-marathon-predictor/
├── requirements.txt
└── backend/
    ├── main.py             # FastAPI app & /predict endpoint
    ├── simulation.py       # Monte Carlo race simulation
    ├── model.py            # Fatigue multiplier model
    ├── course.py           # GPX parser → per-km pace multipliers
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

## Fatigue Coefficient Guide

| Runner level | Suggested `fatigue_coeff` | Behaviour |
|---|---|---|
| World-class elite | `0.00005–0.0001` | Minimal late-race slowdown |
| Sub-elite | `0.0002–0.0004` | Moderate fade after 35 km |
| Club runner | `0.0005–0.001` | Noticeable wall effect |

## References

- **GPX source:** TCS London Marathon 2025 official course file.
