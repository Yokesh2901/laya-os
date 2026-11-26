"""
Unit tests validating LAYA OS systemd services, installer, and ISO build configuration.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_systemd_services_use_venv_and_pythonpath():
    sys_svc = (REPO_ROOT / "system/services/laya-system.service").read_text(encoding="utf-8")
    ai_svc = (REPO_ROOT / "system/services/laya-ai.service").read_text(encoding="utf-8")

    for content, module in [
        (sys_svc, "system.dbus.service"),
        (ai_svc, "laya.main"),
    ]:
        assert "WorkingDirectory=/opt/laya-os" in content
        assert "Environment=PYTHONPATH=/opt/laya-os" in content
        assert f"ExecStart=/opt/laya-os/.venv/bin/python3 -m {module}" in content
        assert "/usr/bin/python3" not in content


def test_installer_validation_and_session_integration():
    installer = (REPO_ROOT / "os/installer/install-laya.sh").read_text(encoding="utf-8")

    # Pre-flight validation
    assert "REQUIRED_DIRS=(" in installer
    assert "REQUIRED_FILES=(" in installer
    assert "python3 -m venv --help" in installer

    # Venv & dependency verification
    assert "python3 -m venv --system-site-packages" in installer
    assert "import psutil, requests, pydantic, yaml, numpy" in installer
    assert "import system.dbus.service" in installer

    # Session starter integration
    assert "systemctl --user start laya-system.service" in installer
    assert "systemctl --user start laya-ai.service" in installer
    assert "/usr/share/wayland-sessions/laya-os.desktop" in installer

    # Preserves existing Ubuntu GNOME desktop
    assert "ubuntu.desktop" not in installer
    assert "gnome.desktop" not in installer


def test_required_assets_exist_in_repo():
    expected_files = [
        "pyproject.toml",
        "requirements.txt",
        "system/services/laya-system.service",
        "system/services/laya-ai.service",
        "os/branding/icons/laya-logo.svg",
        "os/branding/icons/laya-orb.svg",
        "os/branding/wallpapers/laya-cosmic-dark.svg",
        "os/branding/grub/theme.txt",
        "os/installer/laya-session.desktop",
        "os/packages/ubuntu-packages.txt",
    ]
    for rel in expected_files:
        assert (REPO_ROOT / rel).is_file(), f"Missing required asset: {rel}"


def test_build_iso_ubuntu_2604_compatibility():
    build_sh = (REPO_ROOT / "os/image-build/build-iso.sh").read_text(encoding="utf-8")
    grub_theme = (REPO_ROOT / "os/branding/grub/theme.txt").read_text(encoding="utf-8")

    assert "lupin-casper" not in build_sh
    assert "laya-os-alpha-0.1-fixed-amd64.iso" in build_sh
    assert "--repack-only" in build_sh
    assert "ubuntu.sources" in build_sh
    assert "main restricted universe multiverse" in build_sh
    assert "filesystem.manifest" in build_sh
    assert ".disk/info" in build_sh
    assert "update-initramfs -u -k all" in build_sh
    assert "grub-file --is-x86-linux" in build_sh
    assert "grub-script-check" in build_sh
    assert "-sort" in build_sh
    assert "insmod iso9660" in build_sh
    assert "insmod linux" in build_sh
    assert "search --no-floppy --set=root --file /casper/vmlinuz" in build_sh
    assert "background.png" not in grub_theme
