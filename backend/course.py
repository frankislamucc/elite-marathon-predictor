import numpy as np
import xml.etree.ElementTree as ET
import math
import os

# Pace multiplier model:
#   Uphill:   +0.033% per metre of elevation gain
#   Downhill: -0.018% per metre of elevation loss (less benefit than uphill cost)
GAIN_FACTOR = 0.00033
LOSS_FACTOR = 0.00018

GPX_NS = {"gpx": "http://www.topografix.com/GPX/1/1"}
DEFAULT_GPX = os.path.join(
    os.path.dirname(__file__),
    "gpx_20250427_id10099_race1_20241212094041.gpx",
)


def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres between two GPS points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _parse_gpx(gpx_path):
    """Return lists of cumulative distances (m) and elevations (m) from a GPX file."""
    tree = ET.parse(gpx_path)
    root = tree.getroot()

    points = []
    for trkpt in root.findall(".//gpx:trkpt", GPX_NS):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        ele_elem = trkpt.find("gpx:ele", GPX_NS)
        ele = float(ele_elem.text) if ele_elem is not None else 0.0
        points.append((lat, lon, ele))

    cum_dist = [0.0]
    for i in range(1, len(points)):
        d = _haversine(points[i - 1][0], points[i - 1][1], points[i][0], points[i][1])
        cum_dist.append(cum_dist[-1] + d)

    return cum_dist, points


def _interpolate_ele(cum_dist, points, target_m):
    """Linearly interpolate elevation at a given cumulative distance."""
    for i in range(1, len(cum_dist)):
        if cum_dist[i] >= target_m:
            span = cum_dist[i] - cum_dist[i - 1]
            frac = (target_m - cum_dist[i - 1]) / span if span else 0
            return points[i - 1][2] + frac * (points[i][2] - points[i - 1][2])
    return points[-1][2]


def _compute_km_multipliers(cum_dist, points, num_km=42):
    """Compute a pace multiplier per km from elevation gain/loss."""
    multipliers = []

    for km in range(num_km):
        start_m = km * 1000
        end_m = (km + 1) * 1000 if km < num_km - 1 else cum_dist[-1]

        start_ele = _interpolate_ele(cum_dist, points, start_m)
        end_ele = _interpolate_ele(cum_dist, points, end_m)

        # Walk through actual trackpoints inside this km for detailed gain/loss
        gain, loss = 0.0, 0.0
        prev_ele = start_ele

        for i in range(len(cum_dist)):
            if cum_dist[i] <= start_m:
                continue
            if cum_dist[i] > end_m:
                break
            diff = points[i][2] - prev_ele
            if diff > 0:
                gain += diff
            else:
                loss += abs(diff)
            prev_ele = points[i][2]

        # Account for interpolated endpoint
        diff = end_ele - prev_ele
        if diff > 0:
            gain += diff
        else:
            loss += abs(diff)

        multipliers.append(1.0 + gain * GAIN_FACTOR - loss * LOSS_FACTOR)

    return np.array(multipliers)


def LondonCourseProfile(gpx_path=DEFAULT_GPX):
    """Return a 42-element numpy array of pace multipliers parsed from GPX elevation data."""
    cum_dist, points = _parse_gpx(gpx_path)
    return _compute_km_multipliers(cum_dist, points)



