#!/usr/bin/env bash
# ==============================================================================
# LAYA OS - Reproducible Bootable ISO Build System
# Builds an installable Ubuntu 26.04 LTS live ISO with LAYA OS pre-installed.
# Must be run on an Ubuntu/Debian Linux host with root privileges.
# ==============================================================================

set -euo pipefail

ISO_NAME="${ISO_NAME:-laya-os-alpha-0.1-fixed-amd64.iso}"
UBUNTU_SUITE="${UBUNTU_SUITE:-resolute}"
UBUNTU_MIRROR="${UBUNTU_MIRROR:-http://archive.ubuntu.com/ubuntu/}"
UBUNTU_SECURITY_MIRROR="${UBUNTU_SECURITY_MIRROR:-http://security.ubuntu.com/ubuntu/}"
WORK_DIR="${WORK_DIR:-/tmp/laya-os-build}"
ROOTFS_DIR="${WORK_DIR}/rootfs"
IMAGE_DIR="${WORK_DIR}/image"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUT_DIR="${OUT_DIR:-${REPO_ROOT}}"
GENERATE_ISO=false
REPACK_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --generate) GENERATE_ISO=true ;;
        --repack-only)
            GENERATE_ISO=true
            REPACK_ONLY=true
            ;;
        *)
            echo "[Error] Unknown argument: $arg" >&2
            exit 1
            ;;
    esac
done

OUTPUT_ISO="${OUT_DIR}/${ISO_NAME}"

echo "=== [LAYA OS] ISO Build Pipeline ==="
echo "Target Suite : Ubuntu ${UBUNTU_SUITE} (x86_64)"
echo "Output ISO   : ${OUTPUT_ISO}"
echo "Work Dir     : ${WORK_DIR}"
echo "Repack Only  : ${REPACK_ONLY}"

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

REQUIRED_TOOLS=("debootstrap" "mksquashfs" "xorriso" "grub-mkrescue" "grub-file" "grub-script-check")
MISSING_TOOLS=()
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [ "${GENERATE_ISO}" = false ]; then
    echo "[Dry-Run] Pass --generate (full build) or --repack-only (existing WORK_DIR) as root on Ubuntu."
    if [ "${#MISSING_TOOLS[@]}" -gt 0 ]; then
        echo "[Info] Missing build tools on this host: ${MISSING_TOOLS[*]}"
        echo "Install on Ubuntu via: sudo apt-get install -y debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin grub-common mtools"
    fi
    exit 0
fi

if [ "$EUID" -ne 0 ]; then
    echo "[Error] --generate / --repack-only must be run as root (sudo)." >&2
    exit 1
fi

if [ "${#MISSING_TOOLS[@]}" -gt 0 ]; then
    echo "[Error] Missing required build tools: ${MISSING_TOOLS[*]}" >&2
    exit 1
fi

if [ ! -d "/usr/lib/grub/i386-pc" ]; then
    echo "[Error] BIOS GRUB modules missing (/usr/lib/grub/i386-pc). Install 'grub-pc-bin'." >&2
    exit 1
fi

if [ ! -d "/usr/lib/grub/x86_64-efi" ]; then
    echo "[Warning] UEFI GRUB modules missing (/usr/lib/grub/x86_64-efi). Install 'grub-efi-amd64-bin' for UEFI boot support." >&2
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

mkdir -p "${ROOTFS_DIR}" "${IMAGE_DIR}/casper" "${IMAGE_DIR}/boot/grub/fonts" "${IMAGE_DIR}/.disk"

if [ "${REPACK_ONLY}" = false ]; then
    # 2. Bootstrap base Ubuntu filesystem (preserves existing rootfs if present)
    if [ ! -f "${ROOTFS_DIR}/etc/os-release" ]; then
        echo "[1/7] Running debootstrap for Ubuntu ${UBUNTU_SUITE}..."
        debootstrap --arch=amd64 "${UBUNTU_SUITE}" "${ROOTFS_DIR}" "${UBUNTU_MIRROR}"
    else
        echo "[1/7] Existing rootfs detected at ${ROOTFS_DIR}; skipping debootstrap."
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

        # Configure hostname, hosts, and casper live session defaults BEFORE regenerating initramfs
        echo 'laya-os' > /etc/hostname
        printf '127.0.0.1\tlocalhost\n127.0.1.1\tlaya-os\n' > /etc/hosts
        cat > /etc/casper.conf <<'CASPER_EOF'
