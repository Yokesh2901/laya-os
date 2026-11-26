"""
Unit tests for LAYA OS 3D Fibonacci Particle Sphere simulation.
"""

import pytest
from desktop.widgets.particle_orb import ParticleSphereSimulator


def test_particle_sphere_generation():
    sim = ParticleSphereSimulator(num_particles=500)
    assert len(sim.points_3d) == 500

    # Ensure points lie on unit sphere (radius ~= 1.0)
    for x, y, z in sim.points_3d[:20]:
        radius_sq = x * x + y * y + z * z
        assert abs(radius_sq - 1.0) < 0.05


def test_particle_projection():
    sim = ParticleSphereSimulator(num_particles=200)
    sim.update_rotation(delta_time=0.016)

    projected = sim.project_particles(width=800, height=600, scale=100.0, audio_energy=150.0)
    assert len(projected) > 0

    for sx, sy, depth, alpha in projected[:20]:
        assert isinstance(sx, float)
        assert isinstance(sy, float)
        assert depth > 0.0
        assert 0.0 <= alpha <= 1.0
