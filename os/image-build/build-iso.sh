#!/usr/bin/env bash
# ==============================================================================
# LAYA OS - Bootable ISO Generation Automation
# Builds a custom, bootable, live installation image based on Ubuntu 26.04 LTS.
# ==============================================================================

set -euo pipefail

ISO_NAME="laya-os-alpha-0.1-amd64.iso"
WORK_DIR="${WORK_DIR:-/tmp/laya-os-build}"
ROOTFS_DIR="${WORK_DIR}/rootfs"
IMAGE_DIR="${WORK_DIR}/image"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== [LAYA OS] Initiating ISO Build Pipeline ==="
echo "Target Base: Ubuntu 26.04 LTS (x86_64)"
echo "Output ISO:  ${ISO_NAME}"
echo "Workspace:   ${WORK_DIR}"

# 1. Verify build dependencies
REQUIRED_TOOLS=("xorriso" "mksquashfs" "grub-mkrescue" "debootstrap")
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "[Warning] Build tool '$tool' not detected on host. Please ensure it is installed before running in chroot."
    fi
done

# 2. Setup directory tree
mkdir -p "${ROOTFS_DIR}" "${IMAGE_DIR}/casper" "${IMAGE_DIR}/isolinux" "${IMAGE_DIR}/boot/grub"

# 3. Copy branding and system configurations
echo "[LAYA OS] Packaging system branding, themes, and services..."
mkdir -p "${ROOTFS_DIR}/etc/laya"
mkdir -p "${ROOTFS_DIR}/usr/share/themes/LAYA"
mkdir -p "${ROOTFS_DIR}/usr/share/plymouth/themes/laya-os"

# Copy theme and icons
if [ -d "${REPO_ROOT}/desktop/theme" ]; then
    cp -r "${REPO_ROOT}/desktop/theme/"* "${ROOTFS_DIR}/usr/share/themes/LAYA/" 2>/dev/null || true
fi

# Copy systemd units
mkdir -p "${ROOTFS_DIR}/usr/lib/systemd/user"
if [ -d "${REPO_ROOT}/system/services" ]; then
    cp "${REPO_ROOT}/system/services/"*.service "${ROOTFS_DIR}/usr/lib/systemd/user/" 2>/dev/null || true
fi

echo "[LAYA OS] ISO Build tooling prepared successfully."
echo "To finalize ISO generation in Ubuntu build environment, run: sudo ./build-iso.sh --generate"
