"""Structural checks and a solver-backed reference case."""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from workforce_optimization.model import build_problem, check_solution
from workforce_optimization.solve import solve, require_optimal


class StaffingModelTests(unittest.TestCase):
    def test_overnight_break_and_paid_shift(self):
        p = build_problem()
        self.assertEqual(set(np.flatnonzero(p.coverage[:, 21])), {21, 22, 23, 1, 2, 3})
        self.assertEqual(p.shift_cost[15], 171)
        np.testing.assert_equal(p.coverage.sum(axis=0), np.full(24, 6))
        self.assertEqual(p.a.shape, (146, 144))

    def test_reported_optimum_and_actual_shortage(self):
        p = build_problem()
        r = require_optimal(solve(p))
        self.assertAlmostEqual(r["objective"], 184848, places=5)
        self.assertTrue(check_solution(p, r["values"])["feasible"])
        v = np.array(r["values"])
        np.testing.assert_allclose(v[72:96], np.maximum(p.demand[:, 0]-p.coverage@v[:24], 0))
        np.testing.assert_allclose(v[120:144], np.maximum(p.demand[:, 1]-p.coverage@v[24:48], 0))
        self.assertFalse(check_solution(p, np.zeros(144))["feasible"])


if __name__ == "__main__":
    unittest.main()
