def fatigue_multiplier(distance_km, fatigue_coeff):
    if distance_km <= 30:
        return 1.0
    else:
        return 1.0 + fatigue_coeff * ((distance_km - 30) ** 1.3)


# Optimal marathon temperature for elite runners (Ely et al., 2007)
OPTIMAL_TEMP_C = 8.0

# Base slowdown: ~0.03% per °C above optimal (conservative elite estimate)
HEAT_PENALTY_PER_C = 0.0003

# Progressive heat drift: thermoregulation degrades over the race,
# so later kilometres are disproportionately affected.
# Modelled as a linear ramp from 1.0× at km 1 to HEAT_DRIFT_MAX× at km 42.
HEAT_DRIFT_MAX = 1.8


def heat_multiplier(distance_km, temp_celsius):
    """Pace multiplier due to ambient temperature.

    Below the optimal temperature the effect is neutral (no cold bonus
    is applied — elites dress for conditions and wind-chill is not modelled).

    Above the optimum:
      base_penalty  = 0.03 % per °C above 8 °C
      drift_factor  = linearly ramps from 1.0 (km 1) to 1.8 (km 42)
                      to capture progressive core-temp rise
      multiplier    = 1 + base_penalty × drift_factor

    At London's typical 15 °C this gives roughly +0.2 % at km 1
    rising to +0.4 % by km 42 — consistent with published data showing
    ~1-2 % total race slowdown at 15 °C vs ideal conditions.
    """
    if temp_celsius <= OPTIMAL_TEMP_C:
        return 1.0

    excess = temp_celsius - OPTIMAL_TEMP_C
    base_penalty = excess * HEAT_PENALTY_PER_C

    # Linear drift: 1.0 at km 1 → HEAT_DRIFT_MAX at km 42
    drift = 1.0 + (HEAT_DRIFT_MAX - 1.0) * ((distance_km - 1) / 41)

    return 1.0 + base_penalty * drift