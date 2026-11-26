# Contributing to LAYA OS

Thank you for your interest in contributing to **LAYA OS**!

## Development Workflow

1. Fork the repository and create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Set up the local development environment:
   ```bash
   ./scripts/setup-dev.sh
   ```
3. Make your changes following the repository architecture (`laya/`, `desktop/`, `system/`, `os/`).
4. Add unit or integration tests under `tests/unit/` or `tests/integration/`.
5. Ensure the full test suite passes before opening a pull request:
   ```bash
   pytest
   ```

## Security & Privacy Rules
- Never commit API keys, `.env` files, personal data, or local `.db` files.
- Never bypass `SecurityPolicyEngine` or introduce unrestricted shell execution from AI components.
