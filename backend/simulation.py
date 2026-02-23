import numpy as np
from model import fatigue_multiplier
from course import LondonCourseProfile

def simulate_race(pb_seconds, fatigue_coeff, simulations=10000):

    base_pace = pb_seconds / 42.195
    course_profile = LondonCourseProfile()

    results = []

    for _ in range(simulations):
        total_time = 0

        for km in range(42):
            fatigue = fatigue_multiplier(km + 1, fatigue_coeff)
            noise = np.random.normal(0, 0.003)

            km_time = base_pace * fatigue * course_profile[km] * (1 + noise)
            total_time += km_time

        results.append(total_time)

    results = np.array(results)

    return {
        "mean_time": results.mean(),
        "std_dev": results.std(),
        "p5": np.percentile(results, 5),
        "p95": np.percentile(results, 95),
    }
