#!/usr/bin/env bash
# ==============================================================================
# LAYA OS - Non-Destructive System Installer for Ubuntu 26.04 LTS
# Installs LAYA OS as an independent Wayland session and systemd user services
# without modifying or replacing the existing Ubuntu GNOME desktop.
# ==============================================================================

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "[Error] Please run as root (e.g., sudo ./install-laya.sh)" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INSTALL_DIR="/opt/laya-os"

echo "=== LAYA OS Alpha 0.1 Installer ==="

# ------------------------------------------------------------------------------
# 1. Pre-flight Validation Checks (Stop safely if dependencies/files missing)
# ------------------------------------------------------------------------------
echo "[1/6] Running pre-flight validation checks..."

for bin in python3 systemctl; do
    if ! command -v "${bin}" >/dev/null 2>&1; then
        echo "[Error] Required system command '${bin}' not found. Aborting." >&2
        exit 1
    fi
done

if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "[Error] Python 'venv' module is unavailable. Install 'python3-venv' via APT and retry." >&2
    exit 1
fi

REQUIRED_DIRS=(
    "${REPO_ROOT}/laya"
    "${REPO_ROOT}/desktop"
    "${REPO_ROOT}/system"
    "${REPO_ROOT}/os"
)
for dir_path in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "${dir_path}" ]; then
        echo "[Error] Required source directory missing: ${dir_path}" >&2
        exit 1
    fi
done

REQUIRED_FILES=(
    "${REPO_ROOT}/pyproject.toml"
    "${REPO_ROOT}/requirements.txt"
    "${REPO_ROOT}/system/services/laya-system.service"
    "${REPO_ROOT}/system/services/laya-ai.service"
    "${REPO_ROOT}/os/branding/icons/laya-logo.svg"
    "${REPO_ROOT}/os/branding/icons/laya-orb.svg"
    "${REPO_ROOT}/os/branding/wallpapers/laya-cosmic-dark.svg"
    "${SCRIPT_DIR}/laya-session.desktop"
)
for file_path in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "${file_path}" ]; then
        echo "[Error] Required source file missing: ${file_path}" >&2
        exit 1
    fi
done

# ------------------------------------------------------------------------------
# 2. Install Application Modules & Assets into /opt/laya-os
# ------------------------------------------------------------------------------
echo "[2/6] Installing LAYA OS modules into ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"
rm -rf "${INSTALL_DIR}/laya" "${INSTALL_DIR}/desktop" "${INSTALL_DIR}/system" "${INSTALL_DIR}/os"
cp -r "${REPO_ROOT}/laya" "${REPO_ROOT}/desktop" "${REPO_ROOT}/system" "${REPO_ROOT}/os" "${INSTALL_DIR}/"
cp "${REPO_ROOT}/pyproject.toml" "${REPO_ROOT}/requirements.txt" "${INSTALL_DIR}/"
if [ -f "${REPO_ROOT}/.env.example" ]; then
    cp "${REPO_ROOT}/.env.example" "${INSTALL_DIR}/.env.example"
fi
chmod -R a+rX "${INSTALL_DIR}"

# ------------------------------------------------------------------------------
# 3. Create /opt/laya-os/.venv & Verify Python Dependencies
# ------------------------------------------------------------------------------
echo "[3/6] Setting up Python virtual environment at ${INSTALL_DIR}/.venv..."
if [ ! -d "${INSTALL_DIR}/.venv" ]; then
    python3 -m venv --system-site-packages "${INSTALL_DIR}/.venv"
fi

"${INSTALL_DIR}/.venv/bin/python3" -m pip install --upgrade pip
"${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

echo "[3/6] Verifying core Python dependencies and module imports..."
PYTHONPATH="${INSTALL_DIR}" "${INSTALL_DIR}/.venv/bin/python3" -c "
import psutil, requests, pydantic, yaml, numpy
import system.dbus.service
import laya.main
import desktop.shell.main
print('[OK] Core Python dependencies and LAYA modules verified.')
"

if ! "${INSTALL_DIR}/.venv/bin/python3" -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')" 2>/dev/null; then
    echo "[Warning] GTK4/Libadwaita PyGObject bindings not found in system site-packages."
    echo "          Install on Ubuntu via: sudo apt-get install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1"
fi

chmod -R a+rX "${INSTALL_DIR}/.venv"

# ------------------------------------------------------------------------------
# 4. Install CLI Wrappers & Wayland Session Starter
# ------------------------------------------------------------------------------
echo "[4/6] Installing CLI wrappers in /usr/local/bin..."
for cmd in \
    "laya-dbus:system.dbus.service" \
    "laya-core:laya.main" \
    "laya-desktop:desktop.shell.main" \
    "laya-launcher:desktop.launcher.main" \
    "laya-dock:desktop.dock.main" \
    "laya-settings:desktop.settings.main"; do
    bin_name="${cmd%%:*}"
    mod_name="${cmd##*:}"
    cat > "/usr/local/bin/${bin_name}" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${INSTALL_DIR}"
