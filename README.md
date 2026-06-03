# Vacuum Gauge

Firmware for a digital vacuum pressure gauge built around a **Posifa** I2C
pressure sensor and a **LILYGO T-QT Pro (ESP32-S3)** with a 128 × 128 GC9A01
TFT display. The gauge reads the sensor, auto-ranges the pressure between Torr
and milli-Torr, shows it on the TFT, and exposes a command interface (over USB
serial **and** WiFi/TCP) for configuration, calibration, and data readout.

## Features

- Periodic sensor reads (every 500 ms) with conversion of raw counts to Torr.
- Auto-ranging display: whole Torr, tenths of a Torr, or mTorr depending on the
  reading.
- User-trimmable zero offsets — a coarse **Torr** offset and a fine **mTorr**
  offset — adjustable from the two on-board buttons or over the command interface.
- **Two pressure-conversion modes:** the built-in factory formula, or an
  optional **piece-wise-linear (PWL) calibration table** that is field-editable
  over the command interface.
- **Wireless command link:** STA-mode WiFi with a TCP server, exposed as a second
  command stream so every command works identically over USB or the network.
- Settings (offsets, calibration mode + table, WiFi credentials) persisted to
  SPIFFS and reloaded on boot; auto-saved when changed.

## Hardware

| Component        | Detail                                            |
| ---------------- | ------------------------------------------------- |
| MCU board        | LILYGO T-QT Pro (ESP32-S3)                         |
| Display          | 128 × 128 GC9A01 TFT (via TFT_eSPI)               |
| Sensor           | Posifa pressure sensor, I2C address `0x50`        |
| I2C pins         | SDA = GPIO 43, SCL = GPIO 44 @ 100 kHz            |
| Buttons          | Button A = GPIO 0, Button B = GPIO 47             |
| Wireless         | ESP32-S3 WiFi (BLE-capable; **no Bluetooth Classic**) |

### Button behavior

Each button press nudges the active zero offset. Which trim is adjusted follows
the current reading range (coarse Torr above ~10 Torr, fine mTorr below):

- **Button A** — increase offset (+1 Torr or +10 mTorr)
- **Button B** — decrease offset (−1 Torr or −10 mTorr)

## Command interface

Commands are ASCII lines, accepted identically over USB serial or the WiFi/TCP
link. A `?`-prefixed command is a get/set: send `G<name>` to read or
`S<name>,<value>` to set (e.g. `GTOFFSET`, `STOFFSET,5`). Other commands take
their argument inline (e.g. `CALPRES,760`). Successful commands reply with an
ACK; errors reply with a NAK (`?`).

### General

| Command     | Action                                            |
| ----------- | ------------------------------------------------- |
| `GVER`      | Return the firmware version string                |
| `?NAME`     | Get/set the device name (use a unique name per unit) |
| `GPRES`     | Return calibrated pressure (Torr)                 |
| `GRPRES`    | Return the last raw pressure counts               |
| `GRAW`      | Return a fresh **averaged** raw reading (8 samples)|
| `GRTEMP`    | Return raw temperature sensor counts              |
| `?TOFFSET`  | Get/set the coarse Torr offset                    |
| `?MTOFFSET` | Get/set the fine milli-Torr offset                |
| `SAVE`      | Save parameters to flash                          |
| `LOAD`      | Load the saved parameters from flash              |

### Calibration

| Command          | Action                                                    |
| ---------------- | --------------------------------------------------------- |
| `?CALMODE`       | Conversion mode: `0` = factory formula, `1` = PWL table   |
| `CALPRES,<torr>` | Capture a cal point: average the raw counts now and pair them with `<torr>` |
| `CALDUMP`        | List the calibration table (`raw  torr` per line)         |
| `CALCLEAR`       | Empty the table (to build a new one from scratch)         |
| `CALDEF`         | Restore the factory-default calibration table             |

### WiFi

| Command          | Action                                                    |
| ---------------- | --------------------------------------------------------- |
| `SSID` / `SSID,<text>` | Get / set the WiFi network name                     |
| `PASS` / `PASS,<text>` | Get / set the WiFi password (echoed in plaintext)   |
| `?WPORT`         | Get/set the TCP port for the wireless link (default `23`) |
| `WIFICONN`       | Save WiFi settings and (re)connect                        |
| `WIFI`           | Report status: SSID, connected, IP address, port          |

## Calibration procedure (PWL table)

