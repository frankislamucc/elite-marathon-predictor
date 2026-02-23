import numpy as np
from model import fatigue_multiplier
from course import LondonCourseProfile

def simulate_race_per_km(pb_seconds, fatigue_coeff, simulations=10000):
    base_pace = pb_seconds / 42.195
    course_profile = LondonCourseProfile()  # returns 42-element array

    all_total_times = []
    all_splits = []

    for _ in range(simulations):
        km_splits = []

        for km in range(42):
            fatigue = fatigue_multiplier(km + 1, fatigue_coeff)
            noise = np.random.normal(0, 0.003)

            km_time = base_pace * fatigue * course_profile[km] * (1 + noise)
            km_splits.append(km_time)  # time for this km

        total_time = sum(km_splits)
        all_total_times.append(total_time)
        all_splits.append(km_splits)

    all_total_times = np.array(all_total_times)
    all_splits = np.array(all_splits)  # shape: (simulations, 42)

    # Compute mean per-km split across all simulations
    mean_splits = all_splits.mean(axis=0)

    return {
        "mean_time": all_total_times.mean(),
        "std_dev": all_total_times.std(),
        "p5": np.percentile(all_total_times, 5),
        "p95": np.percentile(all_total_times, 95),
        "mean_splits": mean_splits  # array of 42 per-km times in seconds
    }