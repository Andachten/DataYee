"""Pytest configuration and fixtures"""

import pytest
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_raw_data():
    """Sample raw force curve data for testing"""
    import numpy as np

    length = 1000
    height = np.linspace(0, 1, length)
    deflection = np.sin(height * 10) * 100e-12

    return {
        "retract": {
            "measuredHeight": height.reshape(-1, 1).astype("<f4"),
            "vDeflection": deflection.reshape(-1, 1).astype("<f4"),
        },
        "extend": {
            "measuredHeight": height.reshape(-1, 1).astype("<f4"),
            "vDeflection": deflection.reshape(-1, 1).astype("<f4"),
        },
    }
