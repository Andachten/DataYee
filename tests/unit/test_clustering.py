"""Unit tests for clustering module."""

import pytest
import numpy as np
from src.core.clustering import (
    Lc_transformer,
    count_0,
    wlc_dist,
    sort_similar,
    KMsClustering,
)


class TestClusteringFunctions:
    """Test clustering functions."""

    def test_count_0(self):
        """Test count_0 function."""
        x = np.array([[1, 2], [3, 4], [5, 6]])
        result = count_0(x)
        assert isinstance(result, int)
        assert result >= 0

    def test_wlc_dist(self):
        """Test WLC distance calculation."""
        s1 = np.array([10, 20, 15, 25, 30, 40, 20, 30])
        s2 = np.array([12, 22, 18, 28, 32, 42, 22, 32])
        result = wlc_dist(s1, s2)
        assert 0 <= result <= 1

    def test_sort_similar(self):
        """Test similarity sorting."""
        matrix = np.array([
            [0, 1, 2, 3],
            [1, 0, 1.5, 2.5],
            [2, 1.5, 0, 2],
            [3, 2.5, 2, 0],
        ])
        result = sort_similar(0, matrix)
        assert result[0] == 0  # First should be itself
        assert len(result) == 4

    def test_kmeans_clustering(self):
        """Test KMeans clustering."""
        matrix = np.array([
            [0, 1, 10, 11],
            [1, 0, 9, 10],
            [10, 9, 0, 1],
            [11, 10, 1, 0],
        ])
        labels = KMsClustering(matrix, n_clusters=2)
        assert len(labels) == 4
        assert set(labels).issubset({0, 1})
