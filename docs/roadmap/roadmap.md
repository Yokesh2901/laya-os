# LAYA OS Release Roadmap

## Phase 1: Foundation (Current Milestone)
- [x] Repository architecture and dependency definitions
- [x] Design system specification & GTK4/CSS theme
- [x] Vector branding assets (Logo, Orb, Wallpapers)
- [x] Security and isolation architecture documentation
- [x] Automated unit and integration test framework

## Phase 2: Custom LAYA Desktop Shell
- [ ] GTK4 / Libadwaita Desktop Shell & top panel
- [ ] Application launcher with XDG desktop entry indexing and Tamil phonetic transliteration
- [ ] Glassmorphic dock with active window indicators and Laya AI trigger
- [ ] Notification centre and system tray integrations
- [ ] LAYA OS Settings app (Voice, Model, Theme, Display)

## Phase 3: LAYA AI Core Microservices
- [ ] Voice Recognition (STT) microservice supporting Sarvam saaras:v4 and local Whisper/Vosk
- [ ] Text-to-Speech (TTS) microservice with natural Indian female voice (Sarvam bulbul:v4-flash, Edge-TTS, Piper)
- [ ] Wake-word detection engine ("Hey Laya", "Laya", "ஹே லயா")
- [ ] Small Language Model (SLM) conversational agent with Ollama / local runtime
- [ ] Multi-turn session context and SQLite persistent memory

## Phase 4: OS Integration & D-Bus Service
- [ ] `org.laya.SystemCore` D-Bus daemon
- [ ] Allowlisted action dispatcher (Apps, Audio, Brightness, Hardware stats, File search)
- [ ] Confirmation prompt service for sensitive actions
- [ ] systemd user service manifests (`laya-ai.service`, `laya-system.service`)

## Phase 5: OS Distribution & Bootable ISO
- [ ] Automated Ubuntu 26.04 live-build tooling
- [ ] Custom Plymouth boot splash and GRUB bootloader theme
- [ ] Pre-configured installer (Calamares / Subiquity)
- [ ] Clean VirtualBox VM testing & validation

## Phase 6: Alpha 0.1 Release
- [ ] End-to-end acceptance testing
- [ ] GitHub release package preparation
- [ ] Documentation and user guide finalization
