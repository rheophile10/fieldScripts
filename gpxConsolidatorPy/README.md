# GPX Track and Waypoint Consolidator

python utility for combining and filtering GPX files from multiple sources.

## Overview

This tool efficiently consolidates tracks and waypoints from multiple GPX files into a single output file. It's particularly useful for:

- Combining GPS data from multiple devices or recording sessions
- Filtering tracks by specific date and time ranges
- Organizing and managing large collections of GPX files
- Preserving all waypoint data while avoiding naming conflicts

## Project Structure

```
.
├── consolidator.py      # Main script
├── README.md            # This documentation
└── gpx_files/           # Default directory for input GPX files (created automatically)
```

## Usage

```
python consolidator.py [-h] [-i INPUT] [-o OUTPUT] [--rename] [--tracks-only] 
                       [--waypoints-only] [--filter-date FILTER_DATE]
                       [--start-time START_TIME] [--end-time END_TIME]
                       [--no-time-filter]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `-i`, `--input` | Directory containing GPX files | `./gpx_files` |
| `-o`, `--output` | Output file path | `./consolidated_gpx.gpx` |
| `--rename` | Always rename elements with source filename | False |
| `--tracks-only` | Process only tracks, ignore waypoints | False |
| `--waypoints-only` | Process only waypoints, ignore tracks | False |
| `--filter-date` | Filter to include points from this date (YYYY-MM-DD) | Today |
| `--start-time` | Filter to include points after this time (HH:MM) | 06:00 |
| `--end-time` | Filter to include points before this time (HH:MM) | 20:00 |
| `--no-time-filter` | Disable time filtering of track points | False |

## Example Commands

### Basic usage (default directory)

```bash
python consolidator.py
```

### Combine files from a specific directory

```bash
python consolidator.py -i ./my_gpx_files -o combined.gpx
```

### Filter by specific dates

```bash
python consolidator.py -i Apr_5 -o Apr05_Combined.gpx --filter-date 2025-04-05
python consolidator.py -i Apr_6 -o Apr06_Combined.gpx --filter-date 2025-04-06
python consolidator.py -i Apr_7 -o Apr07_Combined.gpx --filter-date 2025-04-07
python consolidator.py -i Apr_8 -o Apr08_Combined.gpx --filter-date 2025-04-08
python consolidator.py -i Apr_9 -o Apr09_Combined.gpx --filter-date 2025-04-09
```

### Filter by time range

```bash
# Only include track points between 8:00 and 17:00
python consolidator.py --start-time 08:00 --end-time 17:00
```

### Process only tracks or waypoints

```bash
# Only process tracks, ignore waypoints
python consolidator.py --tracks-only

# Only process waypoints, ignore tracks
python consolidator.py --waypoints-only
```

### Force renaming all elements

```bash
# Rename all elements with source filename for better organization
python consolidator.py --rename
```
