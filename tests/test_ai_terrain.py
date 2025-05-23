# In tests/test_ai_terrain.py
import pytest
import numpy as np
from ai_terrain import AITerrainGenerator

def test_ai_terrain_normalize():
    heightmap1 = np.array([[0, 50], [100, 100]], dtype=np.float32)
    normalized1 = AITerrainGenerator._normalize(heightmap1)
    # Expected: (arr - min) / (max - min) -> (arr - 0) / (100 - 0)
    expected1 = np.array([[0/100, 50/100], [100/100, 100/100]], dtype=np.float32)
    assert np.array_equal(normalized1, expected1)

    heightmap2 = np.array([[10, 10], [10, 10]], dtype=np.float32) # Flat
    normalized2 = AITerrainGenerator._normalize(heightmap2)
    # Expected: if max == min, should return all zeros
    assert np.array_equal(normalized2, np.array([[0, 0], [0, 0]], dtype=np.float32))

    heightmap3 = np.array([[0, 0.5], [1.0, 0.75]], dtype=np.float32) # Already in [0,1] but not normalized to its own range
    normalized3 = AITerrainGenerator._normalize(heightmap3) 
    # Expected: (arr - min) / (max - min) -> (arr - 0) / (1.0 - 0)
    expected3 = (heightmap3 - np.min(heightmap3)) / (np.max(heightmap3) - np.min(heightmap3))
    assert np.allclose(normalized3, expected3)

    heightmap4 = np.array([[-10, 0], [10, 20]], dtype=np.float32)
    normalized4 = AITerrainGenerator._normalize(heightmap4)
    # Expected: (arr - (-10)) / (20 - (-10)) -> (arr + 10) / 30
    expected4 = (heightmap4 - (-10)) / (20 - (-10))
    assert np.allclose(normalized4, expected4)