The PWL table maps the raw sensor count (`GRAW`/`GRPRES`) to pressure in Torr by
linear interpolation. Each unit's sensor differs, so the table can be rebuilt in
the field. Readings outside the table's range are extrapolated along the nearest
end segment.

To capture or update points:

1. Enable the table: `SCALMODE,1` (use `SCALMODE,0` to revert to the factory formula).
2. Bring the system to a **known** pressure. Atmosphere (`760` Torr) is a free
   anchor; other points need a reference gauge.
3. (Optional) Check stability with `GRAW` a few times.
4. Capture the point: e.g. `CALPRES,760`. The firmware averages 8 raw readings
   and stores `(rawAverage, 760)`.
   - If the new raw value is within **100 counts** of an existing point, that
     point is **replaced**; otherwise a new point is **added**.
   - The table is kept sorted by raw value and saved to flash immediately.
5. Repeat at other known pressures. Use `CALDUMP` to review, `CALCLEAR` to start
   over, or `CALDEF` to restore the factory table.

Notes:

- The table holds up to **32 points**. Monotonicity is not enforced — entering
  inconsistent points will produce a poor curve, so build it in a sensible order.
- More points where the sensor curve is steep (near atmosphere) improve accuracy.

## Wireless setup (WiFi → virtual COM port)

The gauge joins your WiFi in **station (STA) mode** and runs a TCP server. On the
host, a TCP↔virtual-serial bridge exposes each gauge as a COM port, so existing
serial applications connect to it like any wired device.

### One-time configuration (over USB)

```
SSID,YourNetwork
PASS,YourPassword
WIFICONN
WIFI               # wait for "Connected: TRUE" and note the IP address
NAME,Gauge-A       # give each unit a unique, recognizable name
```

Credentials persist, so the gauge auto-connects on every subsequent boot.

### Host bridge

The gauge presents a raw TCP socket (default port `23`). Bridge it to a virtual
serial port:

- **macOS / Linux** (`socat`):
  ```
  socat pty,link=/tmp/ttyGauge-A,raw,echo=0 tcp:<gauge-ip>:23
  ```
  Your application then opens `/tmp/ttyGauge-A`.

- **Windows:** use **HW VSP3** (free GUI — create a virtual COM mapped to
  `<gauge-ip>:23`), or `com0com` + `hub4com`.

### Multiple devices on one host

All gauges can run on the **same WiFi and the same TCP port (23)** — each has its
own IP address, so they don't conflict. To manage several units:

1. Give each a unique `NAME` and note its IP (`WIFI` over USB).
2. Recommended: set a **DHCP reservation** per unit on your router so each gauge
   always gets the same IP. (The firmware uses DHCP; it does not set a static IP.)
3. On the host, run **one bridge per device**, each pointing at that device's IP
   and mapping to its own virtual COM port. For example, on macOS:
   ```
   socat pty,link=/tmp/ttyGauge-A,raw,echo=0 tcp:192.168.1.51:23 &
   socat pty,link=/tmp/ttyGauge-B,raw,echo=0 tcp:192.168.1.52:23 &
   ```
   On Windows, create one HW VSP3 mapping per gauge (e.g. COM10→.51, COM11→.52).

Each gauge accepts **one TCP client at a time**; a new connection replaces the
previous one.

## Building

This is a [PlatformIO](https://platformio.org/) project targeting the
`espressif32` platform with the Arduino framework.

```bash
# Build
pio run

# Build, upload, and open the serial monitor
pio run -t upload -t monitor
```

> **Flashing tip:** only one program can hold the USB serial port at a time.
> Close any open serial monitor (Arduino IDE / VSCode / `pio device monitor`)
> before uploading, or the upload fails with a "port busy" error.

The required libraries are vendored under [`lib/`](lib/) so the build is
self-contained:

- **GAACE** — command processor, debug, button, ring buffer, char allocator
- **arduino-timer** — lightweight periodic task scheduler
- **TFT_eSPI** — display driver, pre-configured for the LilyGo T-QT Pro S3
  (`Setup211_LilyGo_T_QT_Pro_S3.h`, with `USE_HSPI_PORT` set for the ESP32-S3)

Because these are vendored snapshots, upstream library updates won't flow in
automatically — update the copies in `lib/` if you need newer versions.

## Project layout

```
.
├── platformio.ini         PlatformIO environment (board: lilygo-t3-s3)
├── src/VacuumGauge.cpp     Application firmware
├── include/VacuumGauge.h   Function prototypes
└── lib/                    Vendored libraries (GAACE, arduino-timer, TFT_eSPI)
```

## License

Copyright © GAACE.
