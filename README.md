# K1 Nexus — Printer Command Center

K1 Nexus is an unofficial desktop control application for compatible Creality K1-series printers reachable over the local network.

It provides a single desktop interface for printer status, motion and temperature controls, filament operations, G-code file management, self-check functions, settings, and diagnostics.

> **Important:** K1 Nexus is an independent community project and is not affiliated with, endorsed by, or supported by Creality.

## Features

- Live printer connection/status over LAN
- Nozzle, bed, and chamber temperature information
- Print progress and print controls
- X/Y/Z motion and homing controls
- Filament controls
- G-code file listing, upload/download, rename/delete, and print actions supported by the printer LAN interface
- Self-check and device settings
- Diagnostics panel
- Dark K1 Nexus desktop interface
- Cross-platform Python codebase

The experimental 3D model preview and camera-recording features are intentionally not included in this release.

## Supported desktop platforms

### macOS
Requires Python 3 with Tkinter. Double-click **Run K1 Nexus.command**, or run:

```bash
python3 k1_touch.py
```

On first launch, macOS may require you to allow the downloaded launcher in Privacy & Security depending on how the ZIP/repository was obtained.

### Windows
Install Python 3 with Tkinter (included with the normal python.org Windows installer) and enable **Add Python to PATH** during installation.

Double-click:

```text
Run K1 Nexus.bat
```

The launcher tries the Windows `py -3` launcher first and then `python`.

### Linux
Install Python 3 and your distribution's Tkinter package. Common package names include `python3-tk`.

Then run:

```bash
chmod +x run_k1_nexus.sh
./run_k1_nexus.sh
```

or:

```bash
python3 k1_touch.py
```

## Python dependencies

K1 Nexus currently uses only Python standard-library modules. There are no third-party pip dependencies in this release. `requirements.txt` is included to make that explicit.

## Getting started

1. Connect the computer and printer to the same local network.
2. Start K1 Nexus using the launcher for your operating system.
3. Enter the printer's LAN IP address in the top-right field.
4. Select **Reconnect**.
5. Confirm that the application reports **Connected**.

The default address shown by the application may not match your printer. Use the address assigned to your printer on your network.

## Repository layout

```text
K1-Nexus/
├── k1_touch.py              # Main application
├── Run K1 Nexus.command     # macOS launcher
├── Run K1 Nexus.bat         # Windows launcher
├── run_k1_nexus.sh          # Linux launcher
├── requirements.txt         # Dependency declaration
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── .gitignore
└── .gitattributes
```

## Compatibility notes

The desktop application itself is written to avoid macOS-only application APIs. Printer-side functionality still depends on the LAN interfaces exposed by the printer firmware. A feature may therefore behave differently on another printer model or firmware revision even when K1 Nexus itself runs correctly on Windows, macOS, or Linux.

K1 Nexus should not be treated as a replacement for printer safety systems. Keep the printer supervised when appropriate and verify motion/temperature commands before using them.

## Development

A quick syntax check can be run with:

```bash
python3 -m py_compile k1_touch.py
```

