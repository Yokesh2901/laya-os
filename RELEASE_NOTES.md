# LAYA OS Alpha 0.1 Release Notes

**Tag:** `v0.1.0-alpha`  
**Base:** Ubuntu 26.04 LTS (x86_64)  

## Highlights
- **LAYA Desktop Shell:** Custom GTK4 / Libadwaita shell, top status panel, glassmorphic dock, searchable application launcher with Tamil phonetic mapping, settings app, and 60 FPS 3D Fibonacci Particle Sphere widget.
- **LAYA AI Core:** Modular STT (`saaras:v4` + offline fallback), TTS (`bulbul:v4-flash`, Edge-TTS, `espeak-ng`, PipeWire `pw-play`), Wake-Word VAD, SQLite persistent memory, Ollama LLM adapter, and Tamil/English/Tanglish conversational agent.
- **LAYA System Core (`org.laya.SystemCore`):** Session D-Bus service with strict action allowlisting, interactive confirmation dialogs, PipeWire audio control, display brightness control, XDG `.desktop` launcher, and hardware telemetry.
- **OS Distribution Tooling:** Non-destructive Ubuntu 26.04 Wayland session installer (`install-laya.sh`), Plymouth/GRUB branding, and reproducible `debootstrap` + `mksquashfs` + `grub-mkrescue` ISO build script (`build-iso.sh`).
- **Verification:** 20/20 automated unit and integration tests passing.
