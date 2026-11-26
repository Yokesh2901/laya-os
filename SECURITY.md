# Security Policy

## Supported Versions

| Version | Supported |
| :--- | :--- |
| `0.1.0-alpha` | Active Development |

## Security Architecture
LAYA OS enforces a strict **Zero-Trust AI Execution** model:
- The AI Core has zero direct access to `/bin/sh` or `sudo`.
- All OS actions pass through `org.laya.SystemCore` and `SecurityPolicyEngine`.
- Destructive or sensitive operations (poweroff, reboot, lock, file deletion, process termination) require explicit user confirmation.

## Reporting a Vulnerability
Please do **not** open a public GitHub issue for security vulnerabilities. Report vulnerabilities privately to `core@laya-os.org` with steps to reproduce and impact details.
