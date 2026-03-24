# Cyclist — Home Assistant Menstrual Cycle Tracker
### Roadmap

A Home Assistant custom component that tracks menstrual cycles and surfaces fertility awareness data at a glance. Designed for avoiding or planning pregnancy using calendar-based predictions.

> **Disclaimer:** This is a personal home automation tool, not a medical device. Calendar-based fertility prediction has ~21% accuracy without additional physiological data. Always combine with other methods for contraception.

---

## Architecture Overview

- **Type:** HA Custom Component (`custom_components/cyclist/`)
- **Setup:** UI-based Config Flow + Options Flow (no YAML required)
- **Storage:** `hass.helpers.storage.Store` (JSON, persisted in `.storage/`)
- **Distribution:** HACS-compatible

### Entities

| Entity | Description |
|---|---|
| `sensor.cyclist_cycle_day` | Current day in cycle (1-based) |
| `sensor.cyclist_phase` | `menstruation` / `follicular` / `ovulation` / `luteal` |
| `sensor.cyclist_fertility` | `fertile` / `low` / `safer` |
| `sensor.cyclist_next_period` | Days until predicted next period |
| `binary_sensor.cyclist_period_active` | `on` while period is ongoing |
| `calendar.cyclist` | Predicted periods + fertile windows (3 months ahead) |

### Services

| Service | Description |
|---|---|
| `cyclist.log_period_start` | Mark period start — accepts optional `date:` for backdating |
| `cyclist.update_settings` | Update cycle length and/or period duration at any time |

### Settings (configurable via UI Options or `update_settings` service)

| Setting | Default | Description |
|---|---|---|
| `cycle_length` | `28` | Days between period starts (full cycle length) |
| `period_duration` | `5` | Days a period typically lasts |

---

## Core Design Decisions

**No history required.** The only factual data point we need is "when did the last period start?" Everything else is derived from the two user-configured settings. There is no backfilling, no import of past cycles. If the last period start date isn't known, the integration runs in "estimated" mode using settings alone.

**Backdating period start.** Life doesn't always get logged in real time. `log_period_start` accepts an optional `date:` parameter so a period that started 1–2 days ago can be recorded accurately. Defaults to today if omitted.

**Settings over statistics.** Cycle length and period duration are explicitly set by the user — not computed from history. These are the authoritative values. A future optional rolling-average feature could supplement them, but user intent wins.

**Fertility labels:** `fertile` / `low` / `safer` — never "safe", which implies a certainty the method does not provide.

---

## Milestones

### M1 — Foundation
*Goal: Project skeleton, data storage, and core cycle math*

- [ ] `manifest.json` — domain, version, HA min version, iot_class: local_push
- [ ] `const.py` — DOMAIN, storage key, phase/fertility constants
- [ ] `strings.json` — UI strings for config flow and options flow
- [ ] `config_flow.py`:
  - Initial setup: enter `cycle_length` (default 28) and `period_duration` (default 5)
  - Options flow: update either setting after setup
- [ ] Storage layer — `Store` wrapper with async load/save:
  ```json
  {
    "version": 1,
    "last_period_start": "2026-03-10",
    "settings": {
      "cycle_length": 28,
      "period_duration": 5
    }
  }
  ```
- [ ] `cycle_math.py` — Pure Python, no HA dependencies:
  - Current cycle day: `(today - last_period_start).days + 1`
  - Period active: cycle day ≤ period_duration
  - Predicted ovulation day: `cycle_length - 14` (from cycle start)
  - Fertile window: day `(cycle_length - 18)` → day `(cycle_length - 11)`
  - Fertility buffer: ±2 days outside fertile window = `low`; else `safer`
  - Phase detection:
    - `menstruation`: days 1 → period_duration
    - `follicular`: period_duration+1 → fertile_window_start-1
    - `ovulation`: fertile_window center ±2 days
    - `luteal`: fertile_window_end+1 → cycle_length
  - Next period date: `last_period_start + cycle_length`
  - Days until next period: `next_period_date - today`

