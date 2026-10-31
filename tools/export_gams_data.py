"""Regenerate the GAMS input include from the canonical Python input files."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from workforce_optimization.model import build_problem, load_data


def main():
    problem = build_problem()
    demand, config = load_data()
    lines = ["* Generated from data/hourly_demand.csv and data/parameters.json.",
             "* Regenerate with: python tools/export_gams_data.py", ""]
    for h in range(24):
        for c, name in enumerate(["parsian", "mehr"]):
            lines.append(f"demand('{name}','h{h}') = {demand[h,c]};")
        lines.append(f"shiftCost('h{h}') = {problem.shift_cost[h]:g};")
        penalty = config['penalty_parsian_day'] if 7 <= h < 18 else config['penalty_parsian_night']
        lines.append(f"penalty('parsian','h{h}') = {penalty};")
        lines.append(f"penalty('mehr','h{h}') = {config['penalty_mehr']};")
    names = {"shiftCap": "shift_capacity", "activeMin": "minimum_active",
             "activeMax": "maximum_active", "shortageMax": "hourly_shortage_limit"}
    for gams, key in names.items():
        lines.append(f"{gams} = {config[key]};")
    lines.extend([f"dailyCap('parsian') = {config['daily_shortage_parsian']};",
                  f"dailyCap('mehr') = {config['daily_shortage_mehr']};"])
    (ROOT / "gams/data.inc").write_text("\n".join(lines)+"\n")


if __name__ == "__main__":
    main()
