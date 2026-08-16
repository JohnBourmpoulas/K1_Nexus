# K1 Nexus

K1 Nexus is a cross-platform desktop application for monitoring and
controlling compatible Creality K1 3D printers over a local network.

The project provides a lightweight desktop interface for common printer
operations including status monitoring, temperature monitoring, motion
control, filament operations, G-code file management, printer self-check
functions, settings, diagnostics, and local network profiles.

K1 Nexus is an independent open-source project and is not affiliated
with, endorsed by, or maintained by Creality.

## Features

Current features include:

-   Live printer connection status
-   Nozzle temperature monitoring
-   Heated bed temperature monitoring
-   Chamber temperature monitoring
-   Current print status
-   Print progress
-   Layer information
-   Print timing information
-   Printer position information
-   Pause, resume, and stop controls
-   Printer LED control
-   Manual X, Y, and Z movement
-   Homing controls
-   Filament operations
-   G-code file listing
-   G-code upload
-   File download
-   File deletion
-   Starting prints from the application
-   Saved network profiles
-   Printer self-check functions
-   Application and printer settings
-   Built-in diagnostics

## Supported Platforms

K1 Nexus is intended to run on macOS, Windows, and Linux.

  Operating System   Launcher
  ------------------ ------------------------
  macOS              `Run K1 Nexus.command`
  Windows            `Run K1 Nexus.bat`
  Linux              `run_k1_nexus.sh`

The main application is written in Python and uses Tkinter for the
graphical interface.

## Printer Compatibility

K1 Nexus is currently developed primarily for the Creality K1 family.

Compatibility may vary depending on the printer model, firmware version,
network configuration, and the services exposed by the installed printer
firmware.

Not every K1 model and firmware version has been tested. Reports from
users testing other configurations are welcome.

## Requirements

-   Python 3
-   Tkinter
-   A compatible Creality K1 printer
-   A local network connection between the computer and printer

Additional Python dependencies, if required by a particular version, are
listed in `requirements.txt`.

## Installation

### Clone the repository

``` bash
git clone https://github.com/JohnBourmpoulas/K1_Nexus.git
cd K1_Nexus
```

Alternatively, download the repository as a ZIP file from GitHub and
extract it.

### macOS

Run:

``` text
Run K1 Nexus.command
```

If macOS does not allow the launcher to execute, open Terminal in the
project directory and run:

``` bash
chmod +x "Run K1 Nexus.command"
```

Then start the launcher again.

### Windows

Make sure Python 3 is installed, then run:

``` text
Run K1 Nexus.bat
```

### Linux

Make the launcher executable:

``` bash
chmod +x run_k1_nexus.sh
```

Then run:

``` bash
./run_k1_nexus.sh
```

## Connecting to a Printer

K1 Nexus communicates with the printer over the local network.

1.  Turn on the printer.
2.  Make sure the computer and printer are connected to the same local
    network.
3.  Find the printer's local IP address.
4.  Start K1 Nexus.
5.  Enter the printer IP address in the connection field.
6.  Select `Reconnect`.

Example local IP address:

``` text
192.168.1.195
```

When communication is established, K1 Nexus displays the printer as
connected.

## Application Sections

### Home

The Home screen provides an overview of the printer, including
temperatures, print state, progress, position, timing information, and
print controls.

### Control

The Control section provides manual printer controls, including axis
movement and homing operations.

### Filament

The Filament section provides filament-related printer operations.

### Files

The Files section provides access to G-code file management and
supported print operations.

Depending on the printer firmware, this can include listing files,
uploading G-code, downloading files, deleting files, and starting a
print.

### Networking

The Networking section maintains network profiles used by K1 Nexus.

A saved profile can contain:

-   SSID
-   Password
-   Priority

Network profiles stored in K1 Nexus should not be confused with Wi-Fi
networks stored by the printer firmware.

Saving a network profile in the application does not guarantee that the
Wi-Fi credentials are written to the printer. Printer-side Wi-Fi
configuration depends on interfaces made available by the installed
firmware.

### Self Check

The Self Check section provides access to supported printer self-test
functions.

### Settings

The Settings section contains available application and printer-related
configuration.

### Diagnostics

The Diagnostics section provides information that can help identify
communication and printer-interface problems.

## Networking Limitations

K1 Nexus communicates with the printer using interfaces available over
the local network.

Some Creality firmware versions do not expose an interface that allows
K1 Nexus to modify the printer's saved Wi-Fi credentials.

For this reason, network profiles created in K1 Nexus may currently be
stored only by the application.

Printer-side Wi-Fi management remains an area for future development.

## Current Limitations

K1 Nexus depends on services exposed by the printer firmware.
Functionality can therefore vary between firmware versions and printer
configurations.

Current limitations include:

-   Compatibility with every Creality K1 model and firmware version has
    not been verified.
-   Printer-side Wi-Fi configuration is not guaranteed on stock
    firmware.
-   Some printer functions may not be exposed by certain firmware
    versions.
-   K1 Nexus does not automatically obtain root access or bypass printer
    security.
-   The application currently requires Python rather than being
    distributed as a fully self-contained native installer.

## Project Status

K1 Nexus is under active development.

The current goal is to provide a practical, lightweight desktop control
application for Creality K1 printers while maintaining support for
macOS, Windows, and Linux.

Areas planned for future development include:

-   Improved automatic printer discovery
-   Broader K1-family compatibility
-   Improved network management
-   Additional printer telemetry
-   Enhanced file management
-   Improved diagnostics
-   User interface improvements
-   Easier installation and setup
-   Standalone application packages for macOS, Windows, and Linux

## Contributing

Bug reports, testing, suggestions, and code contributions are welcome.

When reporting a problem, include as much of the following information
as possible:

-   Operating system
-   Python version
-   Printer model
-   Printer firmware version
-   Relevant error message
-   Relevant diagnostic output
-   Steps required to reproduce the problem

Do not include passwords, authentication credentials, or other sensitive
information in issues or diagnostic reports.

See `CONTRIBUTING.md` for additional contribution information.

## Security

K1 Nexus communicates with devices on the local network.

Do not publish Wi-Fi passwords, SSH or root passwords, authentication
credentials, or other sensitive network information in GitHub issues,
screenshots, logs, or diagnostic reports.

Security-related information is available in `SECURITY.md`.

## License

K1 Nexus is released under the MIT License.

See the `LICENSE` file for the full license text.

## Disclaimer

K1 Nexus is an independent open-source project.

Creality and related product names are trademarks of their respective
owners. This project is not affiliated with, sponsored by, endorsed by,
or officially supported by Creality.

3D printers contain moving parts and components that operate at high
temperatures. Remote-control functionality should be used responsibly.
