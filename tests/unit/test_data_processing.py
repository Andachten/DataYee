"""Unit tests for data processing functions."""

import pytest
import numpy as np
from src.core.data_processing import (
    lcfunc,
    wlc2lc,
    lcfunc1d,
    rotate,
    get_slope,
    is_number,
    WRC_transformer,
    Lc_transformer,
    mlti_Gaussian,
)


class TestWLCFunctions:
    """Test WLC (Worm-Like Chain) functions."""

    def test_lcfunc_basic(self):
        """Test basic WLC force calculation."""
        x = np.linspace(0.1e-9, 1e-9, 50)
        lc = 50e-9
        lp = 0.36e-9
        result = lcfunc(x, lc, lp)
        assert result.shape == x.shape
        assert np.all(result > 0)

    def test_lcfunc1d(self):
        """Test 1D WLC force calculation."""
        x = 10.0  # nm
        lc = 30.0  # nm
        lp = 0.36  # nm
        result = lcfunc1d(x, lc, lp)
        assert isinstance(result, float)
        assert result > 0

    def test_wlc2lc_conversion(self):
        """Test WLC contour length conversion."""
        x = np.array([10e-9, 20e-9, 30e-9])
        f = np.array([10e-12, 50e-12, 100e-12])
        lp = np.array([0.36e-9])
        result = wlc2lc(x, f, lp)
        assert result.shape == x.shape

    def test_rotate(self):
        """Test rotation function."""
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        result = rotate(x, y, 50, 0.1)
        assert result.shape == x.shape

    def test_get_slope(self):
        """Test slope calculation."""
        x = np.linspace(0, 10, 100)
        y = 2 * x + 1
        slope = get_slope(x, y, index=-1)
        assert abs(slope - 2.0) < 0.1


class TestUtilities:
    """Test utility functions."""

    def test_is_number(self):
        """Test string number checking."""
        assert is_number("3.14") is True
        assert is_number("42") is True
        assert is_number("hello") is False
        assert is_number("3.14.15") is False


class TestTransformers:
    """Test data transformation functions."""

    def test_wrc_transformer(self):
        """Test WRC transformation."""
        f = np.array([20, 30, 40, 50, 60])
        x = np.array([10, 20, 30, 40, 50])
        force, lc = WRC_transformer(f, x, thr=20)
        assert len(force) == len(lc)
        assert np.all(force >= 20)

    def test_multi_gaussian(self):
        """Test multi-Gaussian function."""
        x = np.linspace(0, 100, 200)
        params = [25, 10, 5, 75, 15, 3]
        result = mlti_Gaussian(x, *params)
        assert result.shape == x.shape
        assert np.max(result) > 0
