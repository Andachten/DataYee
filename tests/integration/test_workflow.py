"""Integration tests for complete workflows."""

import pytest
import numpy as np


class TestSMFSWorkflow:
    """Integration tests for SMFS (Single-Molecule Force Spectroscopy) workflow."""

    def test_workflow_imports(self):
        """Test that all core modules can be imported."""
        from src.core import data_processing, file_io, fitting, clustering
        from src.models import force_curve
        assert data_processing is not None
        assert file_io is not None
        assert fitting is not None
        assert clustering is not None
        assert force_curve is not None

    def test_force_curve_data_creation(self):
        """Test force curve data structure creation."""
        from src.models.force_curve import ForceCurveData, OffsetData

        fc = ForceCurveData()
        assert fc.tasktype == ""
        assert fc.springConstant == 0.01
        assert isinstance(fc.offset, OffsetData)

    def test_zipfileopera_creation(self):
        """Test archive manager creation."""
        from src.core.file_io import zipfileopera

        zpo = zipfileopera()
        assert zpo.version == "version2"
        assert len(zpo) == 0
