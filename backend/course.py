import numpy as np

# Course profile for London Marathon
def LondonCourseProfile():
    profile = np.ones(42)

    profile[0:5] *= 0.998 #adrenaline from the start
    profile[20:25] *= 1.002 # Tower Bridge climb + slight fatigue
    profile[35:40] *= 1.003 # Late race fatigue

    return profile



