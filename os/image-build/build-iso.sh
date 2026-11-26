#!/usr/bin/env bash
# ==============================================================================
# LAYA OS - Reproducible Bootable ISO Build System
# Builds an installable Ubuntu 26.04 LTS live ISO with LAYA OS pre-installed.
# Must be run on an Ubuntu/Debian Linux host with root privileges.
# ==============================================================================

set -euo pipefail

ISO_NAME="${ISO_NAME:-laya-os-alpha-0.1-amd64.iso}"
UBUNTU_SUITE="${UBUNTU_SUITE:-resolute}"
UBUNTU_MIRROR="${UBUNTU_MIRROR:-http://archive.ubuntu.com/ubuntu/}"
WORK_DIR="${WORK_DIR:-/tmp/laya-os-build}"
ROOTFS_DIR="${WORK_DIR}/rootfs"
IMAGE_DIR="${WORK_DIR}/image"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
GENERATE_ISO=false

for arg in "$@"; do
    case "$arg" in
        --generate) GENERATE_ISO=true ;;
    esac
done

echo "=== [LAYA OS] ISO Build Pipeline ==="
echo "Target Suite : Ubuntu ${UBUNTU_SUITE} (x86_64)"
echo "Output ISO   : ${ISO_NAME}"
echo "Work Dir     : ${WORK_DIR}"

# 1. Verify required Linux build tools
REQUIRED_TOOLS=("debootstrap" "mksquashfs" "xorriso" "grub-mkrescue")
MISSING_TOOLS=()
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [ "${GENERATE_ISO}" = false ]; then
    echo "[Dry-Run] Pass --generate as root on Ubuntu to execute full debootstrap & ISO build."
    if [ "${#MISSING_TOOLS[@]}" -gt 0 ]; then
        echo "[Info] Missing build tools on this host: ${MISSING_TOOLS[*]}"
        echo "Install on Ubuntu via: sudo apt-get install -y debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools"
    fi
    exit 0
fi

if [ "$EUID" -ne 0 ]; then
    echo "[Error] --generate must be run as root (sudo)."
    exit 1
fi

if [ "${#MISSING_TOOLS[@]}" -gt 0 ]; then
    echo "[Error] Missing required build tools: ${MISSING_TOOLS[*]}"
    exit 1
fi

cleanup_mounts() {
    echo "[LAYA OS] Cleaning up chroot bind mounts..."
    umount -lf "${ROOTFS_DIR}/dev/pts" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/dev" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/proc" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/sys" 2>/dev/null || true
}
trap cleanup_mounts EXIT

mkdir -p "${ROOTFS_DIR}" "${IMAGE_DIR}/casper" "${IMAGE_DIR}/boot/grub"

# 2. Bootstrap base Ubuntu filesystem
if [ ! -f "${ROOTFS_DIR}/etc/os-release" ]; then
    echo "[1/6] Running debootstrap for ${UBUNTU_SUITE}..."
    debootstrap --arch=amd64 "${UBUNTU_SUITE}" "${ROOTFS_DIR}" "${UBUNTU_MIRROR}"
fi

# 3. Prepare chroot environment & copy LAYA OS source
echo "[2/6] Configuring chroot and copying LAYA OS..."
mount --bind /dev "${ROOTFS_DIR}/dev"
mount --bind /dev/pts "${ROOTFS_DIR}/dev/pts"
mount -t proc proc "${ROOTFS_DIR}/proc"
mount -t sysfs sysfs "${ROOTFS_DIR}/sys"
cp /etc/resolv.conf "${ROOTFS_DIR}/etc/resolv.conf"

mkdir -p "${ROOTFS_DIR}/tmp/laya-src"
cp -r "${REPO_ROOT}/." "${ROOTFS_DIR}/tmp/laya-src/"

# 4. Install kernel, live-boot, desktop packages, and LAYA OS inside chroot
echo "[3/6] Installing Ubuntu packages and LAYA OS inside chroot..."
chroot "${ROOTFS_DIR}" /bin/bash -c "
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y linux-image-generic casper lupin-casper network-manager systemd-sysv sudo
    grep -vE '^(#|\s*$)' /tmp/laya-src/os/packages/ubuntu-packages.txt | xargs -r apt-get install -y || true
    cd /tmp/laya-src/os/installer && chmod +x install-laya.sh && ./install-laya.sh
    echo 'laya-os' > /etc/hostname
    rm -rf /tmp/laya-src /var/lib/apt/lists/*
"

cleanup_mounts

# 5. Extract kernel + initrd and build squashfs
echo "[4/6] Copying kernel/initrd and compressing filesystem.squashfs..."
cp "${ROOTFS_DIR}/boot/vmlinuz-"* "${IMAGE_DIR}/casper/vmlinuz"
cp "${ROOTFS_DIR}/boot/initrd.img-"* "${IMAGE_DIR}/casper/initrd"

mksquashfs "${ROOTFS_DIR}" "${IMAGE_DIR}/casper/filesystem.squashfs" -comp xz -e boot

printf "%s" "$(du -sx --block-size=1 "${ROOTFS_DIR}" | cut -f1)" > "${IMAGE_DIR}/casper/filesystem.size"

# 6. Configure GRUB and build hybrid ISO
echo "[5/6] Configuring GRUB bootloader..."
cp "${REPO_ROOT}/os/branding/grub/theme.txt" "${IMAGE_DIR}/boot/grub/theme.txt"
cat > "${IMAGE_DIR}/boot/grub/grub.cfg" <<'EOF'
set default="0"
set timeout=5

menuentry "Try or Install LAYA OS (Alpha 0.1)" {
    linux /casper/vmlinuz boot=casper quiet splash ---
    initrd /casper/initrd
}

menuentry "LAYA OS (Safe Graphics Mode)" {
    linux /casper/vmlinuz boot=casper nomodeset ---
    initrd /casper/initrd
}
EOF

echo "[6/6] Generating bootable ISO image: ${ISO_NAME}..."
grub-mkrescue -o "${REPO_ROOT}/${ISO_NAME}" "${IMAGE_DIR}"

echo "=== [LAYA OS] Build Complete: ${REPO_ROOT}/${ISO_NAME} ==="
