import numpy as np
from PIL import Image
import random
from scipy.ndimage import gaussian_filter
from typing import Tuple, Optional, Dict, Callable


class AITerrainGenerator:
    """
    Robust and extensible AI terrain generator for BAR map creation.
    Supports multiple terrain patterns and utility functions.
    """

    def __init__(self):
        self.patterns: Dict[str, Callable[[int], np.ndarray]] = {
            'mountain_range': self._generate_mountain_range,
            'river_valley': self._generate_river_valley,
            'plateau': self._generate_plateau,
            'crater': self._generate_crater,
            'hills': self._generate_hills,
            'archipelago': self._generate_archipelago
        }

    def generate_terrain(
        self,
        size: int = 1024,
        terrain_type: str = 'random',
        seed: Optional[int] = None,
        noise_level: float = 0.05,
        smoothing: float = 2.0
    ) -> Tuple[np.ndarray, str]:
        """
        Generate a terrain heightmap.
        Args:
            size: Size of the square heightmap.
            terrain_type: Type of terrain ('random' or one of the patterns).
            seed: Optional RNG seed.
            noise_level: Amplitude of added noise.
            smoothing: Sigma value for Gaussian smoothing.
        Returns:
            heightmap: 2D numpy array of floats in [0, 1].
            terrain_type: The terrain type used.
        """
        self._validate_size(size)
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        if terrain_type == 'random':
            terrain_type = random.choice(list(self.patterns.keys()))
        if terrain_type not in self.patterns:
            raise ValueError(f"Unknown terrain type: {terrain_type}")
        heightmap = self.patterns[terrain_type](size)
        if noise_level > 0:
            heightmap += np.random.normal(0, noise_level, (size, size))
        if smoothing > 0:
            heightmap = gaussian_filter(heightmap, sigma=smoothing)
        heightmap = self._normalize(heightmap)
        return heightmap, terrain_type

    @staticmethod
    def _normalize(heightmap: np.ndarray) -> np.ndarray:
        min_val = np.min(heightmap)
        max_val = np.max(heightmap)
        if max_val - min_val == 0:
            return np.zeros_like(heightmap)
        return (heightmap - min_val) / (max_val - min_val)

    @staticmethod
    def _validate_size(size: int):
        if not isinstance(size, int) or size < 16:
            raise ValueError("Size must be an integer >= 16.")

    def _generate_mountain_range(self, size: int) -> np.ndarray:
        heightmap = np.zeros((size, size), dtype=np.float32)
        ridge_direction = random.uniform(0, np.pi)
        ridge_offset = random.uniform(-size/4, size/4)
        for i in range(size):
            for j in range(size):
                dist = abs(i * np.cos(ridge_direction) + j * np.sin(ridge_direction) - ridge_offset)
                height = np.exp(-dist**2 / (2 * (size/5)**2))
                heightmap[i, j] += height
        for _ in range(5):
            x = random.randint(0, size-1)
            y = random.randint(0, size-1)
            radius = random.randint(size//10, size//5)
            peak_height = random.uniform(0.5, 1.0)
            for i in range(max(0, x-radius), min(size, x+radius)):
                for j in range(max(0, y-radius), min(size, y+radius)):
                    dist = np.sqrt((i-x)**2 + (j-y)**2)
                    if dist < radius:
                        heightmap[i, j] += peak_height * (1 - dist/radius)
        return heightmap

    def _generate_river_valley(self, size: int) -> np.ndarray:
        heightmap = np.ones((size, size), dtype=np.float32) * 0.7
        points = self._generate_river_points(size)
        river_width = size // 20
        valley_width = size // 5
        for i in range(size):
            for j in range(size):
                min_dist = self._min_dist_to_river(i, j, points)
                heightmap[i, j] = self._river_valley_height(min_dist, river_width, valley_width)
        return heightmap

    @staticmethod
    def _generate_river_points(size: int):
        points = []
        x = random.randint(0, size//4)
        y = random.randint(0, size-1)
        points.append((x, y))
        while x < size-1:
            x += random.randint(size//20, size//10)
            y_change = random.randint(-size//10, size//10)
            y = max(0, min(size-1, y + y_change))
            points.append((x, y))
        return points

    def _min_dist_to_river(self, i: int, j: int, points) -> float:
        min_dist = float('inf')
        for p1, p2 in zip(points[:-1], points[1:]):
            line_dist = self._point_to_line_dist(i, j, p1[0], p1[1], p2[0], p2[1])
            min_dist = min(min_dist, line_dist)
        return min_dist

    @staticmethod
    def _river_valley_height(min_dist, river_width, valley_width):
        if min_dist < river_width:
            return 0.1
        elif min_dist < valley_width:
            valley_factor = (min_dist - river_width) / (valley_width - river_width)
            return 0.1 + 0.6 * valley_factor
        else:
            return 0.7

    def _generate_plateau(self, size: int) -> np.ndarray:
        heightmap = np.zeros((size, size), dtype=np.float32)
        noise = np.random.normal(0, 0.1, (size, size))
        heightmap += noise
        num_plateaus = random.randint(2, 5)
        for _ in range(num_plateaus):
            cx = random.randint(size//4, 3*size//4)
            cy = random.randint(size//4, 3*size//4)
            plateau_radius = random.randint(size//8, size//4)
            plateau_height = random.uniform(0.5, 0.8)
            for i in range(size):
                for j in range(size):
                    dist = np.sqrt((i-cx)**2 + (j-cy)**2)
                    if dist < plateau_radius:
                        heightmap[i, j] = max(heightmap[i, j], plateau_height)
                    elif dist < plateau_radius + size//20:
                        edge_factor = 1 - (dist - plateau_radius) / (size//20)
                        cliff_height = plateau_height * edge_factor
                        heightmap[i, j] = max(heightmap[i, j], cliff_height)
        return heightmap

    def _generate_crater(self, size: int) -> np.ndarray:
        heightmap = np.ones((size, size), dtype=np.float32) * 0.6
        num_craters = random.randint(3, 8)
        for _ in range(num_craters):
            cx = random.randint(size//8, 7*size//8)
            cy = random.randint(size//8, 7*size//8)
            crater_radius = random.randint(size//16, size//8)
            rim_height = random.uniform(0.2, 0.4)
            for i in range(max(0, cx-crater_radius*2), min(size, cx+crater_radius*2)):
                for j in range(max(0, cy-crater_radius*2), min(size, cy+crater_radius*2)):
                    dist = np.sqrt((i-cx)**2 + (j-cy)**2)
                    if dist < crater_radius:
                        crater_depth = 0.3 * (dist / crater_radius)
                        heightmap[i, j] = min(heightmap[i, j], 0.3 + crater_depth)
                    elif dist < crater_radius * 1.2:
                        rim_factor = 1 - (dist - crater_radius) / (0.2 * crater_radius)
                        heightmap[i, j] += rim_height * rim_factor
        return heightmap

    def _generate_hills(self, size: int) -> np.ndarray:
        heightmap = np.zeros((size, size), dtype=np.float32)
        scale = size // 64
        for octave in range(1, 5):
            octave_scale = scale * (2 ** octave)
            amplitude = 1.0 / octave
            grid_size = size // octave_scale + 2
            grid = np.random.rand(grid_size, grid_size)
            for i in range(size):
                for j in range(size):
                    grid_i = i / octave_scale
                    grid_j = j / octave_scale
                    i0 = int(grid_i)
                    j0 = int(grid_j)
                    i1 = i0 + 1
                    j1 = j0 + 1
                    si = grid_i - i0
                    sj = grid_j - j0
                    si = si * si * (3 - 2 * si)
                    sj = sj * sj * (3 - 2 * sj)
                    v00 = grid[i0, j0]
                    v01 = grid[i0, j1]
                    v10 = grid[i1, j0]
                    v11 = grid[i1, j1]
                    v0 = v00 * (1 - si) + v10 * si
                    v1 = v01 * (1 - si) + v11 * si
                    value = v0 * (1 - sj) + v1 * sj
                    heightmap[i, j] += value * amplitude
        return heightmap

    def _generate_archipelago(self, size: int) -> np.ndarray:
        heightmap = np.zeros((size, size), dtype=np.float32)
        heightmap.fill(0.2)
        num_islands = random.randint(5, 15)
        for _ in range(num_islands):
            cx = random.randint(size//8, 7*size//8)
            cy = random.randint(size//8, 7*size//8)
            island_radius = random.randint(size//16, size//8)
            island_height = random.uniform(0.4, 0.7)
            for i in range(max(0, cx-island_radius*2), min(size, cx+island_radius*2)):
                for j in range(max(0, cy-island_radius*2), min(size, cy+island_radius*2)):
                    dist = np.sqrt((i-cx)**2 + (j-cy)**2)
                    if dist < island_radius:
                        island_factor = 1 - (dist / island_radius) ** 2
                        heightmap[i, j] = max(heightmap[i, j], 0.3 + island_height * island_factor)
        return heightmap

    @staticmethod
    def _point_to_line_dist(x, y, x1, y1, x2, y2):
        A = x - x1
        B = y - y1
        C = x2 - x1
        D = y2 - y1
        dot = A * C + B * D
        len_sq = C * C + D * D
        if len_sq == 0:
            return np.sqrt(A * A + B * B)
        param = dot / len_sq
        if param < 0:
            xx = x1
            yy = y1
        elif param > 1:
            xx = x2
            yy = y2
        else:
            xx = x1 + param * C
            yy = y1 + param * D
        return np.sqrt((x - xx) ** 2 + (y - yy) ** 2)

    @staticmethod
    def save_preview(heightmap: np.ndarray, filename: str = "terrain_preview.png") -> str:
        """
        Save a preview image of the heightmap.
        Args:
            heightmap: 2D numpy array.
            filename: Output filename.
        Returns:
            The filename used.
        """
        img_data = (AITerrainGenerator._normalize(heightmap) * 255).astype(np.uint8)
        img = Image.fromarray(img_data)
        img.save(filename)
        return filename
