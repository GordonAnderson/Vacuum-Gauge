# Vacuum Gauge — User Manual

A compact, low-cost digital vacuum gauge that mounts directly on a KF16
flange. It reads pressure from a Posifa MEMS Pirani sensor, shows it on a
round TFT display, and reports it to a host application over USB-C or WiFi.

## Overview

The gauge's enclosure is 3D-printed and serves double duty as the KF16
clamp — there is no separate housing. A single USB-C connector supplies
power and carries the command/data link to host software; the same command
interface is also available wirelessly once the gauge is joined to a WiFi
network. Two buttons on the case let you trim the zero point without a host
connection.

## Specifications

| Parameter | Value |
| --- | --- |
| Pressure sensor | Posifa PVC4101 MEMS Pirani vacuum transducer, factory-calibrated, I2C address `0x50` |
| Pressure range (sensor) | 0.1 mTorr – 760 Torr |
| Accuracy (sensor, factory) | ±15% of reading from 1 mTorr–200 Torr; ±50% of reading above 200 Torr (near atmosphere) or below 1 mTorr — field calibration (see [Calibration](#calibration)) can improve on this for an individual unit, especially near atmosphere |
| Resolution / repeatability | 1 mTorr / ±2% of reading |
| Sensor response time | 250 ms |
| Sensor supply / current | 3.3 Vdc, ~22 mA |
| Sensor operating temp (guaranteed accuracy) | -20 to 65 °C |
| Sensor survival limits (absolute max) | -25 to 85 °C operating / -40 to 90 °C storage |
| Sensor overpressure rating | 27.5 bar absolute (survival limit, not an operating spec) |
| Wetted materials | Epoxy, FR4, glass, nickel, silicon, gold |
| Display | 128×128 round TFT (GC9A01) |
| Controls | 2 tactile buttons (A/B); no other indicators |
| MCU | LILYGO T-QT Pro (ESP32-S3) |
| Power / host interface | USB-C — power and USB serial together, no separate switch or battery |
| Wireless | STA-mode WiFi with TCP command server |
| Vacuum interface | KF16 flange; the gauge's 3D-printed enclosure is the clamp |
| Firmware | Open source, built with [PlatformIO](https://platformio.org/) (this repository) |

> Sensor specs above are from Posifa's PVC4100-series datasheet (model
> PVC4101, Rev A, Dec 2025) — confirmed against the part marking
> "PVC4101 SENSOR 14.65PSI 6SMD". Its I2C address matches this gauge's
> firmware default exactly.

## Safety and Operating Limits

- **Overpressure.** The sensor survives up to 27.5 bar absolute without
  damage — far beyond anything a KF16 system sees even fully vented to
  atmosphere. This is a survival limit, not an operating spec: the gauge is
  for vacuum service only.
- **Temperature.** The sensor's accuracy specs are guaranteed over -20 to
  65 °C. It survives -25 to 85 °C operating / -40 to 90 °C storage without
  damage, but accuracy isn't guaranteed near those extremes. The display and
  electronics haven't been separately characterized at any of these limits.
- **Gas species.** Pirani gauges infer pressure from a gas's thermal
  conductivity, so the reading depends on what gas is actually present. Both
  the factory formula and the field-calibrated table on this gauge are built
  against air/atmosphere — readings for any other gas (helium, hydrogen,
  argon, etc.) will be off unless you calibrate against that specific gas.
  The sensor's wetted materials (epoxy, FR4, glass, nickel, silicon, gold)
  also bound what it can safely see — avoid process gases or vapors that
  attack any of those.
- **KF16 clamp.** The enclosure *is* the clamp. Center the O-ring/centering
  ring before tightening, and inspect the 3D-printed clamp features
  periodically for wear, same as any KF clamp.

## Getting Started

1. Center the KF16 centering ring/O-ring, then mount the gauge using its
   enclosure as the clamp.
2. Connect a USB-C cable from the gauge to the host computer or instrument —
   this is the only connection needed; power comes through the same cable.
3. On power-up the display briefly shows "GAACE", then switches to the live
   pressure readout.
4. With the chamber at atmosphere, the display should settle near 760 Torr
   within a few seconds.

## Reading the Display

The display auto-ranges based on the live reading:

| Reading | Shown as |
| --- | --- |
| Above 100 Torr | Whole Torr (e.g., `432 Torr`) |
| 1–100 Torr | Torr, one decimal (e.g., `18.7 Torr`) |
| Below 1 Torr | Milli-Torr, whole number (e.g., `850 mTorr`) |

**Note:** the buttons switch between coarse and fine zero-offset trim at a
different threshold (10 Torr) than the display switches units (100 Torr / 1
Torr). So between 1 and 10 Torr, the screen still reads in Torr, but the
buttons are already adjusting the fine milli-Torr offset underneath it.

## Button Controls

Each press nudges the active zero offset by a fixed step. Which offset is
active follows the current reading:

- **Above 10 Torr** — coarse trim, ±1 Torr per press
- **At or below 10 Torr** — fine trim, ±10 mTorr per press

| Button | Effect |
| --- | --- |
| A | Increase the active offset |
| B | Decrease the active offset |

Offsets are bounded to ±700 Torr (coarse) / ±10,000 mTorr (fine), and changes
are written to flash automatically within about 10 seconds. They can also be
set precisely from the command interface (`?TOFFSET`, `?MTOFFSET`) instead of
stepping through individual button presses.

## Command Interface

Every command works identically over the USB-C serial connection or the
WiFi/TCP link (see [Wireless Setup](#wireless-setup)). Commands are ASCII
lines; a `?`-prefixed command is a get/set — send `G<name>` to read or
`S<name>,<value>` to set (e.g. `GTOFFSET`, `STOFFSET,5`). Other commands take
their argument inline (e.g. `CALPRES,760`). A successful command replies with
an ACK; an error replies with a NAK (`?`).

### General

| Command | Action |
| --- | --- |
| `GVER` | Return the firmware version string |
| `?NAME` | Get/set the device name (use a unique name per unit) |
| `GPRES` | Return calibrated pressure (Torr) |
| `GRPRES` | Return the last raw pressure counts |
| `GRAW` | Return a fresh **averaged** raw reading (8 samples) |
| `GRTEMP` | Return raw temperature sensor counts |
| `?TOFFSET` | Get/set the coarse Torr offset |
| `?MTOFFSET` | Get/set the fine milli-Torr offset |
| `SAVE` | Save parameters to flash |
| `LOAD` | Load the saved parameters from flash |

### Calibration

| Command | Action |
| --- | --- |
| `?CALMODE` | Conversion mode: `0` = factory formula, `1` = field PWL table |
| `CALPRES,<torr>` | Capture a cal point: average the raw counts now and pair them with `<torr>` |
| `CALDUMP` | List the calibration table (`raw  torr` per line) |
| `CALCLEAR` | Empty the table (to build a new one from scratch) |
| `CALDEF` | Restore the factory-default calibration table |

### WiFi

| Command | Action |
| --- | --- |
| `SSID` / `SSID,<text>` | Get / set the WiFi network name |
| `PASS` / `PASS,<text>` | Get / set the WiFi password (echoed in plaintext) |
| `?WPORT` | Get/set the TCP port for the wireless link (default `23`) |
| `WIFICONN` | Save WiFi settings and (re)connect |
| `WIFI` | Report status: SSID, connected, IP address, port |

## Calibration

The gauge can convert raw sensor counts to Torr two ways, selected with
`?CALMODE`:

- **`0` — factory formula.** A fixed conversion built into the firmware.
  Works out of the box; no setup needed.
- **`1` — field PWL table.** A piece-wise-linear table you build by
  capturing known pressure points. The sensor's factory accuracy spec is
  ±50% of reading above 200 Torr (the firmware calls this its "trend only"
  region) and ±15% below that — calibrating against your own reference
  points, especially near atmosphere, meaningfully tightens this up for an
  individual unit.

The table maps raw sensor counts to Torr by linear interpolation, with
extrapolation along the nearest end segment outside the table's range. Each
unit's sensor differs, so build the table from your own reference points
rather than copying another unit's.

To capture or update points:

1. Switch to the table: `SCALMODE,1` (`SCALMODE,0` reverts to the factory
   formula).
2. Bring the system to a **known** pressure. Atmosphere (`760` Torr) is a
   free anchor; other points need a calibrated reference gauge.
3. Optionally check stability with a few `GRAW` reads.
4. Capture the point: e.g. `CALPRES,760`. The firmware averages 8 raw
   readings and stores `(rawAverage, 760)`.
   - A new point within **100 counts** of an existing one **replaces** it;
     otherwise it's **added**.
   - The table is re-sorted by raw value and saved to flash immediately.
5. Repeat at other known pressures — more points near atmosphere improve
   accuracy there, since the Pirani curve is steepest in that region.

The table holds up to **32 points** and does not enforce monotonicity, so
enter points in a sensible order. Use `CALDUMP` to review the current table,
`CALCLEAR` to start over, or `CALDEF` to restore the factory table.

## Wireless Setup

The gauge joins WiFi in station mode and runs a TCP server, so a host
application sees the same command interface as USB — typically bridged to a
virtual COM port on the host.

### One-time configuration (over USB)

```
SSID,YourNetwork
PASS,YourPassword
WIFICONN
WIFI               # wait for "Connected: TRUE" and note the IP address
NAME,Gauge-A       # give each unit a unique, recognizable name
```

Credentials persist across reboots, so the gauge reconnects automatically.

### Host bridge

The gauge presents a raw TCP socket (default port `23`):

- **macOS / Linux** (`socat`):
  ```
  socat pty,link=/tmp/ttyGauge-A,raw,echo=0 tcp:<gauge-ip>:23
  ```
  Point your application at `/tmp/ttyGauge-A`.
- **Windows:** **HW VSP3** (free GUI, maps a virtual COM port to
  `<gauge-ip>:23`), or `com0com` + `hub4com`.

### Multiple gauges on one host

All gauges can share the same WiFi network and TCP port — each has its own
IP, so they don't conflict.

1. Give each gauge a unique `NAME` and note its IP (`WIFI` over USB).
2. Set a DHCP reservation per gauge on your router so each one keeps the same
   IP (the firmware uses DHCP, not a static address).
3. Run one bridge per gauge on the host, each pointed at that gauge's IP:
   ```
   socat pty,link=/tmp/ttyGauge-A,raw,echo=0 tcp:192.168.1.51:23 &
   socat pty,link=/tmp/ttyGauge-B,raw,echo=0 tcp:192.168.1.52:23 &
   ```

Each gauge accepts one TCP client at a time; a new connection replaces the
previous one.

## Firmware Updates

The firmware is open source and built with PlatformIO — there's no separate
simplified update path; updating means rebuilding and reflashing from source.

1. Install PlatformIO (VS Code extension or the `pio` CLI).
2. Get the firmware source for this gauge (this repository).
3. Connect the gauge via USB-C, and close any program already holding the
   port (Arduino IDE, serial monitor, etc.) — only one program can hold the
   USB serial port at a time, and an upload fails with a "port busy" error
   otherwise.
4. From the project directory:
   ```
   pio run -t upload -t monitor
   ```

## Troubleshooting

- **Reading stuck at 0 Torr / 0 mTorr, even vented to atmosphere.** The
  firmware has no fault indicator for a non-responding sensor — if the I2C
  link to the sensor is broken, the gauge simply reports 0 rather than an
  error. Check the feedthrough wiring/connector before assuming the chamber
  is actually at vacuum.
- **Display blank.** There's no separate power switch or battery, so a blank
  screen almost always means no USB power. Check the cable and host port.
- **WiFi won't connect.** Confirm `SSID`/`PASS` were set and `WIFICONN` was
  sent afterward; query `WIFI` for current status (connected, IP, port).
- **Firmware upload fails with "port busy."** Close any serial monitor or
  other program using the port, then retry.
- **Calibration table full (32 points).** `CALCLEAR` to start fresh, or
  recapture a point within 100 raw counts of an existing one to replace it
  instead of adding a new one.
- **Pressure reads wrong for a non-air gas.** Expected — see
  [Gas species](#safety-and-operating-limits) above; the gauge is calibrated
  against air/atmosphere.

## License

Copyright © GAACE.
