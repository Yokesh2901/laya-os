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
UBUNTU_SECURITY_MIRROR="${UBUNTU_SECURITY_MIRROR:-http://security.ubuntu.com/ubuntu/}"
WORK_DIR="${WORK_DIR:-/tmp/laya-os-build}"
ROOTFS_DIR="${WORK_DIR}/rootfs"
IMAGE_DIR="${WORK_DIR}/image"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
GENERATE_ISO=false

for arg in "$@"; do
    case "$arg" in
        --generate) GENERATE_ISO=true ;;
        *)
            echo "[Error] Unknown argument: $arg" >&2
            exit 1
            ;;
    esac
done

echo "=== [LAYA OS] ISO Build Pipeline ==="
echo "Target Suite : Ubuntu ${UBUNTU_SUITE} (x86_64)"
echo "Output ISO   : ${ISO_NAME}"
echo "Work Dir     : ${WORK_DIR}"

# 1. Verify required source files and Linux build tools
for req_file in \
    "${REPO_ROOT}/os/installer/install-laya.sh" \
    "${REPO_ROOT}/os/packages/ubuntu-packages.txt" \
    "${REPO_ROOT}/os/branding/grub/theme.txt"; do
    if [ ! -f "${req_file}" ]; then
        echo "[Error] Required build input missing: ${req_file}" >&2
        exit 1
    fi
done

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
    echo "[Error] --generate must be run as root (sudo)." >&2
    exit 1
fi

if [ "${#MISSING_TOOLS[@]}" -gt 0 ]; then
    echo "[Error] Missing required build tools: ${MISSING_TOOLS[*]}" >&2
    exit 1
fi

cleanup_mounts() {
    echo "[LAYA OS] Cleaning up chroot bind mounts..."
    umount -lf "${ROOTFS_DIR}/dev/pts" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/dev" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/proc" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/sys" 2>/dev/null || true
    umount -lf "${ROOTFS_DIR}/run" 2>/dev/null || true
}
trap cleanup_mounts EXIT

mkdir -p "${ROOTFS_DIR}" "${IMAGE_DIR}/casper" "${IMAGE_DIR}/boot/grub" "${IMAGE_DIR}/.disk"

# 2. Bootstrap base Ubuntu filesystem
if [ ! -f "${ROOTFS_DIR}/etc/os-release" ]; then
    echo "[1/7] Running debootstrap for Ubuntu ${UBUNTU_SUITE}..."
    debootstrap --arch=amd64 "${UBUNTU_SUITE}" "${ROOTFS_DIR}" "${UBUNTU_MIRROR}"
fi

# 3. Configure Ubuntu DEB822 APT sources (main, restricted, universe, multiverse)
echo "[2/7] Configuring Ubuntu APT sources and chroot mounts..."
mkdir -p "${ROOTFS_DIR}/etc/apt/sources.list.d"
rm -f "${ROOTFS_DIR}/etc/apt/sources.list"
cat > "${ROOTFS_DIR}/etc/apt/sources.list.d/ubuntu.sources" <<EOF
Types: deb
URIs: ${UBUNTU_MIRROR}
Suites: ${UBUNTU_SUITE} ${UBUNTU_SUITE}-updates ${UBUNTU_SUITE}-backports
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

Types: deb
URIs: ${UBUNTU_SECURITY_MIRROR}
Suites: ${UBUNTU_SUITE}-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
EOF

mount --bind /dev "${ROOTFS_DIR}/dev"
mount --bind /dev/pts "${ROOTFS_DIR}/dev/pts"
mount -t proc proc "${ROOTFS_DIR}/proc"
mount -t sysfs sysfs "${ROOTFS_DIR}/sys"
mount --bind /run "${ROOTFS_DIR}/run" || true

rm -f "${ROOTFS_DIR}/etc/resolv.conf"
if [ -f /etc/resolv.conf ]; then
    cp -L /etc/resolv.conf "${ROOTFS_DIR}/etc/resolv.conf"
else
    printf "nameserver 1.1.1.1\nnameserver 8.8.8.8\n" > "${ROOTFS_DIR}/etc/resolv.conf"
fi

mkdir -p "${ROOTFS_DIR}/tmp/laya-src"
cp -r "${REPO_ROOT}/laya" "${REPO_ROOT}/desktop" "${REPO_ROOT}/system" "${REPO_ROOT}/os" \
      "${REPO_ROOT}/pyproject.toml" "${REPO_ROOT}/requirements.txt" "${ROOTFS_DIR}/tmp/laya-src/"
