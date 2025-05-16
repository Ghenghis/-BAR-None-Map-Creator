import unittest
import numpy as np
from ai_terrain import AITerrainGenerator

class TestAITerrainGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = AITerrainGenerator()
        self.size = 128
        self.terrain_types = list(self.generator.patterns.keys())

    def test_generate_all_terrain_types(self):
        for terrain_type in self.terrain_types:
            with self.subTest(terrain_type=terrain_type):
                heightmap, ttype = self.generator.generate_terrain(size=self.size, terrain_type=terrain_type, seed=42)
                self.assertEqual(heightmap.shape, (self.size, self.size))
                self.assertTrue(np.all(heightmap >= 0) and np.all(heightmap <= 1))
                self.assertEqual(ttype, terrain_type)

    def test_generate_random_terrain_type(self):
        heightmap, ttype = self.generator.generate_terrain(size=self.size, terrain_type='random', seed=123)
        self.assertIn(ttype, self.terrain_types)
        self.assertEqual(heightmap.shape, (self.size, self.size))
        self.assertTrue(np.all(heightmap >= 0) and np.all(heightmap <= 1))

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            self.generator.generate_terrain(size=8)

    def test_invalid_terrain_type(self):
        with self.assertRaises(ValueError):
            self.generator.generate_terrain(size=self.size, terrain_type='invalid_type')

    def test_save_preview(self):
        heightmap, _ = self.generator.generate_terrain(size=self.size, terrain_type='hills', seed=99)
        filename = 'test_preview.png'
        result = self.generator.save_preview(heightmap, filename)
        self.assertEqual(result, filename)

if __name__ == '__main__':
    unittest.main()