exec "${INSTALL_DIR}/.venv/bin/python3" -m ${mod_name} "\$@"
EOF
    chmod 0755 "/usr/local/bin/${bin_name}"
done

cat > /usr/local/bin/laya-session-start <<'EOF'
#!/usr/bin/env bash
set -u

export XDG_CURRENT_DESKTOP="LAYA:GNOME"
export XDG_SESSION_TYPE="wayland"
export PYTHONPATH="/opt/laya-os"

start_laya_services() {
    if command -v dbus-update-activation-environment >/dev/null 2>&1; then
        dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE PYTHONPATH || true
    fi
    systemctl --user daemon-reload || true
    systemctl --user start laya-system.service || true
    systemctl --user start laya-ai.service || true
}

stop_laya_services() {
    systemctl --user stop laya-ai.service laya-system.service 2>/dev/null || true
}
trap stop_laya_services EXIT

if [ -n "${WAYLAND_DISPLAY:-}" ]; then
    # Running inside an active Wayland compositor
    start_laya_services
    exec /usr/local/bin/laya-desktop
elif command -v mutter >/dev/null 2>&1; then
    # Standalone GDM Wayland session hosted by Mutter
    start_laya_services
    exec mutter --wayland -- /usr/local/bin/laya-desktop
else
    echo "[Error] No Wayland display or Mutter compositor available." >&2
    exit 1
fi
EOF
chmod 0755 /usr/local/bin/laya-session-start

# ------------------------------------------------------------------------------
# 5. Install Separate Wayland Session & Application Desktop Entries
#    (Preserves existing Ubuntu GNOME sessions untouched)
# ------------------------------------------------------------------------------
echo "[5/6] Registering LAYA OS Wayland session and desktop entries..."
mkdir -p /usr/share/wayland-sessions /usr/share/applications
cp "${SCRIPT_DIR}/laya-session.desktop" /usr/share/wayland-sessions/laya-os.desktop
chmod 0644 /usr/share/wayland-sessions/laya-os.desktop

cat > /usr/share/applications/laya-desktop.desktop <<'EOF'
[Desktop Entry]
Name=LAYA Desktop
Comment=Launch LAYA OS Desktop Shell
Exec=/usr/local/bin/laya-desktop
Icon=laya-logo
Terminal=false
Type=Application
Categories=System;
EOF

cat > /usr/share/applications/laya-launcher.desktop <<'EOF'
[Desktop Entry]
Name=LAYA Launcher
Comment=Search applications and talk to Laya AI
Exec=/usr/local/bin/laya-launcher
Icon=laya-orb
Terminal=false
Type=Application
Categories=Utility;
EOF

cat > /usr/share/applications/laya-settings.desktop <<'EOF'
[Desktop Entry]
Name=LAYA OS Settings
Comment=Configure Laya AI, Voice, and System Settings
Exec=/usr/local/bin/laya-settings
Icon=laya-logo
Terminal=false
Type=Application
Categories=Settings;
EOF
chmod 0644 /usr/share/applications/laya-*.desktop

# ------------------------------------------------------------------------------
# 6. Install Branding Assets & systemd User Services
# ------------------------------------------------------------------------------
echo "[6/6] Installing branding assets and systemd user services..."
mkdir -p /usr/share/icons/hicolor/scalable/apps /usr/share/backgrounds/laya
cp "${REPO_ROOT}/os/branding/icons/laya-logo.svg" /usr/share/icons/hicolor/scalable/apps/laya-logo.svg
cp "${REPO_ROOT}/os/branding/icons/laya-orb.svg" /usr/share/icons/hicolor/scalable/apps/laya-orb.svg
cp "${REPO_ROOT}/os/branding/wallpapers/laya-cosmic-dark.svg" /usr/share/backgrounds/laya/laya-cosmic-dark.svg
chmod 0644 /usr/share/icons/hicolor/scalable/apps/laya-*.svg /usr/share/backgrounds/laya/laya-cosmic-dark.svg

mkdir -p /usr/lib/systemd/user
cp "${REPO_ROOT}/system/services/laya-system.service" /usr/lib/systemd/user/
cp "${REPO_ROOT}/system/services/laya-ai.service" /usr/lib/systemd/user/
chmod 0644 /usr/lib/systemd/user/laya-*.service

echo "=== LAYA OS Installation Complete! ==="
echo "Existing Ubuntu GNOME desktop has been preserved."
echo "Select 'LAYA OS' at the login screen or run 'laya-desktop' to start."
