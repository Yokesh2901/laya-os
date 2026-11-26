#!/usr/bin/env bash
# ==============================================================================
# LAYA OS - Non-Destructive System Installer for Ubuntu 26.04 LTS
# Installs LAYA OS as an independent Wayland session and systemd user services
# without overwriting the default Ubuntu desktop.
# ==============================================================================

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (e.g., sudo ./install-laya.sh)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INSTALL_DIR="/opt/laya-os"

echo "=== Installing LAYA OS Alpha 0.1 ==="

# 1. Install core code into /opt/laya-os
mkdir -p "${INSTALL_DIR}"
cp -r "${REPO_ROOT}/laya" "${REPO_ROOT}/desktop" "${REPO_ROOT}/system" "${REPO_ROOT}/os" "${REPO_ROOT}/pyproject.toml" "${REPO_ROOT}/requirements.txt" "${INSTALL_DIR}/"

# 2. Install Python dependencies in dedicated venv
if [ ! -d "${INSTALL_DIR}/.venv" ]; then
    python3 -m venv --system-site-packages "${INSTALL_DIR}/.venv"
fi
"${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

# 3. Create CLI wrappers in /usr/local/bin
for cmd in "laya-dbus:system.dbus.service" "laya-core:laya.main" "laya-desktop:desktop.shell.main" "laya-launcher:desktop.launcher.main" "laya-dock:desktop.dock.main" "laya-settings:desktop.settings.main"; do
    bin_name="${cmd%%:*}"
    mod_name="${cmd##*:}"
    cat > "/usr/local/bin/${bin_name}" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${INSTALL_DIR}"
exec "${INSTALL_DIR}/.venv/bin/python3" -m ${mod_name} "\$@"
EOF
    chmod +x "/usr/local/bin/${bin_name}"
done

# 4. Create Wayland session starter
cat > /usr/local/bin/laya-session-start <<'EOF'
#!/usr/bin/env bash
systemctl --user start laya-system.service || true
systemctl --user start laya-ai.service || true
exec /usr/local/bin/laya-desktop
EOF
chmod +x /usr/local/bin/laya-session-start

# 5. Install Wayland session & desktop entries
mkdir -p /usr/share/wayland-sessions /usr/share/applications
cp "${SCRIPT_DIR}/laya-session.desktop" /usr/share/wayland-sessions/laya-os.desktop

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

# 6. Install branding assets & systemd user services
mkdir -p /usr/share/icons/hicolor/scalable/apps /usr/share/backgrounds/laya
cp "${REPO_ROOT}/os/branding/icons/laya-logo.svg" /usr/share/icons/hicolor/scalable/apps/laya-logo.svg
cp "${REPO_ROOT}/os/branding/wallpapers/laya-cosmic-dark.svg" /usr/share/backgrounds/laya/laya-cosmic-dark.svg

mkdir -p /usr/lib/systemd/user
cp "${REPO_ROOT}/system/services/"*.service /usr/lib/systemd/user/

echo "=== LAYA OS Installation Complete! ==="
echo "You can now select 'LAYA OS' at the login screen or launch 'laya-desktop'."
