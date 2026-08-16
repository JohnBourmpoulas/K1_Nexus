# K1 Nexus - Printer Command Center

K1 Nexus is an unofficial cross-platform desktop application for controlling and monitoring compatible Creality K1-series 3D printers over a local network.

It was created after the touchscreen on my own Creality K1 stopped working. The printer itself was still working, so I wanted a simple way to control and monitor it directly from my computer without depending on the printer's display.

What started as a solution to that problem became K1 Nexus: a desktop control center that brings the main printer functions together in one application.

K1 Nexus is an independent community project and is not affiliated with, endorsed by, or supported by Creality.

## Screenshots

### Printer Monitoring

The Home screen shows the current printer status, nozzle, bed and chamber temperatures, print progress, timing information and basic print controls.

![K1 Nexus Home](assets/screenshots/home.png)

### Printer Control

The Control screen provides manual X/Y/Z movement, axis homing, nozzle and bed temperature controls, fan controls, print speed and flow settings.

![K1 Nexus Control](assets/screenshots/control.png)

### Diagnostics

The Diagnostics screen shows the communication between K1 Nexus and the printer. It can also be used to send G-code commands directly for testing and troubleshooting.

![K1 Nexus Diagnostics](assets/screenshots/diagnostics.png)

## Features

K1 Nexus currently provides:

- Connection to compatible Creality K1-series printers over the local network
- Real-time printer status
- Nozzle, bed and chamber temperature monitoring
- Print progress and timing information
- Pause, resume and stop controls
- X, Y and Z movement
- Axis homing
- Nozzle and bed temperature control
- Part, chamber and auxiliary fan control
- Print speed and flow control
- Filament loading and unloading controls
- G-code file browsing
- G-code file upload
- Supported file downloads
- File rename and delete operations
- Starting print jobs directly from the application
- Self-check functions
- Printer settings
- Built-in diagnostics
- Direct G-code command interface
- Dark desktop interface

Camera recording and the experimental 3D model preview are not included in this release.

## Supported Platforms

K1 Nexus is designed to run on:

- macOS
- Windows
- Linux

The application is written in Python and uses Tkinter for its graphical interface.

Printer-side functionality depends on the LAN interfaces exposed by the printer firmware. Some functions may behave differently depending on the printer model and firmware version.

## Requirements

To run K1 Nexus you need:

- Python 3
- Tkinter
- A compatible Creality K1-series printer
- A computer and printer connected to the same local network

K1 Nexus currently uses Python standard-library modules and does not require additional third-party Python packages.

## Installation

Download or clone the repository.

The application files are located inside the `K1_Nexus` directory.

### macOS

Open:

```text
Run K1 Nexus.command
```

Alternatively, open Terminal inside the `K1_Nexus` directory and run:

```bash
python3 k1_touch.py
```

Depending on macOS security settings and how the repository was downloaded, macOS may ask for permission before opening the launcher.

### Windows

Make sure Python 3 is installed.

The standard Python installer for Windows normally includes Tkinter. During installation, enabling `Add Python to PATH` is recommended.

Open:

```text
Run K1 Nexus.bat
```

Alternatively, open Command Prompt or PowerShell inside the `K1_Nexus` directory and run:

```text
python k1_touch.py
```

### Linux

Install Python 3 and Tkinter using your distribution's package manager if they are not already installed.

Make the launcher executable:

```bash
chmod +x run_k1_nexus.sh
```

Then run:

```bash
./run_k1_nexus.sh
```

Alternatively:

```bash
python3 k1_touch.py
```

## Connecting to the Printer

1. Connect the computer and printer to the same local network.
2. Start K1 Nexus.
3. Find the IP address assigned to the printer by your network.
4. Enter the printer IP address in the field at the top-right of K1 Nexus.
5. Select `Reconnect`.
6. Wait for the application to report `Connected`.

The IP address shown by default in the application may not match your printer. Always use the IP address currently assigned to your printer.

## Application Sections

### Home

The Home screen gives a quick view of the printer.

It displays current temperatures, target temperatures, printer status, print progress, file information, print time and the current X/Y/Z position when this information is available from the printer.

Basic print controls and LED controls are also available from this screen.

### Control

The Control section provides manual control of the printer.

It includes:

- X/Y/Z movement
- XY and full homing
- Movement step selection
- Nozzle temperature
- Bed temperature
- Part/model fan
- Chamber fan
- Auxiliary fan
- Print speed
- Flow rate

### Filament

The Filament section provides controls for filament operations supported by the printer.

### Files

The Files section provides access to G-code files exposed by the printer and allows supported file operations such as upload, download, rename, delete and starting a print.

### Self Check

The Self Check section provides access to available printer self-test functions.

Available functions depend on the printer and firmware version.

### Settings

The Settings section provides access to supported printer configuration options.

### Diagnostics

The Diagnostics section displays communication between K1 Nexus and the printer.

It is useful for troubleshooting, development and checking the information exposed by the printer.

A direct G-code input is also available for advanced testing.

## Repository Structure

```text
K1_Nexus/
├── README.md
├── LICENSE
├── assets/
│   └── screenshots/
│       ├── home.png
│       ├── control.png
│       └── diagnostics.png
└── K1_Nexus/
    ├── k1_touch.py
    ├── Run K1 Nexus.command
    ├── Run K1 Nexus.bat
    └── run_k1_nexus.sh
```

### Application Files

`k1_touch.py`

Main K1 Nexus application.

`Run K1 Nexus.command`

Launcher for macOS.

`Run K1 Nexus.bat`

Launcher for Windows.

`run_k1_nexus.sh`

Launcher for Linux.

## Compatibility

K1 Nexus is intended for compatible Creality K1-series printers that expose the required control and status interfaces over the local network.

The desktop application is designed to avoid platform-specific dependencies where possible, but printer functionality depends on the interfaces exposed by each firmware version.

Compatibility with every K1-series printer and every firmware revision cannot be guaranteed.

If a feature does not respond as expected, the Diagnostics section can help identify which printer interfaces are available.

Testing and feedback from users with different K1-series models and firmware versions are welcome.

## Network Access

K1 Nexus communicates with the printer over the local network.

The application does not configure the printer's Wi-Fi network and does not manage or store printer Wi-Fi profiles.

The printer must already be connected to a network that is reachable from the computer running K1 Nexus.

K1 Nexus is intended for local network communication with the printer.

## Safety

K1 Nexus can send movement, temperature, filament and print-control commands to a connected 3D printer.

Always check the printer before sending commands and follow the normal safety procedures recommended for your machine.

Do not leave the printer unattended when performing operations that require supervision.

K1 Nexus should not be considered a replacement for the printer's built-in safety systems.

## Project Status

K1 Nexus is an independent project under active development.

The current release focuses on local printer control, monitoring, file management, self-check functions, settings and diagnostics through a cross-platform desktop interface.

The project started as a practical solution for controlling a K1 with a broken touchscreen and is being developed further as a general desktop control application for compatible K1-series printers.

Bug reports, testing, suggestions and contributions are welcome.

## Disclaimer

K1 Nexus is an unofficial project.

Creality and the Creality K1 product names are trademarks of their respective owners. This project is not affiliated with, endorsed by, or supported by Creality.

Use the software at your own risk.

## License

K1 Nexus is released under the MIT License.

See the `LICENSE` file for the full license text.
