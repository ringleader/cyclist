# Cyclist — Home Assistant Menstrual Cycle Tracker

A Home Assistant custom component that tracks menstrual cycles and surfaces fertility awareness data at a glance. Designed for avoiding or planning pregnancy using calendar-based predictions.

> **Disclaimer:** This is a personal home automation tool, not a medical device. Calendar-based fertility prediction has ~21% accuracy without additional physiological data. Always combine with other methods for contraception.

## Installation

### HACS
1. Open HACS
2. Add this repository as a Custom Repository (Integration)
3. Install Cyclist
4. Restart Home Assistant

### Manual
1. Copy the `custom_components/cyclist` folder to your `<config_dir>/custom_components/` directory.
2. Restart Home Assistant.

## Setup

1. Go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for "Cyclist".
3. Enter your typical Cycle Length and Period Duration.
4. **Important:** After setup, call the `cyclist.log_period_start` service to set the start date of your last period. Without this, sensors will show "unknown".

## Entities

- `sensor.cyclist_cycle_day`: Current day in cycle (1-based)
- `sensor.cyclist_phase`: Phase (menstruation, follicular, ovulation, luteal)
- `sensor.cyclist_fertility`: Fertility status (fertile, low, safer)
- `sensor.cyclist_next_period`: Days until predicted next period
- `binary_sensor.cyclist_period_active`: On while period is ongoing
- `calendar.cyclist_predictions`: Predicted periods + fertile windows (3 months ahead)

## Services

### `cyclist.log_period_start`
Mark period start. Accepts an optional `date:` parameter (YYYY-MM-DD) for backdating if you forgot to log it on the exact day.

### `cyclist.update_settings`
Update your configured `cycle_length` and/or `period_duration` at any time.
