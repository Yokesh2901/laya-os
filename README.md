# LAYA OS — Intelligence Within

<p align="center">
  <img src="os/branding/icons/laya-logo.svg" width="160" alt="LAYA OS Logo" />
</p>

<p align="center">
  <strong>An AI-Native, Voice-First Linux Operating System Built on Ubuntu 26.04 LTS</strong>
</p>

<p align="center">
  <a href="docs/architecture/overview.md">Architecture</a> •
  <a href="docs/security/security-model.md">Security Model</a> •
  <a href="docs/roadmap/roadmap.md">Roadmap</a> •
  <a href="DEVELOPMENT_STATUS.md">Development Status</a>
</p>

---

## 🌟 Vision

LAYA OS transforms the personal computing experience by putting conversational artificial intelligence at the very heart of the operating system. Built on Ubuntu 26.04 LTS and modern Wayland display technology, LAYA OS allows users to operate their computer primarily through voice and natural dialogue in **Tamil, English, and Tanglish (Tamil-English code-switching)**.

- **AI-Native:** AI services are deeply integrated into the OS session layer via standard Linux D-Bus protocols.
- **Voice-First:** Ultra-fast, low-latency wake-word ("Hey Laya") and speech recognition designed specifically for Indian languages and English.
- **Privacy-Focused:** Local-first architecture utilizing Small Language Models (Ollama / Llama / Phi-3) and offline speech engines. Zero unsolicited telemetry.
- **Zero-Trust Security:** Strict allowlisted system actions; the LLM is prohibited from unrestricted shell execution.
- **Futuristic Aesthetic:** Glassmorphic, dark-mode GTK4/Libadwaita desktop with 60 FPS audio-reactive particle visualizer.

---

## 🎨 Design System

LAYA OS features a custom visual identity inspired by deep space and quantum neural networks:

| Token | Name | Hex Code | Purpose |
| :--- | :--- | :--- | :--- |
| **Base** | Midnight Navy | `#090B18` | System workspace & background |
| **Surface** | Deep Surface | `#111429` | Windows, cards, glassmorphic panels |
| **Accent 1** | Electric Violet | `#8B5CF6` | Primary interactive highlights & borders |
| **Accent 2** | Deep Purple | `#6D28D9` | Gradients and secondary surfaces |
| **Highlight**| Cyan Glow | `#22D3EE` | Voice activity & active state indicator |
| **Text** | Soft White | `#F8FAFC` | High-contrast accessible typography |

---

## 🏛️ System Architecture

LAYA OS is structured into four decoupled layers:

1. **OS Foundation:** Ubuntu 26.04 LTS, Linux Kernel 6.x, Wayland, GNOME/Mutter compositor, PipeWire audio routing.
2. **LAYA Desktop:** Custom GTK4 / Libadwaita top panel, glassmorphic dock, application launcher with Tamil phonetic search, 3D particle companion widget, and settings app.
3. **LAYA AI Core:** Decoupled background services managing wake-word detection, speech-to-text (Sarvam saaras:v4 / Whisper), text-to-speech (Sarvam bulbul:v4-flash / Edge-TTS / Piper), conversational LLM orchestration (Ollama), and persistent SQLite memory.
4. **LAYA System Core (`org.laya.SystemCore`):** Secure D-Bus service exposing allowlisted capabilities (application launching, PipeWire volume, display brightness, hardware telemetry, and sandboxed file search) with interactive confirmation dialogs for destructive actions.

---

## 🚀 Getting Started & Development

### Prerequisites (Development Host)
- Ubuntu 26.04 LTS (or Linux with Wayland, Python 3.10+, and GTK4)
- VirtualBox (for VM image testing)

### Installation for Development
```bash
# Clone the repository
git clone https://github.com/laya-os/laya-os.git
cd laya-os

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Run the test suite
pytest
```

---

## 🔒 Security Policy

Please review [Security Model](docs/security/security-model.md) for details on privilege boundaries, permission checks, and vulnerability reporting.

---

## 📄 License

LAYA OS is open-source software licensed under the [Apache License 2.0](LICENSE).
