"""Figures drawn only from certified, exported numerical results."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_plots(directory):
    directory = Path(directory)
    figures = directory / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "savefig.facecolor": "white"})
    rows = read_csv(directory / "hourly_coverage.csv")
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True, layout="constrained")
    for ax, key, title, color in zip(axes, ("parsian", "mehr"),
                                   ("Parsian", "Mehr Iranian"), ("#146C94", "#A0522D")):
        hours = [int(r["hour"]) for r in rows]
        demand = [int(r[f"demand_{key}"]) for r in rows]
        active = [int(r[f"active_{key}"]) for r in rows]
        ax.step(hours, demand, where="mid", label="Required operators", color="#58636D", linestyle="--", lw=1.8)
        ax.step(hours, active, where="mid", label="Scheduled active operators", color=color, lw=2)
        ax.fill_between(hours, active, demand, where=[a < d for a, d in zip(active, demand)],
                        step="mid", color="#D76752", alpha=.22, label="Shortage")
        ax.set(title=title, ylabel="Active operators", xlim=(-.5, 23.5))
        ax.grid(axis="y", alpha=.18)
        ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=8)
    axes[-1].set(xlabel="Hour of day", xticks=list(range(0, 24, 2)))
    fig.suptitle("Demand and scheduled coverage across 24 hours", fontsize=15)
    fig.savefig(figures / "hourly_coverage.png", dpi=180)
    plt.close(fig)
    definitions = [
        ("parsian_shortage_cap", "Daily Parsian shortage allowance (operator-hours)",
         "Allowing more shortage reduces the minimum total cost", 40),
        ("shift_04_cost", "Cost of one shift starting at 04:00 (monetary units)",
         "Cost sensitivity for the shift starting at 04:00", 171)]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for ax, (name, label, title, base) in zip(axes, definitions):
        records = read_csv(directory / f"{name}.csv")
        if any(r["status"] != "optimal" for r in records):
            raise ValueError("Cannot label uncertified results as optimal in a figure.")
        x = [float(r["parameter_value"]) for r in records]
        y = [float(r["objective"]) for r in records]
        ax.plot(x, y, "o-", color="#146C94", markersize=3, lw=1.8)
        ax.axvline(base, color="#A0522D", linestyle="--", label=f"Base value: {base}")
        ax.set(title=title, xlabel=label, ylabel="Minimum total cost (monetary units)")
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.grid(alpha=.18)
        ax.legend(frameon=False, fontsize=8)
    fig.savefig(figures / "scenario_analysis.png", dpi=180)
    plt.close(fig)
