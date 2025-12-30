# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LiveSectional is a Raspberry Pi-based aviation weather visualization system that displays real-time METAR weather data on an LED map. The system uses WS281x RGB LEDs to show flight categories (VFR, MVFR, IFR, LIFR) with color-coded indicators. It includes a Flask web application for configuration and supports optional OLED/LCD displays for detailed weather information.

**Current Version:** v4.600 (Python 3.7+)
**Target Platform:** Raspberry Pi running Raspbian/Raspberry Pi OS
**Installation Path:** /NeoSectional/

## Core Architecture

### Multi-Process Design

The system runs three concurrent processes managed by `startup.py`:

1. **metar-v4.py** - Main METAR data fetching and LED control
2. **metar-display-v4.py** - OLED/LCD display updates (if displays are configured)
3. **check-display.py** - Watchdog process for display monitoring

These processes are started using Python threading and run continuously, updating at intervals defined in `config.py`.

### Data Flow

```
FAA Aviation Weather API (v2)
    ↓
metar-v4.py (fetches METAR/TAF/MOS data)
    ↓
LED Control (rpi_ws281x library)
    ↓
WS281x LED Strip (flight category visualization)

    AND

metar-display-v4.py (parallel process)
    ↓
OLED/LCD displays (detailed weather info)
```

### Key Components

- **webapp.py** - Flask web server (port 5000) providing configuration UI with three editors:
  - Settings Editor (config.py)
  - Airports Editor (airports file)
  - Heat Map Editor (hmdata file - tracks visited airports)

- **config.py** - User configuration file with 160+ settings including LED colors, update intervals, display settings, wipe animations

- **airports** file - Newline-separated list of airport IDs (up to 3000), one per LED position

- **admin.py** - Administrative settings (version, map name, MOS usage)

## FAA API Integration

**IMPORTANT:** As of September 2025, this codebase uses the **FAA Aviation Weather API v2**. The API endpoints are:

- Station Info: `https://aviationweather.gov/api/data/stationinfo?format=xml&ids=`
- METAR Data: `https://aviationweather.gov/api/data/metar?format=xml&hours=2.5&ids=`

**API Limitation:** Maximum 300 airports per request. The code uses `islice()` to batch requests for maps with >300 airports (see `get_apinfo()` and `get_led_map_info()` in webapp.py).

## Common Development Commands

### Running the Application

```bash
# Start the web interface only
sudo python3 webapp.py

# Start the full map system (LEDs + displays)
sudo python3 startup.py run

# Turn off the map
sudo python3 shutoff.py
```

### Testing Hardware

```bash
# Test LED strip
sudo python3 testled.py

# Test OLED displays
sudo python3 testoled.py
```

### Installing Dependencies

```bash
# Install all requirements
sudo pip3 install -r requirements.txt
```

### Configuration File Locations

- Main config: `/NeoSectional/config.py` (or `./config.py` in dev)
- Airports: `/NeoSectional/airports`
- Heat Map: `/NeoSectional/hmdata`
- Logfile: `/NeoSectional/logfile.log`
- Backup config: `/NeoSectional/config-bkup.py`

## Hardware Integration

### LED Control

Uses `rpi_ws281x` library with these default settings:
- GPIO Pin: 18 (PWM)
- LED Count: Defined in config.py (max 3000)
- Frequency: 800kHz
- DMA Channel: 5
- Supports both RGB and GRB LED encodings

### Display Support

- **OLED:** SSD1306 displays via I2C (up to 8 displays)
- **LCD:** 16x2 character displays via RPLCD library
- Configuration in `config.py`: `displayused`, `oledused`, `lcddisplay`, `numofdisplays`

### GPIO Features

- Rotary switch support (for data type selection: METAR/TAF/MOS/Heat Map)
- Pushbutton support (power, data refresh, sleep override)
- Ambient light sensor (for LED dimming)
- Legend LEDs (separate LEDs showing color key)

## Color Coding System

Flight categories follow standard aviation weather colors:
- **VFR** (Visual Flight Rules): Green - `(0, 255, 0)`
- **MVFR** (Marginal VFR): Blue - `(0, 0, 255)`
- **IFR** (Instrument Flight Rules): Red - `(255, 0, 0)`
- **LIFR** (Low IFR): Magenta - `(255, 0, 255)`
- **No Weather**: Gray - `(80, 80, 80)`

