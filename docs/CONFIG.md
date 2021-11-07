# Configuration Management in livesectional

The original design allows for multiple different hardware configurations, airport usage heatmaps, neighboring livesectional devices, LED assignments etc.

Configuration management for these should be predictavle

## Airports: airport data file
This is a mapping of LED positions to purpose, where the purpose is either
- Airport ICAO code
- Used for Map LEGEND ( LGND )
- Turned off ( NULL )

Associating an purpose with an LED is positional
- first line in file goes to LED0
- second line in file goes to LED1 etc.

This data set is strongly coupled with the LED configuration and physical layout. It's likely to be defined once for a specific map build, and is then unlikely to change again.

Might be helpful to have a 'lock', 'unlock' configuration management flag - to prevent inadvertent changing of this data once set. Perhaps the airport listing UI initiates in a read-only mode, with an explicit action to go RW

## Hardware configuration data
Hardware Configuration data is likely to be build specific and unlikely to change over time.

### Hardware configuration includes
- LED Data
 - LED strings size
 - LED type RGB / GRB
- OLED Devices Available
- Switches Available
- Light Sensor

### Connectivity
Manage connectivity information
There are two set of problems in this space
- Initial local configuration setup to get onto a network
- Specific network local setup configuration

This space has a bootstrap problem for initial setup - which might need it's own specific solution

### External Data Sources
There are a number of external data sources used for map, airport and weather data.

For external data sources ; do we need to configure a web proxy option ?

For each data source we need
- Source details (URL)
- Source update frequency
- Should we cache the data and possibly use stale versions ?
 - Should cached data be persistent ?

### Display Configuration
Color Sets
 - Master Color Mode
  - Day / Night
  - Bright / Dimmed
  - Light Mode / Dark Mode -- perhaps
 - Wx Conditions - VFR, MVFR, IFR, LIFR
 - Wx Details
  - Lightning
  - Snow
  - Rain
  - Freezing Rain
  - Dust/Ash
  - Fog
  - Missing Data
Timing Data
 - Daily Schedule


## Device Reset
We need some mechanisms to reset the configuration to some set of defaults
- Hardware setup is unlikely to change between resets
- Log files that contain local user data should be purged

## Operating System upgrades
Full OS upgrades seem to be outside the scope of any of this
Critical security patching may be taken care of at the OS package management level
