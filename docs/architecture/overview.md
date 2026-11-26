# LAYA OS Architecture Blueprint

> **Tagline:** Intelligence Within  
> **Foundation:** Ubuntu 26.04 LTS (x86_64)  
> **Compositor / Display:** Wayland via GNOME/Mutter  
> **Interface Toolkit:** GTK4 / Libadwaita / CSS / PyGObject / PySide6  
> **System IPC:** D-Bus (`org.laya.SystemCore`)  
> **Audio Subsystem:** PipeWire + WirePlumber  

---

## 1. System Architecture Overview

LAYA OS is designed as a cohesive, AI-native operating system where desktop interaction, voice commands, and system automation merge into an intuitive user experience. Rather than treating an AI assistant as an isolated third-party user-space app, LAYA OS places the **Laya AI Core** in direct communication with a secure, permission-governed **Laya System Core** running over systemd user sessions and D-Bus.

```mermaid
flowchart TD
    subgraph UI [User Interaction Layer]
        Mic[🎤 Microphone] -->|PipeWire 16kHz PCM| WakeWord[⚡ Wake-Word Detection]
        WakeWord -->|Trigger: 'Hey Laya'| LayaSTT[🎙️ Laya STT Service]
        Shell[🖥️ LAYA Desktop Shell]
        Launcher[🚀 LAYA App Launcher]
        Dock[⚓ LAYA Dock & Orb]
        Settings[⚙️ LAYA Settings App]
        ParticleWidget[✨ 3D Holographic Particle Widget]
    end

    subgraph CoreAI [LAYA AI Core Microservices]
        LayaSTT -->|Transcribed Text: Tamil/English/Tanglish| DialogMgr[🧠 Conversation & Dialog Manager]
        DialogMgr -->|Prompts & RAG Context| LLMAdapter[🤖 LLM Adapter: Ollama / Local / Cloud]
        LLMAdapter -->|Structured Intent & Speech Text| DialogMgr
        DialogMgr -->|Speech Output| LayaTTS[🔊 Laya TTS Service: Neural Voices]
        DialogMgr <-->|Episodic & Entity Memory| PersistentMem[(💾 Persistent SQLite Memory)]
    end

    subgraph SysCore [LAYA System Core & Security Broker]
        DialogMgr -->|D-Bus Method Call| DBusService[🛡️ org.laya.SystemCore D-Bus Broker]
        DBusService -->|Permission Verification| PolicyEngine[🔐 Security & Allowlist Policy Engine]
        PolicyEngine -->|Approved Safe Action| ActionDispatcher[⚙️ OS Action Execution Engine]
        PolicyEngine -->|Sensitive Action| ConfirmDialog[⚠️ User Confirmation Prompt]
        ConfirmDialog -->|User Authorizes| ActionDispatcher
    end

    subgraph OSFoundation [Ubuntu 26.04 LTS Foundation]
        ActionDispatcher -->|Launch Apps / Parse .desktop| XDG[📂 XDG Desktop Applications]
        ActionDispatcher -->|Audio Vol / Mute| PipeWireCtl[🔈 PipeWire wpctl / pamixer]
        ActionDispatcher -->|Brightness Adjust| BrightnessSys[☀️ brightnessctl / sysfs]
        ActionDispatcher -->|Hardware Telemetry| SystemMon[📊 psutil / /proc]
        ActionDispatcher -->|Sandboxed File Search| FileFinder[🔍 fd / plocate]
        ActionDispatcher -->|Window Placement| WaylandMutter[🪟 Mutter Wayland D-Bus]
    end
```

---

## 2. Core Architectural Pillars

### A. Operating System Foundation
- **Base OS:** Ubuntu 26.04 LTS (Kernel 6.x+, systemd init).
- **Display Server:** Wayland protocol managed by GNOME/Mutter compositor.
- **Audio Routing:** Modern PipeWire and WirePlumber for low-latency full-duplex audio stream routing (essential for real-time speech recognition and echo cancellation).
- **Package Management:** Standard Ubuntu APT repositories combined with LAYA-native `.deb` packages and Flatpak support.

### B. LAYA Desktop Environment
- **Shell & Panel:** Custom top status panel exposing system telemetry, quick-settings flyout, network controls, volume slider, and Laya AI voice activity status.
- **Application Launcher:** Full-screen and popup modal launcher built with GTK4 and Libadwaita, providing instantaneous fuzzy search across standard XDG `.desktop` entries, categorization, and integrated Laya prompt bar.
- **Dock:** Glassmorphic bottom dock featuring running application indicators, pinned favorites, and quick activation of the Laya assistant.
- **3D Particle Companion:** Interactive 60 FPS Fibonacci sphere and particle face widget rendering user speech feedback and system state changes.

### C. LAYA AI Core
- **Voice Recognition (STT):** Multi-backend adapter supporting both local offline transcription (Whisper, Vosk) and high-accuracy Indian multilingual neural ASR (Sarvam AI `saaras:v4`) for Tamil, English, and Tanglish.
- **Speech Synthesis (TTS):** Indian female neural voice synthesis supporting natural Tamil phonetics, Tanglish transliteration, Edge-TTS (`ta-IN-PallaviNeural`), Piper local TTS, and Sarvam AI `bulbul:v4-flash`.
- **Conversational Brain:** Local-first Small Language Model (SLM) orchestration via Ollama (`phi3`, `mistral`, `llama3`) and external API fallbacks.
- **Memory Engine:** SQLite persistent store tracking user preferences, application usage patterns, and session history while adhering strictly to privacy redaction rules.

### D. LAYA System Core & Security Broker
- **Zero Unrestricted Shells:** Under no circumstances does the LLM possess raw `/bin/sh` or `sudo` execution privileges.
- **D-Bus Isolation:** All system mutations occur through strictly defined D-Bus interfaces on `org.laya.SystemCore`.
- **Policy Enforcement:** Actions are classified into:
  1. *Safe Actions* (e.g., query volume, get CPU stats, open approved applications) executed immediately.
  2. *Sensitive Actions* (e.g., system shutdown, deleting files, modifying network profiles) requiring explicit user confirmation.
