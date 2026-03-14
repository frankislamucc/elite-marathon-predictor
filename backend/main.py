#!/usr/bin/env python3
"""
Elite Marathon Predictor — CLI
Run predictions for the 2026 TCS London Marathon entirely from the terminal.
"""

import sys
from simulation import simulate_race_per_km
from runners import ELITE_MEN_2026


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def time_to_seconds(time_str):
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        h, m, s = map(int, parts)
    elif len(parts) == 2:
        h, m, s = 0, int(parts[0]), int(parts[1])
    else:
        raise ValueError(f"Invalid time format: {time_str!r}  (expected H:MM:SS or MM:SS)")
    return h * 3600 + m * 60 + s


def seconds_to_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}:{m:02d}:{s:02d}"


BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║          🏃  Elite Marathon Predictor  🏃                   ║
║          2026 TCS London Marathon Simulator                 ║
╚══════════════════════════════════════════════════════════════╝
"""


# ------------------------------q---------------------------------------------
# Single-runner prediction
# ---------------------------------------------------------------------------
def predict_single():
    """Prompt the user for a PB and temperature, then run a prediction."""
    print("\n── Single Runner Prediction ──\n")

    pb_time = input("  Enter marathon PB (H:MM:SS): ").strip()
    try:
        pb_seconds = time_to_seconds(pb_time)
    except ValueError as e:
        print(f"  ✗ {e}")
        return

    temp_input = input("  Race-day temperature in °C [15]: ").strip()
    temp_celsius = float(temp_input) if temp_input else 15.0

    sims_input = input("  Number of simulations [10000]: ").strip()
    simulations = int(sims_input) if sims_input else 10000

    print(f"\n  Running {simulations:,} simulations … ", end="", flush=True)
    result = simulate_race_per_km(pb_seconds, temp_celsius=temp_celsius, simulations=simulations)
    print("done.\n")

    print(f"  ┌─────────────────────────────────────────┐")
    print(f"  │  PB               : {pb_time:<20s}│")
    print(f"  │  Temperature      : {temp_celsius}°C{' ' * (16 - len(str(temp_celsius)))}│")
    print(f"  │  Simulations      : {simulations:<20,d}│")
    print(f"  ├─────────────────────────────────────────┤")
    print(f"  │  Predicted median : {seconds_to_time(result['median']):<20s}│")
    print(f"  │  Predicted mean   : {seconds_to_time(result['mean_time']):<20s}│")
    print(f"  │  Best 5%          : {seconds_to_time(result['p5']):<20s}│")
    print(f"  │  Worst 5%         : {seconds_to_time(result['p95']):<20s}│")
    std_str = f"{result['std_dev']:.1f}s"
    dnf_str = f"{result['dnf_rate']:.1%}"
    print(f"  │  Std deviation    : {std_str:<20s}│")
    print(f"  │  DNF rate         : {dnf_str:<20s}│")
    print(f"  └─────────────────────────────────────────┘")

    # Per-km splits
    show = input("\n  Show per-km average splits? (y/N): ").strip().lower()
    if show == "y":
        mean_splits = result["mean_splits"]
        print()
        print(f"  {'KM':>4s}  {'Split':>8s}  {'Cumulative':>10s}")
        print(f"  {'─' * 4}  {'─' * 8}  {'─' * 10}")
        cumulative = 0.0
        for i, split in enumerate(mean_splits, 1):
            cumulative += split
            print(f"  {i:4d}  {seconds_to_time(split):>8s}  {seconds_to_time(cumulative):>10s}")


# ---------------------------------------------------------------------------
# Full elite field leaderboard
# ---------------------------------------------------------------------------
def leaderboard():
    """Simulate every runner in the 2026 elite men's field and print a leaderboard."""
    print("\n── 2026 TCS London Marathon — Elite Men's Leaderboard ──\n")

    temp_input = input("  Race-day temperature in °C [15]: ").strip()
    temp_celsius = float(temp_input) if temp_input else 15.0

    sims_input = input("  Simulations per runner [10000]: ").strip()
    simulations = int(sims_input) if sims_input else 10000

    field = list(ELITE_MEN_2026.items())
    total = len(field)
    results = []

    print(f"\n  Simulating {total} runners × {simulations:,} races each …")

    for idx, (name, pb) in enumerate(field, 1):
        pct = idx / total * 100
        print(f"\r  [{idx:2d}/{total}] {pct:5.1f}%  {name:<25s}", end="", flush=True)

        pb_seconds = time_to_seconds(pb)
        r = simulate_race_per_km(pb_seconds, temp_celsius=temp_celsius, simulations=simulations)

        dnf_pct = r["dnf_rate"]
        is_dnf = dnf_pct > 0.5

        results.append({
            "name": name,
            "pb": pb,
            "predicted_time": "DNF" if is_dnf else seconds_to_time(r["median"]),
            "predicted_seconds": float("inf") if is_dnf else r["median"],
            "dnf_rate": f"{dnf_pct:.1%}",
            "status": "DNF" if is_dnf else "Finished",
        })

    print("\r" + " " * 60, end="\r")  # clear progress line

    # Sort: finishers first by time, then DNFs
    results.sort(key=lambda x: (x["status"] == "DNF", x["predicted_seconds"]))

    # Print table
    print(f"\n  Race conditions: {temp_celsius}°C  |  {simulations:,} simulations per runner\n")
    print(f"  {'#':>3s}  {'Runner':<25s}  {'PB':>8s}  {'Predicted':>9s}  {'DNF%':>6s}  Status")
    print(f"  {'─' * 3}  {'─' * 25}  {'─' * 8}  {'─' * 9}  {'─' * 6}  {'─' * 8}")

    for i, r in enumerate(results, 1):
        marker = "  🔴" if r["status"] == "DNF" else ""
        print(
            f"  {i:3d}  {r['name']:<25s}  {r['pb']:>8s}  {r['predicted_time']:>9s}"
            f"  {r['dnf_rate']:>6s}  {r['status']}{marker}"
        )

    print()


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------
def main():
    print(BANNER)

    while True:
        print("  Choose an option:\n")
        print("    [1]  Predict a single runner")
        print("    [2]  Full elite-field leaderboard")
        print("    [q]  Quit\n")

        choice = input("  ▸ ").strip().lower()

        if choice == "1":
            predict_single()
            print()
        elif choice == "2":
            leaderboard()
        elif choice in ("q", "quit", "exit"):
            print("  Goodbye! 👋\n")
            sys.exit(0)
        else:
            print("  ✗ Invalid choice, try again.\n")


if __name__ == "__main__":
    main()