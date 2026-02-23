from fastapi import FastAPI
from simulation import simulate_race

app = FastAPI()

# Utility functions to convert time formats
def time_to_seconds(time_str):
    h, m, s = map(int, time_str.split(":"))
    return h * 3600 + m * 60 + s

def seconds_to_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}:{m:02d}:{s:02d}"

@app.post("/predict")
def predict(pb_time: str, fatigue_coeff: float):

    pb_seconds = time_to_seconds(pb_time)
    result = simulate_race(pb_seconds, fatigue_coeff)

    return {
        "predicted_mean": seconds_to_time(result["mean_time"]),
        "lower_5_percent": seconds_to_time(result["p5"]),
        "upper_95_percent": seconds_to_time(result["p95"]),
        "std_dev_seconds": result["std_dev"],
    }