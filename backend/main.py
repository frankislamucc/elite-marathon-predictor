from fastapi import FastAPI
from simulation import simulate_race_per_km
from runners import ELITE_MEN_2026

app = FastAPI()


def time_to_seconds(time_str):
    h, m, s = map(int, time_str.split(":"))
    return h * 3600 + m * 60 + s


def seconds_to_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}:{m:02d}:{s:02d}"


# ---------------------------------------------------------------------------
# Single-runner prediction
# ---------------------------------------------------------------------------
@app.post("/predict")
def predict(pb_time: str, temp_celsius: float = 15.0):
    pb_seconds = time_to_seconds(pb_time)
    result = simulate_race_per_km(pb_seconds, temp_celsius=temp_celsius)

    return {
        "pb": pb_time,
        "predicted_median": seconds_to_time(result["median"]),
        "predicted_mean": seconds_to_time(result["mean_time"]),
        "best_5_percent": seconds_to_time(result["p5"]),
        "worst_5_percent": seconds_to_time(result["p95"]),
        "std_dev_seconds": round(result["std_dev"], 1),
        "dnf_rate": f"{result['dnf_rate']:.1%}",
        "temp_celsius": result["temp_celsius"],
    }


# ---------------------------------------------------------------------------
# Full elite field leaderboard
# ---------------------------------------------------------------------------
@app.get("/leaderboard")
def leaderboard(
    temp_celsius: float = 15.0,
    simulations: int = 10000,
):
    """Simulate every runner in the 2026 elite men's field and return a ranked leaderboard."""
    results = []

    for name, pb in ELITE_MEN_2026.items():
        pb_seconds = time_to_seconds(pb)
        r = simulate_race_per_km(pb_seconds, temp_celsius=temp_celsius, simulations=simulations)

        dnf_pct = r["dnf_rate"]
        is_dnf = dnf_pct > 0.5  # majority of sims were DNFs

        results.append({
            "name": name,
            "pb": pb,
            "predicted_time": "DNF" if is_dnf else seconds_to_time(r["median"]),
            "predicted_seconds": float("inf") if is_dnf else round(r["median"], 2),
            "dnf_rate": f"{dnf_pct:.1%}",
            "status": "DNF" if is_dnf else "Finished",
        })

    # Sort: finishers by predicted time, then DNFs at the bottom
    results.sort(key=lambda x: (x["status"] == "DNF", x["predicted_seconds"]))

    return {
        "race": "2026 TCS London Marathon",
        "conditions": {
            "temp_celsius": temp_celsius,
            "simulations": simulations,
        },
        "field_size": len(results),
        "leaderboard": results,
    }