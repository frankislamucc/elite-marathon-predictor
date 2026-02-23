def fatigue_multiplier(distance_km, fatigue_coeff):
    if distance_km <= 30:
        return 1.0
    else:
        return 1.0 + fatigue_coeff * ((distance_km - 30) ** 1.3)