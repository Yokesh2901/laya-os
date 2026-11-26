<#
.SYNOPSIS
Creates a clean VirtualBox VM for testing LAYA OS ISO installation.
Allocates 8 GB RAM, 4 vCPUs, and 64 GB dynamic VDI storage without modifying existing VMs.
#>

param(
    [string]$VmName = "LAYA-OS-Alpha-Test",
    [string]$IsoPath = "E:\Laya_OS\laya-os\laya-os-alpha-0.1-amd64.iso",
    [string]$VmFolder = "E:\Virtual Box"
)

$VBoxManage = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
if (-not (Test-Path $VBoxManage)) {
    Write-Error "VBoxManage.exe not found at $VBoxManage"
    exit 1
}

$existing = & $VBoxManage list vms | Select-String "`"$VmName`""
if ($existing) {
    Write-Output "VM '$VmName' already exists. Skipping creation."
    exit 0
}

Write-Output "Creating VirtualBox VM '$VmName'..."
& $VBoxManage createvm --name $VmName --ostype "Ubuntu_64" --basefolder $VmFolder --register

& $VBoxManage modifyvm $VmName `
    --memory 8192 `
    --cpus 4 `
    --vram 128 `
    --graphicscontroller vmsvga `
    --firmware efi `
    --nic1 nat `
    --audio-enabled on `
    --audio-driver default `
    --audio-controller hda

$vdiPath = Join-Path (Join-Path $VmFolder $VmName) "$VmName.vdi"
& $VBoxManage createmedium disk --filename $vdiPath --size 65536 --format VDI

& $VBoxManage storagectl $VmName --name "SATA Controller" --add sata --controller IntelAhci
& $VBoxManage storageattach $VmName --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium $vdiPath

if (Test-Path $IsoPath) {
    & $VBoxManage storagectl $VmName --name "IDE Controller" --add ide
    & $VBoxManage storageattach $VmName --storagectl "IDE Controller" --port 0 --device 0 --type dvddrive --medium $IsoPath
    Write-Output "Attached ISO: $IsoPath"
} else {
    Write-Warning "ISO not found at $IsoPath yet. Build the ISO in Ubuntu first, then attach it."
}

Write-Output "VM '$VmName' configured successfully (8 GB RAM, 4 CPUs, 64 GB dynamic VDI)."
