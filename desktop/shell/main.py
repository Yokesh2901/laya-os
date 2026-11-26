"""
LAYA OS - Desktop Shell Coordinator
Coordinates top status panel, bottom dock, application launcher, and global keybindings.
"""

import sys
import os
import logging
from typing import Optional

from system.dbus.service import LayaSystemCore
from desktop.launcher.main import LayaLauncherWindow
from desktop.dock.main import LayaDock
from desktop.widgets.particle_orb import ParticleSphereSimulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("laya.shell")


class LayaDesktopShell:
    """Master controller for the LAYA Desktop environment."""

    def __init__(self):
        logger.info("Initializing LAYA Desktop Shell...")
        self.sys_core = LayaSystemCore()
        self.dock = LayaDock()
        self.launcher = LayaLauncherWindow()
        self.orb_simulator = ParticleSphereSimulator(num_particles=800)
        self.is_running = False

    def toggle_launcher(self):
        """Opens or closes the application launcher."""
        logger.info("[Shell] Toggling application launcher.")

    def run(self):
        """Starts the desktop shell event loop."""
        self.is_running = True
        logger.info("LAYA Desktop Shell active on Wayland session.")


def main():
    shell = LayaDesktopShell()
    shell.run()


if __name__ == "__main__":
    main()
