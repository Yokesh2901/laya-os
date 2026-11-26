"""
LAYA OS - 3D Holographic Particle Sphere Widget
Generates 3D Fibonacci lattice points and projects audio-reactive particle visualizations.
"""

import math
from typing import List, Tuple


class ParticleSphereSimulator:
    """Computes 3D Fibonacci sphere particle coordinates and perspective projection."""

    def __init__(self, num_particles: int = 1200):
        self.num_particles = num_particles
        self.points_3d = self._generate_fibonacci_sphere(num_particles)
        self.rot_x = 0.0
        self.rot_y = 0.0

    @staticmethod
    def _generate_fibonacci_sphere(n: int) -> List[Tuple[float, float, float]]:
        """Distributes points evenly on a sphere using the Golden Ratio."""
        points = []
        phi = (1.0 + math.sqrt(5.0)) / 2.0  # Golden ratio
        for i in range(n):
            y = 1.0 - (2.0 * i) / float(n - 1) if n > 1 else 0.0
            radius = math.sqrt(max(0.0, 1.0 - y * y))
            theta = 2.0 * math.pi * i / phi
            x = radius * math.cos(theta)
            z = radius * math.sin(theta)
            points.append((x, y, z))
        return points

    def update_rotation(self, delta_time: float = 0.016):
        """Advances rotation angles for 60 FPS animation."""
        self.rot_x += 0.5 * delta_time
        self.rot_y += 0.8 * delta_time

    def project_particles(self, width: int, height: int, scale: float = 80.0, audio_energy: float = 0.0) -> List[Tuple[float, float, float, float]]:
        """
        Projects 3D points to 2D screen coordinates with perspective and audio responsiveness.
        Returns list of (screen_x, screen_y, depth, alpha).
        """
        cx = width / 2.0
        cy = height / 2.0
        distance = 3.0
        # Expand sphere with audio energy
        effective_scale = scale * (1.0 + min(audio_energy / 500.0, 0.4))

        cos_x, sin_x = math.cos(self.rot_x), math.sin(self.rot_x)
        cos_y, sin_y = math.sin(self.rot_y), math.cos(self.rot_y)

        projected = []
        for x, y, z in self.points_3d:
            # Rotate around Y axis
            x1 = x * cos_y + z * sin_y
            y1 = y
            z1 = -x * sin_y + z * cos_y

            # Rotate around X axis
            x2 = x1
            y2 = y1 * cos_x - z1 * sin_x
            z2 = y1 * sin_x + z1 * cos_x

            # Perspective projection
            depth = z2 + distance
            if depth > 0.1:
                factor = effective_scale / depth
                sx = cx + x2 * factor
                sy = cy + y2 * factor
                alpha = max(0.2, min(1.0, (z2 + 1.0) / 2.0))
                projected.append((sx, sy, depth, alpha))

        return projected