Additional weather indicators:
- Lightning: Yellow blink
- High Winds: LED blink
- Precipitation: Alternating colors (rain, snow, freezing rain, etc.)

## Transitional Wipes

The system includes visual "wipe" animations during weather data updates. Configured in `wipes-v4.py`, options include:
- Rainbow, Fade, Shuffle, Radar, Circle, Square, Up/Down, Morse Code, Rabbit Chase, Checker

Settings: `num_<wipename>` determines how many times to run each wipe type.

## Web Interface Architecture

Flask routes are organized by function:
- `/` or `/index` - Homepage
- `/confedit` - Settings editor
- `/apedit` - Airports editor
- `/hmedit` - Heat Map editor
- `/led_map` - Visual map layout using Folium
- `/lsremote` - Mobile-friendly remote control
- `/tzset` - Timezone configuration
- `/expandfs` - Filesystem expansion utility

The web interface uses:
- Flask with Jinja2 templates
- Bootstrap CSS framework (via templates)
- HTML5 color pickers for RGB color selection
- Folium for interactive map visualization

## Logging

Uses `logzero` library with rotating log files:
- Location: `/NeoSectional/logfile.log`
- Max size: 1MB per file
- Backup count: 1 rotation
- Log levels: DEBUG, INFO, WARNING, ERROR (set via `config.loglevel`)

## File Organization

```
/NeoSectional/
├── webapp.py              # Flask web server
├── startup.py             # Multi-process launcher
├── metar-v4.py            # Main METAR/LED logic
├── metar-display-v4.py    # Display update logic
├── check-display.py       # Display watchdog
├── wipes-v4.py            # LED animation effects
├── config.py              # User settings (generated by web UI)
├── admin.py               # Admin settings
├── airports               # Airport list file
├── hmdata                 # Heat map data
├── templates/             # Flask HTML templates
├── static/                # CSS, JavaScript, images
└── profiles/              # Pre-configured config templates
```

## Python Version & Dependencies

**Python 3.7+** required. Key dependencies:
- `Flask` - Web framework
- `rpi_ws281x` - LED control (replaces deprecated neopixel)
- `adafruit-circuitpython-ssd1306` - OLED displays
- `RPLCD` - LCD displays
- `folium` - Interactive maps
- `logzero` - Logging
- `requests` - HTTP requests
- `beautifulsoup4`, `lxml` - XML parsing

## Important Notes for Development

### Configuration Changes
When modifying `config.py` through code, use the `readconf()` and `writeconf()` functions in `webapp.py` to maintain proper formatting. The web interface handles RGB-to-hex conversion for color pickers.

### API Request Batching
For maps with >300 airports, always use the batching pattern with `islice()` as shown in `get_apinfo()` (webapp.py:1676-1730). The FAA API will fail if too many airports are requested in a single call.

### LED Indexing
Airport positions in the `airports` file directly correspond to LED positions (0-indexed). The first airport listed controls LED 0, second controls LED 1, etc.

### Process Management
The map can be controlled via web routes or system commands. Always use proper process cleanup when stopping the map (see `/shutdown1` route in webapp.py).

### Testing Without Hardware
The codebase expects Raspberry Pi GPIO hardware. Running on non-RPi systems will fail during LED/display initialization. For development on other platforms, you'll need to mock the hardware libraries.

### Heat Map Feature
Tracks which airports have been visited (landed at). Data stored in `hmdata` file as `AIRPORT_ID count` pairs. This feature is purely cosmetic and doesn't affect weather display.

### Critical FAA API Error Handling (Fixed in v4.600+)
**Previous Bug:** Earlier versions had infinite retry loops when fetching weather data. If any airport in the final chunk returned an HTTP 204 (No Content) or other error, the system would retry forever and never display weather data, even for airports that returned successful data.

**Current Implementation:** The code now includes smart retry logic:
- **HTTP 204 (No Content):** Immediate skip - this is valid, means no weather data available
- **Empty XML Response** (`no element found`): Only retry 2 times, then move on (20 seconds max)
- **Network/Timeout Errors:** Retry up to 10 times (100 seconds max)
- **Graceful degradation:** Continues processing with available data if some airports fail
- **Better logging:** Shows retry attempts, error types, and specific HTTP error codes

**Impact:** Before fix, KWLD returning empty XML caused 100+ second hang and no weather display. Now it retries twice (20 seconds) then continues, displaying weather for all other airports.
