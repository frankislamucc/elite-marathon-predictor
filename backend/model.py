import numpy as np


# ---------------------------------------------------------------------------
# Fatigue model
# ---------------------------------------------------------------------------
# The fatigue coefficient is no longer a single fixed value.  Each simulation
# draws from a log-normal distribution whose *median* depends on the runner's
# calibre (PB).  This means:
#   - Most races: moderate, realistic fatigue
#   - Some races: an unusually good day (low fatigue)
#   - Some races: a total bonk (high fatigue — 5-10+ min slower)
#
# The sigma of the log-normal controls how wild the variance is.

# Tier thresholds (PB in seconds) and their median fatigue coefficients + sigma
# Faster runners are more consistent but still vulnerable.
FATIGUE_TIERS = [
    # (max_pb_seconds, median_coeff, sigma)
    (2 * 3600 + 5 * 60,   0.0008,  1.0),   # World-class (sub-2:05)
    (2 * 3600 + 10 * 60,  0.0014,  1.1),   # International elite (2:05–2:10)
    (2 * 3600 + 15 * 60,  0.0022,  1.2),   # Sub-elite (2:10–2:15)
    (float("inf"),         0.0035,  1.3),   # Club-level (2:15+)
]


def get_fatigue_tier(pb_seconds):
    """Return (median_coeff, sigma) for a runner's PB."""
    for max_pb, coeff, sigma in FATIGUE_TIERS:
        if pb_seconds <= max_pb:
            return coeff, sigma
    return FATIGUE_TIERS[-1][1], FATIGUE_TIERS[-1][2]


def sample_fatigue_coeff(pb_seconds, rng=None):
    """Draw a random fatigue coefficient for one simulated race.

    Uses a log-normal distribution so the median race is 'normal' but there
    is a long right tail of blow-up performances.
    """
    if rng is None:
        rng = np.random.default_rng()
    median, sigma = get_fatigue_tier(pb_seconds)
    # log-normal: median = exp(mu), so mu = ln(median)
    mu = np.log(median)
    return rng.lognormal(mu, sigma)


def fatigue_multiplier(distance_km, fatigue_coeff):
    """Per-km pace multiplier from fatigue.  Onset after 30 km."""
    if distance_km <= 30:
        return 1.0
    else:
        return 1.0 + fatigue_coeff * ((distance_km - 30) ** 1.8)


# ---------------------------------------------------------------------------
# DNF model
# ---------------------------------------------------------------------------
# Base DNF probability per race, scaled by tier.  At major marathons ~2-5%
# of elite starters DNF.  We model this as a per-km hazard that increases
# sharply after 30 km — most DNFs happen in the last 12 km.

DNF_BASE_RATES = [
    # (max_pb_seconds, race_dnf_probability)
    (2 * 3600 + 5 * 60,   0.03),   # 3% for world-class
    (2 * 3600 + 10 * 60,  0.05),   # 5% for international
    (2 * 3600 + 15 * 60,  0.07),   # 7% for sub-elite
    (float("inf"),         0.10),   # 10% for club-level
]


def get_dnf_rate(pb_seconds):
    """Return overall race DNF probability for a runner's calibre."""
    for max_pb, rate in DNF_BASE_RATES:
        if pb_seconds <= max_pb:
            return rate
    return DNF_BASE_RATES[-1][1]


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