if [ -f "${REPO_ROOT}/.env.example" ]; then
    cp "${REPO_ROOT}/.env.example" "${ROOTFS_DIR}/tmp/laya-src/.env.example"
fi

# 4. Install kernel, casper live-boot, GDM3, desktop packages, and LAYA OS
echo "[3/7] Installing Ubuntu 26.04 packages and LAYA OS inside chroot..."
chroot "${ROOTFS_DIR}" /bin/bash -c "
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends \
        linux-image-generic \
        casper \
        gdm3 \
        network-manager \
        systemd-sysv \
        sudo \
        dbus-x11 \
        locales \
        ca-certificates
    locale-gen en_US.UTF-8 || true

    # Install full LAYA OS package manifest
    mapfile -t PKGS < <(grep -vE '^(#|\s*$)' /tmp/laya-src/os/packages/ubuntu-packages.txt)
    if [ \"\${#PKGS[@]}\" -gt 0 ]; then
        apt-get install -y \"\${PKGS[@]}\"
    fi

    # Configure hostname, hosts, and casper live session defaults
    echo 'laya-os' > /etc/hostname
    printf '127.0.0.1\tlocalhost\n127.0.1.1\tlaya-os\n' > /etc/hosts
    cat > /etc/casper.conf <<'CASPER_EOF'
export USERNAME=\"laya\"
export USERFULLNAME=\"LAYA OS Live User\"
export HOST=\"laya-os\"
export BUILD_SYSTEM=\"Ubuntu\"
export FLAVOUR=\"LAYA OS\"
CASPER_EOF

    # Run non-destructive LAYA OS installer
    cd /tmp/laya-src/os/installer
    chmod +x install-laya.sh
    ./install-laya.sh

    # Verify critical session and service files exist
    test -f /usr/share/wayland-sessions/laya-os.desktop
    test -f /usr/lib/systemd/user/laya-system.service
    test -f /usr/lib/systemd/user/laya-ai.service
    test -x /opt/laya-os/.venv/bin/python3

    rm -rf /tmp/laya-src /var/lib/apt/lists/*
    apt-get clean
"

# Generate casper package manifest before unmounting
chroot "${ROOTFS_DIR}" dpkg-query -W --showformat='${Package} ${Version}\n' > "${IMAGE_DIR}/casper/filesystem.manifest"

cleanup_mounts

# 5. Extract kernel + initrd and build squashfs
echo "[4/7] Copying kernel/initrd..."
VMLINUZ_FILE="$(ls -1 "${ROOTFS_DIR}/boot/vmlinuz-"* | head -n 1)"
INITRD_FILE="$(ls -1 "${ROOTFS_DIR}/boot/initrd.img-"* | head -n 1)"
if [ -z "${VMLINUZ_FILE}" ] || [ -z "${INITRD_FILE}" ]; then
    echo "[Error] Kernel or initrd not found in ${ROOTFS_DIR}/boot" >&2
    exit 1
fi
cp "${VMLINUZ_FILE}" "${IMAGE_DIR}/casper/vmlinuz"
cp "${INITRD_FILE}" "${IMAGE_DIR}/casper/initrd"

echo "[5/7] Compressing filesystem.squashfs..."
rm -f "${IMAGE_DIR}/casper/filesystem.squashfs"
mksquashfs "${ROOTFS_DIR}" "${IMAGE_DIR}/casper/filesystem.squashfs" -comp xz \
    -e tmp/* var/tmp/* proc/* sys/* dev/* run/*

printf "%s" "$(du -sx --block-size=1 "${ROOTFS_DIR}" | cut -f1)" > "${IMAGE_DIR}/casper/filesystem.size"
echo "LAYA OS Alpha 0.1 - Release amd64 ($(date +%Y%m%d))" > "${IMAGE_DIR}/.disk/info"

# 6. Configure GRUB and build hybrid UEFI/BIOS ISO
echo "[6/7] Configuring GRUB bootloader..."
cp "${REPO_ROOT}/os/branding/grub/theme.txt" "${IMAGE_DIR}/boot/grub/theme.txt"
cat > "${IMAGE_DIR}/boot/grub/grub.cfg" <<'EOF'
insmod all_video
search --no-floppy --set=root --file /casper/vmlinuz

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

echo "[7/7] Generating bootable ISO image: ${ISO_NAME}..."
grub-mkrescue -o "${REPO_ROOT}/${ISO_NAME}" "${IMAGE_DIR}"

echo "=== [LAYA OS] Build Complete: ${REPO_ROOT}/${ISO_NAME} ==="
