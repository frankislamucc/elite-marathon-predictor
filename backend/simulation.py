import numpy as np
from model import (
    fatigue_multiplier,
    heat_multiplier,
    sample_fatigue_coeff,
    get_dnf_rate,
)
from course import LondonCourseProfile

# London Marathon historical average temperature
DEFAULT_TEMP_C = 15.0


def simulate_race_per_km(pb_seconds, fatigue_coeff_override=None,
                          temp_celsius=DEFAULT_TEMP_C, simulations=10000):
    """Monte Carlo marathon simulation with realistic variance.

    Key differences from a naive model:
      1. Fatigue coefficient is drawn per-simulation from a log-normal
         distribution (unless overridden), producing good days AND blow-ups.
      2. Per-km noise is *asymmetric* and *grows with distance* —
         later km can go very wrong but not magically fast.
      3. A DNF hazard accumulates after 30 km; some simulations are DNFs.
    """
    rng = np.random.default_rng()

    base_pace = pb_seconds / 42.195
    course_profile = LondonCourseProfile()  # 42-element array
    dnf_rate = get_dnf_rate(pb_seconds)

    # Convert overall DNF probability into a per-km hazard after km 30.
    # P(finish) = (1 - h)^12  =>  h = 1 - (1 - dnf_rate)^(1/12)
    if dnf_rate > 0:
        per_km_dnf_hazard = 1 - (1 - dnf_rate) ** (1 / 12)
    else:
        per_km_dnf_hazard = 0.0

    finish_times = []
    dnf_count = 0
    all_splits = []

    for _ in range(simulations):
        # Draw this race's fatigue coefficient
        if fatigue_coeff_override is not None:
            fc = fatigue_coeff_override
        else:
            fc = sample_fatigue_coeff(pb_seconds, rng)

        km_splits = []
        dnf = False

        for km in range(42):
            dist = km + 1

            # --- DNF check after km 30 ---
            if dist > 30 and per_km_dnf_hazard > 0:
                if rng.random() < per_km_dnf_hazard:
                    dnf = True
                    break

            fatigue = fatigue_multiplier(dist, fc)
            heat = heat_multiplier(dist, temp_celsius)

            # --- Asymmetric noise that grows with distance ---
            # Base sigma grows from 0.005 at km 1 to 0.025 at km 42
            sigma = 0.005 + 0.020 * (km / 41)
            # Positive skew: use exponential spike on top of gaussian
            gaussian_noise = rng.normal(0, sigma)
            # 20% chance of a bad-patch spike per km (cramp, GI, wind, crowd)
            if rng.random() < 0.20:
                gaussian_noise += rng.exponential(sigma * 2.5)

            km_time = base_pace * fatigue * heat * course_profile[km] * (1 + gaussian_noise)
            km_splits.append(km_time)

        if dnf:
            dnf_count += 1
            continue

        total_time = sum(km_splits)
        finish_times.append(total_time)
        all_splits.append(km_splits)

    finish_times = np.array(finish_times)
    all_splits = np.array(all_splits) if all_splits else np.empty((0, 42))

    # Stats over finishers only
    mean_splits = all_splits.mean(axis=0) if len(all_splits) > 0 else np.zeros(42)

    return {
        "mean_time": finish_times.mean() if len(finish_times) > 0 else float("inf"),
        "std_dev": finish_times.std() if len(finish_times) > 0 else 0.0,
        "p5": np.percentile(finish_times, 5) if len(finish_times) > 0 else 0.0,
        "p25": np.percentile(finish_times, 25) if len(finish_times) > 0 else 0.0,
        "median": np.median(finish_times) if len(finish_times) > 0 else 0.0,
        "p75": np.percentile(finish_times, 75) if len(finish_times) > 0 else 0.0,
        "p95": np.percentile(finish_times, 95) if len(finish_times) > 0 else 0.0,
        "mean_splits": mean_splits,
        "temp_celsius": temp_celsius,
        "dnf_count": dnf_count,
        "dnf_rate": dnf_count / simulations,
        "finishers": len(finish_times),
        "simulations": simulations,
    }