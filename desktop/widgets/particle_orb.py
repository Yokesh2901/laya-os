"""
LAYA OS - 3D Holographic Particle Sphere Widget
Generates 3D Fibonacci lattice points and renders 60 FPS audio-reactive GTK4 visualizations.
"""

import math
from typing import List, Tuple, Optional


class ParticleSphereSimulator:
    """Computes 3D Fibonacci sphere particle coordinates and perspective projection."""

    def __init__(self, num_particles: int = 1200):
        self.num_particles = num_particles
        self.points_3d = self._generate_fibonacci_sphere(num_particles)
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.audio_energy = 0.0

    @staticmethod
    def _generate_fibonacci_sphere(n: int) -> List[Tuple[float, float, float]]:
        """Distributes points evenly on a sphere using the Golden Ratio."""
        points = []
        phi = (1.0 + math.sqrt(5.0)) / 2.0
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

    def project_particles(
        self, width: int, height: int, scale: float = 80.0, audio_energy: float = 0.0
    ) -> List[Tuple[float, float, float, float]]:
        """
        Projects 3D points to 2D screen coordinates with perspective and audio responsiveness.
        Returns list of (screen_x, screen_y, depth, alpha).
        """
        cx = width / 2.0
        cy = height / 2.0
        distance = 3.0
        effective_scale = scale * (1.0 + min(audio_energy / 500.0, 0.4))

        cos_x, sin_x = math.cos(self.rot_x), math.sin(self.rot_x)
        cos_y, sin_y = math.cos(self.rot_y), math.sin(self.rot_y)

        projected = []
        for x, y, z in self.points_3d:
            x1 = x * cos_y + z * sin_y
            y1 = y
            z1 = -x * sin_y + z * cos_y

            x2 = x1
            y2 = y1 * cos_x - z1 * sin_x
            z2 = y1 * sin_x + z1 * cos_x

            depth = z2 + distance
            if depth > 0.1:
                factor = effective_scale / depth
                sx = cx + x2 * factor
                sy = cy + y2 * factor
                alpha = max(0.2, min(1.0, (z2 + 1.0) / 2.0))
                projected.append((sx, sy, depth, alpha))

        return projected


def create_gtk_orb_widget(size: int = 180, num_particles: int = 500):
    """Creates a GTK4 DrawingArea rendering the 60 FPS 3D Laya Particle Orb."""
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk, GLib

    sim = ParticleSphereSimulator(num_particles=num_particles)
    area = Gtk.DrawingArea()
    area.set_content_width(size)
    area.set_content_height(size)

    def on_draw(_area, cr, width, height):
        # Clear background (transparent)
        cr.set_source_rgba(0.035, 0.043, 0.094, 0.0)
        cr.paint()

        scale = min(width, height) * 0.9
        particles = sim.project_particles(width, height, scale=scale, audio_energy=sim.audio_energy)
        for sx, sy, depth, alpha in particles:
            # Blend between Electric Violet (#8B5CF6) and Cyan (#22D3EE) based on depth
            t = max(0.0, min(1.0, (depth - 2.0) / 2.0))
            r = 0.133 * (1 - t) + 0.545 * t
            g = 0.827 * (1 - t) + 0.361 * t
            b = 0.933 * (1 - t) + 0.965 * t
            cr.set_source_rgba(r, g, b, alpha * 0.9)
            radius = 1.2 + (1.0 - t) * 1.1
            cr.arc(sx, sy, radius, 0, 2 * math.pi)
            cr.fill()

    area.set_draw_func(on_draw)

    def on_tick():
        sim.update_rotation(0.016)
        area.queue_draw()
        return True

    GLib.timeout_add(16, on_tick)
    return area, sim
