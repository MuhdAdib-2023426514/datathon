"""
Synthetic Gravity Model Unit Tests (W0 / W6)
Tests predictive R² formula vs squared correlation and zero flow behavior.
"""

import unittest
import numpy as np


def calc_predictive_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """True out-of-sample predictive R² = 1 - (SSE / SST)."""
    sse = np.sum((y_true - y_pred) ** 2)
    sst = np.sum((y_true - np.mean(y_true)) ** 2)
    if sst == 0:
        return 0.0
    return float(1.0 - (sse / sst))


def calc_corr_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Squared Pearson correlation."""
    if len(y_true) < 2 or np.std(y_true) == 0 or np.std(y_pred) == 0:
        return 0.0
    r = np.corrcoef(y_true, y_pred)[0, 1]
    return float(r ** 2)


class TestGravityFixtures(unittest.TestCase):
    def test_predictive_r2_vs_squared_correlation(self):
        """
        Regression test for Finding 5:
        Demonstrate that a severely miscalibrated model (e.g. predicting 10x true value)
        can have Corr^2 = 1.0 while having a deeply negative predictive R².
        """
        y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        # Model predicts perfectly linearly, but with massive bias/scale error:
        y_pred = y_true * 10.0  # [100, 200, 300, 400, 500]

        r2_corr = calc_corr_squared(y_true, y_pred)
        r2_pred = calc_predictive_r2(y_true, y_pred)

        self.assertAlmostEqual(r2_corr, 1.0, places=4)
        # Predictive R² must be heavily negative because SSE >> SST
        self.assertLess(r2_pred, -50.0)

    def test_well_calibrated_predictions(self):
        y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        y_pred = np.array([11.0, 19.0, 31.0, 39.0, 50.0])

        r2_pred = calc_predictive_r2(y_true, y_pred)
        self.assertGreater(r2_pred, 0.95)


if __name__ == "__main__":
    unittest.main()
