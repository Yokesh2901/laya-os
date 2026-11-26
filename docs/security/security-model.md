# LAYA OS Security & Isolation Model

## 1. Principles of Security

Security is an uncompromising requirement in LAYA OS. Because the operating system is AI-native and voice-activated, the security architecture operates under a **Zero-Trust AI Execution** model.

### 1.1 Core Mandates
1. **Never allow unrestricted shell execution from an LLM:**
   The AI assistant is strictly forbidden from executing arbitrary shell strings (e.g. `system("bash -c ...")`, `eval()`).
2. **Strict Action Allowlisting:**
   Every system capability exposed to the AI must correspond to an explicit, typed, and schema-validated method in the `Laya System Core` (D-Bus service).
3. **Privilege Separation:**
   The AI service runs as an unprivileged user process in the systemd user session (`laya-ai.service`). System-level modifications must go through PolicyKit or standard authorization mechanisms.
4. **Destructive Action Confirmation:**
   Any action with potential data loss or operational disruption (e.g., system power-off, file deletion, service stoppage) triggers a desktop confirmation prompt requiring explicit user authorization.
5. **No Embedded Secrets:**
   No API keys, credentials, tokens, or personal identifiers are hard-coded in the source tree. All secrets reside in user-managed environment variables or the system keyring.
6. **Air-Gapped & Offline Operability:**
   The desktop environment and core OS controls function completely without an internet connection. Local STT, local SLM, and local TTS ensure user privacy.

---

## 2. Action Classification & Permission Matrix

| Action | Classification | Privilege Level | Confirmation Required | Execution Pathway |
| :--- | :--- | :--- | :--- | :--- |
| Query CPU / RAM / Disk | Safe | Unprivileged | No | `/proc`, `psutil` |
| Adjust Volume / Mute | Safe | User Audio Session | No | PipeWire / `wpctl` |
| Adjust Display Brightness | Safe | Hardware Group | No | `brightnessctl` |
| Launch Known Desktop App | Safe | Unprivileged XDG | No | `Gio.DesktopAppInfo` |
| Search User Files | Safe | User Sandbox | No | Scoped file finder |
| Close Non-Essential Window | Safe | User Wayland Session | No | Wayland / Mutter API |
| Power Off / Reboot System | Sensitive | systemd-logind | **YES (GUI Prompt)** | `systemctl poweroff` |
| Delete Files / Purge Cache | Sensitive | User Filesystem | **YES (GUI Prompt)** | Trash / File broker |
| Modify Network Settings | Sensitive | NetworkManager | **YES (PolicyKit)** | `nmcli` / D-Bus |
| Install / Remove Packages | Sensitive | APT / PackageKit | **YES (Administrator)**| `pkexec` / PackageKit |

---

## 3. Sandboxing & Fault Isolation

```
+--------------------------------------------------------------+
|                         WAYLAND DISPLAY                      |
|                                                              |
|   +-------------------+              +-------------------+   |
|   |   LAYA Desktop    |              | LAYA Applications |   |
|   +---------+---------+              +---------+---------+   |
|             |                                  |             |
|   +---------v---------+                        |             |
|   | LAYA AI Core Svc  |                        |             |
|   | (systemd user)    |                        |             |
|   +---------+---------+                        |             |
|             | (D-Bus Method Calls)             |             |
|   +---------v----------------------------------v---------+   |
|   |        org.laya.SystemCore (Policy Enforcer)         |   |
|   +---------+----------------------------------+---------+   |
|             |                                  |             |
|   +---------v---------+              +---------v---------+   |
|   | Safe Linux Drivers|              | PolicyKit Prompt  |   |
|   | PipeWire / XDG    |              | (User Confirms)   |   |
|   +-------------------+              +-------------------+   |
+--------------------------------------------------------------+
```

If the `laya-ai.service` process terminates unexpectedly, crashes, or encounters memory exhaustion, **the LAYA Desktop remains 100% operational**. The systemd user manager automatically restarts the AI service using exponential backoff without interrupting active desktop windows or user workflows.