export USERNAME=\"laya\"
export USERFULLNAME=\"LAYA OS Live User\"
export HOST=\"laya-os\"
export BUILD_SYSTEM=\"Ubuntu\"
export FLAVOUR=\"LAYA OS\"
CASPER_EOF
        update-initramfs -u -k all

        # Run non-destructive LAYA OS installer inside chroot
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

    chroot "${ROOTFS_DIR}" dpkg-query -W --showformat='${Package} ${Version}\n' > "${IMAGE_DIR}/casper/filesystem.manifest"
    cleanup_mounts

    # 5. Extract kernel + initrd (dereference symlinks) and build squashfs
    echo "[4/7] Copying kernel and initrd..."
    VMLINUZ_FILE="$(ls -1 "${ROOTFS_DIR}/boot/vmlinuz-"* | sort -V | tail -n 1)"
    INITRD_FILE="$(ls -1 "${ROOTFS_DIR}/boot/initrd.img-"* | sort -V | tail -n 1)"
    if [ -z "${VMLINUZ_FILE}" ] || [ -z "${INITRD_FILE}" ]; then
        echo "[Error] Kernel or initrd not found in ${ROOTFS_DIR}/boot" >&2
        exit 1
    fi
    cp -L "${VMLINUZ_FILE}" "${IMAGE_DIR}/casper/vmlinuz"
    cp -L "${INITRD_FILE}" "${IMAGE_DIR}/casper/initrd"

    echo "[5/7] Compressing filesystem.squashfs..."
    rm -f "${IMAGE_DIR}/casper/filesystem.squashfs"
    mksquashfs "${ROOTFS_DIR}" "${IMAGE_DIR}/casper/filesystem.squashfs" -comp xz \
        -e tmp/* var/tmp/* proc/* sys/* dev/* run/*

    printf "%s" "$(du -sx --block-size=1 "${ROOTFS_DIR}" | cut -f1)" > "${IMAGE_DIR}/casper/filesystem.size"
else
    echo "[1-5/7] Reusing existing staged kernel, initrd, and filesystem.squashfs in ${IMAGE_DIR}..."
    if [ -f "${ROOTFS_DIR}/boot/vmlinuz-"* ] 2>/dev/null && [ ! -f "${IMAGE_DIR}/casper/vmlinuz" ]; then
        VMLINUZ_FILE="$(ls -1 "${ROOTFS_DIR}/boot/vmlinuz-"* | sort -V | tail -n 1)"
        cp -L "${VMLINUZ_FILE}" "${IMAGE_DIR}/casper/vmlinuz"
    fi
    if [ -f "${ROOTFS_DIR}/boot/initrd.img-"* ] 2>/dev/null && [ ! -f "${IMAGE_DIR}/casper/initrd" ]; then
        INITRD_FILE="$(ls -1 "${ROOTFS_DIR}/boot/initrd.img-"* | sort -V | tail -n 1)"
        cp -L "${INITRD_FILE}" "${IMAGE_DIR}/casper/initrd"
    fi
fi

# Validate kernel, initrd, and squashfs before ISO generation
for casper_file in "${IMAGE_DIR}/casper/vmlinuz" "${IMAGE_DIR}/casper/initrd" "${IMAGE_DIR}/casper/filesystem.squashfs"; do
    if [ ! -s "${casper_file}" ]; then
        echo "[Error] Required casper artifact missing or empty: ${casper_file}" >&2
        exit 1
    fi
done

echo "[Validation] Checking x86 Linux bzImage header via grub-file..."
grub-file --is-x86-linux "${IMAGE_DIR}/casper/vmlinuz"

echo "LAYA OS Alpha 0.1 - Release amd64 ($(date +%Y%m%d))" > "${IMAGE_DIR}/.disk/info"

# 6. Configure GRUB and validate syntax
echo "[6/7] Configuring and validating GRUB bootloader..."
cp "${REPO_ROOT}/os/branding/grub/theme.txt" "${IMAGE_DIR}/boot/grub/theme.txt"
if [ -f /usr/share/grub/unicode.pf2 ]; then
    cp /usr/share/grub/unicode.pf2 "${IMAGE_DIR}/boot/grub/fonts/unicode.pf2"
fi

cat > "${IMAGE_DIR}/boot/grub/grub.cfg" <<'EOF'
insmod all_video
insmod gfxterm
insmod png
insmod iso9660
insmod part_gpt
insmod part_msdos
insmod ext2
insmod fat
insmod gzio
insmod linux
insmod search_fs_file

search --no-floppy --set=root --file /casper/vmlinuz

set default="0"
set timeout=5

if loadfont /boot/grub/fonts/unicode.pf2 ; then
    set gfxmode=auto
    set gfxpayload=keep
    terminal_output gfxterm
fi

if [ -f /boot/grub/theme.txt ]; then
    set theme=/boot/grub/theme.txt
fi

menuentry "Try or Install LAYA OS (Alpha 0.1)" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper quiet splash ---
    initrd /casper/initrd
}

menuentry "LAYA OS (Verbose / Debug Boot)" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper ---
    initrd /casper/initrd
}

menuentry "LAYA OS (Safe Graphics Mode)" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper nomodeset ---
    initrd /casper/initrd
}
EOF

grub-script-check "${IMAGE_DIR}/boot/grub/grub.cfg"

# 7. Place /boot, vmlinuz, and initrd at low LBAs before filesystem.squashfs
#    to prevent BIOS INT 13h / VirtualBox ATAPI high-LBA read failures.
SORT_FILE="${WORK_DIR}/iso.sort"
cat > "${SORT_FILE}" <<EOF
1000 ${IMAGE_DIR}/boot
900 ${IMAGE_DIR}/casper/vmlinuz
800 ${IMAGE_DIR}/casper/initrd
100 ${IMAGE_DIR}/casper/filesystem.squashfs
EOF

echo "[7/7] Generating bootable ISO image: ${OUTPUT_ISO}..."
grub-mkrescue -o "${OUTPUT_ISO}" "${IMAGE_DIR}" -- -volid "LAYA_OS_ALPHA" -sort "${SORT_FILE}"

# Verify ISO contents and El Torito boot records
echo "[Validation] Verifying El Torito boot records and ISO layout..."
xorriso -indev "${OUTPUT_ISO}" -report_el_torito plain
xorriso -indev "${OUTPUT_ISO}" -ls /casper

echo "=== [LAYA OS] Build Complete: ${OUTPUT_ISO} ==="