### M2 — Sensors
*Goal: Live entities reflecting current cycle state*

- [ ] `sensor.py`:
  - `CycleDaySensor` — current day number, unit: "day"
  - `CyclePhaseSensor` — phase string
  - `FertilitySensor` — `fertile` / `low` / `safer`
  - `NextPeriodSensor` — days remaining, unit: "days"
- [ ] `binary_sensor.py`:
  - `PeriodActiveSensor` — on while cycle_day ≤ period_duration
- [ ] All entities re-evaluate when storage changes
- [ ] When `last_period_start` is not set, all sensors return `unknown` with an attribute `status: "no data — call cyclist.log_period_start"`

### M3 — Services
*Goal: Log and adjust cycle data*

- [ ] `log_period_start`:
  - Optional `date:` field (YYYY-MM-DD), defaults to today
  - Accepts past dates — designed for "she told me it started yesterday"
  - Validates date is not in the future
  - Saves as `last_period_start`, triggers entity refresh
- [ ] `update_settings`:
  - Optional `cycle_length:` (integer, 15–60)
  - Optional `period_duration:` (integer, 1–14)
  - Updates storage, triggers entity refresh
- [ ] `services.yaml` — field definitions, descriptions, and input validation

### M4 — Calendar
*Goal: Forward-looking predictions visible in HA Calendar view*

- [ ] `calendar.py` — `CalendarEntity` implementation
- [ ] Generate events 3 months ahead per predicted cycle:
  - **Period** event: `last_period_start + (N * cycle_length)` for N = 0, 1, 2, 3
  - **Fertile window** event: period start + fertile window days
  - Event descriptions note that predictions are estimates
- [ ] Recalculates on storage change

### M5 — Dashboard & Documentation
*Goal: Ready-to-use dashboard config and clear setup guide*

- [ ] `lovelace_example.yaml`:
  - Entities card with all sensors + binary sensor
  - Gauge card: cycle day progress (1 → cycle_length)
  - Calendar card pointed at `calendar.cyclist`
- [ ] `README.md`:
  - Manual installation and HACS installation
  - First-use: set cycle_length, set period_duration, call log_period_start
  - How to backdate: `cyclist.log_period_start` with `date: "2026-03-22"`
  - Automation examples: notify when fertile window opens, notify 3 days before next period
- [ ] Automation blueprint: fertile window start/end notifications

### M6 — Polish & Testing
*Goal: Robust edge case handling and test coverage*

- [ ] `hacs.json` — HACS manifest
- [ ] `tests/test_cycle_math.py` — pytest suite:
  - Standard 28-day cycle, day 1 / mid-cycle / last day
  - Short cycles (21 days), long cycles (35 days)
  - Very short periods (2 days) and long periods (7 days)
  - Ovulation at non-day-14 positions
  - Backdated period start (set 2 days ago)
  - `last_period_start` not set (no data state)
  - Day exactly on fertile window boundary
- [ ] Edge cases:
  - `last_period_start` in the future — reject with clear error
  - `cycle_length` shorter than `period_duration` — validate and reject
  - Cycle day exceeds `cycle_length` (overdue) — clamp and flag

---

## Algorithm Reference

All predictions use the user-configured `cycle_length` and `period_duration`. No historical averaging.

```
fertile_window_start = cycle_length - 18
fertile_window_end   = cycle_length - 11
ovulation_estimate   = cycle_length - 14   (informational only)

low_zone_start = fertile_window_start - 2
low_zone_end   = fertile_window_end + 2

fertility(day):
  if low_zone_start <= day <= low_zone_end:
    if fertile_window_start <= day <= fertile_window_end:
      return "fertile"
    return "low"
  return "safer"
```

For a 28-day cycle: fertile window = days 10–17, low zone = days 8–19, safer = days 1–7 and 20–28.

---

## Future Ideas (Not Planned)

- BBT (basal body temperature) sensor integration for improved accuracy
- LH surge test result logging
- Symptom tracking (mood, energy, cramps)
- Optional rolling average to nudge `cycle_length` over time
- Multi-person support via multiple config entries
