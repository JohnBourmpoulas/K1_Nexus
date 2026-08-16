# Contributing to K1 Nexus

Contributions and bug reports are welcome.

## Before submitting a change

- Keep the application cross-platform; avoid OS-specific behavior unless it has a Windows/macOS/Linux fallback.
- Preserve existing printer controls unless the change intentionally replaces them.
- Do not commit passwords, Wi-Fi credentials, tokens, private IP inventories, logs containing secrets, or other sensitive data.
- Keep comments concise and in English.
- Run `python3 -m py_compile k1_touch.py` (or `python -m py_compile k1_touch.py` on Windows) before opening a pull request.
- Describe the printer model and firmware version when reporting printer-protocol issues.

## Pull requests

Prefer small, focused changes. Explain what changed, why it changed, and which operating system/printer configuration was tested.
