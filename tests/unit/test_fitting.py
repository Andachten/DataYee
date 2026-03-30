"""Unit tests for fitting module."""

import pytest
import numpy as np
from src.core.fitting import (
    BE,
    Friddle,
    r2_calculate,
    fit,
)


class TestFittingModels:
    """Test energy landscape fitting models."""

    def test_be_model(self):
        """Test Bell-Evans model."""
        x = np.linspace(1e-9, 1e-6, 100)  # Loading rates
        x_beta = 5e-9  # Distance to barrier
        k_off = 1e-4  # Unfolding rate
        result = BE(x, x_beta, k_off)
        assert result.shape == x.shape
        assert np.all(result > 0)

    def test_friddle_model(self):
        """Test Friddle model."""
        x = np.linspace(1e-9, 1e-6, 100)
        x_beta = 5e-9
        k_off = 1e-4
        Feq = 10e-12
        result = Friddle(x, x_beta, k_off, Feq)
        assert result.shape == x.shape

    def test_r2_calculate(self):
        """Test R-squared calculation."""
        y_actual = np.array([1, 2, 3, 4, 5])
        y_predicted = np.array([1.1, 2.05, 2.95, 4.1, 4.9])
        r2 = r2_calculate(y_actual, y_predicted)
        assert 0 < r2 < 1

    def test_fit_be(self):
        """Test Bell-Evans fitting."""
        x_arr = np.linspace(1e-9, 1e-6, 50)
        y_arr = BE(x_arr, 5e-9, 1e-4) + np.random.normal(0, 1e-12, 50)
        bounds = [[1e-9, 20e-9], [1e-6, 1e-2]]
        result = fit(x_arr, y_arr, bounds, methods="BE")
        assert result is not False
        assert "r_2" in result
        assert "arg" in result
        assert result["r_2"] > 0
