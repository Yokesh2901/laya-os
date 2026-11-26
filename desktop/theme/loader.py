"""
LAYA OS - GTK4 Theme Loader
Loads laya-theme.css into the active Gdk.Display.
"""

from pathlib import Path
import logging

logger = logging.getLogger("laya.desktop.theme")


def apply_laya_theme():
    """Applies the LAYA OS Midnight Navy & Glassmorphism CSS theme to GTK4."""
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk, Gdk
    except (ImportError, ValueError):
        return False

    css_path = Path(__file__).parent / "laya-theme.css"
    if not css_path.exists():
        logger.warning(f"Theme CSS not found at {css_path}")
        return False

    display = Gdk.Display.get_default()
    if display is None:
        return False

    provider = Gtk.CssProvider()
    provider.load_from_path(str(css_path))
    Gtk.StyleContext.add_provider_for_display(
        display,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
    return True
